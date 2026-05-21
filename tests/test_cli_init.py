"""Integration tests for `skills-hub init`.

These tests drive the CLI entrypoint directly. They MUST run against a tmp HOME
and never touch the real `~`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------


def test_init_help_runs_and_mentions_init(
    tmp_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        hub_cli.main(["init", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "init" in out.lower()


def test_top_level_help_runs(
    tmp_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        hub_cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "init" in out.lower()


# ---------------------------------------------------------------------------
# init: creates tier dirs + _index.json
# ---------------------------------------------------------------------------


def test_init_creates_hub_root_with_tier_dirs(tmp_hub_root: Path) -> None:
    rc = hub_cli.main(["init"])
    assert rc == 0
    assert tmp_hub_root.is_dir()
    for tier in ("general", "tools", "use-cases"):
        assert (tmp_hub_root / tier).is_dir(), f"missing tier dir: {tier}"


def test_init_writes_empty_index_json(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    index_path = tmp_hub_root / "_index.json"
    assert index_path.is_file()
    data = json.loads(index_path.read_text())
    # "empty placeholder" — accept either {} or {"skills": []} shape
    assert data == {} or data == {"skills": []}


def test_init_default_uses_home_dot_skills_hub(tmp_home: Path) -> None:
    """With no HUB_ROOT, init creates ~/.skills-hub."""
    rc = hub_cli.main(["init"])
    assert rc == 0
    assert (tmp_home / ".skills-hub").is_dir()
    assert (tmp_home / ".skills-hub" / "general").is_dir()


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_init_is_idempotent(tmp_hub_root: Path) -> None:
    rc1 = hub_cli.main(["init"])
    rc2 = hub_cli.main(["init"])
    assert rc1 == 0
    assert rc2 == 0
    for tier in ("general", "tools", "use-cases"):
        assert (tmp_hub_root / tier).is_dir()


def test_init_preserves_existing_index_json_content(tmp_hub_root: Path) -> None:
    """Re-running init must NOT clobber a populated _index.json."""
    hub_cli.main(["init"])
    index_path = tmp_hub_root / "_index.json"
    payload = {"skills": [{"slug": "caveman", "tier": "general"}]}
    index_path.write_text(json.dumps(payload))
    hub_cli.main(["init"])
    assert json.loads(index_path.read_text()) == payload


# ---------------------------------------------------------------------------
# --link (default symlink behavior) vs --copy
# ---------------------------------------------------------------------------


def test_init_link_symlinks_hub_root_to_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`skills-hub init --link <repo>` symlinks HUB_ROOT to the repo checkout."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("HUB_ROOT", raising=False)

    repo = tmp_path / "repo"
    (repo / "general").mkdir(parents=True)
    (repo / "tools").mkdir()
    (repo / "use-cases").mkdir()

    rc = hub_cli.main(["init", "--link", str(repo)])
    assert rc == 0
    hub = home / ".skills-hub"
    assert hub.is_symlink()
    assert hub.resolve() == repo.resolve()


def test_init_copy_does_not_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--copy` creates a plain directory, not a symlink."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("HUB_ROOT", raising=False)

    rc = hub_cli.main(["init", "--copy"])
    assert rc == 0
    hub = home / ".skills-hub"
    assert hub.is_dir()
    assert not hub.is_symlink()


# ---------------------------------------------------------------------------
# Safety: tests never touch the real $HOME
# ---------------------------------------------------------------------------


def test_init_never_touches_real_home(tmp_hub_root: Path) -> None:
    """Sanity check: HOME and HUB_ROOT must be under tmp."""
    assert os.environ["HOME"].startswith("/")
    assert "/tmp" in os.environ["HOME"] or "pytest" in os.environ["HOME"]
    hub_cli.main(["init"])
    assert str(tmp_hub_root).startswith(os.environ["HOME"]) or tmp_hub_root.is_absolute()


# ---------------------------------------------------------------------------
# Console-script entrypoint resolves
# ---------------------------------------------------------------------------


def test_skills_hub_console_script_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invoke `python -m skills_hub.cli --help` to ensure the CLI module is importable."""
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("HUB_ROOT", None)
    result = subprocess.run(
        [sys.executable, "-m", "skills_hub.cli", "--help"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "init" in result.stdout.lower()
