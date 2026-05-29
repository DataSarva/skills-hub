---
name: flow-telugu-comedy-reel
description: >-
  End-to-end pipeline to turn a Telugu story (e.g. a classic like Barishter Parvateesam) into a finished,
  publish-ready vertical comedy reel using Google Flow (Veo "Omni Flash") for video + authentic native
  Telugu voiceover + Telugu captions. Covers: grok-authored full script, shots.json backbone, Flow Characters
  locked to a USER MASTER IMAGE (Add-from-Project) plus a per-shot wardrobe/feature anchor for cross-shot
  consistency, batch clip generation through the opencli browser bridge, native-Telugu VO via Google Cloud
  TTS te-IN Chirp3-HD (NOT xAI — that is English-accented), watermark removal, gap-free continuous VO at
  1.15-1.25x, and Remotion render with correctly-shaped Telugu subtitles. Use whenever the user wants a
  character-consistent animated comedy reel from a story with authentic Telugu audio + captions. Triggers on
  "make a telugu reel", "parvateesam reel", "flow comedy reel", "telugu story to video", "character reel with
  my reference image", "authentic telugu voiceover reel".
tier: general
version: 2
tags: [google-flow, veo, telugu, tts, cloud-tts, chirp3, reel, character-consistency, remotion, comedy, instagram]
---


> 🎬 **Child of the [[insta-video]] master reel pipeline.** Voice = [[telugu-raw-reel-voice]] · Telugu subs = [[telugu-voice-and-text]] · scene SFX/foley = [[reel-sfx-foley]] · publish = [[instagram-reel-publish]] / [[youtube-shorts-publish]].

# Flow → authentic-Telugu comedy reel (end to end)

Proven on the **Barishter Parvateesam** ladies-compartment reel (`~/Downloads/insta_story/flow_parvateesam/`, 9 beats, ~60s, 1080×1920). This skill is the ORCHESTRATOR; it leans on component skills:
- `google-flow-agent-driver` — driving Flow via opencli (read it for the base DOM/driver mechanics).
- `telugu-voice-and-text` — Telugu VO + Remotion subtitle component (Noto Sans Telugu shaping).
- `veo-watermark-remover` — the `veo_wmremove` binary.
- `instagram-reel-publish` / `youtube-shorts-publish` — shipping.

The bundled `scripts/` are the working copies (already fixed for the current Flow UI). The reference impl with all dirs is the Parvateesam project.

## Pipeline (run in order)

```
0 script    → grok CLI writes a full Telugu reel script (hook + beats + per-shot visual/narration/onscreen)
1 shots.json→ machine backbone: id, scene, chars[@handles], video_prompt, narration_te, onscreen_te
2 chars     → Flow Characters. Hero = USER MASTER IMAGE (Add from Project). Others = text. IDENTITY GATE.
3 clips     → one prompt → one 8s 9:16 clip per shot, summoning @handles (gen_all_clips.sh, resumable)
4 VO        → native Telugu via Google Cloud TTS te-IN Chirp3-HD (cloud_tts.sh) — capture durations
5 watermark → veo_wmremove each clip -> clean_clips/
6 continuous→ rebuild_continuous.sh: VO is the spine, each clip time-fit to its line -> NO gaps, mute native audio
7 render    → gen_timeline.py + Remotion -> 1080×1920 reel with Telugu CC
```

Project dir layout (same as `google-flow-agent-driver`):
`shots.json bin/ clips/ clean_clips/ audio/ final_clips/ final_audio/ remotion/{src,public/{clips,audio}} masters/`

## Step 0 — grok writes the full script (don't hand-write it)

Pipe the source story to grok; demand the exact output format. Requirements that worked: opening HOOK is a warm funny FEMALE storyteller addressing the audience; ONE continuous flowing narration (no disjoint lines); ~22-26 shots for a 2.5-min master OR ~7-9 for a tight cut; animated-comedy style; recurring characters consistent. Output is `CHARACTERS:` then `SHOTS:` with `VISUAL/NARRATION_TE/ONSCREEN_TE` per shot. Convert to the `shots.example.json` schema.

## Step 1 — shots.json

`meta` carries `voice`, `champion_grade`, `champion_camera`, `width/height/fps`, `title_te`. Each shot: `id, scene, chars (the @handles present), video_prompt (ends "no text"), narration_te, onscreen_te, dur, vo_dur`. The grade+camera strings are appended to every video_prompt for a coherent look.

## Step 2 — Characters: lock the HERO to a user master image (THE consistency win)

Flow Characters give cross-shot identity. **For a hero whose exact look matters (a book-cover character, a brand mascot), lock it to the user's MASTER IMAGE, not a text description.**

- **opencli CANNOT upload a local file** (no upload subcommand). The USER uploads the master into Flow once: composer **+ (Add Media) → Upload media**, or it lands in **Uploads**. (They're already logged in; this one manual step is expected.)
- Then create the Character FROM that upload: go to `PROJ/characters`, click **`Add from Project`** (fire it), select the master tile, click **`Add to Character`**, set the name via the React native-setter (see `flow_make_character.sh`), click **Done**. Now `@Name` resolves to the master likeness.
- Other characters (lady, guard, …): text descriptions via `flow_make_character.sh`.

**CRITICAL — Flow re-renders the character in its own 3D-Pixar style and DROPS wardrobe/features.** The master's top hat / tailcoat / mustache were lost when summoned by `@handle` alone. **Fix: repeat the exact wardrobe + signature feature in EVERY shot prompt**, foregrounded. Anchor used for Parvateesam (inject right after the first `@Hero`):

```
(THE SAME MAN IN EVERY SHOT, with a HUGE bold black upward-curled handlebar mustache clearly on his face,
 tall black top hat, black tailcoat with tails, white cravat bow, white dhoti, bright red briefcase, rolled green bedroll)
```

The most-distinctive feature (mustache) drops first on WIDE shots — name it explicitly. **Identity gate: screenshot every character before generating clips.**

## Step 3 — generate clips (Flow UI selectors — these bite)

Use `gen_all_clips.sh <profile> <PROJ>` (resumable; skips existing `clips/shotN.mp4`). It reads each prompt from shots.json, prepends a non-`@` lead-in word (Slate eats a leading `@`), sets the composer, submits, polls, downloads. **Cost: ~25 credits per 8s Omni Flash clip — budget hard (130 credits ≈ 5 clips). Reuse good clips; do tight cuts; never regen a clip that's already fine.**

Settings-menu fixes (encoded in `flow_gen_clip.sh`):
- Menu options are **icon-prefixed** — innerText is `play_circle\nVideo`, `crop_9_16\n9:16`. **Exact-match `===` fails silently → composer stays in Nano Banana IMAGE mode → no video renders, poll times out at ready:0.** Match with regex on `innerText` (normalize `\n`→`|`).
- **Click "Video" FIRST**, then re-query the menu — durations (4s/6s/8s/10s) only appear after switching to Video.
- Radix/Flow controls ignore synthetic `.click()` — dispatch full pointer events (`fire()` helper in every script).
- Generate at **8s** (Flow only allows 4/6/8/10); continuous-fit later stretches each to its VO line.
- **Pin the LOCATION in the prompt** (e.g. "INSIDE the train compartment") — else Veo carries the previous scene's setting and you get a continuity outlier (a compartment beat rendered on the platform).

Verify each downloaded clip by eye (right character + wardrobe + mustache + correct setting); re-roll only true failures (each = 25 cr).

## Step 4 — authentic Telugu VO (Google Cloud TTS, NOT xAI)

xAI TTS `eve`/`Leo` are English-trained → Telugu sounds accented ("not authentic"). **Use Google Cloud TTS native `te-IN-Chirp3-HD-*`** (female: Leda / Aoede / Kore) via `cloud_tts.sh`. Auth = `gcloud auth print-access-token` (no API key); quota header `x-goog-user-project: <gcloud-active-project>` (NOT contentgen's `GOOGLE_CLOUD_PROJECT=contentsarva`, which 404s). One-time `gcloud services enable texttospeech.googleapis.com`. Free tier covers reels.

Chirp3-HD gotchas (hit in production):
- **Commas barely pause** → comma lists run together. Split list items into **short sentences with periods** (and `...` for a beat): `"...ఊరగాయలు. అప్పడాలు. ఇంకా ఆ ప్రసిద్ధమైన ఆకుపచ్చ పక్క చుట్ట."`
- **Avoid the zero-width-joiner (ZWNJ) in transliterated English words** — `బెడ్‌రోల్` garbled. Prefer a clean native word (`పక్క చుట్ట` = bedroll).
- No SSML; control pace with `speakingRate` (1.0 clear, 1.05-1.15 lively). Capture each mp3 duration (`ffprobe`).

```bash
bash scripts/cloud_tts.sh audio/shot7.txt audio/shot7.mp3 te-IN-Chirp3-HD-Leda 1.05
```

## Step 5 — watermark removal

`veo-watermark-remover` skill / `veo_wmremove --no-banner -i clips/shotN.mp4 -o clean_clips/shotN.mp4`. ~1.4 fps CPU (~135s/8s clip). **Run each clip as its own command, NOT chained in one fragile subshell** — a killed/collided job truncates the mp4 (`moov atom not found`). Verify `ffprobe` duration after each.

## Step 6 — continuous gap-free VO (the "no burst-gap" fix)

`rebuild_continuous.sh` (env `VO_X=1.15 BREATH=0.25`): speeds each VO line by `VO_X` (pitch-preserved), sets each shot `dur = vo_dur + BREATH`, and `setpts`-fits the clean clip to that length so motion maps onto the spoken line. VO covers ~97% → fast but flowing, no dead silence. **Do NOT use a fixed-speed approach (e.g. 1.5x video) — that re-introduces the burst-gap feel the user hated.** `VO_X` 1.15 = clearer, 1.25 = punchier. Also mutes native Veo audio (`-an`).

## Step 7 — render with Telugu CC

`gen_timeline.py` → `remotion/timeline.json`; then `npx remotion render src/index.ts Reel out/reel.mp4 --concurrency=2`. The bundled `Reel.tsx` uses `OffthreadVideo muted` + per-shot `<Audio>` VO + a `Subtitle` (narration, synced to vo_dur) + optional `Kicker` (onscreen). Telugu shapes correctly because Remotion renders via headless Chromium (HarfBuzz) with `@remotion/google-fonts/NotoSansTelugu` — never bake Telugu in the video model or ffmpeg drawtext. Drop the music bed for comedy unless you have a fitting playful track.

**Render-collision gotcha:** never run two renders to the same output path, and never `cp` the output while a render is writing it → corrupt H264 (`Invalid NAL unit size`). Render to a fresh path, validate with `ffmpeg -v error -i out.mp4 -f null -`, then copy.

## Definition of done (full prod reel)

1080×1920 · authentic native-Telugu VO · native Veo audio stripped · gap-free continuous VO at 1.15-1.25x ·
watermark removed · correctly-shaped Telugu CC · hero consistent across all shots · decodes clean. Then publish via `instagram-reel-publish` / `youtube-shorts-publish`.
