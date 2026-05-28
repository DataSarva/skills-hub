---
name: telugu-voice-and-text
description: >-
  Produce correct Telugu voiceover AND correctly-shaped Telugu on-screen text / subtitles for
  videos and reels. Use whenever a video needs Telugu narration (TTS) or Telugu captions /
  subtitles / titles. Two hard-won rules: (1) generate Telugu VO with the xAI TTS API
  (/v1/tts, voices eve/Leo, language te); (2) NEVER bake Telugu text via the video model and
  NEVER use ffmpeg drawtext — both mangle Telugu conjuncts — instead render Telugu text in POST
  with Remotion + Noto Sans Telugu (Chromium does full HarfBuzz shaping), synced to the VO.
  Proven end-to-end in the prahaladhudu v3 devotional reel.
tier: general
version: 2
tags: [telugu, tts, voiceover, subtitles, captions, remotion, xai, cloud-tts, chirp3, noto-sans-telugu, indic, reels]
---

# Telugu voice + Telugu text (the two things that always go wrong)

Two independent problems, both solved here. Telugu (and other Indic scripts) need **complex-text
shaping** (conjuncts, vowel signs reordering). Most tools don't do it. These do.

## ⭐ AUTHENTICITY UPDATE (2026-05): for natural Telugu, prefer Google Cloud TTS over xAI

xAI TTS (`eve`/`Leo`) is **English-trained** → Telugu is intelligible but **accented/non-native** (a user
flagged it "not authentic"). For genuinely native Telugu, use **Google Cloud Text-to-Speech `te-IN-Chirp3-HD-*`**
voices (female: `Leda`, `Aoede`, `Kore`; pick by ear). Auth via `gcloud auth print-access-token` (no API key);
quota header `x-goog-user-project: <gcloud-active-project>` (use `gcloud config get-value project`, NOT
contentgen's `GOOGLE_CLOUD_PROJECT=contentsarva`, which 404s). One-time `gcloud services enable texttospeech.googleapis.com`. Free tier covers reels.

```bash
# POST https://texttospeech.googleapis.com/v1/text:synthesize  (Bearer token + x-goog-user-project)
# body: {"input":{"text":...},"voice":{"languageCode":"te-IN","name":"te-IN-Chirp3-HD-Leda"},"audioConfig":{"audioEncoding":"MP3","speakingRate":1.05}}
```
Chirp3-HD gotchas: **commas barely pause** — split list items into short sentences with **periods** (`...` for a beat) or they run together; **avoid the zero-width-joiner (ZWNJ) in transliterated English loanwords** (`బెడ్‌రోల్` garbles — use a native word like `పక్క చుట్ట`); no SSML, control pace via `speakingRate`. Working helper: `flow-telugu-comedy-reel/scripts/cloud_tts.sh`. Keep using xAI only when gcloud isn't available. (Part 2 below — Telugu on-screen text via Remotion — is unchanged and applies to both.)

---

## Part 1 — Telugu voiceover (xAI TTS)

**Endpoint:** `POST https://api.x.ai/v1/tts` · **Auth:** `Bearer $XAI_API_KEY` (key starts `xai-`).

- **Voices:** `eve` = warm female devotional (best for storytelling/devotional). `Leo` = authoritative
  male elder. **Language: `te`.**
- Telugu output is natural + intelligible (verified by blind transcription). `[pause]` markers in the
  text work for beat control.
- **Always capture the duration** (`ffprobe`) — it drives subtitle timing and shot length.
- **On this Mac Mini** the key lives in Infisical folder `contentgen` as `GROK_API_KEY` (not
  `XAI_API_KEY`). Alias it and run under `iex`:
  ```bash
  iex contentgen -- bash -c 'export XAI_API_KEY="${XAI_API_KEY:-$GROK_API_KEY}"; bash tts.sh line.txt out.mp3 eve te'
  ```

**Working `tts.sh`:**
```bash
#!/usr/bin/env bash
# tts.sh <text_file> <out_mp3> [voice=eve] [lang=te]
set -euo pipefail
TXT="${1:?}"; OUT="${2:?}"; VOICE="${3:-eve}"; LANG="${4:-te}"
: "${XAI_API_KEY:?set XAI_API_KEY}"; mkdir -p "$(dirname "$OUT")"
BODY=$(python3 - "$TXT" "$VOICE" "$LANG" <<'PY'
import sys, json
print(json.dumps({"text": open(sys.argv[1], encoding="utf-8").read(),
  "voice_id": sys.argv[2], "language": sys.argv[3],
  "output_format": {"codec":"mp3","sample_rate":44100,"bit_rate":192000}}))
PY
)
H=$(curl -s -w "%{http_code}" -X POST https://api.x.ai/v1/tts \
  -H "Authorization: Bearer $XAI_API_KEY" -H "Content-Type: application/json" \
  -d "$BODY" --output "$OUT")
[ "$H" = 200 ] || { echo "HTTP $H: $(head -c 300 "$OUT")" >&2; exit 1; }
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT"  # -> seconds
```
HTTP **403 "used all available credits / monthly spending limit"** = the xAI *team* is out of API
credits (top up at console.x.ai → Billing). This is the metered API; the grok.com *subscription* is
separate and does NOT cover `/v1/tts`.

---

## Part 2 — Telugu on-screen text / subtitles (render in POST, never bake)

**The two failures to avoid:**
1. **Do NOT ask a video model (grok `video_gen` / imagine) to put Telugu text in the frame.** It
   produces garbled / wrong Telugu glyphs. Generate clips text-free; add text afterward.
2. **Do NOT use `ffmpeg drawtext` for Telugu.** ffmpeg has no complex-script (HarfBuzz) shaping, so
   conjuncts and vowel signs break apart. (A known hack is rendering each caption in Chrome → PNG →
   overlay, but that's brittle.)

**The fix: render Telugu text with Remotion.** Remotion renders via headless Chromium = full HarfBuzz
shaping → Telugu conjuncts/matras render perfectly. Load the font with `@remotion/google-fonts`:

```bash
npm i remotion @remotion/cli @remotion/google-fonts react react-dom   # node 18+; v22 verified
```
```tsx
import {loadFont} from '@remotion/google-fonts/NotoSansTelugu';
const {fontFamily} = loadFont();   // then use fontFamily in style
```

**Synced-subtitle component (proven styling — gold on dark, bottom third):**
```tsx
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
const Subtitle: React.FC<{text:string; voFrames:number}> = ({text, voFrames}) => {
  const f = useCurrentFrame(); const out = Math.max(12, voFrames);
  const opacity = interpolate(f, [0,8,out-8,out+10],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return (
    <AbsoluteFill style={{justifyContent:'flex-end',alignItems:'center',paddingBottom:250,paddingInline:36}}>
      <div style={{opacity,maxWidth:'90%',textAlign:'center',fontFamily,fontSize:58,lineHeight:1.34,
        color:'#FFE08A',fontWeight:700,textShadow:'0 3px 16px rgba(0,0,0,0.9),0 0 2px #000',
        background:'rgba(14,6,0,0.5)',padding:'20px 30px',borderRadius:24}}>{text}</div>
    </AbsoluteFill>
  );
};
```
Drive each subtitle's `voFrames` from the matching TTS clip's duration × fps, and place it in a
`<Sequence from={shotStartFrame} durationInFrames={shotDurFrames}>` next to its `<Audio>`. That keeps
the Telugu caption locked to the spoken line. Per-shot `<Audio src={staticFile('audio/shotN.mp3')}/>`
for the VO; a single top-level looped `<Audio volume={0.16} loop>` for the music bed.

**Gotchas:**
- Assets must live under `remotion/public/` for `staticFile()` (symlink your `clips/` + `audio/` in).
- `@remotion/google-fonts` logs "Made N network requests to load fonts" — harmless; silence with
  `loadFont({ ignoreTooManyRequestsWarning: true })` if desired.
- Render: `remotion render src/index.ts <CompId> out/reel.mp4 --concurrency=2`. 9:16 reel = 1080×1920.
- `tsconfig.json` needs `"resolveJsonModule": true` if you import a `timeline.json` of shot timings.

---

## End-to-end pattern (prahaladhudu v3, proven)
1. Write `narration_te` per shot → `tts.sh` (eve, te) → `shotN.mp3` + capture each duration.
2. Generate video clips **with no text in frame**.
3. Remotion comp: clips (`OffthreadVideo`, `objectFit:'cover'`) + per-shot VO `<Audio>` + the
   `Subtitle` above (synced to VO duration) + music bed; render 1080×1920.
4. Result: correct Telugu narration + crisply-shaped Telugu subtitles, none of it baked by the
   video model.

Reference implementation: `~/Downloads/insta_story/grok-cli/prahaladhudu/v3/` (`bin/tts.sh`,
`remotion/src/Reel.tsx`, `shots.json`).
