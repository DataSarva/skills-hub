"""Read-only diagnostics for installed Skills Hub links."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import fs, indexer

_SKILL_DOC = "SKILL.md"


@dataclass(frozen=True)
class Diagnostic:
    broken: list[Path]
    non_symlink: list[Path]

    def is_ok(self) -> bool:
        return not self.broken and not self.non_symlink


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _same_path(left: Path, right: Path) -> bool:
    return left.resolve(strict=False) == right.resolve(strict=False)


def _looks_like_skill(path: Path) -> bool:
    return path.is_dir() and (path / _SKILL_DOC).is_file()


def _append_once(paths: list[Path], path: Path) -> None:
    if path not in paths:
        paths.append(path)


def check_health(hub_root: str | Path) -> Diagnostic:
    """Inspect agent skill directories without mutating them."""
    root = Path(hub_root).expanduser().resolve(strict=False)
    idx = indexer.build_index(root)
    expected_targets = {entry.path.resolve(strict=False) for entry in idx.entries}
    broken: list[Path] = []
    non_symlink: list[Path] = []

    for entry in idx.entries:
        target = entry.path.resolve(strict=False)
        for agent in fs.AGENTS:
            link = fs.agent_target_dir(agent) / entry.slug
            if link.is_symlink():
                if not _same_path(link, target) or not target.exists():
                    _append_once(broken, link)
            elif link.exists():
                _append_once(non_symlink, link)
            else:
                _append_once(non_symlink, link)

    for agent in fs.AGENTS:
        agent_dir = fs.agent_target_dir(agent)
        if not agent_dir.is_dir():
            continue
        for child in sorted(agent_dir.iterdir(), key=lambda path: path.name):
            if child.is_symlink():
                target = child.resolve(strict=False)
                if _is_under(target, root) and (
                    not target.exists() or target.resolve(strict=False) not in expected_targets
                ):
                    _append_once(broken, child)
            elif _looks_like_skill(child):
                _append_once(non_symlink, child)

    return Diagnostic(broken=broken, non_symlink=non_symlink)
