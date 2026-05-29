---
name: veo-watermark-remover
description: Remove the Google Veo / Gemini "✦" sparkle watermark from generated videos (and Gemini image watermarks) using allenk's VeoWatermarkRemover CLI — deterministic reverse-alpha-blending, no AI hallucination, no quality loss, audio passthrough. Use whenever a clip came out of Google Flow / Veo / Gemini Omni Flash and needs the corner watermark gone before publishing. Triggers on "remove veo watermark", "remove gemini watermark", "flow clip has a watermark", "veo sparkle", "clean the google video watermark".
tier: tools
version: 2
tags: [veo, gemini, flow, watermark, video, ffmpeg, post-processing]
---


> 🎬 **Child of the [[insta-video]] master reel pipeline.** Voice = [[telugu-raw-reel-voice]] · Telugu subs = [[telugu-voice-and-text]] · scene SFX/foley = [[reel-sfx-foley]] · publish = [[instagram-reel-publish]] / [[youtube-shorts-publish]].

# Veo / Gemini watermark remover

Google Flow / Veo / Gemini Omni Flash videos carry a translucent **4-point "✦" sparkle** watermark in the **bottom-right** corner (720p portrait: a 48×48 diamond at ~(600,1160) in a 720×1280 frame). `allenk/VeoWatermarkRemover` removes it by **reverse alpha blending** — it knows the watermark's exact alpha mask and inverts the compositing equation, so the underlying pixels are reconstructed mathematically. No generative inpainting, no hallucinated content, no quality loss, audio is passed through. Verified clean on Flow Omni Flash 9:16 clips.

The same author's `GeminiWatermarkTool` removes the **Gemini image** watermark (C++ build); the video binary here also handles images.

## Get the binary (one-time)

It ships as a prebuilt CLI in GitHub Releases (no source build needed for the video tool).

```bash
gh release download v0.6.1-demo --repo allenk/VeoWatermarkRemover \
  --pattern "*macOS*" --dir /tmp/veo        # or *Linux* / *Windows*
unzip -o /tmp/veo/*.zip -d /tmp/veo
BIN=/tmp/veo/GeminiWatermarkTool-Video
chmod +x "$BIN"
xattr -dr com.apple.quarantine "$BIN"       # macOS Gatekeeper: unsigned demo binary
```

Check the latest tag with `gh release view --repo allenk/VeoWatermarkRemover`. Assets:
`GeminiWatermarkTool-{macOS-Universal,Linux-x64,Windows-x64}-Video.zip`.

A working copy is already installed in the gajendra reel project at
`~/Downloads/insta_story/gemini_prod/bin/tools/veo_wmremove` (macOS universal, quarantine cleared).

## Run it

```bash
"$BIN" --no-banner -i in.mp4 -o out_clean.mp4
```

- **Auto-detect** locks the watermark by normalized cross-correlation (NCC); logs e.g.
  `Locked region: 720p-1 portrait -> (600,1160) 48x48 (NCC 0.98)`. Then per-frame **adaptive
  alpha** (bisection feedback) so motion / heterogeneous backgrounds don't leave residue or dark holes.
- Audio is preserved (`+audio`). Output is re-encoded H.264.
- `--no-banner` keeps logs script/agent friendly.

### Flags worth knowing
- `-o` optional for video (auto-names if omitted).
- `--variant 720p-1 | 720p-2` — escape hatch when auto-detect SKIPs (rare; it now probes 12 frames across the first 90% to survive intro fade-ins).
- `--region br:auto` or `--region x,y,w,h` — force the watermark region.
- `-f / --force` — process even when detection is unsure (can damage clean clips; only if you KNOW there's a watermark).
- `-t <0..1>` — detection confidence threshold (default 0.25).
- `--legacy` / `--no-legacy` — pin/skip the pre-Gemini-3.5 watermark profile (auto-fallback is on by default).

## Gotchas (hit in production)

- **Speed: ~1.4 fps on macOS CPU** (no Vulkan — "Vulkan loader unavailable on macOS … falling back to CPU"). An 8 s / 192-frame clip ≈ 135 s. Budget ~40 min for a 19-clip batch. Install MoltenVK / LunarG Vulkan SDK for GPU accel if you need it faster. Linux/Windows with a GPU are much faster.
- **Output dir must exist** — the tool fails with `Failed to open output file` if the `-o` parent dir is missing. `mkdir -p` first.
- **macOS quarantine** — first run is blocked by Gatekeeper; `xattr -dr com.apple.quarantine <bin>` (the user asked for this tool, so clearing quarantine is expected).
- It's a **demo build** — a few content classes can leave a tiny residue on a handful of frames; the README documents a manual touch-up (decompose to PNGs → GUI Custom mode alpha slider → recompose). For typical clips the auto pipeline is clean.

## Verify removal

```bash
ffmpeg -y -sseof -0.2 -i out_clean.mp4 -vframes 1 /tmp/last.png
ffmpeg -y -i /tmp/last.png -vf "crop=300:200:420:1040" /tmp/br.png   # bottom-right where ✦ sat
```
Look at `/tmp/br.png` — corner should be clean background, no sparkle, no smudge.

## Batch pattern (clean → then speed/mute downstream)

```bash
for f in clips/shot*.mp4; do
  n=$(basename "$f")
  "$BIN" --no-banner -i "$f" -o ".wm_tmp/$n"
done
# downstream: ffmpeg setpts/atempo speed, -an to drop the model's native audio, etc.
```

Pairs with `[[google-flow-agent-driver]]` (the Flow clip-generation driver) — watermark removal is the first post-process step before speed-up and Remotion assembly.

## Other tools evaluated (rejected)
- `allenk/GeminiWatermarkTool` — C++/cmake build, **images only** (the Veo *video* path is this separate binary).
- `dinoBOLT/Gemini-Watermark-Remover` — Chrome extension, LaMa inpainting, **images only**, browser UI.
- `GargantuaX/gemini-watermark-remover` — not needed once allenk's video tool worked.
