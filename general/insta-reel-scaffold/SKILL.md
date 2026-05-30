---
name: insta-reel-scaffold
description: Engine/scaffolder for the Telugu IG reel pipeline — lays down the proven bin/ + Remotion comp + hook-trimmer harness into a fresh project so every new video starts ready-to-run instead of hand-copying an old project. Use at the START of any new reel build (after picking a work dir), as the build engine behind insta-video. Packages the multi-clip-per-beat rebuild, key-word/end-card Remotion comp, content-aware foley, and the edition matrix.
tier: general
tags: [reel, video, scaffold, remotion, pipeline, telugu, instagram]
version: 1
---

# insta-reel-scaffold — the reusable reel engine

This is the **build engine** behind [[insta-video]]. It scaffolds the proven harness so each new
reel starts from a working pipeline, and it documents the exact commands to drive it. Use it the
moment a new video has a work dir. Child/sibling skills own the creative details:
[[telugu-raw-reel-voice]] (script + VO) · [[grok-imagine-agent-driver]] / [[google-flow-agent-driver]]
(clips) · [[telugu-voice-and-text]] (Telugu text/subs) · [[reel-sfx-foley]] (foley) ·
[[instagram-reel-publish]] / [[youtube-shorts-publish]] (publish).

## Scaffold a new project

```bash
bash ~/.skills-hub/general/insta-reel-scaffold/scaffold.sh <project_dir>
```

Lays down: `bin/` (the pipeline), `remotion/` (comp + configs + reused node_modules), `hook_trimmer/`,
and all asset dirs (`clips/ clean_clips/ audio_{male,female}/ sfx/ music/ hook/ vo_txt{,_f}/ …`).

## The pipeline (what the engine runs)

A reel = an optional **real-clip hook** (beat 0) + N narration **beats**, each beat = its Telugu VO +
1–2 video clips fitted to that VO, with Telugu **kicker** (top) + **key-word** (centre) overlays, an
anthem **music bed**, **foley**, and an IG-spec encode.

Data model — `shots.json` / `shots_v2.json`:
```json
{ "meta": {"fps":30,"width":1080,"height":1920},
  "shots": [ {"id":1, "narration_te":"…", "onscreen_te":"<kicker>",
              "keyword_te":"<primary term, optional>", "endcard_te":"<final-beat CTA, optional>",
              "clips":["shot1","golconda"]   // 1+ clip names in clean_clips/; 2+ = faster cuts
            } ] }
```

Per-edition build (one command, end-to-end):
```bash
# multi-clip-per-beat (v2 — preferred): fit clips→VO, render, foley, prepend hook, IG encode
SHOW_KEYWORDS=1 bin/make_edition_v2.sh <male|female> <VO_X> <out_basename>
# single-clip-per-beat (v1, simpler): bin/make_edition.sh <gender> <VO_X> <out_basename>
```

Stages inside `make_edition_v2.sh`:
1. `rebuild_v2.py` — `atempo=VO_X` on each beat's VO, then split the beat's VO time across its `clips`
   and `setpts`-fit each clip to its slice (long beats → 2 faster cuts, not one slow-mo shot).
2. `gen_timeline_v2.py` — emit `remotion/timeline.json` with per-beat **segments** + kicker/keyword/endcard
   (`SHOW_KEYWORDS=0` omits the centre key-word overlay; kickers always stay).
3. `npx remotion render Reel` — the comp plays each beat's segments in sequence with one VO, Telugu text
   via Noto Sans Telugu (NEVER ffmpeg drawtext / never bake text in the video model).
4. `gen_sfx_cues.py` + `sfx_mix.py` — content-aware foley (ambience bed per location, event hits,
   anthem vocal swell on the climax beat), VO loudnorm ≈ -13 (-12 male), music bed ≈ 0.06.
5. prepend the conformed hook (`hook/hook_conf.mp4`) and encode IG-spec
   (1080×1920 H.264 high yuv420p, AAC 48k, `+faststart`).

## The edition matrix (default deliverables)

Produce **full** + **90s** × **male** + **female** unless told otherwise:
- **full** = natural pace (`VO_X≈1.25`); **90s** = faster (`VO_X` tuned so total ≤90s) keeping ALL beats.
- To hit ≤90s with the natural voice instead of speeding: **trim the tail** (drop the spoken CTA, end on
  the payoff beat) and add a silent `endcard_te` follow-nudge. Pick `VO_X` from the printed raw VO sum:
  `VO_X ≈ raw_total / target_body` where `target_body ≈ 90 - hook_len`.

## The real-clip hook (beat 0) — pattern interrupt

A reel that opens on a **real clip making a provocative/false claim**, then hard-cuts into your
high-energy rebuttal, crushes shares + comments + completion. Flow:
```bash
yt-dlp -o hook/ig_hook_raw.mp4 "<instagram/yt url>"               # download the real clip
# remove burned-in caption: if it's on a letterbox bar, fill the bar black (footage untouched):
ffmpeg -i hook/ig_hook_raw.mp4 -vf "drawbox=x=0:y=0:w=W:h=<bar_h>:color=black:t=fill" -c:a copy hook/ig_hook_clean.mp4
python3 hook_trimmer/server.py            # open http://127.0.0.1:8770 — scrub, set OUT at end of the line, Cut
# -> writes hook/ig_hook_trimmed.mp4 ; conform to body params:
ffmpeg -i hook/ig_hook_trimmed.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -af "loudnorm=I=-15:TP=-1.5,aresample=48000" -c:v libx264 -profile:v high -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 hook/hook_conf.mp4
```
`make_edition*.sh` prepends `hook/hook_conf.mp4` automatically. Keep the hook's **original audio** under
the cut; the anthem + VO burst in on the hard cut. (The trimmer is a tiny local HTTP server with Range
support + an `/cut` ffmpeg endpoint; bundled in `hook_trimmer/`.)

## Clip generation + mapping (Grok or Flow)

Generate 9:16 **text-free** clips ([[grok-imagine-agent-driver]] batches them; diegetic text on
maps/banners/inscriptions is fine — only caption *overlays* are guarded). Clips land in arbitrary order:
download all, extract one mid-frame each, **read them to identify content**, then name them
`clean_clips/<name>.mp4` (cropped to 1080×1920) and reference those names in `shots.json` `clips`.
For density / "more video faster", run a 2nd B-roll batch and give long beats 2 clips.

## Gotchas (baked in from real builds)

- `validate_reel.sh`'s `strings`-based moov check gives **false negatives**; verify faststart by atom
  order (`ftyp → moov`) or `grep -a moov`, not `strings`.
- Renders share `remotion/public` symlinks → run editions **sequentially**, not in parallel.
- Keep VO speed via `atempo=VO_X` (pitch-preserving). Remotion render output is
  `remotion/out/tel_<gender>.mp4` (VO-only audio); foley/music are mixed after.

## Make a per-video reference skill when done

After a reel ships, capture it as a thin **case-study** skill (see [[telangana-video]] as the template):
the concept, the creative decisions, links to the project dir + which pipeline knobs were used. These
build a `/`-callable library of past videos to take inspiration from — they do NOT fork this engine.
