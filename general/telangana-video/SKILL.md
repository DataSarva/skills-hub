---
name: telangana-video
description: Case-study / inspiration reference for the "తెలంగాణ పేరు ఎక్కడిది?" viral history reel (the name-origin of Telangana) built 2026-05-30. Invoke when making a NEW reel and you want a worked example to take inspiration from — the clapback-hook-from-a-real-clip concept, the Telangana-slang register, the 4-edition matrix, key-word overlays, anthem BGM, and which pipeline knobs were used. This is a REFERENCE, not an executable pipeline — the engine is insta-reel-scaffold and the orchestrator is insta-video. Also the TEMPLATE for how every finished reel gets its own thin reference skill.
tier: general
tags: [reel, case-study, telugu, telangana, reference, viral, history]
version: 1
---

# telangana-video — case study (inspiration reference)

A worked, shipped example to copy *ideas* from when building the next reel. Not a pipeline — to build,
use [[insta-reel-scaffold]] (engine) under [[insta-video]] (orchestrator). Project assets live at
`~/Downloads/insta_story/grok_agent_telangana/`.

## The video

**"తెలంగాణ పేరు ఎక్కడిది?"** — the real 2000-year history of the *name* Telangana (Gondi "తెలంగాధ్" →
Trilinga Desha → తెలుగు అంగన → Mulk-i-Tilang → the 1418 Tellapur "తెలుంగానపురం" stone inscription →
Nizam era → 1956 merger → 2 June 2014 statehood). Source: `telangana/raw_story.md` (a dry documentary)
→ rewritten as a punchy, proud, spoken-Telangana reel.

## What made it work (steal these)

1. **Clapback hook from a REAL clip.** Open on a real IG clip of someone *dismissing* Telangana
   ("there's no word Telangana in the dictionary"), hard-cut into a furious rebuttal
   ("**తెలంగాణ అనే పదమే లేదా?!**"). Pattern-interrupt + correcting a false claim = shares + comments +
   completion (the IG signals that matter most). The real clip's burned-in caption was removed by
   filling its letterbox bar black; the user trimmed it in the bundled `hook_trimmer/` browser UI.
2. **Raw spoken-Telangana register**, not bookish Telugu. HARD RULE from the user: **never use "బై"**
   anywhere, any voice. Gender-neutral narration so one script serves both male & female.
3. **Open on anger, end on pride.** Beat 1 = angry existence-questioning hook; final beat = the 2014
   statehood swell. Cut the spoken "like & follow" CTA — replace with a silent on-screen **end-card**.
4. **Key-word overlays** of the primary terms/synonyms (తెలంగాధ్, త్రిలింగ→తెలింగ→తెలంగాణ, తెలుగు అంగన,
   ముల్క్-ఇ-తిలంగ్, తెలుంగానపురం, తెలంగాణ•మరాఠ్వాడా) — centre pill, staggered under the top kicker. They
   double-lock pronunciation of rare proper nouns the TTS can fumble.
5. **Famous-song BGM** = *Jaya Jaya He Telangana* (flute instrumental bed + vocal swell at the climax).
6. **Cinematic-realistic Grok Imagine clips** (documentary B-roll, no recurring characters → skip the
   character ref-sheet gate). A 2nd B-roll batch + **multi-clip-per-beat** added density / "more video
   faster". Diegetic text (map labels, "Jai Telangana" banners, inscription carvings) was kept.

## Creative decisions / knobs used

- **Editions:** full (`VO_X≈1.25`, ~94–110s) + 90s (faster, all beats) × male (Puck/pro) & female
  (Leda/flash). v2 hero = `telangana_female_v2.mp4`: full's natural voice, beats 1→10 ending on 2014,
  multi-clip beats, key-word text, `VO_X≈1.35`, ~89s.
- **Pronunciation at speed:** female flash slurred proper nouns when sped hard. Fix = crisp-articulation
  style prompt + **enunciation-space the proper nouns** at the source (`ముల్క్ ఇ తిలంగ్`,
  `తెలుంగాన పురం`) — NOT just slowing down. Over-speeding (1.55–1.6×) also over-stressed the opening
  word; the user preferred the natural pace.
- **Replace clips that "don't make sense"** — an AI "hand rubbing a map with an eraser" read as
  nonsense; regenerated as a clean 1950s newsreel instead.

## Pointers

- Project: `~/Downloads/insta_story/grok_agent_telangana/` (`shots_v2.json`, `bin/`, `VO_SCRIPT.md`,
  `caption.json`, `yt_metadata.json`, the 4 `telangana_*` renders + `telangana_female_v2.mp4`).
- Memory: `project_telangana_reel` (this host's auto-memory).
- Engine + how-to: [[insta-reel-scaffold]]. Voice: [[telugu-raw-reel-voice]]. Clips:
  [[grok-imagine-agent-driver]]. Text: [[telugu-voice-and-text]]. Foley: [[reel-sfx-foley]].

## This file is the template

Every finished reel should get a thin skill like this: **concept · what worked · knobs · pointers to
assets + the engine.** Keep it short (inspiration, not a runbook). Name it `<topic>-video`. Create via
`skills-hub new <topic>-video --tier general`, then `git push && skills-hub sync`.
