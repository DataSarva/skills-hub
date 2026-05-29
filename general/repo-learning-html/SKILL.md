---
name: repo-learning-html
description: Build or update a local HTML learning session for explaining a repository, framework, architecture, or codebase in a diagram-first beginner-friendly way, with an ilearn sidecar chat backed by codex exec or claude -p. Use when the user asks to "teach me", "explain this repo/framework", "learn me this", create a learning HTML, or make a reusable mental-model artifact separate from ireview.
---

# Repo Learning HTML

Create persistent local learning pages with `~/.ilearn`. This is for durable human-readable repo teaching, not review workflow. The output should be diagram-first, source-anchored, and useful for repeated learning without burning tokens every time.

## Workflow

1. Inspect the target repo first: `README`, `AGENTS.md`/`CLAUDE.md`, docs, package manifests, route/service/schema directories, tests, and existing architecture notes.
2. Build a compact session JSON with this shape:
   - `title`, `repo_path`, `goal`, `summary`
   - `source_paths`: key files or directories the learner should inspect
   - `sections`: each has `id`, `kicker`, `title`, `summary`, `diagram`, `points`, `details`, `files`
   - `glossary`: `{ "term": "...", "def": "..." }`
3. Prefer diagrams over paragraphs. Use `diagram.type` values supported by ilearn:
   - `flow`: left-to-right lifecycle or data path
   - `layers`: stack/architecture layers
   - `grid`: module map or concept map
4. Keep section copy beginner-friendly but technically exact. Avoid cute analogies. Use short bullets, canonical terms, and source file anchors.
5. Create or update the session:

```bash
ilearn new "Framework Name: Learning Map" --repo /path/to/repo --from-json /path/to/session.json --id framework-name --open
```

6. If the server is not running, start it:

```bash
ilearn server
```

The page URL is `http://127.0.0.1:8787/s/<session-id>`.

## Sidecar

The page includes a right-side chat. It should stay read-only:

- Codex path: `codex exec --ephemeral -s read-only --cd <repo> --skip-git-repo-check <prompt>`
- Claude path: `claude -p --no-session-persistence --permission-mode dontAsk --allowedTools Read,Grep,Glob,LS --add-dir <repo> <prompt>`

Use the static page for stable teaching. Use sidecar chat only for follow-up questions, file lookups, and gaps.

## NotebookLM

NotebookLM is not part of the default flow. Do not build NotebookLM UI, MCP, or CLI automation unless the user explicitly asks for it in the current turn.

If explicitly requested, only export a source bundle:

```bash
ilearn bundle <session-id>
```

This writes `~/.ilearn/bundles/<session-id>/learning-brief.md`, `session.json`, and `source-manifest.txt`. Stop there unless the user asks to push it into NotebookLM.

## html-anything

`/Users/aisarva/Downloads/osp/html-anything` is a heavier HTML authoring app. Use it when the user wants a polished standalone HTML artifact, social/export formats, or agent-assisted HTML generation. Use `ilearn` when the user wants the persistent repo tutor with sidecar chat.

## Quality Bar

- First viewport must show the repo/framework identity and the mental model.
- Every important concept should point to files.
- No long walls of prose.
- No destructive repo operations.
- Do not edit `.env`; follow the global Infisical rules for commands needing secrets.
