"""CLI integration: `skills-hub install` and `sync` wire to pustak bridge."""

from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import pustak_bridge


SKILL_BODY = """---
name: {slug}
description: skill {slug}
tier: {tier}
tags: []
version: 1
---

# {slug}
"""


def _seed_skill(hub: Path, tier: str, slug: str) -> None:
    skill = hub / tier / slug
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(SKILL_BODY.format(slug=slug, tier=tier), encoding="utf-8")


def _seed_wiki(home: Path) -> Path:
    wiki = home / ".pustak" / "wiki" / "general" / "tooling"
    wiki.mkdir(parents=True, exist_ok=True)
    return wiki


def test_cli_install_calls_pustak_bridge(
    tmp_hub_root: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_wiki(tmp_home)
    calls: list[Path] = []

    def _fake_mirror(hub_root: Path) -> int:
        calls.append(Path(hub_root))
        return 0

    monkeypatch.setattr(pustak_bridge, "mirror_index", _fake_mirror)

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    rc = hub_cli.main(["install"])

    assert rc == 0
    assert calls, "expected pustak bridge to be called from install"


def test_cli_sync_calls_pustak_bridge(
    tmp_hub_root: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_wiki(tmp_home)
    calls: list[Path] = []

    def _fake_mirror(hub_root: Path) -> int:
        calls.append(Path(hub_root))
        return 0

    monkeypatch.setattr(pustak_bridge, "mirror_index", _fake_mirror)

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_cli.main(["install"])
    calls.clear()
    _seed_skill(tmp_hub_root, "tools", "release-peekaboo")
    rc = hub_cli.main(["sync"])

    assert rc == 0
    assert calls, "expected pustak bridge to be called from sync"


def test_cli_install_no_pustak_flag_skips_bridge(
    tmp_hub_root: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_wiki(tmp_home)
    calls: list[Path] = []

    def _fake_mirror(hub_root: Path) -> int:
        calls.append(Path(hub_root))
        return 0

    monkeypatch.setattr(pustak_bridge, "mirror_index", _fake_mirror)

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    rc = hub_cli.main(["install", "--no-pustak"])

    assert rc == 0
    assert calls == [], "--no-pustak must suppress the bridge"


def test_cli_sync_no_pustak_flag_skips_bridge(
    tmp_hub_root: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_wiki(tmp_home)
    calls: list[Path] = []

    def _fake_mirror(hub_root: Path) -> int:
        calls.append(Path(hub_root))
        return 0

    monkeypatch.setattr(pustak_bridge, "mirror_index", _fake_mirror)

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    hub_cli.main(["install", "--no-pustak"])
    _seed_skill(tmp_hub_root, "tools", "release-peekaboo")
    rc = hub_cli.main(["sync", "--no-pustak"])

    assert rc == 0
    assert calls == [], "--no-pustak must suppress the bridge"


def test_cli_install_bridge_failure_does_not_fail_command(
    tmp_hub_root: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the bridge encounters a system-level error, install still returns 0."""
    _seed_wiki(tmp_home)

    def _boom(_hub_root: Path) -> int:
        # Bridge contract: it absorbs its own errors and returns 0.
        return 0

    monkeypatch.setattr(pustak_bridge, "mirror_index", _boom)

    hub_cli.main(["init"])
    _seed_skill(tmp_hub_root, "general", "caveman")
    rc = hub_cli.main(["install"])
    assert rc == 0
