"""Integration tests for `skills_hub.doctor`.

`doctor` is read-only: walks agent dirs and reports broken / missing /
unexpected symlinks. Exits non-zero if anything is wrong.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import doctor as hub_doctor
from skills_hub import fs as hub_fs
from skills_hub import install as hub_install


SKILL_BODY = """---
name: {slug}
description: skill {slug}
tier: general
tags: []
version: 1
---

# {slug}
"""


def _seed(hub: Path, slug: str) -> Path:
    skill = hub / "general" / slug
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(SKILL_BODY.format(slug=slug), encoding="utf-8")
    return skill


def test_doctor_clean_install_is_ok(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed(tmp_hub_root, "caveman")
    hub_install.install(tmp_hub_root)

    report = hub_doctor.check_health(tmp_hub_root)
    assert report.is_ok()
    assert report.broken == []


def test_doctor_detects_broken_symlink(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed(tmp_hub_root, "caveman")
    hub_install.install(tmp_hub_root)

    # Delete the hub-side skill — agent symlinks now dangle.
    shutil.rmtree(tmp_hub_root / "general" / "caveman")

    report = hub_doctor.check_health(tmp_hub_root)
    assert not report.is_ok()
    assert any("caveman" in str(p) for p in report.broken)


def test_doctor_detects_non_symlink_entry(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed(tmp_hub_root, "caveman")
    hub_install.install(tmp_hub_root)

    # Place a plain directory where a symlink should live.
    rogue_agent = hub_fs.agent_target_dir("claude")
    rogue_dir = rogue_agent / "rogue"
    rogue_dir.mkdir()
    (rogue_dir / "SKILL.md").write_text("not a symlink")

    report = hub_doctor.check_health(tmp_hub_root)
    assert not report.is_ok()


def test_cli_doctor_returns_zero_on_clean(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed(tmp_hub_root, "caveman")
    hub_install.install(tmp_hub_root)
    rc = hub_cli.main(["doctor"])
    assert rc == 0


def test_cli_doctor_returns_nonzero_on_broken(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    _seed(tmp_hub_root, "caveman")
    hub_install.install(tmp_hub_root)
    shutil.rmtree(tmp_hub_root / "general" / "caveman")
    rc = hub_cli.main(["doctor"])
    assert rc != 0


def test_doctor_module_is_readonly() -> None:
    """Doctor must not mutate filesystem."""
    import inspect

    src = inspect.getsource(hub_doctor)
    for forbidden in ("os.symlink", "os.rename", "os.replace", "shutil.rmtree", "shutil.move"):
        assert forbidden not in src, f"doctor must be read-only, found {forbidden!r}"
