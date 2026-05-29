---
name: autoresearch-scaffold
description: Drop a self-improving autoresearch loop into ANY project. Scaffolds the karpathy/autoresearch pattern — immutable metric harness + mutable subject + one comparable scalar reward + jsonl ledger with keep/discard/crash + an LLM proposer (grok reasons about each next variant) + a NEVER-STOP loop + a human-readable frontier dashboard. Use when the user wants to optimize a metric, run an overnight experiment loop, auto-tune anything (prompts, hyperparams, configs, render settings), make a process self-improving, or "set up an autoresearch loop" / "apply autoresearch to X". Specializes the generic `autoresearch` skill into a reusable scaffolder; reelforge (video reels) is a worked instance.
tier: general
tags: [autoresearch, self-improving, optimization, experiment-loop, scaffold, llm-proposer, karpathy]
version: 1
---

# autoresearch-scaffold

Set up a self-improving research loop in any project. Based on a thorough read of
[karpathy/autoresearch](https://github.com/karpathy/autoresearch) + the reelforge build.

## The pattern (9 principles — keep these intact)
1. **Immutable harness vs mutable subject.** The metric/eval is fixed ground truth; only the
   "subject" (what produces the artifact) changes.
2. **One scalar metric, engineered to be comparable across changes.** (autoresearch: val_bpb,
   vocab-independent + fixed time budget.) Higher = better here.
3. **Fixed budget per trial** → comparability.
4. **Ledger + champion.** Every trial logged with status `keep` (beat running-best) / `discard` /
   `crash`. Champion = running-best = what the prod path reads. (autoresearch uses git commits +
   `git reset` on regressions; this scaffold uses experiments.jsonl + champion.json. For pure-code
   subjects you can additionally commit-on-keep / reset-on-discard to mirror autoresearch exactly.)
5. **The agent IS the proposer** — an LLM reasons about the next variant from the ledger, not blind
   search. `forge/propose.py --llm` pipes the goal + history to `grok -p` (free, headless).
6. **Simplicity criterion** — prefer the simpler variant on ties.
7. **NEVER STOP** — autonomous until interrupted.
8. **Crash handling** — failed generation logged as `crash`, loop continues.
9. **Human-readable artifact** — `progress.png` frontier + `STATUS.md`.

## How to use it
```bash
python ~/.skills-hub/general/autoresearch-scaffold/scaffold.py <target_project_dir>
cd <target_project_dir>/autoresearch
MAX_TRIALS=5 SLEEP=0 bash forge/loop.sh      # hello-world converges to reward~1 (proves the spine)
```
Then fill the **3 hooks** (everything else is generic and done):
- `forge/generate.sh` — `variant.json, $OUT` → produce your artifact (model/API/CLI/build).
- `forge/metric.py` — `compute(path)` → dict of raw, objective measurements (cheap, deterministic).
- `forge/reward.py` — `score(measurements)` → `{reward, components}`. **Make must-haves a
  multiplicative gate** (`reward = gate * (base + niceties)`) with a smoothstep so search keeps a gradient.

Edit `knobs.yaml` (search space) + `program.md` (the goal the LLM proposer reads). Then:
```bash
USE_LLM=1 bash forge/loop.sh                  # 24/7; grok reasons about each variant
python forge/dashboard.py && open STATUS.md    # progress
```
For true 24/7, wrap `loop.sh` in a launchd/nohup daemon (inject secrets via your secrets manager).

## Designing the reward (the make-or-break step)
A noisy/gameable metric makes the loop optimize garbage. Anchor it in **objective measurement**,
ideally distance to a **real reference** (reelforge scores generated clips against a real Netflix
clip via OpenCV optical-flow/palette — no LLM in the hot loop = free + un-hackable). Reserve any LLM
judge for the subjective residue, and periodically anchor with a few **human ratings** to catch
judge drift / reward-hacking.

## Worked example
`reelforge` (use-case skill `reelforge-autoresearch`): optimizes Telugu devotional video reels —
motion as a hard multiplicative gate (optical-flow energy vs a real reference), grok native T2V as
the near-free generator, LLM proposer authoring choreography prompts. Read it for a full instance.

## Requirements
python3 + `pyyaml` + `matplotlib`; `grok` CLI for `--llm` (else it falls back to epsilon-greedy search).
