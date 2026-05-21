"""Unit tests for the `hub-fs` deep module (`skills_hub.fs`).

`hub-fs` is the ONLY place in the codebase that knows where files live.
These tests pin the public surface area.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from skills_hub import fs as hub_fs


# ---------------------------------------------------------------------------
# hub_root()
# ---------------------------------------------------------------------------


def test_hub_root_defaults_to_dot_skills_hub_under_home(tmp_home: Path) -> None:
    """With no HUB_ROOT env var, hub_root() resolves to ~/.skills-hub."""
    assert hub_fs.hub_root() == tmp_home / ".skills-hub"


def test_hub_root_respects_env_override(tmp_hub_root: Path) -> None:
    """HUB_ROOT env var overrides the default."""
    assert hub_fs.hub_root() == tmp_hub_root


def test_hub_root_expands_user_in_env_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HUB_ROOT may use ~ — it must be expanded."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HUB_ROOT", "~/custom-hub")
    assert hub_fs.hub_root() == home / "custom-hub"


def test_hub_root_returns_absolute_path(tmp_home: Path) -> None:
    assert hub_fs.hub_root().is_absolute()


# ---------------------------------------------------------------------------
# tier_dir(tier)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tier", ["general", "tools", "use-cases"])
def test_tier_dir_for_each_known_tier(tier: str, tmp_hub_root: Path) -> None:
    assert hub_fs.tier_dir(tier) == tmp_hub_root / tier


def test_tier_dir_rejects_unknown_tier(tmp_hub_root: Path) -> None:
    with pytest.raises(ValueError):
        hub_fs.tier_dir("nope")


def test_tier_dir_rejects_empty_string(tmp_hub_root: Path) -> None:
    with pytest.raises(ValueError):
        hub_fs.tier_dir("")


# ---------------------------------------------------------------------------
# skill_dir(tier, slug)
# ---------------------------------------------------------------------------


def test_skill_dir_joins_tier_and_slug(tmp_hub_root: Path) -> None:
    assert hub_fs.skill_dir("general", "caveman") == tmp_hub_root / "general" / "caveman"


def test_skill_dir_rejects_unknown_tier(tmp_hub_root: Path) -> None:
    with pytest.raises(ValueError):
        hub_fs.skill_dir("invalid", "caveman")


@pytest.mark.parametrize("bad_slug", ["", "with/slash", "with\\back", ".", "..", "with space"])
def test_skill_dir_rejects_malformed_slug(bad_slug: str, tmp_hub_root: Path) -> None:
    with pytest.raises(ValueError):
        hub_fs.skill_dir("general", bad_slug)


# ---------------------------------------------------------------------------
# agent_target_dir(agent)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "agent,expected_suffix",
    [
        ("claude", ".claude/skills"),
        ("codex", ".codex/skills"),
        ("gemini", ".gemini/skills"),
        ("pi", ".pi/agent/skills"),
        ("feynman", ".feynman/agent/skills"),
        ("agents", ".agents/skills"),
    ],
)
def test_agent_target_dir_for_each_known_agent(
    agent: str, expected_suffix: str, tmp_home: Path
) -> None:
    assert hub_fs.agent_target_dir(agent) == tmp_home / expected_suffix


def test_agent_target_dir_rejects_unknown_agent(tmp_home: Path) -> None:
    with pytest.raises(ValueError):
        hub_fs.agent_target_dir("notanagent")


# ---------------------------------------------------------------------------
# cross_agent_alias_dir()
# ---------------------------------------------------------------------------


def test_cross_agent_alias_dir_is_dot_agents_skills(tmp_home: Path) -> None:
    """The cross-agent open-standard symlink farm lives at ~/.agents/skills."""
    assert hub_fs.cross_agent_alias_dir() == tmp_home / ".agents" / "skills"


def test_cross_agent_alias_dir_matches_agents_target(tmp_home: Path) -> None:
    """The alias dir must equal agent_target_dir('agents') so callers can use either."""
    assert hub_fs.cross_agent_alias_dir() == hub_fs.agent_target_dir("agents")


# ---------------------------------------------------------------------------
# Purity: hub_fs must not touch the filesystem on import or on read funcs
# ---------------------------------------------------------------------------


def test_hub_fs_does_not_create_directories(tmp_hub_root: Path) -> None:
    """Calling read functions must NOT create real dirs — pure path arithmetic only."""
    _ = hub_fs.hub_root()
    _ = hub_fs.tier_dir("general")
    _ = hub_fs.skill_dir("general", "demo")
    _ = hub_fs.agent_target_dir("claude")
    _ = hub_fs.cross_agent_alias_dir()
    assert not tmp_hub_root.exists()


# ---------------------------------------------------------------------------
# Tier constant exposure (for callers that iterate the three tiers)
# ---------------------------------------------------------------------------


def test_tiers_constant_is_general_tools_usecases() -> None:
    assert tuple(hub_fs.TIERS) == ("general", "tools", "use-cases")


def test_agents_constant_covers_known_targets() -> None:
    assert set(hub_fs.AGENTS) >= {
        "claude",
        "codex",
        "gemini",
        "pi",
        "feynman",
        "agents",
        "chakra",
        "investsarva",
    }
