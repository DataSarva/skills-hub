---
name: google-flow-agent-driver
description: Drive Google Flow (labs.google/fx/tools/flow, Gemini "Omni Flash" video model) fully automated via the opencli Browser Bridge — build reusable named Characters, generate text-free 9:16/16:9 video clips that summon those characters by @name, download them, then assemble a finished reel (watermark removal + speed-up + Telugu/other-language VO + Remotion subtitles). Use whenever a reel or video clip needs to come out of Google Flow / Veo / Gemini Omni Flash. Triggers on "google flow", "flow omni flash", "make a reel with google flow", "gemini video", "veo video via web", "opencli flow automation", "flow character consistency", "@character flow".
tier: general
version: 1
tags: [google-flow, gemini, veo, omni-flash, opencli, browser-automation, video, reel, instagram-reel-source]
---

# Google Flow agent driver

End-to-end recipe for driving **Google Flow** (`labs.google/fx/tools/flow`, the Gemini **Omni Flash** video model) **directly through the browser** via the `opencli` Browser Bridge. Flow has **no public video API** — it's a web app, so we drive the real logged-in Chrome session. This is the Flow analogue of `[[grok-imagine-agent-driver]]`; Flow is usually the better choice because **native Characters give true cross-shot identity lock** and generation runs on the **subscription** (no metered API credit wall).

Proven end-to-end on a 19-shot, 103 s Telugu devotional reel (`~/Downloads/insta_story/gemini_prod/`). Reuse that dir's `bin/` scripts — they encode everything below.

## Mental model

Flow = a project workspace with a bottom **composer**. You pick output type (Image / **Video** / Frames), model (**Omni Flash** for video), aspect (9:16 / 16:9), duration (4/6/8/10 s), count (1×–4×), type a prompt, hit submit (→). Clips render in ~2–3 min and land as tiles in **All Media**. **Characters** (left rail) are reusable cast members: design once, then **summon with `@Name`** in any prompt for visual+vocal consistency. An **Agent** toggle turns the composer conversational (give it a brief, it orchestrates) — but for a scripted, deterministic batch use **direct mode** (Agent OFF), one prompt → one clip.

Requirements every run:
1. opencli daemon running + Browser Bridge extension connected to a Chrome profile that is **signed into labs.google/fx with Veo/Flow access (AI Pro or Ultra)**. Verify: `opencli doctor` and `opencli profile list` both show **connected**. Login is interactive — the user must sign in; you cannot.
2. The visible "✦" watermark and the model's native audio are dealt with in post (see Assembly).

## THREE DOM gotchas that will silently break you (read first)

1. **Radix/Flow controls ignore synthetic `.click()`.** The model/settings chip, menu items, Agent toggle, submit, download — all need **real pointer events**. Dispatch the full sequence:
   ```js
   function fire(el){const r=el.getBoundingClientRect();const o={bubbles:true,cancelable:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:0,pointerId:1,pointerType:"mouse",isPrimary:true};
     ["pointerdown","mousedown","pointerup","mouseup","click"].forEach(t=>el.dispatchEvent(t.startsWith("pointer")?new PointerEvent(t,o):new MouseEvent(t,o)));}
   ```
   `opencli browser click <ref>` is also synthetic for these — prefer `fire()` via `browser eval`. (Plain page buttons are fine with native click.)

2. **The composer is a Slate editor that eats a LEADING `@`.** A prompt that *starts* with `@Gajendra…` puts Slate in mention-query mode and the rest of the text is swallowed → the clip generates from an almost-empty prompt (you'll see the downloaded filename become just `@`, and the video is unrelated garbage). **Fix: never start a prompt with `@`.** Prepend a lead-in word (e.g. `"Cinematic devotional scene. "`). A **mid-text `@Name` in a single bulk `type` stays as plain text and resolves to the character** — no popup dance needed. (The autocomplete popup only appears if you type `@` as discrete keystrokes; the bulk insert via `opencli type` skips it, which is what we want.)

3. **`opencli browser type` REPLACES the composer content each call** — you cannot build a prompt incrementally. Type the whole prompt in one call. (After submit, Flow auto-clears the composer, so the next shot starts fresh.)

## Phase 0 — sanity
```bash
opencli doctor          # Daemon + Extension + Connectivity all green
opencli profile list    # note the profile alias, e.g. mxtkmkyn
opencli --profile <alias> browser open "https://labs.google/fx/tools/flow"
# If it lands on the marketing page / Google sign-in, the user must sign in first.
opencli --profile <alias> browser eval '(()=>[...document.querySelectorAll("button")].some(b=>b.innerText.trim()==="New project"))()'
```
Click **New project** (fire it) → you get a `/project/<uuid>` URL. Capture that PROJ url; everything keys off it.

## Phase 1 — build named Characters (the identity gate, STRICT)
For each character, navigate to `PROJ/characters` (the create composer is always there), type a description, submit, wait for the base image, set the name, click Done. Then it's summonable as `@Name`. Script: `bin/flow_make_character.sh <profile> <PROJ> <Name> <desc>`. Key steps it encodes:
- `opencli type "div[contenteditable=true]" "<desc>"` → focus composer → `opencli keys Enter` (Enter submits; the page transitions to the "Untitled Character" editor and starts a Nano-Banana base image).
- Poll until an editor `<input value="Untitled Character">` exists AND an `<img src*=media>` appears (the base image; ~30–60 s).
- Set the name on a **React-controlled input** via the native setter (plain `.value=` won't stick):
  ```js
  const inp=[...document.querySelectorAll("input")].find(e=>e.value==="Untitled Character");
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;
  s.call(inp,"Gajendra"); inp.dispatchEvent(new Event("input",{bubbles:true})); inp.dispatchEvent(new Event("change",{bubbles:true})); inp.blur();
  ```
- `fire()` the **Done** button → returns to project. Characters appear in **All Media** (filter: Characters) and resolve in prompts as `@Name`.
- Skip "Select a voice" if you're doing VO externally (we use xAI TTS, see Assembly).

**Gate hard here** — identity drift at the character stage poisons every clip. Screenshot each character; re-roll until it's right before generating any scenes.

## Phase 2 — generate clips (direct mode, one prompt → one clip)
Per shot, set the composer settings then type+submit. The settings chip (`button[aria-haspopup=menu]` whose text matches `Video|Image|Banana`) opens a popover with: type (Image / **Video** / Frames), aspect (9:16 / 16:9), count (1×–4×), **model** (Omni Flash), duration (4/6/8/10 s), credits estimate. `fire()` the chip, then `fire()` the exact-text option (`"Video"`, `"9:16"`, `"8s"`, `"1x"`), then `keys Escape`. Script: `bin/flow_gen_clip.sh` + batch `bin/gen_all_clips.sh` (resumable — skips existing `clips/shotN.mp4`).

Prompt rules (Omni Flash best practices, from deepmind.google/models/gemini-omni/prompt-guide):
- **Never start with `@`** (gotcha #2). Prepend a lead-in.
- **Motion is the gate** — write choreography with explicit physical verbs (lunges, swings, recoils, water bursts), weight, momentum. A gorgeous static "living photo" is a failure for a reel.
- Specify framing + camera move, subject + action, lighting/grade, style, location. Reuse a consistent **grade + camera** string across all shots for a coherent look.
- End with **"no text"** — never let Flow bake on-screen text (Telugu/Indic glyphs come out garbled). Captions are added in post.
- Reference characters mid-text as `@Name`.

Submit = `fire()` the `arrow_forward` button at `y>650`. Poll: track count of `video` elements with a `src*=media` URL; done when count increased AND no `\d+%` progress text remains (~2–3 min for 8 s).

**Download** (the fetch-to-blob path is CORS-blocked — the media URL 302s cross-origin): use Flow's own UI. `fire()` the newest video tile to open the viewer → `fire()` the button whose `<i>` text is `download` → the file lands in `~/Downloads` named from the prompt. Diff `~/Downloads/*.mp4` before/after to grab it, then move to `clips/shotN.mp4`.

**Moderation**: a clip that never starts (stays 0 %, no new tile) with a tile showing *"This generation might violate our policies"* = a silent block. Reword to **benevolent framing** — no distress/violence cues (drop "tear", "trembling", "pain", "claw/blade reaching AT a victim"); frame deities *softening*, divine light *dissolving*. (Cost us a shot until reworded.)

## Phase 3 — assembly (watermark → speed → VO → subtitles)
Flow clips have the bottom-right "✦" watermark and the model's own audio. Finish in post:
1. **Watermark removal** — `[[veo-watermark-remover]]` (allenk VeoWatermarkRemover, reverse alpha, ~1.4 fps CPU). `bin/postprocess.sh` does this first.
2. **Speed + mute** — listeners dislike slow narration; speed video and drop the native audio: `ffmpeg -i clean.mp4 -filter:v "setpts=PTS/1.5" -an -c:v libx264 -crf 18 out.mp4`. Speed VO independently pitch-preserved: `ffmpeg -i vo.mp3 -filter:a "atempo=1.25" vo_fast.mp3`. (Video 1.5×, VO 1.25× worked well — engaging but still intelligible.)
3. **Voiceover** — for Telugu/Indic, do NOT rely on Omni's audio; use `[[telugu-voice-and-text]]` (xAI TTS `eve`/`Leo`) per shot, capture each duration.
4. **Subtitles + final render** — **Remotion** (headless-Chromium HarfBuzz = correct Indic shaping; ffmpeg drawtext does NOT shape conjuncts). `OffthreadVideo muted` clips + per-shot `<Audio>` VO + synced subtitle + looped music bed → render 1080×1920. See `[[telugu-voice-and-text]]` for the comp.

**Continuous voiceover (avoid the "burst…gap…burst" feel).** If each shot's narration is much shorter than its clip, the VO plays in bursts with dead silence between — disjointed. Fix: make the **VO the spine** — write fuller narration that flows as one continuous story, then set each shot's `dur = vo_dur + ~0.2s` breath and **time-fit the clip to that** (`ffmpeg setpts=PTS*(target/clip_len)`) so motion maps onto the spoken line. Result: voice covers ~97% of the reel with only natural breaths, every clip + caption synced to its line. (`bin/rebuild_continuous.sh` does exactly this.) Keep VO at 1.25× for a fast-but-clear pace.

Backbone for the whole pipeline is a single `shots.json` (`id, scene, dur, chars, video_prompt, narration_te, onscreen_te, vo_dur`) that drives TTS, clip gen, and the Remotion timeline — exactly like the grok reel pipeline.

## Reusable scripts (in `~/Downloads/insta_story/gemini_prod/bin/`)
- `flow_make_character.sh` / `build_characters.sh` — Phase 1.
- `flow_gen_clip.sh` / `gen_all_clips.sh` — Phase 2 (resumable).
- `postprocess.sh` — Phase 3 watermark + speed + duration recompute.
- `tts_all.sh`, `gen_timeline.py`, `render.sh` + `remotion/` — VO + assembly.
- `tools/veo_wmremove` — the watermark binary.

## Webwright (rejected alternative)
`microsoft/Webwright` (Playwright coding-agent) was considered but is a poor fit for login-gated Flow: it launches its own Chromium and Google blocks automated login ("browser not secure") + it needs an LLM API key. opencli (real Chrome + the user's real Google session) is the right tool here.
