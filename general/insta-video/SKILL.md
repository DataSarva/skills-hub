---
name: insta-video
description: >-
  MASTER orchestrator for making and publishing a Telugu Instagram/YouTube reel end-to-end. THIS is the
  one skill the user invokes (/insta-video <what they want>); it owns the production pipeline and routes
  to the right child skills based on the prompt — research, raw Telugu story+script, clip generation
  (Google Flow / Grok Imagine), watermark removal, raw human Telugu voiceover, Telugu subtitles, reel
  assembly, scene SFX/foley, loudness + IG-spec encode, and publishing to Instagram + YouTube. Use
  whenever the user says /insta-video, "make a reel", "make an insta video", "create a Telugu reel/short",
  or asks to do any stage of that pipeline. Reads the prompt, picks the stages needed, and invokes the
  registered child skills in order. Defaults learned from production (parvateesam): female Leda voice on
  gemini flash, raw Telangana storyteller style, frame-accurate foley with a comedy sting on the ending.
tier: general
tags: [insta-video, reel, telugu, orchestrator, master-skill, pipeline, instagram, youtube, shorts, video-production, sfx, voiceover]
version: 1
---

# /insta-video — master reel pipeline (parent skill)

The single entry point for producing a Telugu IG/YouTube reel. The user calls **`/insta-video <prompt>`**;
read the prompt, decide which stages are needed, and **invoke the child skills below in order** via the
Skill tool. Don't reimplement a child's logic here — each child owns its details; this skill is the map
+ router + the production defaults that make the output good.

> Trigger: only the user invokes this (it's the parent). When invoked, restate the plan (which stages
> you'll run for this prompt), then execute stage by stage, showing the user the artifact at each gate
> (script → clips → VO → assembled reel → foley mix → publish). Publishing is irreversible — confirm
> before posting unless the user said "publish".

## The pipeline (stage → child skill)

| # | Stage | Child skill | When to run |
|---|-------|-------------|-------------|
| 0 | Research / niche / story options | [[instagram-reel-research]] | prompt asks to study a niche, find ideas, or analyze reference reels |
| 1 | **Story + script** (raw colloquial Telugu, gender-correct address) | [[telugu-raw-reel-voice]] (Part 1) | always, unless a script is given |
| 2 | **Generate video clips** (9:16, character-consistent, text-free) | [[google-flow-agent-driver]] (Flow/Veo) **or** [[grok-imagine-agent-driver]] (Grok Imagine) | pick by prompt/availability; Flow = character @names + cleaner toon, Grok = imagine canvas |
| 3 | Watermark removal + speed/clean | [[veo-watermark-remover]] (+ project `postprocess.sh`) | when clips carry a Veo/Flow watermark |
| 4 | **Voiceover** (raw human Telugu, NOT flat TTS) | [[telugu-raw-reel-voice]] (Part 2) | always — Gemini-TTS, male=Puck/pro, female=any/flash |
| 5 | **Telugu subtitles / on-screen text** (Remotion + Noto, never bake/drawtext) | [[telugu-voice-and-text]] (Part 2) | when captions/kickers are wanted |
| 6 | **Assemble reel** (clips + VO + subs, sync clips to VO) | [[flow-telugu-comedy-reel]] / project Remotion comp (`rebuild_continuous.sh` → `gen_timeline.py` → render) | always |
| 7 | **Scene SFX / foley** (frame-accurate background sound) | [[reel-sfx-foley]] | when "background sounds / SFX / make it convincing" — strongly recommended for every reel |
| 8 | **Loudness + IG-spec encode** | [[reel-sfx-foley]] / [[telugu-raw-reel-voice]] (Part 3/4) | always before publish — VO loudnorm ≈ -13..-11 LUFS, 1080×1920 H.264 High yuv420p AAC +faststart |
| 9 | **Publish** | [[instagram-reel-publish]] + [[youtube-shorts-publish]] | when the user says publish/post; IG caption = logline+hashtags, YT title needs `#Shorts` |

Frames-to-reel without a model project: [[frames-to-reel-ffmpeg]].

## Routing by prompt — examples
- "make a Telugu comedy reel about X" → 1→2(Flow)→4→5→6→7→8, then ask to publish (9).
- "re-voice / add SFX to this existing reel" → 4 and/or 7 only, on the existing render (see the re-voice
  flow in [[telugu-raw-reel-voice]] Part 3 — regen VO, refit clips, re-render, foley, encode).
- "find me a story idea / study this niche" → 0 only.
- "publish this to IG and YT" → 8 (verify spec) → 9.
- "louder / fix the audio / SFX wrong" → 7+8 re-mix (edit `sfx_cues.json`, re-run `sfx_mix.py`).

## Production defaults (learned from the parvateesam build — apply unless told otherwise)
- **Story:** raw colloquial Telangana register; gender-correct address (girls never say "బై"); don't
  reuse one line; write it to be performed, period-separated for TTS beats.
- **Voice:** Gemini-TTS (Google Cloud `text:synthesize`). Male = **Puck** on `gemini-2.5-pro-tts`
  (fallbacks Iapetus→Sadaltager→Umbriel→Orus→Charon); Female = any of 14 on `gemini-2.5-flash-tts`
  (flash sounds more real than pro for female). Style prompt = "lively young Telangana storyteller…".
- **Clips:** 9:16, character-consistent, **text-free** (add Telugu text in post, never via the video model).
- **Sync:** fit each clip's length to its VO (`rebuild_continuous.sh`, `VO_X≈1.25`) so motion maps to speech.
- **Foley:** see the frames, match each cue to the on-screen event, one ambience bed per location,
  **comedy sting on the ending beat**, no recurring boing, check scream gender. ([[reel-sfx-foley]])
- **Loudness:** VO must be IG-loud (≈ -13 LUFS, music ≈0.05, `amix normalize=0`, limiter) — quiet = dull.
- **Publish:** both platforms; 67s vertical is fine (IG Reels & YT Shorts both ≤~3min). Deleting an old
  YT needs `youtube.force-ssl` scope (upload token is 403 on delete) → YouTube Studio UI.
- **Reference project:** `~/Downloads/insta_story/flow_parvateesam/` (bin/ scripts, sfx_cues.json, sfx/).

## Registered child skills
[[instagram-reel-research]] · [[telugu-raw-reel-voice]] · [[telugu-voice-and-text]] ·
[[google-flow-agent-driver]] · [[grok-imagine-agent-driver]] · [[veo-watermark-remover]] ·
[[flow-telugu-comedy-reel]] · [[frames-to-reel-ffmpeg]] · [[reel-sfx-foley]] ·
[[instagram-reel-publish]] · [[youtube-shorts-publish]]

Also relevant: [[reelforge-autoresearch]] (auto-optimize the recipe), [[instasarva integration]] (Slack-driven runs).
