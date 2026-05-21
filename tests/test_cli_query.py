"""Integration tests for `skills-hub list / show / search` CLI subcommands."""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs
from skills_hub import install as hub_install


SKILL_BODY = """---
name: {slug}
description: {description}
tier: {tier}
tags: [{tags}]
version: 1
---

# {slug}
"""


def _seed_skill(
    hub: Path,
    tier: str,
    slug: str,
    *,
    description: str = "",
    tags: list[str] | None = None,
) -> Path:
    skill = hub / tier / slug
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        SKILL_BODY.format(
            slug=slug,
            tier=tier,
            description=description,
            tags=", ".join(tags or []),
        ),
        encoding="utf-8",
    )
    return skill


def _seed_default(hub: Path) -> None:
    _seed_skill(hub, "general", "caveman", description="Ultra-compressed mode", tags=["style"])
    _seed_skill(hub, "general", "oracle", description="Predictive coding oracle", tags=["coding"])
    _seed_skill(hub, "tools", "release-peekaboo", description="Release helper", tags=["release"])


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_cli_list_prints_all_skills(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    for slug in ("caveman", "oracle", "release-peekaboo"):
        assert slug in out


def test_cli_list_filter_by_tier(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["list", "--tier", "general"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "caveman" in out
    assert "oracle" in out
    assert "release-peekaboo" not in out


def test_cli_list_filter_by_tag(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["list", "--tag", "release"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "release-peekaboo" in out
    assert "caveman" not in out


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def test_cli_show_prints_frontmatter_and_installed_where(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["show", "caveman"])
    assert rc == 0
    out = capsys.readouterr().out

    assert "caveman" in out
    assert "Ultra-compressed mode" in out
    # Installed-where map names every agent dir we deployed into.
    for agent in hub_fs.AGENTS:
        agent_dir = hub_fs.agent_target_dir(agent)
        assert str(agent_dir) in out or agent in out


def test_cli_show_unknown_slug_returns_nonzero(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    rc = hub_cli.main(["show", "does-not-exist"])
    assert rc != 0


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


def test_cli_search_matches_description(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["search", "predictive"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "oracle" in out
    assert "caveman" not in out


def test_cli_search_matches_tag(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    capsys.readouterr()

    rc = hub_cli.main(["search", "release"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "release-peekaboo" in out


def test_cli_search_no_match_is_zero(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hub_cli.main(["init"])
    _seed_default(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    rc = hub_cli.main(["search", "zzznomatchzzz"])
    assert rc == 0
