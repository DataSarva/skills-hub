# Judge rubrics

For each downloaded asset, score against the appropriate rubric BEFORE moving to the next step. Use multimodal vision to view the image / extracted frame. Threshold to advance: **weighted score ≥ 7.5/10** AND no auto-fail trigger.

## Gate strictness by phase

- **Phase 1 (character ref sheets) → STRICT GATE.** Identity drift here compounds across every video. Re-roll until ref sheet is internally consistent and locks the character. Two reroll attempts max, then accept and document the canonical character.
- **Phase 2 (video shots, batched) → LOOSE GATE.** Refs already locked so identity tends to hold. Most shots will pass on first render. Re-roll only major failures (broken identity, wrong subject, dense voice in audio). Cosmetic drift (hair length, prop angle) → document and keep.
- **Phase 3 (stitched final) → STRICT GATE on the final mp4.** Re-stitch with different fade/order if transitions are jarring or shots are misordered.

## Auto-fail triggers (any one = redo or accept-with-document, never silently move on)

- Visible text, labels, panel numbers, captions, watermarks, or any rendered writing
- Subject identity wrong (asked for woman, got man; asked for child, got adult)
- Forbidden elements present (asked for bare tree, got leaves/fruit; asked for empty hands, got props)
- Content that violates safety policy (will be visible as a refusal placeholder)

## Rubric 1 — Character reference sheet

| Criterion | Weight | Scoring guide |
|---|---|---|
| Internal consistency across 4 panels | 40% | 10: identical face/clothing/props all 4; 7: minor drift in pose or one panel slightly different; 4: clear identity change between panels |
| Visual detail richness | 25% | 10: photoreal fabric, skin, prop texture all crisp; 6: stylized or soft; 3: muddy / low detail |
| Mood + personality match to spec | 20% | 10: nailed the descriptor adjectives (e.g. "expectant", "serene"); 7: close; 4: generic |
| Lighting per spec | 15% | 10: soft diffused studio as requested; 6: harsh or inconsistent across panels |

**Acceptable drift to document and keep:** hair / facial hair details that diverge from spec but stay consistent across all 4 panels. Identity lock matters more than spec-exactness for downstream animation.

**Re-roll triggers:** identity drift between panels, forbidden props present, missing major distinguishing features.

## Rubric 2 — Still frame (skip if going straight to video)

| Criterion | Weight | Scoring guide |
|---|---|---|
| Identity vs. reference sheet | 40% | 10: indistinguishable from ref; 6: same person but minor drift; 3: clearly different |
| Composition (vertical 9:16 framing, focal arrangement) | 25% | 10: subject placement is cinematic, leaves room for motion; 6: workable but flat |
| Mood + lighting per scene spec | 20% | 10: golden-hour / dawn / etc. spot-on; 6: close; 4: wrong time of day |
| Aspect ratio (9:16 honored) | 10% | 10: 1080×1920 or near; 5: square or 4:3; 0: landscape |
| Tech cleanliness (no text, no artifacts) | 5% | binary 10 or 0 |

## Rubric 3 — Video clip (6s)

| Criterion | Weight | Scoring guide |
|---|---|---|
| Identity preservation vs. reference sheet | 35% | 10: perfect lock across all 6 seconds; 7: stable but slight micro-drift on detail; 4: face / clothing changes mid-clip |
| Cinematic composition & motion | 25% | 10: smooth single-arc camera move, subject positioning excellent; 6: stutter or awkward camera; 3: chaotic |
| Mood + lighting consistency | 20% | 10: matches reel aesthetic, lighting stable across frames; 6: lighting wobbles; 3: stylistic break |
| Aspect ratio (9:16 honored) | 10% | 10: 720×1280 or 1080×1920; 5: square; 0: landscape (cropable but lossy) |
| Audio (ambient only, no voice) | 10% | 10: pure ambient bed, no speech; 5: faint synthetic narration; 0: clear human voice (will fight in post) |

**Frame extraction for judging:**
```bash
ffmpeg -y -ss <duration/2> -i shot_NN_raw.mp4 -frames:v 1 -q:v 2 shot_NN_frame.jpg
```

**Audio voice-detection quick check:**
```bash
ffmpeg -i shot_NN_raw.mp4 -af silencedetect=n=-30dB:d=0.5 -f null - 2>&1 | grep silence_duration | wc -l
```
If silence_duration count is 0 across the 6 seconds, audio is dense — likely contains speech. If ≥ 2 silence intervals, audio is sparse — likely ambient bed only. (Not a substitute for actually listening when stakes are high.)

## Drift documentation template

When accepting a result with known drift, write a one-line note in `<run>/DRIFT_LOG.md`:

```
shot_NN — accepted with drift: <what drifted, e.g. tree trunk slightly forked differently from ref sheet>. Reason: <re-roll quota cost vs. severity>.
```

This keeps the chain of decisions auditable when the final reel is reviewed.

## Cross-shot identity drift (multi-character reels)

When the SAME character appears in multiple shots, Grok can render them differently each time even when refs are locked. Common drift axes:
- Hair (silver vs bald)
- Facial hair (clean-shaven vs moustache)
- Skin tone (subtle)
- Prop fidelity (basket weave pattern, dhoti drape)

If drift between shots is detected:
1. Identify which version is canonical (usually the earlier or more prominent shot).
2. In the next prompt to Grok, explicitly say: "The character [<Name>] in shot N had <feature A>, but the canonical look is <feature B> from shot M. For all remaining shots, render [<Name>] exactly as <feature B>."
3. Re-render the divergent shots only if they're foreground / hero shots. Background appearances can be accepted.

Document accepted drift in `<run>/DRIFT_LOG.md`.

## When to stop iterating

**Hard rule: max 2 re-rolls per asset.** After that, accept and document. Reasons:
- Grok's randomness means rerolls often drift further, not closer.
- Quota burn compounds across shots — 6 shots × 3 rerolls each = 18 video gens = nearly daily cap.
- The cumulative "good enough" reel ships; the perfectionist reel never does.
