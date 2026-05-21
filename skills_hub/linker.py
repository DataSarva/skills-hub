"""Filesystem mutation helpers for Skills Hub migrations."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import uuid


def _same_link_target(target: Path, link_path: Path) -> bool:
    try:
        return link_path.resolve(strict=True) == target.resolve(strict=True)
    except FileNotFoundError:
        return os.readlink(link_path) == os.fspath(target)


def _remove_non_symlink(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def write_symlink(target: Path, link_path: Path, force: bool = False) -> None:
    """Atomically create or repoint a symlink at ``link_path``."""
    target = Path(target)
    link_path = Path(link_path)
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.is_symlink():
        if _same_link_target(target, link_path):
            return
    elif link_path.exists():
        if not force:
            raise FileExistsError(f"refusing to clobber non-symlink: {link_path}")
        _remove_non_symlink(link_path)

    temp_link = link_path.parent / f".{link_path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    try:
        os.symlink(target, temp_link, target_is_directory=True)
        os.replace(temp_link, link_path)
    finally:
        if temp_link.is_symlink() or temp_link.exists():
            temp_link.unlink()


def move_dir(src: Path, dest: Path) -> None:
    """Rename a directory, refusing to overwrite an existing destination."""
    src = Path(src)
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f"destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.rename(src, dest)
