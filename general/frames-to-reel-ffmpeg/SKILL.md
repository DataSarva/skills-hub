---
name: frames-to-reel-ffmpeg
description: Assemble N still storyboard frames (1080×1920 9:16 JPGs) into one Instagram-ready MP4 reel using ffmpeg — per-shot Ken Burns motion (slow zoom in/out/pan-down/pan-up), crossfade concatenation, and a silent AAC track so IG accepts the upload. Use whenever the user has source frames but no native motion video — typically the fallback when Grok Imagine video quota is hit and only the storyboard images survived, OR when the workflow is intentionally still-only (riddles, quotes, captioned posters). Triggers on "assemble reel from frames", "ken burns", "stills to video", "ffmpeg storyboard", "frames to mp4", "build reel from images", "stitch jpgs into reel", or any variant of turning static images into a 9:16 reel.
tier: general
tags: [ffmpeg, video, reel, instagram, ken-burns, fallback]
version: 1
---

# frames-to-reel-ffmpeg

When you have a sequence of 1080×1920 storyboard JPGs and need a finished 9:16 reel, this skill produces one with:

- Per-shot Ken Burns motion (slow zoom or pan — never static)
- Crossfade transitions between shots (default 0.3s)
- Silent stereo AAC audio track (Instagram rejects video-only mp4)
- `yuv420p` 8-bit color (full broadcast compatibility — `yuvj420p` from JPG sources is converted explicitly)
- `+faststart` for streaming-friendly mp4

Output: a single 1080×1920 H.264 mp4 ready for `[[instagram-reel-publish]]`.

## When to use

- **Grok Imagine quota exhausted before video stage** — image quota gives 4 stills, video quota gives 0. Storyboard frames are all you have.
- **Riddle / quote / poster reels** — text-on-image content where animation doesn't add value.
- **Quick-turnaround pivots** — need to ship tonight, no time for a 15-min video generation per shot.
- **Validation harness** — testing the IG-upload pipeline without burning a real Grok video gen.

## When NOT to use

- The shots are meant to depict actual motion (a person walking, a flame igniting, a camera fly-through). Ken Burns is a workaround, not a substitute — viewers can tell. Use [[grok-imagine-agent-driver]] or wait for video quota reset.
- The frames are not pre-cropped to 9:16. This skill assumes 1080×1920 input. For other aspects, crop first or it will black-bar.
- More than ~8 shots. Crossfade math becomes unwieldy and viewers tire of zoom-and-fade. For long content, generate actual motion.

## Inputs you must provide

- **Frame paths** — ordered list of 1080×1920 JPG/PNG files. Order = playback order.
- **Per-shot duration** in seconds. Total ≤ 90s for IG Reels; ≥ 3s.
- **Per-shot motion direction** — one of `in`, `out`, `down`, `up`, `left`, `right`, `static`. Match motion to content (zoom-in for reveals, pan-down to follow gaze, static for text-heavy frames where motion competes with reading).
- **Output path** — final reel.mp4 location.

## Canonical assemble.sh template

The bundled `scripts/assemble.sh` is parameterized — copy it into the reel run dir, edit the three arrays at top, run it. No other changes needed.

```bash
# Top of assemble.sh — the only thing you customize per reel
RUN_DIR="<path to reel dir>"            # contains storyboard_frames/ and will get clips/, final/
declare -a ORDER=(01 02 04 03)          # narrative order of frame_NN.jpg files
declare -a DURS=(3.5 3.5 6 3)           # per-shot seconds, must sum to ≤ 90 - (N-1)*0.3
declare -a ZOOMS=("in" "in" "down" "out") # per-shot motion direction
```

Then:

```bash
bash scripts/assemble.sh
# -> writes <RUN_DIR>/clips/shot_NN.mp4 per shot
# -> writes <RUN_DIR>/final/reel_silent.mp4 (silent intermediate)
# -> writes <RUN_DIR>/final/reel.mp4 (with silent AAC track, IG-ready)
```

Validate the output with `[[instagram-reel-publish]] scripts/validate_reel.sh` BEFORE uploading.

## Motion direction guide

| Direction | When | What it does |
|---|---|---|
| `in` | Reveals, build-ups, "watch this object" | Zoom in 1.0 → 1.10 over the shot, slight emphasis |
| `out` | Pull-back reveals, "see the whole picture" | Start zoomed 1.10, end at 1.0 |
| `down` | Follow gaze downward, reveal hidden object below | Slow downward pan + slight zoom in |
| `up` | Reveal something above, looking-up moment | Slow upward pan + slight zoom in |
| `left` / `right` | Follow motion implied in frame | Horizontal pan, slight zoom |
| `static` | Text-heavy frames where motion distracts from reading | No zoom or pan, just hold |

**Rule of thumb:** 90% of shots should have *some* motion. A reel of frozen frames feels broken to viewers, even if the frames are beautiful.

## Crossfade math (why the offsets matter)

ffmpeg `xfade` requires explicit start-offsets per transition. The math:

```
shot_01: 0  -> d1
shot_02: d1 - 0.3  -> (d1 + d2) - 0.3     (overlap 0.3s with shot_01)
shot_03: (d1 + d2) - 0.6  -> (d1 + d2 + d3) - 0.6
shot_04: (d1 + d2 + d3) - 0.9  -> (d1 + d2 + d3 + d4) - 0.9
```

Each crossfade subtracts 0.3s from the total runtime. Final duration: `sum(DURS) - (N-1) * 0.3`.

For tonight's deepam reel: 3.5 + 3.5 + 6 + 3 = 16s raw → 16 - 0.9 = 15.1s final ✓

## Critical pix_fmt fix

Source JPGs encode in JPEG color range, which ffmpeg's libx264 will output as `yuvj420p`. Instagram (and many players) prefer broadcast-range `yuv420p`. **Always** include `-pix_fmt yuv420p` in the libx264 step. The bundled `assemble.sh` handles this; if you write your own pipeline, don't forget it.

Symptom of forgetting: `validate_reel.sh` exits 1 with `FAIL pixel format = 'yuvj420p'`.

To convert an already-built reel without re-encoding from frames:

```bash
ffmpeg -y -i reel_yuvj.mp4 -vf format=yuv420p -c:v libx264 -crf 18 -preset medium -c:a copy reel_yuv.mp4
```

## Silent AAC track (IG-mandatory)

Even if your reel is silent by design (riddles, quotes), the mp4 MUST carry an audio stream or IG silently rejects it. Add one:

```bash
ffmpeg -y -i reel_silent.mp4 -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" \
  -shortest -c:v copy -c:a aac -b:a 128k -movflags +faststart \
  reel.mp4
```

If you DO have music, see [[soundcloud-music-mix]] (if exists) or `~/Documents/insta_ai_vid/docs/music-and-instagram-upload-workflow.md` for the SoundCloud → ffmpeg mix pattern with `-af "atrim,afade=t=out:..."`.

## Common pitfalls

1. **`-loop 1` on the input** — required for ffmpeg to read a single image as a video stream. Forgetting it produces a 0-duration clip.
2. **`-framerate` BEFORE `-i`, `-r` AFTER** — `-framerate` sets the input rate (how fast frames are read from disk); `-r` sets output rate. For single-image input both should match (default 30).
3. **`zoompan` `d=` is in frames, not seconds** — `d=$frames` where `$frames = $duration * $fps`. Off-by-30 here cuts your shot to 1/30 of its intended length.
4. **`zoompan` `s=` defines output resolution** — set to `1080x1920` per shot, not the input image's resolution, or you'll get an unscaled crop.
5. **Pre-upscale before zoompan** — `zoompan` operates per pixel; if you zoom into a 1080×1920 source, you get pixelated mush. The bundled script scales the input 4× first (`scale=1080*4:1920*4`) and crops/zooms from that, then downsamples to 1080×1920 on output. Smooth zoom.
6. **`xfade` offsets are absolute, not relative** — `offset=3.2` means "the transition starts at second 3.2 of the COMBINED timeline", not "3.2 seconds into the previous clip". See math above.
7. **Don't `concat` instead of `xfade` for transitions** — plain `concat` produces hard cuts. Use `xfade` (filter_complex) for smooth crossfades.
8. **`yuv420p` not `yuvj420p`** — see "Critical pix_fmt fix" above.
9. **Silent reel needs explicit silent audio track** — see "Silent AAC track" above.
10. **`-movflags +faststart` on final encode** — without it, the moov atom lands at the end of the file and IG (or any web player) must download the whole file before playback can start. This breaks IG's upload pre-validation in some cases.

## Bundled resources

| File | Purpose |
|---|---|
| `scripts/assemble.sh` | Parameterized end-to-end assembler. Edit ORDER + DURS + ZOOMS arrays at top, run. |
| `references/motion-recipes.md` | Verbatim ffmpeg snippets for each motion direction (`in`, `out`, `down`, `up`, etc.) — copy-paste when writing a custom pipeline. |

## Related skills

- [[instagram-reel-publish]] — validate + upload the mp4 this skill produces.
- [[grok-imagine-agent-driver]] — the source of the storyboard frames (when video quota fails this skill picks up the pieces).
