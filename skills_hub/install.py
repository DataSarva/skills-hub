"""Install and synchronize Skills Hub links into agent skill directories."""

from __future__ import annotations

import json
from pathlib import Path

from . import fs, indexer, linker

_INDEX_NAME = "_index.json"


def _hub_root(hub_root: str | Path) -> Path:
    return Path(hub_root).expanduser().resolve(strict=False)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _write_index(root: Path, index: indexer.Index) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(index.to_dict(), indent=2, sort_keys=True)
    (root / _INDEX_NAME).write_text(f"{payload}\n", encoding="utf-8")


def _agent_dirs() -> list[Path]:
    return [fs.agent_target_dir(agent) for agent in fs.AGENTS]


def _agent_children() -> list[Path]:
    children: list[Path] = []
    for agent_dir in _agent_dirs():
        if agent_dir.is_dir():
            children.extend(sorted(agent_dir.iterdir(), key=lambda path: path.name))
    return children


def _remove_hub_symlinks(root: Path, *, only_missing: bool) -> None:
    for path in _agent_children():
        if not path.is_symlink():
            continue
        target = path.resolve(strict=False)
        if not _is_under(target, root):
            continue
        if only_missing and target.exists():
            continue
        path.unlink()


def install(hub_root: str | Path) -> indexer.Index:
    """Install every indexed skill into every known agent directory."""
    root = _hub_root(hub_root)
    index = indexer.build_index(root)
    for entry in index.entries:
        for agent in fs.AGENTS:
            linker.write_symlink(entry.path, fs.agent_target_dir(agent) / entry.slug)
    _write_index(root, index)
    return index


def uninstall(hub_root: str | Path) -> None:
    """Remove only agent symlinks that point into the hub root."""
    _remove_hub_symlinks(_hub_root(hub_root), only_missing=False)


def sync(hub_root: str | Path) -> indexer.Index:
    """Reconcile agent links with the current hub contents."""
    root = _hub_root(hub_root)
    index = install(root)
    _remove_hub_symlinks(root, only_missing=True)
    _write_index(root, indexer.build_index(root))
    return index
