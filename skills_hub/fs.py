"""Pure path authority for Skills Hub.

This module is intentionally limited to path arithmetic. None of the read
helpers create directories or inspect filesystem contents.
"""

from __future__ import annotations

import os
from pathlib import Path

TIERS = ("general", "tools", "use-cases")
DEFAULT_USE_CASES = ("investsarva", "pustak", "chakra", "memsarva", "pi", "feynman")

_DEFAULT_HUB_NAME = ".skills-hub"

AGENTS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
    "gemini": ".gemini/skills",
    "pi": ".pi/agent/skills",
    "feynman": ".feynman/agent/skills",
    "agents": ".agents/skills",
    # Chakra framework runtime + chakra-bootstrapped use-case agents.
    # Each has its own AGENTS.md instruction file alongside skills/, and
    # runs on the hermes kernel. Hub installs general/tools symlinks into
    # each so the chakra-side agent auto-finds every hub skill.
    "chakra": ".chakra/skills",
    "investsarva": ".investsarva/skills",
}


def _absolute(path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _validate_tier(tier: str) -> None:
    if tier not in TIERS:
        raise ValueError(f"unknown tier: {tier!r}")


def _validate_slug(slug: str) -> None:
    if not isinstance(slug, str):
        raise ValueError("slug must be a string")
    if (
        not slug
        or slug in {".", ".."}
        or "/" in slug
        or "\\" in slug
        or any(char.isspace() for char in slug)
    ):
        raise ValueError(f"malformed slug: {slug!r}")


def hub_root() -> Path:
    """Return the configured hub root as an absolute path."""
    raw_root = os.environ.get("HUB_ROOT")
    if raw_root:
        return _absolute(Path(raw_root))
    return _absolute(Path.home() / _DEFAULT_HUB_NAME)


def pustak_repo_dir() -> Path:
    """Return the local Pustak repository path."""
    raw_repo = os.environ.get("PUSTAK_REPO")
    if raw_repo:
        return _absolute(Path(raw_repo))
    return _absolute(Path.home() / "aisarva" / "pustak")


def tier_dir(tier: str) -> Path:
    """Return the directory for a known tier."""
    _validate_tier(tier)
    return hub_root() / tier


def skill_dir(tier: str, slug: str) -> Path:
    """Return the directory for a skill slug within a known tier."""
    _validate_tier(tier)
    _validate_slug(slug)
    return tier_dir(tier) / slug


def use_case_link_dir(name: str) -> Path:
    """Return the hub symlink path for a use-case skill root."""
    return skill_dir("use-cases", name)


def use_case_root_dir(name: str) -> Path:
    """Return the conventional use-case home directory."""
    _validate_slug(name)
    return _absolute(Path.home() / f".{name}")


def use_case_skills_dir(name: str) -> Path:
    """Return the conventional use-case skills directory."""
    return use_case_root_dir(name) / "skills"


def agent_target_dir(agent: str) -> Path:
    """Return the target skills directory for a known agent."""
    try:
        suffix = AGENTS[agent]
    except KeyError as exc:
        raise ValueError(f"unknown agent: {agent!r}") from exc
    return _absolute(Path.home() / suffix)


def cross_agent_alias_dir() -> Path:
    """Return the cross-agent alias directory."""
    return agent_target_dir("agents")
