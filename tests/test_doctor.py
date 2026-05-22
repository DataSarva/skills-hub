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


# ---------------------------------------------------------------------------
# S9: use-case-owned real dirs are allowed (not flagged as non-symlink).
# ---------------------------------------------------------------------------


def _make_owned_skill(use_case_skills_root: Path, slug: str) -> Path:
    """Create a real-dir skill inside a use-case's own skills root."""
    use_case_skills_root.mkdir(parents=True, exist_ok=True)
    skill = use_case_skills_root / slug
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(SKILL_BODY.format(slug=slug), encoding="utf-8")
    return skill


def _plant_real_dir_in_agent(agent: str, slug: str) -> Path:
    """Plant a real dir (not a symlink) at the agent's target/slug location."""
    agent_dir = hub_fs.agent_target_dir(agent)
    agent_dir.mkdir(parents=True, exist_ok=True)
    real = agent_dir / slug
    real.mkdir(parents=True, exist_ok=True)
    (real / "SKILL.md").write_text("real dir", encoding="utf-8")
    return real


def test_doctor_does_not_flag_use_case_owned_real_dir(tmp_hub_root: Path) -> None:
    """Agent-side real dir whose slug exists in a registered use-case is allowed."""
    hub_cli.main(["init"])

    # Stand up the use-case skills root with one owned skill.
    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    _make_owned_skill(uc_skills, "price-watch")

    # Register the use-case via the hub.
    use_cases.register("investsarva", uc_skills)

    # The chakra agent owns a real dir for this slug.
    _plant_real_dir_in_agent("claude", "price-watch")

    report = hub_doctor.check_health(tmp_hub_root)
    # Not flagged as non-symlink.
    assert all("price-watch" not in str(p) for p in report.non_symlink), (
        f"price-watch should not be flagged as non-symlink: {report.non_symlink}"
    )
    # No broken either.
    assert report.broken == []
    # Owned status surfaces it informationally.
    owned = getattr(report, "owned", [])
    assert any("price-watch" in str(p) for p in owned), (
        f"price-watch should show in report.owned: {owned}"
    )
    # Doctor exits ok (informational, exit 0).
    assert report.is_ok()


def test_doctor_flags_unowned_real_dir(tmp_hub_root: Path) -> None:
    """A real-dir intrusion not owned by any registered use-case stays flagged."""
    hub_cli.main(["init"])

    # Register a use-case but only with a different slug.
    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    _make_owned_skill(uc_skills, "price-watch")
    use_cases.register("investsarva", uc_skills)

    # Plant an unowned real dir at a different slug.
    _plant_real_dir_in_agent("claude", "random-rogue")

    report = hub_doctor.check_health(tmp_hub_root)
    assert any("random-rogue" in str(p) for p in report.non_symlink)
    assert not report.is_ok()


def test_doctor_owned_classification_routes_through_use_cases_module(
    tmp_hub_root: Path,
) -> None:
    """A real dir owned by an unregistered use-case is still flagged.

    Ownership must be determined via `use_cases.list_registered()`, not by
    sniffing `~/.<slug>/skills/`. Without registration, the agent-side
    real dir is just an intrusion.
    """
    hub_cli.main(["init"])

    # Build a use-case skills root but DO NOT register it.
    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    _make_owned_skill(uc_skills, "price-watch")

    _plant_real_dir_in_agent("claude", "price-watch")

    report = hub_doctor.check_health(tmp_hub_root)
    assert any("price-watch" in str(p) for p in report.non_symlink), (
        "unregistered use-case must not grant ownership"
    )
    assert not report.is_ok()


def test_doctor_owned_does_not_hardcode_slugs() -> None:
    """The doctor source must not name any specific use-case slug."""
    import inspect

    src = inspect.getsource(hub_doctor)
    # Whichever default-use-case strings are listed must not appear inside doctor.
    for slug in ("investsarva", "pustak", "chakra", "memsarva", "pi", "feynman",
                 "price-watch", "news-catalyst", "scheduled-report",
                 "wiki-archive", "learning-summary", "health-check"):
        assert slug not in src, f"doctor must not hardcode {slug!r}"


def test_cli_doctor_verbose_lists_owned_entries(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`skills-hub doctor --verbose` prints owned entries with `owned:` prefix."""
    hub_cli.main(["init"])

    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    _make_owned_skill(uc_skills, "price-watch")
    use_cases.register("investsarva", uc_skills)
    _plant_real_dir_in_agent("claude", "price-watch")

    rc = hub_cli.main(["doctor", "--verbose"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "owned:" in captured.out
    assert "price-watch" in captured.out


def test_cli_doctor_default_omits_owned_entries(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Default `skills-hub doctor` (no --verbose) hides owned entries."""
    hub_cli.main(["init"])

    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    _make_owned_skill(uc_skills, "price-watch")
    use_cases.register("investsarva", uc_skills)
    _plant_real_dir_in_agent("claude", "price-watch")

    rc = hub_cli.main(["doctor"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "owned:" not in captured.out
    assert "non-symlink" not in captured.out


def test_cli_doctor_returns_zero_when_only_owned_dirs_present(
    tmp_hub_root: Path,
) -> None:
    """If the only oddity is owned use-case dirs, exit is 0."""
    hub_cli.main(["init"])

    home = Path.home()
    uc_skills = home / ".investsarva" / "skills"
    for slug in ("price-watch", "news-catalyst", "scheduled-report"):
        _make_owned_skill(uc_skills, slug)
    use_cases.register("investsarva", uc_skills)
    for slug in ("price-watch", "news-catalyst", "scheduled-report"):
        _plant_real_dir_in_agent("claude", slug)

    rc = hub_cli.main(["doctor"])
    assert rc == 0


def test_doctor_module_does_not_hardcode_dot_dir() -> None:
    """Doctor must not literal-read `~/.<usecase>/skills/`."""
    import inspect

    src = inspect.getsource(hub_doctor)
    # No DEFAULT_USE_CASES iteration; ownership goes through use_cases module.
    assert "DEFAULT_USE_CASES" not in src
    assert "use_case_skills_dir" not in src


# Imports used only by the S9 tests above.
from skills_hub import use_cases  # noqa: E402
