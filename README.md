# skills-hub

Canonical Mac-Mini skills registry. One source of truth for every AI agent on this host — Claude Code, Codex CLI, Gemini CLI, Pi (chakra kernel adapter), Feynman, OpenClaw, and any future agent that follows the [SKILL.md open standard](https://www.thepromptindex.com/how-to-use-ai-agent-skills-the-complete-guide.html). Chakra itself is the Mac-Mini framework runtime (`~/.chakra/`) — it orchestrates pi/hermes/pustak as components and has no agent-level skill discovery path of its own.

## Why

Each CLI ships its own skill discovery path (`~/.claude/skills`, `~/.codex/skills`, `~/.gemini/skills`, `~/.agents/skills`, plus per-repo `.claude/skills`, `.agents/skills`, `.gemini/skills`). Without a hub, the same skill ends up triplicated, drifts, and rots. This hub keeps **one canonical copy per skill** and symlinks it into every agent's discovery path so all agents auto-find it with zero manual intervention.

## Layout

```
general/        Cross-agent, cross-use-case (caveman, tdd, frontend-design, debugging, …)
tools/          CLI/SDK-specific (claude-api, codex-cli, gemini-cli, google-cloud, openclaw, grok, …)
use-cases/      Per-project (investsarva, pustak, chakra, memsarva, …) — usually symlinks to ~/.<usecase>/skills/
bin/            Hub CLI: skills-hub install|sync|list|show|search|new
tests/          Symlink-resolution tests per agent
docs/           Layout + contribution guide
```

## Tiers

- **general** — used everywhere. No domain coupling. Examples: caveman, tdd, debugging, frontend-design, brainstorming.
- **tools** — tied to a specific external tool/SDK. Examples: claude-api, gemini-cli, openclaw-relay, google-cloud, grok.
- **use-cases** — owned by a use-case root (`~/.investsarva/skills/`, `~/.pustak/skills/`). Hub *exposes* via symlink; use-case still owns.

## Discovery contract

After `skills-hub install` runs, **every** agent on this Mac Mini finds every applicable skill automatically — no flags, no manual paths.

| Agent | Discovery path | How hub plugs in |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | symlink per skill |
| Codex CLI | `~/.codex/skills/<name>/SKILL.md` + `~/.agents/skills/` alias | symlink |
| Gemini CLI | `~/.gemini/skills/<name>/SKILL.md` + `~/.agents/skills/` alias | symlink |
| Pi (chakra kernel adapter) | `~/.pi/agent/skills/<name>/SKILL.md` | symlink |
| Feynman | `~/.feynman/agent/skills/<name>/SKILL.md` | symlink |
| OpenClaw | per project `.claude/skills/` or `~/.openclaw/skills/` | symlink |
| Per-repo agents | `.agents/skills/<name>` | optional symlink farm |

The `~/.agents/skills/` directory is materialized as a symlink farm covering `general/` + `tools/` so any agent that follows the cross-agent open standard finds skills without further config.

## CLI

```bash
skills-hub install        # full deploy: link this repo into every agent dir on this host
skills-hub sync           # reconcile after pulls (idempotent)
skills-hub list [--tier general|tools|use-cases] [--tag ...]
skills-hub show <slug>
skills-hub search <query>
skills-hub new <slug> --tier general|tools|use-cases
skills-hub doctor         # verify symlinks resolve in every agent dir
```

## Adding a skill

1. `skills-hub new <slug> --tier general` — scaffolds `<tier>/<slug>/SKILL.md` with valid frontmatter.
2. Edit. Commit. Push.
3. On every Mac Mini that has skills-hub installed, `git pull && skills-hub sync` makes it instantly visible to every AI agent.

## References

- [Anthropic skills docs](https://code.claude.com/docs/en/skills)
- [Codex skills docs](https://developers.openai.com/codex/skills)
- [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)
- [Cross-agent sharing patterns (runkids/skillshare)](https://github.com/runkids/skillshare)
- [Pedro Rodrigues / Supabase — skills + MCP context gap](https://www.youtube.com/watch?v=JT3OzDKrucU)
