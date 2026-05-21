"""Integration tests for `skills_hub.install.sync`.

`sync` reconciles agent dirs with the current hub state after a `git pull`.
It must add new skill symlinks and remove orphans whose hub target is gone.
"""
from __future__ import annotations

import shutil
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


def test_sync_adds_new_skills(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_install.install(tmp_hub_root)

    # Simulate `git pull` adding a new skill upstream.
    _seed_skill(tmp_hub_root, "tools", "release-peekaboo")
    hub_install.sync(tmp_hub_root)

    for agent in hub_fs.AGENTS:
        assert (hub_fs.agent_target_dir(agent) / "release-peekaboo").is_symlink()


def test_sync_removes_orphan_symlinks(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    _seed_skill(tmp_hub_root, "general", "oracle")
    hub_install.install(tmp_hub_root)

    # Simulate `git pull` removing a skill.
    shutil.rmtree(tmp_hub_root / "general" / "oracle")
    hub_install.sync(tmp_hub_root)

    for agent in hub_fs.AGENTS:
        assert not (hub_fs.agent_target_dir(agent) / "oracle").exists()
        assert (hub_fs.agent_target_dir(agent) / "caveman").is_symlink()


def test_sync_preserves_foreign_symlinks(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_install.install(tmp_hub_root)

    foreign = tmp_hub_root.parent / "external"
    foreign.mkdir()
    link = hub_fs.agent_target_dir("claude") / "external"
    link.symlink_to(foreign, target_is_directory=True)

    hub_install.sync(tmp_hub_root)
    assert link.is_symlink()
    assert link.resolve() == foreign.resolve()


def test_sync_refreshes_index_json(tmp_hub_root: Path) -> None:
    import json

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_install.install(tmp_hub_root)
    _seed_skill(tmp_hub_root, "tools", "release-peekaboo")
    hub_install.sync(tmp_hub_root)
    data = json.loads((tmp_hub_root / "_index.json").read_text())
    slugs = {e["slug"] for e in data["skills"]}
    assert {"caveman", "release-peekaboo"} <= slugs


def test_cli_sync_subcommand(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_install.install(tmp_hub_root)
    _seed_skill(tmp_hub_root, "tools", "release-peekaboo")
    rc = hub_cli.main(["sync"])
    assert rc == 0
    assert (hub_fs.agent_target_dir("claude") / "release-peekaboo").is_symlink()
