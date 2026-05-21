"""Use-case skill root registration for Skills Hub."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from . import fs

DEFAULT_USE_CASES = fs.DEFAULT_USE_CASES


def _resolve_existing_directory(root: str | os.PathLike[str]) -> Path:
    target = Path(root).expanduser()
    if not target.exists():
        raise FileNotFoundError(f"use-case root does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"use-case root is not a directory: {target}")
    return target.resolve()


def _temporary_link_path(link: Path) -> Path:
    return link.with_name(f"{link.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")


def register(name: str, root: str | os.PathLike[str]) -> Path:
    """Register a use-case skill root under the hub."""
    target = _resolve_existing_directory(root)
    link = fs.use_case_link_dir(name)
    link.parent.mkdir(parents=True, exist_ok=True)

    if link.is_symlink():
        if link.resolve() == target:
            return link
    elif link.exists():
        raise FileExistsError(f"use-case path already exists and is not a symlink: {link}")

    tmp_link = _temporary_link_path(link)
    try:
        os.symlink(target, tmp_link, target_is_directory=True)
        os.replace(tmp_link, link)
    finally:
        if tmp_link.is_symlink() or tmp_link.exists():
            tmp_link.unlink()

    return link


def unregister(name: str) -> None:
    """Remove a use-case registration symlink without touching its target."""
    link = fs.use_case_link_dir(name)
    if link.is_symlink():
        link.unlink()
        return
    if link.exists():
        raise IsADirectoryError(f"use-case path exists and is not a symlink: {link}")


def list_registered() -> dict[str, str]:
    """Return registered use cases as name to resolved target path."""
    root = fs.tier_dir("use-cases")
    if not root.is_dir():
        return {}

    registered: dict[str, str] = {}
    for child in sorted(root.iterdir(), key=lambda path: path.name):
        if child.is_symlink():
            registered[child.name] = str(child.resolve())
    return registered


def discover() -> list[str]:
    """Register canonical use cases whose conventional skill roots exist."""
    registered: list[str] = []
    for name in DEFAULT_USE_CASES:
        root = fs.use_case_skills_dir(name)
        if root.is_dir():
            register(name, root)
            registered.append(name)
    return registered
