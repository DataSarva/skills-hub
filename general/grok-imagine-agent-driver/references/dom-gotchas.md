# DOM gotchas & current selectors (2026-05-21 snapshot)

The Grok Imagine UI changes regularly. Re-verify before any production batch by snapshotting visible buttons:

```bash
opencli --profile <alias> browser eval 'Array.from(document.querySelectorAll("button")).filter(b => b.offsetParent !== null).map(b => ({ aria: b.getAttribute("aria-label"), text: (b.textContent||"").trim().slice(0,30) }))'
```

## Toolbar (landing page `https://grok.com/imagine`)

Bottom of viewport (`y` ≈ 700):

| Element | Selector |
|---|---|
| Image toggle | `button` with `text === "Image"`, `aria === null` |
| Video toggle | `button` with `text === "Video"`, `aria === null` |
| Speed pill | `button` with `text === "Speed"`, `aria === null` |
| Quality pill | `button` with `text === "Quality"`, `aria === null` |
| Aspect Ratio (current 9:16) | `button[aria-label="Aspect Ratio"]` with text === "9:16" |
| Agent (Beta) toggle | `button[aria-label="Canvas"]` with `text === "Agent (Beta)"` |
| Upload images | `button[aria-label="Upload images"]` |
| Send | `button[aria-label="Send"]` (**NOT "Submit"**) |
| Stop (when generating) | `button[aria-label="Stop"]` (replaces Send while in-flight) |

## After Agent (Beta) is toggled

Landing flips to a gallery of existing canvases. Bottom shows quick-start chips: `+ Empty Canvas`, `Upload Images`, `Historical Stories`, `Create Worlds`. Click `+ Empty Canvas` to enter a fresh canvas.

## Inside a canvas

| Element | Selector |
|---|---|
| Canvas title | `button` with `text === "Untitled"` (or auto-named text) in the top center. Clicking it is unreliable from JS — accept auto-name. |
| Whiteboard area | center pane, zoom controls bottom center (`aria="Zoom In"`, `aria="Zoom Out"`) |
| Right panel composer | single `div[contenteditable="true"]` with `placeholder="Type a message..."` — it has an `editor` property exposing TipTap/ProseMirror commands (`editor.commands.insertContent(...)`) |
| Send button (right panel) | `button[aria-label="Send"]` |
| Template chips above composer | `Historical Stories`, `Create Worlds`, `Short Film`, `UGC Product Stories` — clicking these auto-fills the composer with a template prompt |

## Asset URL pattern

Every generated image / video lives at:

```
https://assets.grok.com/users/<user-uuid>/generated/<asset-uuid>/<filename>
```

| Asset | Filename |
|---|---|
| Image | `image.png` (or sometimes `image.jpg`) |
| Video | `generated_video.mp4` |
| Multi-part composite | `image.png?cache=1` (same URL, served from different cache) |

**Download trick:** append `?cache=1&dl=1` to bypass Cloudflare content-type gating, and call the fetch from inside the page with `credentials:'include'` and `referrer:'https://grok.com/'`. Direct `curl` will fail.

## Error / status messages (right panel text)

Watch for these in the rightmost text column (`x > 800`, `y < 600`):

| Pattern | Meaning | Action |
|---|---|---|
| `I've hit a temporary quota on new image generations` | Per-session image quota exhausted | Accept existing assets as references; pivot to video animation of refs |
| `parameter issue (duration parsing)` | Asked for a clip longer than the native ~6s limit | Re-send with `--duration 6` and chain Extend Frame |
| `Unfortunately, the video generation tool encountered` | Video tool errored (often duration or aspect) | Read the suggested next-step (Grok usually offers retry / shorter / different aspect) |
| `Generating the N-second cinematic video clip` | Acknowledgment, generation in progress | Routine — keep polling |
| `Selecting reference assets for video generation` | Agent is composing the call | Routine |
| `Planning the multi-view generation workflow` | Agent is composing a ref sheet | Routine — long wait coming (5–13 min) |

## Video aspect ratio (CRITICAL non-determinism)

Grok's video tool **inconsistently** honors aspect ratio requests:
- First clip in a fresh session might return **1168×768 landscape** despite `vertical 9:16` in the prompt.
- A subsequent clip from the same canvas with similar prompt returns **720×1280 (9:16)** as requested.
- No reliable trigger has been identified yet. Solution: accept whatever lands, center-crop to 1080×1920 in post via `scripts/crop_to_9x16.sh`.

## Extension not connecting (`opencli doctor` shows MISSING)

Common causes:
1. Extension loaded in a Chrome profile **other than** the one currently active. Switch to the profile that has OpenCLI in `chrome://extensions/` and toggled ON.
2. Extension is the legacy v1.0.2 unbuilt folder (`tools/opencli/extension/opencli-extension-v1.0.2/`) which lacks `dist/background.js`. Build the v1.0.6 parent folder instead:
   ```bash
   cd tools/opencli/extension && npm install && npm run build
   ```
   Then `Load Unpacked` → select `tools/opencli/extension/` (the parent, not the v1.0.2 subfolder).
3. Daemon stale. `opencli daemon restart` won't help if extension hasn't re-handshaked — reload it from `chrome://extensions/` and click the OpenCLI toolbar popup → connect.
4. Verify both sides see each other: `opencli profile list` should show `<alias> — connected v1.0.6`.

## Native Stitch action (server-side reel assembly)

In Agent (Beta) mode you can ask Grok to combine clips on the canvas into one final timeline:

```
Please use the canvas Stitch action to combine shots 1 through N in order into one final timeline block. Apply a 0.3s fade in/out between consecutive shots.
```

When successful, Grok produces a new video tile on canvas with duration ~ sum of input clips. Same `https://assets.grok.com/users/.../generated/<uuid>/generated_video.mp4` URL pattern — download via `scripts/download_asset.sh`.

**Advantages over local ffmpeg:**
- Aspect normalisation handled (mixed landscape/portrait inputs are auto-cropped)
- Native cross-fade transitions
- Single concatenated audio track (no glitches at seams)
- No need to keep all source clips on local disk

**When Stitch fails or is unavailable**, fall back to `scripts/concat_reel.sh` after cropping mixed-aspect clips with `scripts/crop_to_9x16.sh`.

## Canvas resume after Chrome tab recycle

The opencli `browser open` can land on `about:blank` if the previous Chrome tab was closed/recycled. Re-entry requires:

1. Navigate to `https://grok.com/imagine` (the landing page)
2. Toggle Agent (Beta) to enter the canvas gallery
3. Locate the in-progress canvas by title fragment (most-recent canvas with that title is usually at the top)
4. Click the title's clickable parent (often a `<div role="button">` 1-2 levels up from the `<span>` holding the title text — walk up the DOM and click the first ancestor with `onclick`, `tagName === "BUTTON"`, or `role === "button"`)
5. Verify the composer (`div[contenteditable="true"]` with `.editor` API) is present after navigation

Scripted in `scripts/resume_canvas.sh <profile> "<title fragment>"`. Canvas titles auto-generate from the first prompt (e.g. "Reference sheet for a single c..."), so the title fragment is whatever Grok auto-named it earlier.

The canvas URL `https://grok.com/imagine/agent/<canvas-uuid>` is also stable — if you saved it from a prior session, navigate directly via `opencli browser open <url>` to skip the gallery entirely.

## "Thinking" persistence false positive

The string `Thinking|Generating|Planning|Rendering` may persist in the DOM after generation finishes (it can appear in side-rail history items or stale agent-state widgets). **Do not use `thinking: false` as a completion signal.** Instead poll for a new asset UUID appearing in the page (`scripts/poll_new_uuids.sh`).

## Output parsing of `opencli browser eval`

The CLI wraps JS return values in YAML-ish output with surrounding noise (`Update available:`, `Extension update available:`, `Run: npm install ...`). Don't trust the exit-code or pipe straight to `json.loads`. Pattern that works:

```python
import re, sys
data = sys.stdin.read()
m = re.search(r'\{[^}]+\}', data, re.S)  # crude but reliable for single-line eval returns
result = m.group(0) if m else '{}'
```

For multi-line return values (arrays of objects), redirect to a temp file and grep with `-oE` for the field you need.
