---
name: instagram-reel-publish
description: Publish a finished MP4 to Instagram as a Reel using instagrapi via the contentgen Python venv. Reads IG credentials from Infisical (folder `contentgen`, secrets `IG_USERNAME` / `IG_PASSWORD`) via the iex wrapper — never hardcode creds. Wraps `lib/platforms/instagram_upload.py` in `~/Documents/insta_ai_vid` and the persistent `.instagram_session.json`. Use when the user says "upload to Instagram", "post the reel", "ship to IG", "publish the reel", "post to insta", "drop on Instagram", "upload reel.mp4", or any variant of pushing a finished video to the @aisarva_ Instagram account. Covers pre-upload validation (1080×1920, H.264, AAC, 3–90s), caption JSON format, cover thumbnail, post-publish caption edit, deletion, session expiry, and rate-limit handling.
tier: general
tags: [instagram, publishing, instagrapi, contentgen, reel, infisical]
version: 1
---

# instagram-reel-publish

End-to-end recipe for posting a finished reel to Instagram from the Mac Mini. Lives next to the **contentgen** project (`~/Documents/insta_ai_vid/`) which already owns the venv, the `lib/platforms/instagram_upload.py` script, and a long-lived `.instagram_session.json`.

## Where the pieces live

| Thing | Path |
|---|---|
| Upload script | `~/Documents/insta_ai_vid/lib/platforms/instagram_upload.py` |
| Delete script | `~/Documents/insta_ai_vid/lib/platforms/instagram_delete.py` |
| Session cache | `~/Documents/insta_ai_vid/.instagram_session.json` (auto-managed; safe to delete on stale-session errors) |
| Creds source | Infisical folder `contentgen` → secrets `IG_USERNAME`, `IG_PASSWORD` |
| Creds wrapper | `iex contentgen --` (defined in `/opt/homebrew/bin/iex`) auto-injects both env vars |
| Python venv | The `iex contentgen` wrapper runs `python3` against the contentgen venv |

**Hard rule:** never paste IG creds into a script, never commit `.env` copies, never `--username/--password` on the CLI. Always go through `iex contentgen --`.

## Account in scope

`@aisarva_` — the only Instagram account this skill knows about. If a different IG account is needed, add a new Infisical folder + new wrapper alias before extending this skill.

## Pre-upload validation (run every time)

Instagram silently rejects reels that fail format checks. Validate **before** wasting an upload attempt:

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,duration \
  -of default=noprint_wrappers=1 "$VIDEO"
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels \
  -of default=noprint_wrappers=1 "$VIDEO"
```

Required for IG Reels:

| Field | Required value |
|---|---|
| codec (video) | `h264` |
| pixel format | `yuv420p` (8-bit) |
| resolution | `1080×1920` (9:16) — IG will re-encode anything else, often badly |
| framerate | 23.976–60 (30 is the safe default) |
| duration | 3s ≤ d — IG Reels accept up to ~180s (verified: a 115s reel posted fine). `validate_reel.sh` still warns >90s as conservative; safe to ignore up to ~3min. |
| codec (audio) | `aac` (silent track is fine, see below) |
| audio | MUST exist — IG rejects video-only mp4 |
| container | `.mp4` with `+faststart` (`-movflags +faststart`) |

If your video is silent (e.g. ffmpeg-assembled Ken Burns reel), add a null AAC track:

```bash
ffmpeg -y -i reel_silent.mp4 -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" \
  -shortest -c:v copy -c:a aac -b:a 128k -movflags +faststart \
  reel.mp4
```

The bundled `scripts/validate_reel.sh` does all the above checks and prints OK/FAIL per field.

## Caption JSON format

The script accepts `--caption-file <path>` pointing at a JSON like:

```json
{
  "story_slug": "2026-05-21-deepam-podupu-kadha",
  "logline": "పొడుపు కథ: ఇల్లంతా వెలుగు, బల్లకింద చీకటి. ఇది ఏమిటి? 💡",
  "hashtags": [
    "#Telugu",
    "#TeluguRiddles",
    "#PodupuKathalu",
    "#Deepam",
    "#FolkRiddle"
  ],
  "music_credit": "(internal-only — never shown to viewers)"
}
```

`build_caption()` in `instagram_upload.py` (current behavior):
- Concatenates `logline` + blank line + `hashtags` (one per line).
- **Drops `story_slug` and `music_credit`** — those are internal metadata.

If you need a custom caption shape, pass `--caption "<full string>"` instead. The bundled `references/caption_template.json` has copy-paste skeletons for: Telugu reels (logline-first), English reels, hashtag-heavy growth caption.

## Cover thumbnail

Optional. Pass `--cover <path>.jpg|.png` — should be 1080×1920. Defaults to the first frame of the video (auto-extracted by instagrapi). For Telugu / non-Latin content prefer a hand-picked frame with the readable hook text — IG's thumbnail picker often lands on a low-contrast moment.

```bash
# Extract a sharp frame at second 2 as thumb
ffmpeg -y -ss 2 -i reel.mp4 -frames:v 1 -q:v 2 cover.jpg
```

## Canonical upload command

```bash
cd ~/Documents/insta_ai_vid
iex contentgen -- .venv/bin/python3 lib/platforms/instagram_upload.py \
  --video <path>/reel.mp4 \
  --caption-file <path>/caption.json \
  --cover <path>/cover.jpg
```

> **Use `.venv/bin/python3`, NOT bare `python3`.** `iex contentgen` injects the IG creds but resolves `python3` to `/opt/homebrew/bin/python3` (system), which lacks `instagrapi` → `ModuleNotFoundError: No module named 'instagrapi'`. The deps live in `~/Documents/insta_ai_vid/.venv`; call that interpreter explicitly. (`iex` injects secrets only; it does not activate the venv.)

On success the script prints:

```
Uploaded! media_id=389XXXXXXXXXXXXXXXX
URL: https://www.instagram.com/reel/<code>/
```

`media_id` is the canonical handle — save it. The `/reel/<code>/` URL is what you share. Both work with `media_edit` and `media_delete` later.

## Editing a posted caption (no re-upload)

If the caption was wrong, fix it in-place — no need to delete + re-upload:

```bash
cd ~/Documents/insta_ai_vid
iex contentgen -- python3 -c "
import os
from instagrapi import Client
from pathlib import Path
cl = Client()
cl.load_settings(Path('.instagram_session.json'))
cl.login(os.environ['IG_USERNAME'], os.environ['IG_PASSWORD'])
cl.media_edit('<media_id>', caption='<new full caption>')
print('caption updated')
"
```

`<media_id>` is the numeric `media_id` printed by upload (NOT the URL `<code>`).

## Deleting a posted reel

```bash
cd ~/Documents/insta_ai_vid
iex contentgen -- python3 lib/platforms/instagram_delete.py --media-id <media_id>
```

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `LoginRequired` / `ChallengeRequired` | Session stale or new device alert | Delete `.instagram_session.json` and retry; if challenge persists, log in via IG mobile app once to clear, then retry |
| `ClientError: feedback_required` | Soft ban from too-rapid posting | Wait 30–60 min before retry; widen `delay_range` in script |
| `MediaError: invalid format` | Resolution / codec wrong | Re-run pre-upload validation; re-encode with the silent-AAC ffmpeg snippet above |
| `ClientError: 2fa_required` | 2FA enabled on the account | Disable 2FA on @aisarva_ — instagrapi cannot complete TOTP challenges automatically. Documented limitation. |
| Caption shows raw `{`/`}` braces | You passed JSON to `--caption` instead of `--caption-file` | Switch to `--caption-file` |
| Upload hangs > 5 min | IG throttling new accounts | Cancel, wait 1 hour, retry once; if persists open IG mobile app to clear shadow-block |

## Anti-patterns

- **Don't** create a fresh login object per call — `.instagram_session.json` persists the device + cookies; re-using it is what keeps IG from flagging the account as a new device.
- **Don't** post >3 reels in a 30-min window — instagrapi has `delay_range = [1, 3]` but IG's server-side throttle is per-account.
- **Don't** put `music_credit` in the visible caption — IG's audio licensing scans the audio track, not text. Text credit invites copyright strikes when it doesn't match.
- **Don't** put `story_slug` in the caption — internal metadata; viewers don't care.
- **Don't** rotate the IG_USERNAME / IG_PASSWORD secret without invalidating `.instagram_session.json` — session caches the old auth and the next login will mismatch.

## Related skills

- [[frames-to-reel-ffmpeg]] — produce the MP4 this skill uploads.
- [[grok-imagine-agent-driver]] — produce the source clips that get assembled then uploaded.

## Bundled resources

| File | Purpose |
|---|---|
| `scripts/validate_reel.sh` | Runs ffprobe + checks codec, resolution, duration, audio presence. Exit 0 OK / 1 FAIL. |
| `references/caption_template.json` | 3 caption skeletons (Telugu, English, growth) for copy-paste. |
| `references/error-recipes.md` | Verbatim fix transcripts for the top 5 errors above. |
