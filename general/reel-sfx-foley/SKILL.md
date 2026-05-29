---
name: reel-sfx-foley
description: >-
  Add convincing, frame-accurate scene sound design (foley / background SFX) to a finished reel —
  train/station ambience, steam hiss, whooshes, impacts, screams, laughs, comedy stings — matched to
  what is ACTUALLY on screen and when, then mixed under the VO with the voice kept loud. Use whenever a
  reel/short/video sounds bare with only voice+music, when the user wants background noise / sound
  effects / foley / "scene sounds", or as the SFX stage of the insta-video pipeline. Covers: see-the-
  frames event timing, sourcing the right sound per scene (mixkit by category + ffmpeg-synth steam),
  the reusable cue-sheet + mixer (sfx_cues.json + sfx_mix.py), loudness, and the hard-won rules
  (comedy sting on the ending beat, no recurring boing, check scream gender, one bed per location).
tier: general
tags: [sfx, foley, sound-design, reels, ffmpeg, mixkit, ambience, audio-mix, telugu, video-production]
version: 1
---

# Reel SFX / foley — frame-accurate background sound design

A reel with only VO + music sounds bare. This skill adds scene sound design that lands because each cue
is matched to **what is on screen and exactly when** — not to blind time windows. (A blind pass once put
train sounds on a village shot and a laugh-bed before the gag → rejected. Frame-aware fixed it.)

Child skill of [[insta-video]]; runs AFTER the VO ([[telugu-raw-reel-voice]]) and BEFORE final publish
([[instagram-reel-publish]] / [[youtube-shorts-publish]]).

## The process that works

### 1. SEE the frames first (do not guess timing)
Extract a contact sheet per shot from the **rendered** video and look at it:
```bash
# 6 frames across a shot window [a,b], tiled
for k in 0 1 2 3 4 5; do t=$(python3 -c "print($a+($b-$a)/6*$k+0.4)"); \
  ffmpeg -y -ss $t -i out.mp4 -frames:v 1 -vf scale=240:-1 -q:v 4 /tmp/s_$k.jpg; done
ffmpeg -y -i /tmp/s_0.jpg ... -filter_complex hstack=inputs=6 -q:v 3 SHEET.jpg
```
Read each SHEET and note the **exact second each event peaks**: jump, luggage fall, steam burst,
bedroll-spring, scream, guard whistle, hat-tip. Also read the shot's `video_prompt`/`narration` — it
states the action. The per-shot start times come from the render timeline (cumulative shot durations).

### 2. Source the RIGHT sound per scene
mixkit free-SFX category pages are type-grouped, so *any* item under a category is that sound. Harvest
the direct preview URLs from raw HTML (WebFetch strips them):
```bash
curl -s "https://mixkit.co/free-sound-effects/<cat>/" -H "User-Agent: Mozilla/5.0" \
 | grep -oE 'sfx/[0-9]+/[0-9]+-preview\.mp3' | sort -u
# download: https://assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3
```
Useful categories: `ambience bird whoosh swoosh cartoon scream laugh win impact thud crash pop
footsteps applause nature wind crowd train whistle`. Pick by **duration**: long (>8s) = ambience bed
(trim+loop), short (0.5–3s) = one-shot hit, 2–6s = tune/sting. mixkit previews are CC0 — safe to publish.
**No `steam` category — synthesize it** (deterministic):
```bash
ffmpeg -f lavfi -i "anoisesrc=d=3.4:c=pink:a=0.6" \
  -af "highpass=f=1200,lowpass=f=7000,afade=t=in:d=0.5,afade=t=out:st=2.2:d=1.2" steam.mp3
```

### 3. Cue sheet + mixer (reproducible — and why NOT Remotion)
Frame-accurate placement does **not** need Remotion or any heavier project — an exact-millisecond
`adelay` IS frame-accurate, and a JSON cue sheet is faster to iterate than wiring `<Audio>` tracks.

`sfx_cues.json` (per cue: `file`, `at` sec, `vol`, optional `trim`/`fadein`/`fadeout`; plus
`music_vol`, `vo_loudnorm_I`). `sfx_mix.py` builds the ffmpeg graph and renders an IG-spec mp4. A
reference implementation lives at `~/Downloads/insta_story/flow_parvateesam/bin/sfx_mix.py` +
`sfx_cues.json` + `sfx/` (copy it as the starting point). Core of the mix:
- VO: `[0:a]loudnorm=I=-13:TP=-1.0:LRA=11[vo]` (male can go -12/-11; see [[telugu-raw-reel-voice]]).
- Music bed very low: `[1:a]volume=0.05[mus]`.
- Each cue: `[n:a]atrim=0:TRIM,afade…,volume=V,adelay=MS|MS[cN]`.
- `amix=inputs=…:normalize=0:duration=first` (normalize=0 keeps VO loud — the default halving is what
  made an early mix dull), then `alimiter=limit=0.97,aresample=48000`.
- Encode: `libx264 -profile:v high -pix_fmt yuv420p -color_range tv -r 30 -crf 19`, `aac 192k 48k`,
  `+faststart`. Validate with `instagram-reel-publish/scripts/validate_reel.sh`.

## Hard-won SFX rules (user feedback — follow these)
- **End every reel with a comedy sting on the final comedic beat** (a cartoon/`win` sting ~1–2s before
  the end). Punctuates the joke; don't bury it mid-video.
- **Never reuse a cartoon "boing"/sproing across shots** — it reads as an irritating recurring bell.
- **Check scream/voice gender** — a male-sounding "scream" on a female character is jarring; audition,
  replace, or drop it. When unsure, omit rather than ship a wrong one.
- **One ambience bed per LOCATION**, and cut it when the location changes (village birds ≠ station
  reverb ≠ train-interior rumble). A train sound on a non-train scene breaks it.
- **Keep pre-gag/tense beats quiet** — no crowd/laugh bed before the payoff.
- Voice stays dominant: SFX beds 0.07–0.17, hits 0.3–0.5, music 0.05; VO loudnorm'd on top.

## Related
[[insta-video]] (parent/orchestrator) · [[telugu-raw-reel-voice]] (VO + the re-voice/render flow this
mixes onto) · [[flow-telugu-comedy-reel]] / [[google-flow-agent-driver]] / [[grok-imagine-agent-driver]]
(produce the clips) · [[instagram-reel-publish]] / [[youtube-shorts-publish]] (publish the mixed file).
