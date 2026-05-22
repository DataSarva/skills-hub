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


# ---------------------------------------------------------------------------
# discover_chakra_agents()
# ---------------------------------------------------------------------------


def _make_chakra(home: Path, name: str) -> Path:
    """Create a chakra-shaped dir at ~/.<name>/ with AGENTS.md + skills/."""
    root = home / f".{name}"
    root.mkdir()
    (root / "AGENTS.md").write_text(f"# {name}\n", encoding="utf-8")
    (root / "skills").mkdir()
    return root


def test_discover_returns_chakra_shaped_dirs(tmp_home: Path) -> None:
    """A dir with both AGENTS.md and skills/ is discovered."""
    _make_chakra(tmp_home, "newchakra")
    result = hub_fs.discover_chakra_agents()
    assert "newchakra" in result
    assert result["newchakra"] == ".newchakra/skills"


def test_discover_excludes_dirs_missing_agents_md(tmp_home: Path) -> None:
    root = tmp_home / ".halfchakra"
    root.mkdir()
    (root / "skills").mkdir()  # has skills/ but no AGENTS.md
    result = hub_fs.discover_chakra_agents()
    assert "halfchakra" not in result


def test_discover_excludes_dirs_missing_skills(tmp_home: Path) -> None:
    root = tmp_home / ".halfchakra2"
    root.mkdir()
    (root / "AGENTS.md").write_text("hi", encoding="utf-8")  # missing skills/
    result = hub_fs.discover_chakra_agents()
    assert "halfchakra2" not in result


def test_discover_excludes_static_agent_names_by_name(tmp_home: Path) -> None:
    """Even if `.claude/` happens to be chakra-shaped, it's excluded by name."""
    for name in ("claude", "codex", "gemini", "chakra", "investsarva"):
        _make_chakra(tmp_home, name)
    result = hub_fs.discover_chakra_agents()
    assert "claude" not in result
    assert "codex" not in result
    assert "gemini" not in result
    assert "chakra" not in result
    assert "investsarva" not in result


def test_discover_excludes_pustak_and_skills_hub(tmp_home: Path) -> None:
    _make_chakra(tmp_home, "pustak")
    _make_chakra(tmp_home, "skills-hub")
    result = hub_fs.discover_chakra_agents()
    assert "pustak" not in result
    assert "skills-hub" not in result


def test_discover_skips_non_dirs(tmp_home: Path) -> None:
    (tmp_home / ".afile").write_text("x", encoding="utf-8")
    result = hub_fs.discover_chakra_agents()
    assert ".afile" not in result
    assert "afile" not in result


def test_discover_skips_symlink_children(tmp_home: Path, tmp_path: Path) -> None:
    real = tmp_path / "real-chakra"
    real.mkdir()
    (real / "AGENTS.md").write_text("x", encoding="utf-8")
    (real / "skills").mkdir()
    link = tmp_home / ".linkedchakra"
    link.symlink_to(real, target_is_directory=True)
    result = hub_fs.discover_chakra_agents()
    assert "linkedchakra" not in result


def test_discover_does_not_recurse(tmp_home: Path) -> None:
    nested_parent = tmp_home / ".outer"
    nested_parent.mkdir()
    (nested_parent / "AGENTS.md").write_text("outer", encoding="utf-8")
    skills_dir = nested_parent / "skills"
    skills_dir.mkdir()
    # Place a chakra-shaped dir nested inside — must NOT be discovered.
    nested = nested_parent / "nestedchakra"
    nested.mkdir()
    (nested / "AGENTS.md").write_text("x", encoding="utf-8")
    (nested / "skills").mkdir()
    result = hub_fs.discover_chakra_agents()
    assert "nestedchakra" not in result
    # outer itself is dotted at HOME level and qualifies.
    assert "outer" in result


def test_discover_excludes_non_dotted_children(tmp_home: Path) -> None:
    """Top-level non-dotted dirs are not chakra agents."""
    root = tmp_home / "plain"
    root.mkdir()
    (root / "AGENTS.md").write_text("x", encoding="utf-8")
    (root / "skills").mkdir()
    result = hub_fs.discover_chakra_agents()
    assert "plain" not in result


def test_discover_returns_empty_for_empty_home(tmp_home: Path) -> None:
    assert hub_fs.discover_chakra_agents() == {}
