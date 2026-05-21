"""Integration tests for `skills_hub.install`.

`install` is the orchestrator: it composes `fs` + `linker` to materialize a
per-skill symlink in every documented agent dir, plus the cross-agent alias.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs
from skills_hub import install as hub_install


SKILL_BODY = """---
name: {slug}
description: skill {slug}
tier: {tier}
tags: []
version: 1
---

# {slug}
"""


def _seed_skill(hub: Path, tier: str, slug: str) -> Path:
    skill = hub / tier / slug
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(SKILL_BODY.format(slug=slug, tier=tier), encoding="utf-8")
    return skill


def _seed_minimal_hub(hub: Path) -> None:
    hub.mkdir(parents=True, exist_ok=True)
    for tier in ("general", "tools", "use-cases"):
        (hub / tier).mkdir(parents=True, exist_ok=True)
    _seed_skill(hub, "general", "caveman")
    _seed_skill(hub, "tools", "release-peekaboo")


# ---------------------------------------------------------------------------
# install() — every agent dir + alias gets a symlink for every skill
# ---------------------------------------------------------------------------


def test_install_creates_symlink_in_every_agent_dir(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)

    hub_install.install(tmp_hub_root)

    for agent in hub_fs.AGENTS:
        agent_dir = hub_fs.agent_target_dir(agent)
        for slug, tier in (("caveman", "general"), ("release-peekaboo", "tools")):
            link = agent_dir / slug
            assert link.is_symlink(), f"missing link {link}"
            assert link.resolve() == (tmp_hub_root / tier / slug).resolve()


def test_install_includes_cross_agent_alias(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    alias = hub_fs.cross_agent_alias_dir() / "caveman"
    assert alias.is_symlink()
    assert alias.resolve() == (tmp_hub_root / "general" / "caveman").resolve()


def test_install_is_idempotent(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    hub_install.install(tmp_hub_root)  # second run must not raise
    for agent in hub_fs.AGENTS:
        link = hub_fs.agent_target_dir(agent) / "caveman"
        assert link.is_symlink()


def test_install_writes_index_json(tmp_hub_root: Path) -> None:
    import json

    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    idx = tmp_hub_root / "_index.json"
    data = json.loads(idx.read_text())
    slugs = {e["slug"] for e in data["skills"]}
    assert {"caveman", "release-peekaboo"} <= slugs


# ---------------------------------------------------------------------------
# uninstall — removes ONLY symlinks whose target lives inside hub
# ---------------------------------------------------------------------------


def test_uninstall_removes_only_hub_targeted_symlinks(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_install.install(tmp_hub_root)

    # Foreign symlink in an agent dir pointing outside the hub: must survive.
    foreign_target = tmp_hub_root.parent / "external-skill"
    foreign_target.mkdir()
    foreign_link = hub_fs.agent_target_dir("claude") / "external"
    foreign_link.symlink_to(foreign_target, target_is_directory=True)

    # Non-symlink file in an agent dir: must survive.
    plain = hub_fs.agent_target_dir("claude") / "notes.txt"
    plain.write_text("hello")

    hub_install.uninstall(tmp_hub_root)

    for agent in hub_fs.AGENTS:
        assert not (hub_fs.agent_target_dir(agent) / "caveman").exists()

    assert foreign_link.is_symlink()
    assert plain.read_text() == "hello"


def test_install_then_uninstall_then_install_works(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    hub_install.uninstall(tmp_hub_root)
    hub_install.install(tmp_hub_root)
    assert (hub_fs.agent_target_dir("claude") / "caveman").is_symlink()


# ---------------------------------------------------------------------------
# CLI: skills-hub install / uninstall
# ---------------------------------------------------------------------------


def test_cli_install_subcommand(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    rc = hub_cli.main(["install"])
    assert rc == 0
    assert (hub_fs.agent_target_dir("claude") / "caveman").is_symlink()


def test_cli_uninstall_subcommand(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_minimal_hub(tmp_hub_root)
    hub_cli.main(["install"])
    rc = hub_cli.main(["uninstall"])
    assert rc == 0
    assert not (hub_fs.agent_target_dir("claude") / "caveman").exists()
