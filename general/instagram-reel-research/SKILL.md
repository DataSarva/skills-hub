---
name: instagram-reel-research
description: "Download and analyze Instagram reels or accounts, extract MP4 metadata/audio/frames/contact sheets, create detailed Markdown video analyses with Gemini, and use Grok/xAI through Infisical for niche research, story options, and production-ready Telugu reel storylines. Use when asked to inspect Instagram reels, save reels locally, analyze video/audio/captions, study a reel niche, or generate similar story concepts/scripts."
---


> 🎬 **Child of the [[insta-video]] master reel pipeline.** Voice = [[telugu-raw-reel-voice]] · Telugu subs = [[telugu-voice-and-text]] · scene SFX/foley = [[reel-sfx-foley]] · publish = [[instagram-reel-publish]] / [[youtube-shorts-publish]].

# Instagram Reel Research

Use this skill for the repeatable workflow developed in `/Users/aisarva/Downloads/insta_story`: downloading Instagram reels with `yt-dlp`, extracting audio/frames with `ffmpeg`, analyzing video and audio with Gemini CLI, and generating related story options or scripts with Grok/xAI through Infisical.

## Core Rules

- Do not install packages unless the user explicitly approves. Prefer existing `yt-dlp`, `ffmpeg`, `ffprobe`, `gemini`, and `iex`.
- Do not edit `.env` files. Use Infisical wrappers for Grok/xAI secrets.
- Do not print API keys or secrets.
- For Grok API calls, prefer `iex contentgen --env=dev -- ...` or the repo script's automatic Infisical wrapper.
- For Google/Gemini video analysis, use Gemini CLI when it is authenticated and available.
- Save generated outputs as files in the working project, not only in chat.

## Repo Scripts

The reusable scripts for this workflow live in:

`/Users/aisarva/Downloads/insta_story/scripts/instagram_reel_research/`

Scripts:

- `analyze_reels.py` - download reel URLs or enumerate an account reels URL, extract media assets, run Gemini analysis, and write Markdown analysis files.
- `grok_story.py` - ask Grok for story option lists, full storylines, or raw prompt completions; auto-wraps itself with `iex contentgen --env=dev --` when `GROK_API_KEY` is missing.

## Single Reel Workflow

Run from the repo root:

```bash
python3 scripts/instagram_reel_research/analyze_reels.py \
  --url 'https://www.instagram.com/reels/DXBl54vEvga/' \
  --output-dir .
```

Outputs:

- `reels/` - downloaded MP4, thumbnail, and yt-dlp info JSON.
- `audio/` - extracted audio track.
- `frames/<prefix>/` - sampled frames and contact sheet.
- `metadata/` - source metadata, ffprobe JSON, and loudness report.
- `analysis/<prefix>.analysis.md` - combined Markdown analysis.
- `analysis/<prefix>.gemini-video.md` - raw Gemini video/audio analysis.
- `analysis/<prefix>.gemini-visual.md` - raw Gemini contact-sheet analysis.

Useful options:

```bash
--gemini-model gemini-2.5-flash
--skip-gemini
--cookies-from-browser chrome
--frame-fps 1
--contact-fps 0.5
--yt-dlp-arg <extra-arg>
```

Use `--cookies-from-browser chrome` or another browser only when public extraction fails and the user has a legitimate local browser session.

## Multiple Reels Or Account Workflow

Repeated URLs:

```bash
python3 scripts/instagram_reel_research/analyze_reels.py \
  --url 'https://www.instagram.com/reels/SHORTCODE1/' \
  --url 'https://www.instagram.com/reels/SHORTCODE2/' \
  --output-dir .
```

URL file:

```bash
python3 scripts/instagram_reel_research/analyze_reels.py \
  --url-file reel_urls.txt \
  --output-dir .
```

Account reels URL, when `yt-dlp` can enumerate it:

```bash
python3 scripts/instagram_reel_research/analyze_reels.py \
  --account-url 'https://www.instagram.com/alanati_ai_kathalu/reels/' \
  --limit 26 \
  --output-dir .
```

If account enumeration fails, manually collect reel URLs first, put them in `reel_urls.txt`, and run the URL-file workflow.

## Gemini Analysis Pattern

Use Gemini for multimodal analysis of downloaded media. The script sends:

- the local MP4 for video, audio, language, dialogue paraphrase, niche, visual style, and production pattern.
- the contact sheet for scene-by-scene visual progression, camera/framing, text overlay behavior, and end-card notes.

When manually running Gemini:

```bash
gemini -m gemini-2.5-flash -p 'Analyze @reels/<file>.mp4 ...'
gemini -m gemini-2.5-flash -p 'Analyze @frames/<prefix>/<contact>.jpg ...'
```

Expect direct MP4 analysis to take longer than a still-image prompt.

## Grok Story Research Workflow

Generate a broad story option list from a source analysis:

```bash
python3 scripts/instagram_reel_research/grok_story.py options \
  --source-analysis analysis/<prefix>.analysis.md \
  --count 30 \
  --out story_options.md
```

Generate a full storyline from a selected concept:

```bash
python3 scripts/instagram_reel_research/grok_story.py storyline \
  --source-analysis analysis/<prefix>.analysis.md \
  --concept 'Mouna Vruksham / symbolic Telugu neeti katha: a barren tree gives fruit only to the villager who never asks for it. Moral: desire itself can block blessings.' \
  --duration '90-100 second' \
  --out story.md
```

Run a custom prompt file through Grok:

```bash
python3 scripts/instagram_reel_research/grok_story.py raw \
  --prompt-file prompt.md \
  --out grok_output.md
```

Defaults:

- Model: `grok-4.3` unless `GROK_MODEL` is set.
- Infisical app: `contentgen`.
- Infisical env: `dev`.

## Output Quality Checklist

For each reel analysis, include:

- Source URL and local asset paths.
- Instagram metadata: account, upload date, likes/comments when available, caption.
- Technical media specs from `ffprobe`.
- Audio extraction and loudness notes.
- Visual scene timeline.
- Spoken language and dialogue/narration paraphrase.
- Niche pattern and reusable creative structure.
- Clear caveat when a step was skipped or failed.

For each story/script generated with Grok, ask for:

- Hook line for retention.
- Telugu-rooted genre or tradition.
- Characterization and environment details.
- Scene-by-scene timing.
- Telugu dialogue and English meaning.
- On-screen caption guidance.
- Voice, music, sound effects, and pacing notes.
- Final moral and engagement end card.
