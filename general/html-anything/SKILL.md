---
name: html-anything
description: "Use when the user asks to use, inspect, run, adapt, or make a polished HTML/document artifact with the local open-source html-anything project, especially when deciding whether it fits a docs/wiki/readability workflow, low-token publishing flow, or shareable HTML export."
tier: general
tags: [html, docs, publishing, readability, local-agents, low-token]
version: 1
---

# html-anything

Use this skill for the local open-source project:

- Repo: `/Users/aisarva/Downloads/osp/html-anything`
- Upstream: `https://github.com/nexu-io/html-anything.git`
- App package: `next/` (`@html-anything/next`)
- License: Apache-2.0

## What It Is

HTML Anything is a local-first Next app that turns input text/Markdown/CSV/JSON
into polished single-file HTML by spawning a logged-in coding-agent CLI. It is
not primarily a web-page scraper or readability extractor.

Relevant implementation anchors:

- `README.md` — project overview, supported agents, export targets.
- `next/src/app/api/convert/route.ts` — builds the prompt and streams output.
- `next/src/lib/templates/shared.ts` — shared design prompt prepended to every run.
- `next/src/lib/agents/detect.ts` — local agent/model detection.
- `next/src/lib/agents/argv.ts` — per-agent invocation argv.
- `next/src/lib/templates/skills/` — bundled design/document templates.

## First Checks

If the user explicitly asks to refresh or "pull before researching", do:

```bash
git -C /Users/aisarva/Downloads/osp/html-anything status --short
git -C /Users/aisarva/Downloads/osp/html-anything pull --ff-only
git -C /Users/aisarva/Downloads/osp/html-anything rev-parse --short HEAD
```

If there are local changes, do not overwrite them; inspect first and report the
conflict.

## Running

From repo root:

```bash
cd /Users/aisarva/Downloads/osp/html-anything
pnpm install
pnpm -F @html-anything/next dev
```

Useful checks:

```bash
pnpm -F @html-anything/next typecheck
pnpm -F @html-anything/next test
pnpm -F @html-anything/next build
```

The app scans `PATH` for local agent CLIs such as `claude`, `codex`, `gemini`,
`copilot`, `opencode`, `qwen`, and `aider`. It reuses existing CLI logins; no
separate project API key is required. This does not mean every run is free: the
selected CLI/model may still consume subscription/API quota.

## Decision Rule

Choose the lowest-cost layer that solves the problem:

1. **Readability inside an existing app**: do deterministic reader-mode cleanup
   and CSS first. No model call. Good for Pustak wiki pages, docs readers, and
   captured articles.
2. **Brief for understanding**: generate a cached compact JSON/Markdown brief
   from a capped excerpt. Prefer local/free models (`ollama`, OpenRouter free,
   or cheap Gemini routing) and store the result so it is not regenerated.
3. **Polished shareable artifact**: use HTML Anything when the user wants a
   designed one-pager, article, poster, slide deck, social card, or exportable
   HTML/PNG.

Do not put HTML Anything directly in an always-on capture pipeline unless the
user explicitly accepts the token/runtime cost. For ingestion systems, make it
an on-demand "make beautiful HTML" action.

## Low-Token Pattern

For long docs/wiki pages:

- Strip frontmatter, source metadata, duplicate title, nav boilerplate, and raw
  capture lines before sending anything to a model.
- Cap source text, usually 6k-8k characters for a brief.
- Ask for strict JSON with a small schema:

```text
Use only the supplied source text. Return compact JSON only.
Schema: {"title": string, "brief": string, "key_points": [string], "why_it_matters": string, "confidence": "high|medium|low"}
```

- Cache by page path + content hash, for example
  `~/.pustak/wiki/.briefs/<sha>.json`.
- Render the cached brief in the existing UI; keep the original markdown as the
  source of truth.

Manual calibration on this Mac Mini: `ollama run gemma4:latest` produced usable
brief JSON from about 7.8k input characters in 15-26 seconds on three Pustak
wiki pages. Treat local-model output as a convenience brief, not canonical
knowledge.

## Good Template Picks

For readable documents:

- `doc-kami-parchment` — calm long-doc/one-pager typography.
- `article-magazine` — Substack/Medium-style long article.
- `docs-page` — technical documentation layout with navigation.

For social/share output:

- `card-twitter`
- `card-xiaohongshu`
- `poster-hero`

For presentations:

- `deck-swiss-international`
- `deck-guizang-editorial`
- `deck-open-slide-canvas`

## Pustak Wiki Guidance

For Pustak captures and wiki pages:

- Keep Slack capture -> scraper -> markdown wiki -> qmd indexing deterministic.
- Use HTML Anything design ideas for the `/wiki/...` reader UI.
- Add an optional cached brief panel if the user wants AI understanding.
- Use HTML Anything itself only for an explicit export action, not for the
  default indexed page.

## Safety

- Do not edit `.env` files for this workflow.
- Do not send full 50k-150k character captures to an agent unless the user
  explicitly wants a full designed artifact and accepts the cost.
- Do not claim a model is "free" just because HTML Anything has no API key;
  verify the selected local/CLI model route.
- When adapting code or templates from this project, preserve Apache-2.0 license
  obligations where needed.

