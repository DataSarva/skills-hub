---
name: interactive-review
description: |
  Create an interactive HTML review session in the browser so the user can comment per-section and chat with the agent topic-by-topic, instead of long chat blocks. Use whenever the user types "/html", "/review", "let's discuss this in html", "make this interactive", or whenever you (the agent) are about to produce a structured report with multiple sections that the user will need to react to item-by-item. Backed by the local `ireview` server (~/.ireview/, port 7878). Every agent (Claude Code, Codex, Gemini CLI) can use this — the workflow is CLI-driven.
---

# Interactive Review (`ireview`)

A persistent local web app + CLI for agent↔human discussion. Replaces long chat-block reports + manual copy-paste-back loops.

## **CRITICAL — auto-poll behavior (BTW only)**

**Whenever a conversation has involved an `ireview` session at any point, at the START of every reply turn you MUST run:**

```bash
ireview btw          # BTW side-channel learning questions waiting on you
```

If it returns pending items in any session that's not closed, answer them FIRST via `ireview btwreply <sid> <topic-id> "<terse educational markdown>"`, THEN continue with whatever the user just typed. Surface a one-line note to the user in chat: *"Replied to N pending BTW(s)."* If empty, proceed normally — no need to mention.

**Do NOT call `ireview unread` proactively.** Main-thread comments are the user's own notes, decisions, and lock signals — NOT response requests. Only read main-thread comments when the user EXPLICITLY says `check the review` / `respond to comments` / `check unread`.

**Why split this way**:
- BTW drawer = the user clicks "ask" and types a question expecting a reply. Auto-poll is appropriate.
- Main thread = the user types a comment as part of forming/locking their decision. Some are questions to me, most are notes-to-self / lock signals like "approved" / "let's go with X". Auto-replying to every one of these is noise.

This is also wired in `~/.ireview/auto-poll.sh` (the script the UserPromptSubmit hook runs) — that script only polls BTW.

The polling cost is one cheap subprocess call (~100ms) — well worth the seamless feel.

**The user can still ask for main-thread responses** by saying any of: `check the review`, `respond to comments`, `check unread`, `look at main thread`. In that case use `ireview unread` + `ireview reply`.

## When to use

Use `ireview` instead of dumping a multi-section report into chat when ANY of these hold:
- User types `/html`, `/review`, `/discuss`, `let's go through this in html`, `make it interactive`, `pop up html`.
- You are about to output a structured report with >5 items the user will react to (audit, gap analysis, plan, design spec, code review, brainstorm consolidation, PRD draft, etc.).
- The decision will be reached over multiple turns (not single-shot).
- User has previously asked you to use `ireview` for ongoing work.

Skip if the request is a one-shot question with a single answer.

## Server lifecycle

The server is `~/.ireview/server.py`, port 7878, stdlib-only.

Before any `ireview` command, ensure the server is up:
```bash
ireview status || (nohup python3 ~/.ireview/server.py > ~/.ireview/server.log 2>&1 &)
sleep 1 && ireview status
```

If `ireview` is not on PATH yet, use `python3 ~/.ireview/ireview.py` directly.

## Workflow

### 1. Create a session
Build a JSON file with categorized topics. Each topic gets its own chat thread in the UI.

`topics.json` schema:
```json
{
  "intro": "optional markdown intro",
  "categories": [
    {
      "title": "Category Name",
      "topics": [
        {
          "id": "kebab-id",
          "title": "Topic title",
          "desc": "Full markdown — headings, lists, tables, code blocks, blockquotes, links all render.",
          "status": "info|built|missing|partial"
        }
      ]
    }
  ]
}
```

### Topic `desc` is full GFM markdown

The UI renders `desc` through `marked` + `DOMPurify` (CDN-loaded). USE THIS — don't write walls of text. Concretely, you SHOULD use:
- `## H2` / `### H3` for section structure inside a topic (each topic can have its own sub-sections).
- Bullet + numbered lists for enumerable points (`- item` / `1. item`).
- Tables for comparisons (`| col | col |\n|---|---|`).
- Fenced code blocks for code / configs / diagrams (` ```yaml `, ` ```python `, ` ```text ` for ASCII art).
- `**bold**` + `*italic*` for emphasis.
- `> blockquotes` for definitions / pull quotes.
- `` `inline code` `` for symbol names, paths, env vars.
- `[link](https://…)` — external links open in a new tab.
- `---` for horizontal rule between sub-sections.
- `<details><summary>…</summary>…</details>` for collapsible deep-dives (kept in DOMPurify allowlist).

**Style guidance for topic `desc`**:
- Lead with the one-sentence framing, then expand.
- For decision topics: include a small table comparing options + a "recommendation" subsection.
- For deep-dive topics: include file/line references in fenced blocks, not inline prose.
- Prefer tables and lists over paragraph prose — the UI is read sequentially, scrollable per-topic.
- ASCII diagrams go inside ``` blocks for proper monospace + horizontal scroll.

This means topics can be LONG and information-dense without becoming unreadable — the markdown rendering does the structuring. Don't pre-compress topics that benefit from a table or a code example.

Then:
```bash
ireview new "Session Title" --from-json /tmp/topics.json --open
```
Prints the session URL and opens it in the browser. Tell the user:
> Opened ireview session: <URL>. Drop comments per section. When ready for me to respond, ask "check the review" or "respond to comments".

**UX notes for telling the user about a new session** (the UI auto-handles all of these):
- Drag the splitter between sidebar and main pane to resize. Double-click splitter to reset.
- Click any category header (▾ VISION RECAP, etc.) to collapse/expand. Expanded category bodies are visually separated with a dashed divider so groups don't blend.
- Mobile: hamburger ☰ in header opens sidebar overlay.
- **Unified scroll per topic**: the topic description (markdown) and the discussion thread share ONE scroll container, separated by a `discussion thread` divider. The reader scrolls once from intro to messages instead of fighting two nested scrollers. The composer stays pinned at the bottom.
- Full GFM markdown renders in both topic `desc` AND message bodies (headings, lists, tables, code blocks, blockquotes, links, `<details>`, `<kbd>`).
- Theme toggle 🌙/☀️ in header (persists). Default theme is **light** (warm ivory + clay accents).
- Each topic gets its own chat thread. Sidebar shows status badges + priority + unread dots.
- Every topic has a `💭 BTW · ask` button next to the priority controls — opens an ephemeral learning side-channel drawer on the right.
- The BTW drawer **is resizable**: drag its left edge to widen (down to 320px, up to 92% viewport). Double-click the handle to reset to 440px default. Width persists in localStorage.
- Esc, the × button, or clicking the dim backdrop **closes the BTW drawer and wipes the conversation** (server-side state cleared).

### 2. Wait for user input
Do NOT poll. The user explicitly asks you to "check" / "respond" / "go through replies".

### 3. Respond to comments
```bash
ireview unread <session-id>   # see all pending user messages
```
For each, post a reply:
```bash
ireview reply <session-id> <topic-id> "your concise response"
```
Replies appear in the browser within ~2 seconds via auto-poll.

Optionally update priority based on what was decided:
```bash
ireview priority <session-id> <topic-id> p0|p1|p2|skip
```

### 4. Iterate
User adds more comments → asks you to check → you reply. Repeat until decision reached.

### 4b. BTW — ephemeral learning side-channel per topic

Each topic in the UI has a `💭 BTW · ask` button. When the user clicks it, a right-side drawer opens with its OWN composer + message thread. This is a **side-channel for learning** — the user asks clarifying / context questions that they don't want polluting the main decision thread. Examples:
- *"What does PI-RPC mean exactly?"*
- *"Walk me through how agentscope's MsgHub differs from a Python queue."*
- *"Why is subprocess overhead a problem here?"*

**Semantics**:
- Stored in `topic.btw = {open: bool, messages: [...]}`.
- Surfaced via a separate endpoint, NOT in main `unread`.
- The user closes the drawer → server wipes `messages` and sets `open: false`. Zero persistence after close. "Incognito" by design.
- Pressing Esc in the browser closes it too.
- Pulses orange when there's an open thread with content.

**Workflow** — the auto-poll directive at the top of this doc means `ireview btw` runs at the start of EVERY one of your turns. The user shouldn't need to say "/btw" — you discover their question automatically.

When the user explicitly says `/btw`, `check btws`, `answer btws`, that's a request for an *out-of-band* poll (e.g. they just typed in the drawer and are still typing in the main chat and want priority on the BTW response). Run the same commands:

```bash
ireview btw                          # all open btw threads across all sessions
ireview btw <session-id>             # just one session
```

For each pending question, post an educational/contextual reply:

```bash
ireview btwreply <session-id> <topic-id> "Your concise context-providing answer in markdown. Tables, code, links all render. Treat this as a quick tutorial, not a decision input."
```

**Tone for BTW replies vs main-thread replies**:
- Main-thread replies = decision-track. Crisp, locks-in, references docs.
- BTW replies = learning-track. Explain like the user is asking to understand the *concept*, not to make the call. Use analogies if helpful. Cite a file/line if relevant.
- Keep BTW replies tight — 3–8 sentences is the sweet spot. The user can ask again if they want more.

**Don't conflate**: when the user comments in the BTW drawer, that's a LEARNING question. Do NOT change topic priority, do NOT lock decisions from a BTW answer. Decisions still happen in the main thread.

**Trigger words to check btws**: `/btw`, `check btws`, `answer btws`, `respond to btws`, `there are btws open`. When unsure, do both — run `ireview unread` AND `ireview btw` and answer each in its proper channel.

### 5. Lock decisions
When the user says "we're done" / "act on it" / "close":
```bash
ireview show <session-id> > /tmp/decisions.json    # snapshot final state
ireview close <session-id>
```
Then act on the locked priorities / decisions. The state.json at `~/.ireview/sessions/<id>/state.json` is the durable record.

## CLI reference

| Command | Purpose |
|---|---|
| `ireview new "title" --from-json topics.json [--open]` | Create session, return URL |
| `ireview list` | All sessions |
| `ireview show <id>` | Full session state JSON |
| `ireview unread [<id>]` | Pending main-thread user messages (decisions track) |
| `ireview btw [<id>]` | Pending BTW side-channel questions (learning track) |
| `ireview reply <id> <topic-id> "text"` | Post agent reply on main thread |
| `ireview btwreply <id> <topic-id> "text"` | Post agent reply in the BTW drawer |
| `ireview gmsg <id> "text"` | Post agent message on global thread |
| `ireview priority <id> <topic-id> p0\|p1\|p2\|skip\|null` | Set/clear priority |
| `ireview close <id>` | Mark session done |
| `ireview server` | Run server foreground |
| `ireview status` | Server health check |

## Notes for agents

- Each session's URL is `http://localhost:7878/s/<session-id>`. Localhost-only; safe.
- State persists at `~/.ireview/sessions/<id>/state.json`. Survives reboots.
- UI auto-polls every 2s — your replies are visible to the user without refresh.
- Sidebar shows priority badges + unread dot per topic; user can prioritize / chat from any device on the local network (will need Cloudflare or tailscale for remote).
- Server is single-threaded-safe (file lock). Don't run multiple instances. Bouncing it = `launchctl unload && launchctl load ~/Library/LaunchAgents/com.aisarva.ireview.plist` (a plain `pkill` will be undone by launchd auto-respawn).
- Re-use existing skills (caveman, brainstorming, doc-coauthoring, etc.) — `ireview` is purely the I/O layer.
- The session UI lives at `~/.ireview/index.html`. It imports `marked` + `DOMPurify` from jsDelivr CDN. A backup is at `~/.ireview/index.html.bak`. If the rendering breaks (e.g. CDN blocked), the renderer falls back to escaped-newline plain text — sessions still readable, just less pretty.
- The visual aesthetic was tuned to feel like the [html-effectiveness](https://thariqs.github.io/html-effectiveness/) page — warm ivory + clay accents, serif headlines for the editorial feel, mono-uppercase for eyebrow labels, table headers, badges, kbd, timestamps. If you ever rebuild this UI, keep that vibe: tables with rounded borders + zebra rows, h2s with vertical clay accent bars, gradient stripes on `<pre>` blocks, mono-italic `*emphasis*` colored clay. The palette is `--ivory #FAF9F5`, `--paper #FFFFFF`, `--slate #141413`, `--clay #D97757`, `--oat #E3DACC`, `--olive #788C5D`.
- **Layout invariant — unified topic scroll**: `<main class="main">` holds a `<div id="topicScroll" class="topic-scroll">` wrapper that contains BOTH `.topic-header` and `.messages` (separated by a `.messages-divider`). Only `.topic-scroll` owns `overflow-y: auto`; `.topic-header` and `.messages` do NOT scroll independently. Do not re-add `max-height` or `overflow-y` to those inner blocks — it re-introduces the nested-scroller jail. The composer is a sibling of `.topic-scroll`, not inside it, so it stays pinned at the bottom. Auto-scroll on new messages targets `#topicScroll` (falls back to the message list if the wrapper is absent — keeps older session caches working).
- **Sidebar category separation**: `.cat-body` carries a dashed bottom border + extra bottom padding so expanded categories are visually distinct from neighbors. The last `.cat-body` drops the border (`:last-child`) so the sidebar doesn't end on a stray rule.

## Schema reference

`state.json` for a session:

```jsonc
{
  "id": "kebab-id",
  "title": "Human Readable Title",
  "intro": "markdown",
  "created_at": 1234567890.0,
  "closed": false,
  "topics": [
    {
      "id": "topic-kebab",
      "title": "Topic title",
      "desc": "Full GFM markdown.",
      "category": "Category Name",
      "status": "info|built|missing|partial",
      "priority": "p0|p1|p2|skip|null",
      "messages": [ { "id", "role": "user|claude", "text", "ts" } ],
      "btw": { "open": false, "messages": [ ... same shape ... ] }
    }
  ],
  "global": [ ... message-shape ... ]
}
```

- `messages[]` = main decision thread.
- `btw.messages[]` = ephemeral learning side-channel. Cleared on UI close.
- `global[]` = session-wide channel (rarely used).

## Quality bar for the JSON you send

When you build `topics.json`, treat it like authoring a small site, not a chat dump:
1. Each topic should answer one decision or one fact. Not three.
2. Topic `desc` length: aim for 50–500 words. Longer is fine if richly structured (tables, code, lists).
3. Always include the structure markers — `##` sub-headings, tables for compare/contrast, fenced blocks for any monospaced content.
4. If a topic ends with an explicit ASK (e.g. "Pick A / B / C?"), put it as a final `**Pick:**` line so it's scan-friendly.
5. Decision topics that the user locks via priority should have `"status": "missing"` initially, flip to `"built"` once decided.
6. Cross-reference between topics via the topic id in prose (e.g. "see topic [k-pi]") — the user scrolls/clicks rather than re-reads.

## Triggering from other agents

Codex, Gemini CLI, or any subprocess can shell out:
```bash
ireview new "title" --from-json topics.json --open
ireview unread        # later, when polling for user comments
ireview reply <id> <topic-id> "text"
```

The workflow above applies identically.
