# frames-to-reel-ffmpeg — motion recipes

Verbatim ffmpeg `zoompan` snippets per motion direction. Pre-scaling 4× and outputting `yuv420p` are mandatory in every recipe.

Substitute these variables in each snippet:

- `$IN` — input frame path (jpg/png, 1080×1920)
- `$OUT` — output mp4 path
- `$DUR` — duration in seconds (e.g. `4.0`)
- `$FPS` — frame rate (default `30`)
- `$FRAMES` — `$DUR * $FPS` rounded to int

Common flags used everywhere:

```
-loop 1 -framerate $FPS -i $IN
... -t $DUR -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -preset medium -crf 18
```

---

## `in` — slow zoom in (reveals, build-up, "watch this object")

```bash
ffmpeg -y -loop 1 -framerate 30 -i $IN \
  -filter_complex "[0:v]scale=1080*4:1920*4:force_original_aspect_ratio=increase,crop=1080*4:1920*4,zoompan=z='min(zoom+0.0008,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=1080x1920:fps=30,format=yuv420p" \
  -t $DUR -c:v libx264 -pix_fmt yuv420p -crf 18 $OUT
```

Zoom goes from 1.0 → 1.10 over the shot duration. Adjust `0.0008` proportional to `1/frames` for slower/faster zoom.

---

## `out` — slow zoom out (pull-back reveal, "see the whole picture")

```bash
ffmpeg -y -loop 1 -framerate 30 -i $IN \
  -filter_complex "[0:v]scale=1080*4:1920*4:force_original_aspect_ratio=increase,crop=1080*4:1920*4,zoompan=z='if(eq(on,0),1.10,max(zoom-0.0008,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=1080x1920:fps=30,format=yuv420p" \
  -t $DUR -c:v libx264 -pix_fmt yuv420p -crf 18 $OUT
```

Starts at 1.10 (initialised on frame 0 via `if(eq(on,0),...)`), ends at 1.0.

---

## `down` — pan down + slight zoom in (follow gaze downward, reveal below)

```bash
ffmpeg -y -loop 1 -framerate 30 -i $IN \
  -filter_complex "[0:v]scale=1080*4:1920*4:force_original_aspect_ratio=increase,crop=1080*4:1920*4,zoompan=z='min(zoom+0.0005,1.08)':x='iw/2-(iw/zoom/2)':y='min(ih/2-(ih/zoom/2) + on*2, ih-ih/zoom)':d=$FRAMES:s=1080x1920:fps=30,format=yuv420p" \
  -t $DUR -c:v libx264 -pix_fmt yuv420p -crf 18 $OUT
```

`on` = current output frame counter. `on*2` pans 2 pixels per frame downward, clamped at the bottom edge.

---

## `up` — pan up + slight zoom in (look upward, reveal above)

Same as `down` but flip y direction:

```bash
y='max(ih/2-(ih/zoom/2) - on*2, 0)'
```

---

## `left` — pan left + slight zoom in

```bash
x='max(iw/2-(iw/zoom/2) - on*2, 0)'
y='ih/2-(ih/zoom/2)'
```

---

## `right` — pan right + slight zoom in

```bash
x='min(iw/2-(iw/zoom/2) + on*2, iw-iw/zoom)'
y='ih/2-(ih/zoom/2)'
```

---

## `static` — no motion (text-heavy frames where motion distracts from reading)

```bash
ffmpeg -y -loop 1 -framerate 30 -i $IN \
  -t $DUR -c:v libx264 -pix_fmt yuv420p -crf 18 -vf "format=yuv420p,scale=1080:1920" $OUT
```

Use sparingly — a reel of frozen frames feels broken even when intentional.

---

## Why the 4× pre-scale is mandatory

`zoompan` operates per output pixel. If you zoom 1.0 → 1.10 on a 1080×1920 source, the zoomed-in output samples *fewer* source pixels per output pixel — visible blockiness. Pre-scaling 4× (`scale=1080*4:1920*4`) gives `zoompan` a high-res source to sample from; the final 1080×1920 output is downsampled cleanly.

The cost: ~4× CPU on the encode step. Worth it for any zoom factor > 1.05.

---

## Why `format=yuv420p` appears twice

1. Inside `filter_complex` (after `zoompan`) — converts the working color space to broadcast-range yuv420p.
2. Outside as `-pix_fmt yuv420p` — tells the encoder to use that pixel format.

Both are needed. Some ffmpeg versions ignore the encoder flag if the upstream filter produced `yuvj420p` (JPEG range). Belt-and-suspenders to avoid IG rejecting the upload.

---

## Crossfade transitions (xfade filter)

After per-shot clips are built, combine with `xfade`. Each transition needs an explicit absolute `offset`:

```bash
# Two-shot example:
ffmpeg -y -i shot_01.mp4 -i shot_02.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.3:offset=3.2,format=yuv420p[outv]" \
  -map "[outv]" -c:v libx264 -pix_fmt yuv420p -crf 18 reel.mp4
```

Where `offset=3.2` = (shot_01_duration - 0.3) = 3.5 - 0.3 = 3.2.

For N shots, see the dynamic builder in `scripts/assemble.sh`. Manual computation:

```
xfade_i_offset = sum(DURS[0..i]) - (i * 0.3)
```

---

## Audio (silent AAC track)

Required by Instagram even for silent reels. One-liner:

```bash
ffmpeg -y -i reel_silent.mp4 -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" \
  -shortest -c:v copy -c:a aac -b:a 128k -movflags +faststart reel.mp4
```

If you want music instead, see `~/Documents/insta_ai_vid/docs/music-and-instagram-upload-workflow.md` for the SoundCloud + ffmpeg mix pattern with fade-out.
