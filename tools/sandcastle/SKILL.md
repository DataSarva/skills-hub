---
name: sandcastle
description: >-
  On-demand git-worktree isolation for when an agent is about to MUTATE a tracked
  repo — edit code, modify a repo, fix a bug, make a code change, refactor, add a
  feature, or any write to version-controlled files. Use this the moment you decide
  to change code: it isolates the work in a throwaway worktree on its own branch,
  auto-commits + pushes + opens a PR for operator approval, then tears the worktree
  down so nothing leaks. Do NOT use it for pure chat, reading, research, or running
  read-only commands — only for repo mutation.
tier: tools
tags: [git, worktree, isolation, codebase, pr, chakra, safety]
version: 1
---

# sandcastle — isolate code changes, never touch the live checkout

A **sandcastle** is a git worktree on a dedicated `slice/<slug>-<ts>` branch, backed by
the same `.git` store as the live repo. You edit inside it; the live checkout the
daemons run from is never touched. On completion the change becomes a reviewable PR.

## When to use this (and when NOT)

**Use it** the instant you decide to mutate a tracked repo:
- editing/creating/deleting code or config under version control
- fixing a bug, adding a feature, refactoring, renaming

**Do NOT use it** for:
- answering questions, chatting, explaining
- reading files, searching, running read-only commands
- generating non-repo artifacts (videos, images, reports) that don't change a repo

Pure conversation must create **zero** worktrees. Isolation is for mutation only.

## The workflow (run via your terminal tool)

```bash
# 1. Create an isolated worktree for the repo you're about to change.
chakra sandcastle new --app-repo <path-to-repo>
#    → prints JSON: {"id": ..., "branch": "slice/<slug>-<ts>", "worktree_path": "..."}

# 2. cd into the worktree and make ALL edits there. NEVER edit the live checkout.
cd <worktree_path>
#    ... edit / write / patch files here ...

# 3. Commit your work in the worktree.
chakra sandcastle commit <id> --message "<what you changed>"

# 4. Push + open a PR. Default completion = auto push + gh pr create.
#    The operator approves the PR via a Slack reaction; you do NOT self-merge.
chakra sandcastle pr <id> --title "<concise PR title>"
#    → prints {"branch": ..., "pr_url": ...}  (pr_url null if there was no diff)

# 5. ALWAYS tear the worktree down when done — success OR abort — so nothing leaks.
chakra sandcastle cleanup <id>
```

## Hard rules

- **Never edit the live checkout directly.** All mutation happens inside the worktree.
- **Always `cleanup`** at the end of the task, even if you aborted or hit an error.
  Orphaned worktrees accumulate as junk. (A startup reaper sweeps any you miss, but
  don't rely on it.)
- **No diff → no PR.** If you made no changes, `pr` returns a null URL and opens nothing.
  Don't manufacture an empty PR.
- **One sandcastle per task/thread.** Reuse the same worktree for follow-up edits in the
  same line of work; create a fresh one for unrelated work.

## Inspecting / recovering

```bash
chakra sandcastle list                 # active worktrees + branches
chakra sandcastle cleanup --stale      # reap stale/orphaned worktrees (safe; skips active)
```
