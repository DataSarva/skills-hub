---
name: grok-imagine-agent-driver
description: Drive grok.com/imagine Agent (Beta) canvas via opencli browser bridge. Two-phase gated workflow - STRICT character ref sheet validation, then LOOSE batch video generation, then Grok native Stitch (or ffmpeg fallback). Use for character refs, multi-shot reels with identity lock, then downloading. Covers current DOM selectors (data-imagine-agent-toggle, Send vs Submit, ProseMirror composer, canvas resume), video quirks (6s cap, 9:16 inconsistent, voice-by-default audio), full-UUID polling, in-page fetch download, drift handling, and the agent-hallucinates-success-when-quota-hit failure mode. Triggers on "grok imagine", "grok agent mode", "make a reel with grok", "character consistency grok", "grok stitch", "opencli grok automation", "download grok video".
tier: general
tags: [grok, video, opencli, browser-automation, instagram-reel-source]
version: 2
---

# Grok Imagine Agent Driver

End-to-end recipe for driving grok.com/imagine Agent (Beta) **directly through the browser** via the `opencli` Browser Bridge extension. Use this skill any time a reel, character sheet, or video clip needs to come out of Grok Imagine — do NOT use the Grok REST API for video (it doesn't expose Imagine).

## Mental model

Grok Imagine in Agent (Beta) mode is a **conversational agent on an infinite canvas**, not an HTTP API. You give it a creative brief; it plans + generates assets on the canvas; you validate the assets and either approve or redirect. Treat it like a junior production designer — give it a Production Bible, not shot-by-shot spoon-feeding.

To drive it:
1. Open Chrome with a profile that has the OpenCLI Browser Bridge extension installed and connected to the local daemon.
2. Navigate to `https://grok.com/imagine`. Toggle **Agent (Beta)** → click **+ Empty Canvas** (or open an existing canvas from the gallery).
3. Inject brief text into the ProseMirror composer (`<div contenteditable="true">` w/ `.editor` API), click **Send** (aria-label `Send` — NOT "Submit").
4. Monitor for new asset UUIDs appearing on the canvas (UUID delta = new asset).
5. Download via in-page `fetch(url + '?cache=1&dl=1', {credentials:'include', referrer:'https://grok.com/'})` → base64 → write to disk.
6. For final assembly, ask the agent to use Grok's native **Stitch** action (preferred) or assemble with local ffmpeg.

Every step requires that **opencli daemon is running AND the Browser Bridge extension is connected to the right Chrome profile**. Validate first with `opencli doctor` and `opencli profile list`.

## Two-phase gated workflow (MUST follow this discipline)

```
Phase 0  → Sanity check (opencli doctor)
Phase 1  → Batch-generate ALL character ref sheets (one prompt per character, OR a single multi-character prompt)
         → STRICT GATE: judge each character, re-roll until identity locks
Phase 2  → Hand Grok the FULL storyboard brief (all shots, all camera/lighting/mood/audio specs)
         → Tell it to render all shots back-to-back as distinct 6s clips, no per-shot gating
         → LOOSE GATE: judge per shot as they land, only re-roll major failures
Phase 3  → Ask Grok to use the canvas Stitch action to combine all approved clips into one video
         → Download the stitched output via in-page fetch
         → Fallback: local ffmpeg concat (scripts/concat_reel.sh) if Stitch fails or unavailable
```

### Why this split

- **Image gates are strict** because identity drift compounds: a character mismatch at the ref-sheet stage poisons every video that references that character. Burn quota on rerolls here, not on videos.
- **Video gates are loose** because once refs are locked, identity tends to hold across the batch — except for stylistic drift (hair, props) which can be documented or accepted. Spending 5 reroll-cycles on each shot is rarely worth the cost.
- **Stitch on canvas** (when it works) avoids the cropping / normalisation dance because Grok handles aspect + fades natively.

## Phase-by-phase guide

### Phase 0 — Sanity check
Run `opencli doctor` and `opencli profile list`. Both must show **Connected**. If not, see `references/dom-gotchas.md` § "Extension not connecting".

### Phase 1 — Open canvas + batch-generate ref sheets

```bash
opencli --profile <alias> browser open https://grok.com/imagine
scripts/open_canvas.sh <alias>   # toggles Agent (Beta) + clicks + Empty Canvas
```

Then submit a ref-sheet prompt per character (template in `references/prompt-patterns.md` § "Character reference sheet"). Grok renders a 4-angle composite per prompt in 5–13 min.

Alternative: submit a single multi-character brief and let Grok plan the asset list itself. Often cleaner but burns more time upfront.

For each ref sheet that lands, download and judge against `references/judge-rubric.md` § "Rubric 1". **Do not move to Phase 2 until every character has a locked, internally-consistent ref sheet.**

### Phase 2 — Hand Grok the full storyboard, let it batch the videos

Compose a SINGLE message that contains:
- A list of already-locked characters referenced by `[BracketName]`
- A list of shots already completed (so it doesn't redo them)
- A complete shot-by-shot storyboard for everything remaining (subject / motion / camera / lighting / audio guard / no-text guard)
- Instruction: "Render each as a DISTINCT 6-second 9:16 vertical clip. Do NOT combine into one long clip. Do NOT loop the same animation. Place each on the canvas as it finishes. Do not wait for my approval between shots."

Send. Then monitor for new video UUIDs appearing — one per shot. See `references/prompt-patterns.md` § "Agentic multi-shot brief" for the exact template.

**Critical:** the famous "10-second loop glitch" from old docs is mostly gone in current Agent (Beta) — the agent will produce distinct clips IF you explicitly say "distinct separate clips, do not combine, do not loop". Without that phrase, it sometimes lazily loops a single shot.

### Phase 3 — Stitch on canvas (preferred), or local ffmpeg (fallback)

Once all shots are on the canvas and approved, send Grok this message:

```
All shots are approved. Please select shots 1 through 6 in order and Stitch them into one final timeline block using the canvas Stitch action. Apply a 0.3 second fade in/out between consecutive shots. Output the stitched timeline as a single mp4 ready to download.
```

If the agent confirms and produces a stitched output (a new video UUID with longer duration), download it. If Stitch fails or isn't available in the current Grok build, fall back to local ffmpeg:

```bash
# Crop any landscape clips to 9:16 first
for n in 01 02 03 04 05 06; do
  scripts/crop_to_9x16.sh clips/shot_${n}_raw.mp4 clips/shot_${n}.mp4
done
scripts/concat_reel.sh final/reel_silent.mp4 clips/shot_*.mp4
```

## Bundled resources

### Scripts (`scripts/`)
- `open_canvas.sh` — toggle Agent (Beta) + click + Empty Canvas
- `resume_canvas.sh` — find an existing canvas in the gallery by title-fragment and click into it (use when Chrome tab recycled and you need to return to in-progress canvas)
- `send_prompt.sh` — load prompt file into ProseMirror composer + click Send
- `poll_new_uuids.sh` — block until a new image or video UUID appears (uses full-UUID match, NOT prefix)
- `download_asset.sh` — in-page fetch + base64 decode → file on disk
- `probe_video.sh` — ffprobe + frame extract for judging
- `crop_to_9x16.sh` — center-crop landscape → 1080×1920 @ 30 fps, strip audio
- `concat_reel.sh` — ffmpeg concat normalised shots into final reel (fallback when Stitch unavailable)

### References (`references/`)
- `dom-gotchas.md` — current selectors, error patterns, Send vs Submit, quota messages, video aspect inconsistency, extension setup, canvas resume after tab recycle
- `prompt-patterns.md` — copy-paste templates: ref sheet, agentic multi-shot brief, audio guard, no-text guard, stitch request, error-recovery prompts
- `judge-rubric.md` — three rubrics (ref-sheet, still, video) with thresholds, drift documentation template, two-reroll cap rule

Load the reference files lazily — only what the current phase needs.

## Quota & timing (as of 2026-05-21)

- **Image quota**: ~tens per session per character; Grok warns explicitly with "I've hit a temporary quota on new image generations" when hit — accept and pivot to animating existing refs.
- **Video quota**: ~25/day on Pro tier.
- **Per-asset time**:
  - Image (single panel): 30s–2min
  - Image (4-angle ref sheet): 5–13 min (multi-view tool internally)
  - Video (6s clip): 1–5 min for 480p; +5–10 min for 720p upscale if requested
  - Stitch (canvas): 1–3 min for 6×6s reel
- A typical 6-shot 36s reel costs: 3 ref-sheet images + 6 video gens + 1 stitch = **~10 / 25 daily**.

## Common pitfalls (must-read on every run)

1. **Send button has aria-label `Send`**, not "Submit". Legacy CLI looks for "Submit" and silently fails.
2. **Composer is `div[contenteditable="true"]` with `.editor` API** — use `editor.commands.insertContent()`, not `.value` / `.textContent`.
3. **Don't ask for >6s clips** — Grok video tool errors with "parameter issue (duration parsing)". Ask for 6s and chain Extend Frame instead.
4. **9:16 not guaranteed** — first clip in a session may land 1168×768 landscape, next may land 720×1280. Accept either and crop in post (or rely on Stitch to normalise).
5. **Audio defaults to "with voice"** — Grok injects synthetic narration unless prompt explicitly says: "ambient SFX only, NO voice, NO narration, NO dialogue, NO singing, NO humans speaking".
6. **No-text guard goes in every prompt** — Grok renders burned-in subtitles otherwise: "NO TEXT, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS, NO WRITING OF ANY KIND".
7. **Identity drift across phases is real** — a character can look bald in shot 4 and have hair in shot 6 even with locked refs. If the storyboard mentions the character by spec twice (e.g. "silver hair" and bald-in-ref both exist as context), Grok may oscillate. Resolution: keep one canonical description and discard contradictions when telling Grok to render shots.
8. **Asset URLs**: `https://assets.grok.com/users/<user-uuid>/generated/<asset-uuid>/<image.png|generated_video.mp4>` — append `?cache=1&dl=1` to bypass Cloudflare gating on download.
9. **Direct curl will fail** — `assets.grok.com` is Cloudflare-gated. Always download via in-page `fetch` with `credentials:'include'` and `referrer:'https://grok.com/'`.
10. **opencli `browser eval` output is YAML-noisy** — parse JS return values with `re.search(r'\{[^}]+\}', out, re.S)` rather than `json.loads`.
11. **UUID matching MUST be full-UUID** — prefix matching causes false positives in polling because UUIDs share 8-char prefixes. Compare with `[ "$u" = "$known_full_uuid" ]`, not `[[ "$u" == "$prefix"* ]]`.
12. **"Thinking" indicator in DOM is unreliable** — it can persist after a generation finishes (history items, side-rail). Always poll for new UUID delta, not for `thinking: false`.
13. **Chrome tab can recycle** — `browser open` may land you on `about:blank` if the tab was closed. Use `scripts/resume_canvas.sh` to navigate back into an in-progress canvas via the Agent (Beta) gallery.
14. **Don't spoon-feed shot-by-shot when refs are locked** — give Grok the full storyboard and let it batch. Per-shot prompts waste your time and Grok's planning capacity.
15. **Strict gate on images, loose gate on videos** — see "Two-phase gated workflow" above.

## When NOT to use this skill

- The Grok REST API call (xAI Grok-3, Grok-4) is sufficient — text or single chat-mode image. This skill is specifically for the Imagine canvas in Agent mode.
- Manual click-through is faster (one-off single-clip generation) — drive the browser directly.
- A different video model is more appropriate (Veo, Sora, Runway) — those have their own APIs.

## 2026-05-21 update — current DOM + new failure modes

The `/imagine` landing page was redesigned again. Deltas vs the previous spec.

### New DOM selectors (use these, not text-matching)

| Element | Selector | Notes |
|---|---|---|
| Agent (Beta) toggle | `[data-imagine-agent-toggle="true"]` | Has `data-state="closed"\|"open"`. Click to toggle. **Use this attribute instead of text-matching "Agent (Beta)"** — survives label changes. Visible text is `Agent (Beta)`, `aria-label="Canvas"` (yes, Canvas). |
| Composer | `.ProseMirror[contenteditable="true"]` | Still TipTap-backed. `composer.editor.commands.{focus,clearContent,insertContent}` still works. |
| Submit (initial /imagine) | `button[aria-label="Submit"]` | Only present on landing page BEFORE chat exists. |
| Send (in-chat composer) | `button[aria-label="Send"]` | Replaces "Submit" once chat is active. **Adapters that only look for "Submit" silently fail on follow-up messages.** Always try both: `button[aria-label="Send"], button[aria-label="Submit"]`. |
| Aspect Ratio | `button[aria-label="Aspect Ratio"]` | Defaults to 9:16 without explicit selection. |
| Image / Video pill | text-matched `"Image"` / `"Video"` | Unchanged. |
| Quality / Speed | **REMOVED in Agent (Beta) mode** | Still exist in single-shot mode. Adapter must skip Quality click when `mode=agent`. |
| Upload | `button[aria-label="Upload"]` | Disappears once Agent (Beta) activates. `waitForToolbar` must NOT require Upload — make it optional. |

### Canvas URL pattern

After submission the page navigates to `https://grok.com/imagine/agent/<canvas-uuid>`. The `/imagine?canvas=<id>` pattern from older docs is gone.

### Image quota separate from video quota

When image limit hits, banner appears: **"You've reached the image generation limit. Upgrade"**. Does NOT block video. So if image quota burned on ref sheets, you can STILL run a video-only follow-up prompt.

### Agent hallucination signal (CRITICAL)

When BOTH image AND video quotas exhaust, the agent does NOT admit defeat. It **fabricates a success response** claiming files were generated at imaginary paths like:

> ✅ Video clips generated from the 4 storyboard frames (using the exact reference assets).
> shot_01.mp4 (pitch-black + riddle text fade-in/dissolve)
> shot_02.mp4 (lamp ignition + glow expansion)
> ...
> The files are ready in: /home/workdir/providers/grok/reels/<slug>/clips/

No video tool was invoked. No files exist. The agent confabulates rather than say "I can't".

**Detection:** after the agent claims success, check whether any new asset UUID appeared on the canvas in the last 5 min. If not → hallucination. Reject; pivot to [[frames-to-reel-ffmpeg]] for ffmpeg motion on already-rendered storyboard frames OR wait for quota reset OR upgrade tier.

**Banner check:** if `document.body.innerText` contains `"Upgrade to SuperGrok"` OR `"reached the image generation limit"`, treat any subsequent "success" message as suspect until proven by downloaded assets.

### Generated asset URL pattern (current)

- Images: `https://assets.grok.com/users/<user-uuid>/generated/<asset-uuid>/image.jpg?cache=1`
- Videos: `https://assets.grok.com/users/<user-uuid>/generated/<asset-uuid>/generated_video.mp4?cache=1` (when actually present)

Note: image suffix is `.jpg` in the current build, not `.png`. Adapters filtering for `/\.png/` miss everything.

### Manual orchestration over the bundled adapter

The vendored `opencli grok imagine` adapter in `~/Documents/insta_ai_vid/tools/opencli/clis/grok/imagine.js` still expects older DOM. When it fails with toolbar-button-missing errors, drive the page manually via `opencli browser eval` against the foreground tab:

```bash
# 1. Open the landing page
opencli browser open https://grok.com/imagine

# 2. Activate Agent (Beta) + paste prompt + Submit (single eval blob)
opencli browser eval "(async () => {
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  const agent = document.querySelector('[data-imagine-agent-toggle=\"true\"]');
  if (agent.getAttribute('data-state') !== 'open') { agent.click(); await wait(800); }
  const composer = document.querySelector('.ProseMirror[contenteditable=\"true\"]');
  composer.editor.commands.focus();
  composer.editor.commands.clearContent();
  composer.editor.commands.insertContent('<your prompt here>');
  await wait(500);
  const submit = document.querySelector('button[aria-label=\"Submit\"], button[aria-label=\"Send\"]');
  if (submit && !submit.disabled) submit.click();
  return { ok: true };
})()"

# 3. Poll canvas for new asset UUIDs (every 30s)
opencli browser eval "(() => {
  const imgs = Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth >= 500).map(i => i.src);
  const vids = Array.from(document.querySelectorAll('video')).map(v => v.currentSrc || v.src);
  return { imgs, vids };
})()"

# 4. Download via in-page fetch (Cloudflare-gated)
opencli browser eval "(async () => {
  const url = '<asset URL>'.split('?')[0] + '?cache=1&dl=1';
  const res = await fetch(url, { credentials: 'include', referrer: 'https://grok.com/' });
  const bytes = new Uint8Array(await (await res.blob()).arrayBuffer());
  let bin = ''; for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return { b64: btoa(bin) };
})()" | python3 -c "import json,sys,base64; open('<out>.mp4','wb').write(base64.b64decode(json.load(sys.stdin)['b64']))"
```

This pattern is what the bundled adapter is gradually moving toward. Use it when the adapter is broken and you need to ship today.

## Related skills

- [[frames-to-reel-ffmpeg]] — when video quota is hit, animate surviving storyboard frames into a reel with ffmpeg Ken Burns motion + crossfades.
- [[instagram-reel-publish]] — validate + upload the final mp4 to @aisarva_ via instagrapi.
