---
name: durable-work
description: "Use when a request is repeatable, reusable, recurring, automatable, should become a skill, should be scheduled, or should update an agent workflow. Enforces the no-one-off-work rule: manually calibrate on 3 to 10 items, show output, then codify into a skill/script/schedule after approval."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, automation, cron, launchd, workflow, harness, resolver]
    related_skills: []
---

# Durable Work

## Rule

> You are not allowed to do one-off work. If I ask you to do something and it's the kind of thing that will need to happen again, you must: do it manually the first time on 3 to 10 items. Show me the output. If I approve, codify it into a skill file. If it should run automatically, put it on a cron.The test: if I have to ask you for something twice, you failed.

## When To Use

Use this skill when the user asks for anything that is likely to recur:

- Repeated analysis, reporting, triage, search, cleanup, data enrichment, monitoring, or publishing.
- A workflow that needs judgment the first time and consistency later.
- A task that should become a skill, resolver, checklist, script, CLI, cron job, launchd job, or other scheduled automation.
- A second request for the same kind of work.

Do not use it for truly disposable one-line answers, one-off explanations, or small edits that are unlikely to repeat.

## Workflow

1. Decide whether the task will plausibly happen again. If yes, say you are applying the durable work rule.
2. Manually perform the workflow on 3 to 10 representative items first. Keep enough notes to preserve the process, inputs, commands, edge cases, and judgment calls.
3. Show the user the output from the manual pass. Ask for approval before turning the workflow into a permanent skill or schedule, unless the user explicitly requested codification in the current prompt.
4. Codify the approved workflow:
   - Put judgment, process, domain context, and examples in a `SKILL.md`.
   - Put deterministic, repeatable execution in scripts, CLIs, database queries, tests, or other reliable tooling.
   - Add resolver pointers so future agents know which context to load and when.
   - If it should run without being asked, schedule it with cron, launchd, or the repo's established scheduler.
5. Verify the codified workflow on a small sample, then show the verification output.
6. If later results reveal better rules, update the skill. A recurring workflow should improve instead of accumulating chat-only lore.

## Architecture Rules

- Keep the harness thin and the skills fat. Root agent instructions should be short pointers; durable procedure belongs in skills and references.
- Put judgment in latent space: reading, interpreting, diarizing, synthesizing, comparing, and deciding.
- Put trust in deterministic space: SQL, compiled code, arithmetic, scheduling, idempotent scripts, tests, and repeatable APIs.
- Prefer purpose-built narrow tools over broad slow wrappers.
- Use diarization for real knowledge work: read the relevant source set and produce a structured profile or brief that captures contradictions, timelines, and changes.
- Build learning loops: retrieve, read, diarize, count, synthesize; then survey, investigate, diarize, and rewrite the skill.

## Reference

Read `references/thin-harness-fat-skills.md` when designing a new durable workflow, deciding what belongs in a skill versus a script, or updating an agent harness/resolver pattern.
