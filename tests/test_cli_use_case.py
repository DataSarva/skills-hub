"""Integration tests for `skills-hub use-case ...` CLI subcommand group.

Drives the CLI entrypoint directly. Must never touch the real `~`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs


# ---------------------------------------------------------------------------
# help text
# ---------------------------------------------------------------------------


def test_use_case_help_runs(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        hub_cli.main(["use-case", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    lower = out.lower()
    assert "register" in lower
    assert "discover" in lower
    assert "unregister" in lower
    assert "list" in lower


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


def test_cli_register_creates_symlink(tmp_hub_root: Path) -> None:
    target = tmp_hub_root.parent / "investsarva-skills"
    target.mkdir()

    rc = hub_cli.main(
        ["use-case", "register", "investsarva", "--root", str(target)]
    )
    assert rc == 0

    link = hub_fs.tier_dir("use-cases") / "investsarva"
    assert link.is_symlink()
    assert link.resolve() == target.resolve()


def test_cli_register_missing_root_returns_nonzero(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_hub_root.parent / "nope"
    rc = hub_cli.main(
        ["use-case", "register", "ghost", "--root", str(missing)]
    )
    assert rc != 0


def test_cli_register_requires_root_flag(tmp_hub_root: Path) -> None:
    with pytest.raises(SystemExit):
        hub_cli.main(["use-case", "register", "investsarva"])


# ---------------------------------------------------------------------------
# unregister
# ---------------------------------------------------------------------------


def test_cli_unregister_removes_symlink(tmp_hub_root: Path) -> None:
    target = tmp_hub_root.parent / "pustak-skills"
    target.mkdir()
    hub_cli.main(["use-case", "register", "pustak", "--root", str(target)])

    rc = hub_cli.main(["use-case", "unregister", "pustak"])
    assert rc == 0
    assert not (hub_fs.tier_dir("use-cases") / "pustak").exists()
    # Target untouched.
    assert target.is_dir()


def test_cli_unregister_unknown_is_zero(tmp_hub_root: Path) -> None:
    """Unregistering a name that doesn't exist is a quiet no-op."""
    rc = hub_cli.main(["use-case", "unregister", "no-such"])
    assert rc == 0


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_cli_list_prints_registered_names_and_targets(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    t1 = tmp_hub_root.parent / "isv-skills"
    t1.mkdir()
    t2 = tmp_hub_root.parent / "psk-skills"
    t2.mkdir()

    hub_cli.main(["use-case", "register", "investsarva", "--root", str(t1)])
    hub_cli.main(["use-case", "register", "pustak", "--root", str(t2)])
    capsys.readouterr()  # drain

    rc = hub_cli.main(["use-case", "list"])
    assert rc == 0
    out = capsys.readouterr().out

    assert "investsarva" in out
    assert "pustak" in out
    assert str(t1.resolve()) in out or str(t1) in out
    assert str(t2.resolve()) in out or str(t2) in out


def test_cli_list_empty_runs(tmp_hub_root: Path) -> None:
    rc = hub_cli.main(["use-case", "list"])
    assert rc == 0


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------


def test_cli_discover_registers_existing_defaults(
    tmp_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_home / ".investsarva" / "skills").mkdir(parents=True)
    (tmp_home / ".chakra" / "skills").mkdir(parents=True)

    rc = hub_cli.main(["use-case", "discover"])
    assert rc == 0

    for name in ("investsarva", "chakra"):
        link = hub_fs.tier_dir("use-cases") / name
        assert link.is_symlink()


def test_cli_discover_with_no_roots_is_noop(tmp_home: Path) -> None:
    rc = hub_cli.main(["use-case", "discover"])
    assert rc == 0
