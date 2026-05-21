"""Filesystem scanner for agent skill directories."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from . import fs as hub_fs
from .migrator import AgentSkill


def _home_path(home: Path | None) -> Path:
    if home is None:
        return Path.home()
    path = Path(home).expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _agent_dir(agent: str, home: Path | None) -> Path:
    if home is None:
        return hub_fs.agent_target_dir(agent)
    return _home_path(home) / Path(hub_fs.AGENTS[agent])


def _is_valid_slug(slug: str) -> bool:
    try:
        hub_fs.skill_dir("general", slug)
    except ValueError:
        return False
    return True


def _regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames if not (current / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = current / filename
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _content_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in _regular_files(root):
        relpath = path.relative_to(root).as_posix().encode("utf-8")
        file_hash = hashlib.sha256(path.read_bytes()).digest()
        digest.update(relpath)
        digest.update(b"\0")
        digest.update(file_hash)
        digest.update(b"\0")
    return digest.hexdigest()


def scan_agents(home: Path | None = None) -> list[AgentSkill]:
    """Scan every known agent target and return real skill directories."""
    snapshot: list[AgentSkill] = []
    for agent in hub_fs.AGENTS:
        root = _agent_dir(agent, home)
        if not root.exists() or not root.is_dir() or root.is_symlink():
            continue
        for child in sorted(root.iterdir(), key=lambda path: path.name):
            if child.name.startswith("."):
                continue
            if child.is_symlink() or not child.is_dir() or not _is_valid_slug(child.name):
                continue
            snapshot.append(
                AgentSkill(
                    slug=child.name,
                    agent=agent,
                    source_dir=child,
                    content_hash=_content_hash(child),
                )
            )
    return snapshot
