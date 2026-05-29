---
name: afk-prd-loop
description: End-to-end autonomous workflow for multi-slice PRDs — file the parent PRD as a GitHub issue, file vertical slice issues, do the bottleneck slice inline with TDD, dispatch GREEN implementation of the rest to parallel `codex` CLI sessions in worktree-isolated branches (NEVER CC subagents — those burn session budget), dispatch parallel CC reviewers per PR (reviews are CC's strength), rebase + merge in dependency order, then run the live migration. Use when the user asks for "implement this PRD", "do this AFK", "no babysit", "parallel slices", "rename all X to Y across the codebase", a filesystem refactor, a multi-file rename, or any task with 3 or more independent slices.
---

# AFK PRD loop

The autonomous PRD-to-merged-PRs pipeline. Lock the user into one batch of HITL decisions upfront, then run AFK: parallel codex agents in worktrees write the code, parallel CC reviewers read each PR, the orchestrator rebases conflicts and merges in dependency order, and a final live-deploy step applies the result.

## The hard rule: codex for GREEN, CC subagents for REVIEW

**Never use CC subagents (`Agent({subagent_type: 'general-purpose'})`) for code-writing work.** They burn Claude Code session budget — you will hit your usage limit mid-PRD. Codex sessions bill separately.

Read [references/codex-vs-subagent.md](references/codex-vs-subagent.md) for the decision matrix + invocation patterns.

## The 7-step workflow

### 1. Batch HITL upfront

Identify EVERY human decision the PRD requires (scope choices, defaults, naming, keep-vs-kill). Ask all of them in ONE `AskUserQuestion` call (max 4 questions). After that, the rest is AFK.

If decisions are obvious, skip this step and state defaults inline.

### 2. File PRD + slices via `gh`

- Write PRD body to `/tmp/prd-<topic>.md` covering: why, locked decisions, acceptance criteria, slice list, out-of-scope.
- `gh issue create --repo <owner>/<repo> --title "PRD: <topic>" --body-file /tmp/prd-<topic>.md --label "needs-triage,afk"` → capture the issue number.
- Write a shell script that files each slice via `gh issue create` with structured body. Run it.

Naming: branches `slice/<#>-<slug>`. Titles `slice-N: <verb> <object>`.

### 3. Do the bottleneck slice inline (TDD)

There's usually ONE slice that adds a shared util everything else imports (paths helper, new type, new template render). Do this inline:

1. Branch from `main`. Write RED tests. Confirm they fail.
2. Commit RED: `test(<scope>): RED for <feature> (#<issue>)`.
3. Implement minimal GREEN. Commit: `feat(<scope>): <verb> <object> (#<issue>)`.
4. Push, PR, merge. Pull main locally.

This unblocks the parallel codex agents in step 4.

### 4. Dispatch parallel codex in worktrees

For each remaining independent slice:

```bash
# Worktree from origin/main (now includes the bottleneck slice)
git worktree add -b slice/<#>-<slug> ~/<repo>/.claude/worktrees/codex-slice-<#> origin/main

# Spawn codex in background. nohup detaches; redirect logs.
cd ~/<repo>/.claude/worktrees/codex-slice-<#> && \
  nohup codex exec --dangerously-bypass-approvals-and-sandbox \
    "$(cat /tmp/codex-slice-<#>-prompt.md)" \
    > /tmp/codex-slice-<#>.log 2>&1 &
echo "codex PID=$!"
```

Then set up a harness-tracked watcher so you get notified when codex exits (the watcher exits when codex exits):

```python
Bash(
  command="while kill -0 <PID> 2>/dev/null; do sleep 5; done; tail -30 /tmp/codex-slice-<#>.log",
  run_in_background=True,
)
```

Read [references/worktree-codex-dispatch.md](references/worktree-codex-dispatch.md) for the codex prompt template + brief structure.

Helper script: [scripts/dispatch_codex_worktree.sh](scripts/dispatch_codex_worktree.sh) wraps the worktree + spawn + watcher pattern.

### 5. Parallel CC reviews after ALL agents finish

Don't poll codex. Trust the harness notification. Once all PRs are open, dispatch one `pr-review-toolkit:code-reviewer` CC subagent per PR (reviews are CC's strength, not codex's). Brief each reviewer with: PR number, repo, files-to-focus, what-to-check checklist, and proactively flag merge-order risks if multiple PRs touch the same files.

### 6. Merge in dependency order + resolve conflicts

After reviews come back:

1. Determine merge order — broadest rename/refactor first; same-file PRs rebase on top.
2. Merge first PR via `gh pr merge <#> --repo <r> --squash --delete-branch`.
3. For each subsequent same-file PR, rebase locally to preserve both sets of changes:

```bash
git fetch origin slice/<branch>
git checkout -b tmp-rebase-<#> origin/slice/<branch>
git rebase main  # resolve conflicts inline (see references/conflict-resolution.md)
git push --force-with-lease origin tmp-rebase-<#>:slice/<branch>
git checkout main && git branch -D tmp-rebase-<#>
gh pr merge <#> --squash --delete-branch
```

4. Pull main, run full test suite to confirm green.

Read [references/conflict-resolution.md](references/conflict-resolution.md) for the rebase-when-files-overlap pattern with worked examples.

### 7. Live deploy (HITL boundary)

If the PRD has a live-system component (daemon rename, file migration, config update):

1. **ALWAYS `--dry-run` first.** Show what would change.
2. Run actual migration scripts in idempotent order: state migrations → file renames → daemon restarts.
3. Stability watch: 60–120s checkpoint that daemons hold same PIDs, no respawns, no error spam.
4. Cleanup orphans (old plists, dead symlinks, retired config sections).
5. Update wiki / docs to reflect as-shipped state. Bump `version`. Document any gotchas hit during deploy.

Read [references/migration-patterns.md](references/migration-patterns.md) for idempotent script design (file-level merge, scope fences, in-place config sed, no `rm -rf`, render-before-delete ordering).

## After landing

- Close all slice issues (most auto-close via PR bodies `Closes #N`).
- File follow-up issues for non-blocking polish reviewers flagged but didn't gate on.
- Write to pustak wiki if you discovered any non-obvious gotcha during live deploy. Bump `version`. Append `authored_by`.
- Mark all TaskCreate tasks completed.

## Anti-patterns to avoid

- **Polling codex mid-flight** — harness notifies on exit. Trust it.
- **Sequential slices when they're independent** — parallel.
- **Skipping the bottleneck slice** — if it's a shared util, agents can't start meaningfully until it's merged.
- **CC subagents for code writing** — costs session budget. Codex is for that.
- **Live migrations without dry-run** — every migration has a `--dry-run` mode. Use it.
- **Mid-flight HITL drips** — don't ask the user "how should I handle this minor thing" mid-AFK. Take best judgment + flag in PR body for post-hoc review.

## When this skill ISN'T right

- Single-file edits → just do it inline.
- Exploratory / brainstorming work → `superpowers:brainstorming`.
- Pure debugging → `superpowers:systematic-debugging`.
- Documentation work → `doc-coauthoring`.
- A task that requires user's continuous judgment per slice → stay synchronous; this skill is for AFK execution.
