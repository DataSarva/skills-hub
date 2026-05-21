"""Unit tests for `skills_hub.linker`.

`linker` is the ONLY module allowed to call `os.symlink` / `os.rename`.
Atomic writes (write-temp + rename), idempotency, and clobber refusal are
the deep-module guarantees pinned here.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from skills_hub import linker as hub_linker


# ---------------------------------------------------------------------------
# write_symlink: happy path + idempotency
# ---------------------------------------------------------------------------


def test_write_symlink_creates_link_pointing_at_target(tmp_path: Path) -> None:
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.parent.mkdir(parents=True)

    hub_linker.write_symlink(target, link)

    assert link.is_symlink()
    assert link.resolve() == target.resolve()


def test_write_symlink_creates_parent_dirs(tmp_path: Path) -> None:
    """Parents of the link path are created if missing."""
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "deep" / "nested" / "demo"
    # Parent does NOT exist yet
    assert not link.parent.exists()

    hub_linker.write_symlink(target, link)

    assert link.is_symlink()


def test_write_symlink_is_idempotent_when_link_already_points_to_target(
    tmp_path: Path,
) -> None:
    """Re-running write_symlink with the same target must be a no-op."""
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.parent.mkdir(parents=True)

    hub_linker.write_symlink(target, link)
    inode_before = os.lstat(link).st_ino

    hub_linker.write_symlink(target, link)
    inode_after = os.lstat(link).st_ino

    assert link.is_symlink()
    assert link.resolve() == target.resolve()
    # Idempotent: link was not torn down + recreated
    assert inode_before == inode_after


def test_write_symlink_replaces_existing_symlink_pointing_elsewhere(
    tmp_path: Path,
) -> None:
    """A stale symlink pointing at the wrong target is repointed (still idempotent in intent)."""
    correct_target = tmp_path / "hub" / "general" / "demo"
    correct_target.mkdir(parents=True)
    other_target = tmp_path / "hub" / "general" / "other"
    other_target.mkdir(parents=True)

    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.parent.mkdir(parents=True)
    os.symlink(other_target, link)

    hub_linker.write_symlink(correct_target, link)

    assert link.is_symlink()
    assert link.resolve() == correct_target.resolve()


# ---------------------------------------------------------------------------
# write_symlink: clobber refusal on real directories / files
# ---------------------------------------------------------------------------


def test_write_symlink_refuses_to_clobber_real_directory_without_force(
    tmp_path: Path,
) -> None:
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.mkdir(parents=True)
    (link / "SKILL.md").write_text("real content")

    with pytest.raises(FileExistsError):
        hub_linker.write_symlink(target, link)

    # Real dir untouched
    assert not link.is_symlink()
    assert (link / "SKILL.md").read_text() == "real content"


def test_write_symlink_refuses_to_clobber_real_file_without_force(
    tmp_path: Path,
) -> None:
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.parent.mkdir(parents=True)
    link.write_text("regular file, not a symlink")

    with pytest.raises(FileExistsError):
        hub_linker.write_symlink(target, link)

    assert link.is_file()
    assert not link.is_symlink()


def test_write_symlink_force_overwrites_non_symlink(tmp_path: Path) -> None:
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.mkdir(parents=True)
    (link / "SKILL.md").write_text("will be moved aside")

    hub_linker.write_symlink(target, link, force=True)

    assert link.is_symlink()
    assert link.resolve() == target.resolve()


# ---------------------------------------------------------------------------
# move_dir: atomic move (rename), used to relocate scattered skill dirs
# ---------------------------------------------------------------------------


def test_move_dir_relocates_directory(tmp_path: Path) -> None:
    src = tmp_path / "home" / ".claude" / "skills" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("payload")

    dest = tmp_path / "hub" / "general" / "demo"

    hub_linker.move_dir(src, dest)

    assert not src.exists()
    assert dest.is_dir()
    assert (dest / "SKILL.md").read_text() == "payload"


def test_move_dir_creates_parent_dirs(tmp_path: Path) -> None:
    src = tmp_path / "home" / ".claude" / "skills" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("payload")

    dest = tmp_path / "hub" / "general" / "demo"
    # Hub tier dir does not yet exist
    assert not dest.parent.exists()

    hub_linker.move_dir(src, dest)

    assert dest.is_dir()


def test_move_dir_refuses_to_clobber_existing_dest(tmp_path: Path) -> None:
    src = tmp_path / "home" / ".claude" / "skills" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("new")

    dest = tmp_path / "hub" / "general" / "demo"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("existing")

    with pytest.raises(FileExistsError):
        hub_linker.move_dir(src, dest)

    # Both untouched
    assert (src / "SKILL.md").read_text() == "new"
    assert (dest / "SKILL.md").read_text() == "existing"


# ---------------------------------------------------------------------------
# Atomicity: temp + rename, never a half-written link
# ---------------------------------------------------------------------------


def test_write_symlink_leaves_no_temp_files_behind(tmp_path: Path) -> None:
    target = tmp_path / "hub" / "general" / "demo"
    target.mkdir(parents=True)
    link = tmp_path / "home" / ".claude" / "skills" / "demo"
    link.parent.mkdir(parents=True)

    hub_linker.write_symlink(target, link)

    # Only the link itself should exist in the parent dir.
    siblings = list(link.parent.iterdir())
    assert siblings == [link]
