---
name: panchayat-instagram-import
description: Import the latest saved Instagram reels/videos from the datasarva25 Chrome profile into the Panchayat Reference Studio canvas. Use when the user asks to pull, refresh, import, or replace the Panchayat canvas with the latest/recent saved Instagram reels, especially "latest 50 saved reels/videos", "recent saved reels", or "datasarva Instagram saved".
---

# Panchayat Instagram Import

## Overview

Use this skill to refresh `/Users/aisarva/Documents/panchayat` with the latest saved Instagram videos from the Chrome profile `Profile 2` (`datasarva25@gmail.com`). The app runs on `http://localhost:3003`.

Prefer the bundled script. It preserves the known working path: copy only the datasarva Instagram cookie DB into a temporary Chrome profile, attach through Chrome DevTools Protocol, call Instagram's saved-posts API, replace the Panchayat canvas with exactly 50 videos, cache media through the app API, then delete the temporary browser profile.

## Quick Run

From the repo:

```bash
cd /Users/aisarva/Documents/panchayat
/Users/aisarva/Documents/panchayat/.venv-smoke/bin/python \
  /Users/aisarva/.codex/skills/panchayat-instagram-import/scripts/import_datasarva_saved_reels.py
```

If `.venv-smoke` or Playwright is missing:

```bash
cd /Users/aisarva/Documents/panchayat
npm run smoke:ui:setup
```

Keep the app running on port `3003` before caching:

```bash
npm run dev
```

## Workflow

1. Use Chrome profile `Profile 2`, not `Default` or `Profile 1`.
2. Do not spend time repairing OpenCLI Browser Bridge first. It has repeatedly failed with `Browser Bridge extension not connected`.
3. Use Chrome DevTools direct access through the bundled script.
4. Replace the active canvas, do not append:
   - delete canvas notes, categories, and edges
   - move old on-canvas videos off-canvas
   - insert/update the latest 50 videos on-canvas
5. Cache the 50 videos with `POST http://localhost:3003/api/cache`.
6. Verify:

```bash
sqlite3 -header -column .panchayat-data/panchayat.sqlite \
  "select count(distinct permalink) from videos where on_canvas=1;
   select media_type, count(*) from videos where on_canvas=1 group by media_type;
   select cache_status, count(*) from videos where on_canvas=1 group by cache_status;"
```

## Resources

- `scripts/import_datasarva_saved_reels.py`: end-to-end importer for the known working flow.
