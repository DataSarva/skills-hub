# Prompt patterns

Copy these templates. Replace `<...>` placeholders. Always keep the closing **NO TEXT** and **Audio guard** blocks intact — without them Grok renders burned-in captions and synthetic narration.

## Character reference sheet (4-angle composite, ~5–13 min)

```
Character reference sheet for a single human character I will call [<CharName>]: <full visual description — age, ethnicity, build, face features, facial hair, hair, skin tone, clothing, props, posture, footwear>.

Produce 4 distinct full-body head-to-toe views of THE EXACT SAME person on a single composite sheet, arranged as a 2x2 grid, plain neutral light grey studio background, soft even diffused lighting, identical character in all 4 panels:
(1) front view, full body, <prop placement>
(2) three-quarter left view, full body
(3) right side profile, full body
(4) back view, full body

Photorealistic cinematic film look, ultra-detailed face and clothing, exact same face features, same skin tone, same clothing, same props, same body proportions across all 4 views. This is a character reference sheet for downstream video animation - identity must be 100% consistent.

NO TEXT, NO LABELS, NO PANEL NUMBERS, NO CAPTIONS, NO WATERMARKS, NO WRITING OF ANY KIND ON THE IMAGE.
```

For non-human / scene reference (tree, building, vehicle), substitute "Reference sheet for a single character object I will call [<Name>]" and give 4 views suited to the object (wide front / 3/4 / macro detail / low-angle hero).

## Agentic multi-shot brief (Phase 2 — preferred over shot-by-shot)

Send this ONCE after all ref sheets are locked. Grok produces all shots back-to-back without per-shot gating.

```
You are now in autonomous direction mode for the rest of this <project name> reel. We have already locked these character/object references in this canvas:
- [<Char1>] = <one-line summary>  (ref sheet generated earlier)
- [<Char2>] = <one-line summary>  (ref sheet generated earlier)
- [<Object>] = <one-line summary> (ref sheet generated earlier)

We have already produced and locked:
- Shot 01: <one-line description>
- Shot 02: <one-line description>

Now please produce the remaining N video shots SEQUENTIALLY as N DISTINCT separate 6-second clips. Do NOT combine them into one long clip. Do NOT loop the same animation. Each shot must be its own independent render. Place each clip on the canvas as it finishes. Do NOT wait for my approval between shots - run all N back to back.

For every shot:
- Vertical 9:16 portrait aspect ratio (1080x1920 or closest the tool supports)
- 6 seconds duration (the native limit — do not request longer)
- Photorealistic cinematic film look, subtle 35mm film grain, <palette>, ultra-detailed
- Preserve all locked character identities 100% — use ONLY the bracketed names above, never re-describe characters from scratch (re-description re-randomises identity)
- Smooth single-arc camera motion, no jitter
- Audio: ambient SFX only, NO voice, NO narration, NO dialogue, NO singing, NO humans speaking
- NO TEXT, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS, NO WRITING OF ANY KIND

SHOT 3 - <title>
Subject: <character refs and what they do>.
Action: <one motion arc across 6s>.
Camera motion: <one smooth move>.
Lighting: <key + fill + rim>.
Ambient audio: <2-3 specific SFX>.

SHOT 4 - <title>
... (same structure) ...

SHOT 5 - <title>
... (same structure) ...

SHOT 6 - <title>
... (same structure) ...

Begin with SHOT 3 and continue straight through SHOT 6. Render each in turn.
```

**Critical phrases that prevent the lazy-loop glitch:**
- "DISTINCT separate clips"
- "Do NOT combine them into one long clip"
- "Do NOT loop the same animation"
- "Each shot must be its own independent render"

## Stitch request (Phase 3 — preferred over local ffmpeg)

After all shot clips are on canvas and approved:

```
All shots are approved. Please use the canvas Stitch action to combine shots 1 through N in order into one final timeline block. Apply a 0.3 second fade in and fade out between consecutive shots for smooth transitions. Output the stitched timeline as a single MP4 ready to download.
```

If Grok confirms and produces a new video tile with longer duration (~ N × 6 seconds), download it via `scripts/download_asset.sh`. The stitched output URL is the same `assets.grok.com/users/.../generated/<new-uuid>/generated_video.mp4` pattern.

If Grok responds that Stitch is unavailable or fails, fall back to local ffmpeg:
```bash
scripts/concat_reel.sh final/reel_silent.mp4 clips/shot_01.mp4 clips/shot_02.mp4 ...
```

## Single cinematic still frame (optional — skip if going straight from ref sheet to video)

```
Generate a single cinematic still frame in vertical 9:16 portrait aspect ratio (1080x1920) for shot <NN>.

Subject: <character refs by bracketed name> - identity must match the existing reference sheet, 100% preserved.

Scene: <environment, time of day, weather, secondary subjects in soft focus>.

Composition: <low-angle hero / over-the-shoulder / wide / macro>, depth of field <shallow / deep>.

Lighting: <key direction>, <fill / rim>, <color temperature>, <atmospheric notes>.

Style: photorealistic cinematic film look, subtle 35mm film grain, <palette>, ultra-detailed.

NO TEXT, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS, NO WRITING OF ANY KIND ON THE IMAGE.
```

## Single 6-second video clip (use only when not doing a multi-shot batch)

```
Generate a single 6-second cinematic video clip in vertical 9:16 portrait aspect ratio.

Subject: <named characters [...]> - exact same identities as the reference sheets you generated earlier in this canvas. Identity 100% preserved.

Scene: <environment + secondary subjects>.

Action / motion: <ONE simple motion arc across the 6 seconds>.

Camera motion: <one smooth move across the 6s>. Smooth glide, no jitter.

Lighting: <consistent with reel aesthetic>.

Style: photorealistic cinematic film look, subtle 35mm film grain, <palette>, ultra-detailed.

<<Audio guard — paste verbatim>>

NO TEXT, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS.
```

## Audio guard (paste into EVERY video prompt)

```
Audio: ambient SFX only - <list 2-3 specific sounds: wind, footfall, basket creak, distant bell, instrumental note>. NO voice, NO narration, NO dialogue, NO singing, NO humans speaking - audio track must be purely instrumental and ambient. We will add voiceover in post.
```

Without this guard Grok injects a synthetic narrator reading the prompt text, which is impossible to remove cleanly from the mp4 audio track.

## Extend Frame (for shots > 6s)

After a clip is on canvas:

```
Extend the last clip by <N up to 6> more seconds, preserving the exact same character identity [<CharName>] and visual style.

Continuation: <describe the next motion arc>.

Camera motion: <continue smoothly from previous frame>.

Audio: ambient SFX only - <continuation SFX>. NO voice, NO narration, NO dialogue.

NO TEXT, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS.
```

## Error-recovery prompts

If Grok responds with "parameter issue (duration parsing)":

```
Retry the video generation with a 6-second clip duration (the native limit). <Restate subject, scene, camera, style — keep audio guard and no-text guard intact>.
```

If Grok says "I've hit a temporary quota on new image generations":

```
No more new still images needed. Please ANIMATE the existing [<CharName>] reference (the <panel> from the reference sheet you already generated) directly into a single 6-second cinematic video clip. <camera + lighting + style + audio guard + no-text guard>
```

If a clip lands in landscape instead of 9:16:

```
The previous clip landed in landscape aspect (1168x768). For the next clip, please render directly in vertical 9:16 portrait (720x1280 or 1080x1920). Same subject, same camera move, same audio. Do not re-describe characters — just preserve the locked identity.
```

If character identity drifts between shots (e.g. hair appears that wasn't in ref):

```
The character [<Name>] in the last clip had <drifted feature>, but the locked reference sheet shows <correct feature>. For all future shots in this canvas, please match the reference sheet exactly: <one-line canonical description>. No other variations.
```

Don't try to fix drift retroactively on already-rendered clips — accept and document, or redo the specific shot.
