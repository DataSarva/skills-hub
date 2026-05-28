---
name: youtube-shorts-publish
description: Publish a finished vertical MP4 to YouTube as a Short via the youtube_upload.py script in the contentgen project (Google OAuth, googleapiclient). Reads a long-lived refresh token; creds via the iex contentgen wrapper. Use when the user says "upload to youtube", "post the short", "publish to youtube shorts", "ship to YT", or wants a reel cross-posted to YouTube. Covers metadata JSON, Shorts requirements (vertical ≤60s + #Shorts), the .venv-python and don't-pipe-tail gotchas, OAuth setup, and deletion.
tier: general
version: 1
tags: [youtube, shorts, video, reel, publishing, oauth, contentgen]
---

# youtube-shorts-publish

Post a finished vertical reel to YouTube as a **Short** from the Mac Mini. Lives next to the **contentgen** project (`~/Documents/insta_ai_vid/`), which owns the venv, `lib/platforms/youtube_upload.py`, and a long-lived OAuth refresh token. Sibling of `[[instagram-reel-publish]]` — same project, same `iex contentgen` creds wrapper.

## Where the pieces live

| Thing | Path |
|---|---|
| Upload script | `~/Documents/insta_ai_vid/lib/platforms/youtube_upload.py` (subcommands `upload`, `setup`) |
| OAuth token | `~/Documents/insta_ai_vid/.youtube_token.json` (has `refresh_token` + `client_id`/`client_secret` → auto-refreshes, no re-consent) |
| Client secrets | `~/Documents/insta_ai_vid/youtube_client_secrets.json` |
| Python venv | `~/Documents/insta_ai_vid/.venv` (has `google-api-python-client`) |
| Creds wrapper | `iex contentgen --` (injects Google client id/secret env) |

## Canonical upload command

```bash
cd ~/Documents/insta_ai_vid
iex contentgen -- .venv/bin/python3 -u lib/platforms/youtube_upload.py upload \
  --video <path>/reel_yt60.mp4 \
  --metadata-file <path>/yt_metadata.json
# optional: --thumbnail <path>.jpg  (or --title/--description/--tags instead of --metadata-file)
```

On success prints:
```
Upload complete. Video ID: <id>
{"video_id":"<id>","url":"https://www.youtube.com/shorts/<id>","title":"…"}
```
Defaults: `privacyStatus=public`. Title ≤100 chars, description ≤5000, tags ≤500.

## TWO gotchas (both bit us in production)

1. **Use `.venv/bin/python3`, NOT bare `python3`.** `iex contentgen` injects creds but resolves `python3` to system Python, which lacks `googleapiclient` → `ModuleNotFoundError`. Call the venv interpreter explicitly. (Same trap as `[[instagram-reel-publish]]`.)
2. **Don't pipe the command through `tail`/`head`.** The uploader streams `NN% uploaded…` progress; a pipe buffers it so you see *nothing* until completion and a slow upload looks "hung" for many minutes. Run with `python3 -u` and **redirect to a log file** (`> /tmp/yt_upload.log 2>&1`) you can `cat`, or run in the background and read the log. A 77 MB / 50 s Short uploads in ~1–3 min normally.

## Shorts requirements

- **Vertical 9:16, ≤60s** (1080×1920). YouTube auto-classifies a vertical ≤60s video with **`#Shorts` in the title or description** as a Short.
- Put `#Shorts` first in the description; the first ~3 hashtags also render above the title.
- Custom thumbnails barely show on Shorts (the feed plays the video) — `--thumbnail` is optional; skip unless you specifically want it on the watch page.

## Metadata JSON (`--metadata-file`)

```json
{
  "title": "గజేంద్ర మోక్షం — విష్ణువు 1000 ఏళ్లు ఎందుకు ఆగాడు? 🙏 #Shorts",
  "description": "<hook line>\n<CTA>\n\n#Shorts #GajendraMoksha #Vishnu #TeluguStories #MoralStories …",
  "tags": ["Gajendra Moksha","Vishnu","Telugu stories","moral stories","devotional","Shorts"]
}
```
Non-Latin (Telugu etc.) titles/descriptions upload fine (UTF-8). Verified: a 49.9s Telugu Short posted cleanly → `youtube.com/shorts/<id>`.

## First-time / revoked auth

If `.youtube_token.json` is missing or the refresh fails (revoked, scope change):
```bash
iex contentgen -- .venv/bin/python3 lib/platforms/youtube_upload.py setup
```
Runs the OAuth2 consent flow (opens a browser) and writes a fresh `.youtube_token.json`. Interactive — the user must approve in the browser; you can't complete it headless.

## Deleting a Short
Use the YouTube Studio UI, or `service.videos().delete(id=<video_id>)` via googleapiclient with the same token.

## Cross-posting pattern (Instagram + YouTube from one source)
The reel pipeline (`[[google-flow-agent-driver]]`) builds an **Instagram master** (full, up to ~3 min) and a **≤60s YouTube edition** from the same clips. Publish: IG via `[[instagram-reel-publish]]`, the ≤60s cut here. Keep platform-appropriate captions (IG = logline + many hashtags; YT = title with `#Shorts` + description).
