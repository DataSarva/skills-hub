---
name: telugu-raw-reel-voice
description: >-
  Default way to write Telugu reel stories AND voice them so they sound like a real
  raw human (a Telangana person telling a story to a friend) — NOT the flat, polished,
  "professional newsreader" tone. Two parts, both inline: (1) story/narration writing
  in raw colloquial Telugu with gender-correct address, (2) voiceover via Gemini-TTS
  (Google Cloud Text-to-Speech, gemini-2.5 *-tts models) with a natural-language style
  prompt — this is now the DEFAULT engine, replacing flat xAI/Chirp3 reads. Use whenever
  writing or voicing a Telugu reel/short/story, when a Telugu VO sounds too formal/robotic,
  or when re-voicing an existing reel. Covers the male/female voice picks, the per-gender
  model choice, the reusable gemini_tts.sh helper, and the re-voice-an-existing-reel flow.
tier: general
tags: [telugu, tts, voiceover, gemini-tts, cloud-tts, raw-accent, telangana, storytelling, reels, story-writing]
version: 1
---

# Telugu raw reel — story writing + human voice (DEFAULT)

The problem this fixes: stock Telugu TTS (xAI `eve`/`Leo`, plain Chirp3-HD) reads correctly but sounds
**flat, subtle, professional** — like a newsreader, not like a person. Films and good reels have
*accent, attitude, comic timing, raw human energy*. This skill is the default recipe to get that, in
two independent parts. **Do both** unless told otherwise.

This SUPERSEDES the flat-read guidance in [[telugu-voice-and-text]] for the VO step. That skill's
**Part 2 (Telugu on-screen text / Remotion subtitles) still applies unchanged** — never bake Telugu
text with a video model or `ffmpeg drawtext`; render it in POST with Remotion + Noto Sans Telugu.

---

## Part 1 — Write the story RAW (not bookish)

Default register = **spoken colloquial Telugu**, the way a Telangana person actually talks to a friend,
not formal written/literary Telugu.

- Use casual openers and fillers: `అరెరే`, `ఒరేయ్`, `ఒసేయ్`, `ఏయ్`, `రా`, `బై` (see gender rule),
  `నిజంగా చెప్తున్నా`, `విను ఒక్కసారి`.
- Short punchy sentences. Use **periods, not commas**, for beats (TTS barely pauses on commas).
- Comic/emotional beats over information dumps. A reel is a *performance* — write it to be performed.

### Gender-correct address — HARD RULE
- **Masculine address** (guy speaking / addressing a guy): `ఏం బై`, `ఒరేయ్`, `ఎక్కడున్నవ్` are fine.
- **Feminine voice (girl/woman speaking): NEVER use `బై` or `ఒరేయ్`.** Use `ఒసేయ్`, `ఏయ్`,
  `ఎక్కడ తిరుగుతున్నావ్`. A girl saying "ఏం బై" is wrong and the user will flag it.
- Third-person **narration** (telling a story *about* someone) is gender-neutral and works for any
  narrator voice — most reel narration is this.

### Don't be repetitive
Do not reuse the same opening line / same script across shots or across reels. Rotate phrasings.

---

## Part 2 — Voice it with Gemini-TTS (DEFAULT engine)

**Engine:** Google Cloud Text-to-Speech, **Gemini-TTS** models. This is the only engine here that takes
a natural-language **style prompt** ("speak raw, casual, Telangana street tone…") — that prompt is what
produces the human/raw feel. Telugu (`te-IN`) works even though Google's public docs don't list it.

**Auth (no API key):** `gcloud auth print-access-token` (Bearer) + header
`x-goog-user-project: $(gcloud config get-value project)`. One-time:
`gcloud services enable texttospeech.googleapis.com`. Free tier covers reels.

**Endpoint:** `POST https://texttospeech.googleapis.com/v1/text:synthesize`
**Body shape (note: bare voice name + `prompt` + `modelName`):**
```json
{"input":{"prompt":"<style instruction>","text":"<telugu>"},
 "voice":{"languageCode":"te-IN","name":"Puck","modelName":"gemini-2.5-pro-tts"},
 "audioConfig":{"audioEncoding":"MP3"}}
```
- `voice.name` is the **bare prebuilt name** (`Puck`, `Iapetus`, `Leda`…), NOT `te-IN-Chirp3-HD-Puck`.
- 30 prebuilt voices (16 M / 14 F) all work in `te-IN` in this project.

### Voice + model picks (user verdicts, 2026-05-28)

| Slot | Voice(s) | Model | Why |
|---|---|---|---|
| **Male** | **Puck** (1st). Fallbacks for Telangana slang, in order: **Iapetus → Sadaltager → Umbriel → Orus → Charon** | **`gemini-2.5-pro-tts`** | Pro clearly richer/more expressive than flash for male. |
| **Female** | **any of the 14** (user liked all). Pick one per reel for narrator continuity; rotate across reels. | **`gemini-2.5-flash-tts`** | For female, **flash sounds MORE realistic than pro** — pro sounds processed. |

**Model verdict is gender-dependent** — male→pro, female→flash. Do NOT blanket-default to one tier.

### Style prompts that work
- Storyteller narration (default for reels): *"Narrate like a lively young Telangana street storyteller
  cracking up a close friend — raw, casual, animated, comic timing, full of attitude, fast and natural,
  not formal at all."* (swap "guy"/"girl" to match voice gender).
- Tune per mood: anger, hype, comedy, whisper, sad — the prompt is fully steerable. Vary it per shot
  for dynamics instead of one monotone read.

### Reusable helper (proven)
`~/Downloads/insta_story/tts_samples/gemini_tts.sh` — gender-aware defaults baked in:
```bash
gemini_tts.sh <text_file> <out.mp3> male              # -> Puck / gemini-2.5-pro-tts
gemini_tts.sh <text_file> <out.mp3> female Leda        # -> flash; 4th arg = which female
gemini_tts.sh <text_file> <out.mp3> male Iapetus gemini-2.5-pro-tts /path/prompt.txt   # 6th = mood prompt
```
It prints the clip duration (ffprobe) on stdout — capture it for subtitle/shot timing.

### Gemini 3.1 — not reachable here (yet)
Gemini **3.1** Flash TTS (Apr 2026, more controllable) is NOT usable from this Mac's creds: Cloud TTS
exposes only `gemini-2.5-flash-tts` + `gemini-2.5-pro-tts`; there is no AI-Studio `GEMINI_API_KEY` in
Infisical `contentgen`; Vertex `generateContent` audio output isn't allowlisted. To unlock 3.1: add an
AI-Studio key as `GEMINI_API_KEY` to Infisical `contentgen`, OR get Vertex audio allowlisting, OR wait
for 3.1 to land on Cloud TTS. Until then, 2.5-pro (male) / 2.5-flash (female) is the best available.

### Fallback engines (only if Gemini-TTS unavailable)
- **Google Chirp3-HD** (`te-IN-Chirp3-HD-*`): native Telugu, no style control — flat but authentic.
- **xAI TTS** (`/v1/tts`, `eve`/`Leo`): English-trained, accented/non-native — last resort.

---

## Re-voicing an EXISTING reel (proven flow — parvateesam)

When a finished per-shot reel needs a new voice (project layout: `shots.json` with `narration_te` per
shot, `clean_clips/shotN.mp4` source clips, Remotion comp reading `timeline.json` + `public/audio`,
`public/clips` symlinks). The key trick: **regenerate raw VO, then re-fit the clips to the new VO
length so audio+video stay in sync automatically.**

1. Regenerate each shot's raw VO from `narration_te` with `gemini_tts.sh` into a per-gender `audio_<g>/`.
2. Run the project's `rebuild_continuous.sh` (`VO_X=1.25`) pointed at the gender dirs — it speeds the VO
   and **time-fits each clean clip to its VO length** (single setpts), so motion maps onto narration.
3. `gen_timeline.py` → `timeline.json`; repoint `remotion/public/audio` + `clips` symlinks to the gender
   dirs; `npx remotion render Reel`.
4. Mix the music bed: `ffmpeg -i render.mp4 -stream_loop -1 -i music/bed.wav -filter_complex
   "[1:a]volume=0.16[m];[0:a][m]amix=inputs=2:duration=first" -map 0:v -map "[a]" -c:v copy -shortest out.mp4`.
5. Restore original symlinks + `timeline.json` afterward so the project is left as-found.

Worked end-to-end script: `~/Downloads/insta_story/flow_parvateesam/bin/build_voice_preview.sh`
(`build_voice_preview.sh <male|female> <Voice> <model>` → `preview_<gender>_voice.mp4`).

---

## Memory pointers
Live picks/verdicts also stored in this host's auto-memory `reference_gemini_tts_telugu.md`. Related:
[[telugu-voice-and-text]] (subtitle rendering), [[flow-telugu-comedy-reel]] (full reel pipeline),
[[project_reelforge]] (autoresearch loop that can A/B these voices).
