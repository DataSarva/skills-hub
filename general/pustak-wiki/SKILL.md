---
name: pustak-wiki
description: "Use when diagnosing or explaining Pustak's docs/wiki runtime, Slack #pustak-capture indexed links, qmd indexing, public wiki URLs, or when producing a compact AI-consumable brief from Pustak wiki pages."
tier: general
tags: [pustak, wiki, slack, capture, qmd]
version: 1
---

# pustak-wiki

Use this skill for Pustak wiki questions, especially:

- "Why did Slack say indexed but the link is 403/404?"
- "Where did this captured link go?"
- "Summarize this Pustak wiki/source page for my understanding."
- "Check whether a docs/wiki page should be visible in the web UI."

## Anchors

- Code root: `/Users/aisarva/aisarva/pustak`
- Runtime home: `~/.pustak`
- Wiki root: `~/.pustak/wiki`
- Slack capture channel: `#pustak-capture`
- Main public dashboard host: `https://pustak.investsarva.com`
- API host: `https://api-pustak.investsarva.com`
- Use `iex-pustak -- <cmd>` for commands that need Pustak secrets. Do not edit `.env`.

## Pipeline Shape

Slack or Telegram URL capture writes JSON envelopes under `~/.pustak/inbox/<type>/`.
`capture-drainer` normalizes native Slack messages, writes/merges pages under
`~/.pustak/wiki/general/sources/`, rebuilds the qmd index, archives processed
envelopes, then posts the Slack `indexed:` reply.

The Slack reply only means "the markdown page was written and qmd rebuild did
not fail." It does not by itself prove the external web URL is reachable.

Important implementation files:

- `pustak/lib/slack.py` captures Slack messages and initially posts `:white_check_mark: captured`.
- `pustak/lib/capture_drainer.py` writes `general/sources/*.md`, runs qmd rebuild, and batches Slack `indexed:` replies.
- `pustak/lib/slack_ack.py` formats `indexed: https://pustak.investsarva.com/wiki/<slug>`.
- `deploy/cloudflared/pustak.yml` maps `pustak.investsarva.com` to the dashboard.
- `pustak/lib/public_server.py` is a separate public artifact server and only serves `/` and `/a/<artifact-id>`.

## Fast Diagnosis

Start with the exact URL, slug, or title:

```bash
cd /Users/aisarva/aisarva/pustak
rg -n "<url-or-slug-or-title>" ~/.pustak /Users/aisarva/aisarva/pustak -g '!dashboard/node_modules/**'
```

Then inspect the capture/write trail:

```bash
tail -80 ~/.pustak/logs/capture-drainer/stdout.log
rg -n "<slug-or-url>" ~/.pustak/raw/manifest.jsonl ~/.pustak/state/events.jsonl ~/.pustak/wiki/log.md ~/.pustak/wiki/general/log.md
sed -n '1,220p' ~/.pustak/wiki/general/sources/<slug>.md
```

Check the public route separately from indexing:

```bash
curl -I -L --max-time 20 https://pustak.investsarva.com/wiki/<path-without-.md>
curl -sS -D - --max-time 5 http://127.0.0.1:3002/wiki/<path-without-.md> -o /tmp/pustak-wiki.html
```

Interpretation:

- `302` to `aisarva.cloudflareaccess.com` or browser `403`: Cloudflare Access policy/session problem.
- Local `404` from port `3002`: dashboard route is missing or deployed server has not been rebuilt/restarted.
- Local `200` from port `3002`: app route works; remaining issue is Cloudflare Access or tunnel deployment.
- Port `3001` is not the wiki UI; it is the artifact server for `/a/<artifact-id>`.

## Brief Format

When the user wants a low-token explanation, answer in this shape:

```text
Pipeline:
<one sentence from capture to wiki page>

Status:
<captured_at/write time/page path/qmd result if available>

Why the link failed:
<Cloudflare Access vs missing app route vs not deployed>

Decision:
<whether it should be in web UI, and whether public or Access-protected>

Brief:
<3-5 bullets summarizing the source page>
```

## Manual Calibration

Sampled on 2026-05-27:

- Webwright Microsoft Research link was captured from Slack on 2026-05-26, written by `capture-drainer` to `general/sources/microsoft-com-en-us-research-articles-webwright-a-terminal-is-all-you-need-for-web-agents.md`, then qmd rebuilt `indexed: 355`.
- A Slack capture run wrote `twitter-com-garrytan-status-2042925773300908103-s-52.md` and `cdn-openai-com-pdf-6a2631dc-783e-479b-b1a4-af0cfbd38630-how-openai-uses-codex-pdf.md`, then qmd rebuilt `indexed: 299`.
- Another run wrote `twitter-com-antoinersx-status-2057346702412243323-s-52.md`, found `general/sources/lex-inc-roughdraft.md` already indexed, then qmd rebuilt `indexed: 310`.

These samples confirm the recurring pattern: Slack ack, local markdown write,
qmd rebuild, Slack indexed reply, and a separate web-route/access check.

