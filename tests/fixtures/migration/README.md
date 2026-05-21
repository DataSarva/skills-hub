# Migration fixtures

Sample skill payloads used by the migration tests. Each leaf directory is a
slug-shaped tree containing a `SKILL.md` and optional support files.

* `identical/` — content shared verbatim across multiple agents.
* `divergent/` — variants that differ between agents (used to test conflict
  detection + HITL diff output + `--resolve` arbitration).
* `unique/` — content present in a single agent dir.
