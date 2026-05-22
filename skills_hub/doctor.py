"""Read-only diagnostics for installed Skills Hub links."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import fs, indexer, use_cases

_SKILL_DOC = "SKILL.md"


@dataclass(frozen=True)
class Diagnostic:
    broken: list[Path]
    non_symlink: list[Path]
    owned: list[Path] = field(default_factory=list)

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


def _is_real_dir(path: Path) -> bool:
    return not path.is_symlink() and path.is_dir()


def _registered_owned_slugs() -> set[str]:
    slugs: set[str] = set()
    for target in use_cases.list_registered().values():
        target_dir = Path(target).expanduser().resolve(strict=False)
        if not target_dir.is_dir():
            continue
        for child in target_dir.iterdir():
            if _is_real_dir(child):
                slugs.add(child.name)
    return slugs


def _is_owned_real_dir(path: Path, owned_slugs: set[str]) -> bool:
    return path.name in owned_slugs and _is_real_dir(path)


def _append_once(paths: list[Path], path: Path) -> None:
    if path not in paths:
        paths.append(path)


def check_health(hub_root: str | Path) -> Diagnostic:
    """Inspect agent skill directories without mutating them."""
    root = Path(hub_root).expanduser().resolve(strict=False)
    idx = indexer.build_index(root)
    expected_targets = {entry.path.resolve(strict=False) for entry in idx.entries}
    owned_slugs = _registered_owned_slugs()
    broken: list[Path] = []
    non_symlink: list[Path] = []
    owned: list[Path] = []

    for entry in idx.entries:
        target = entry.path.resolve(strict=False)
        for agent in fs.AGENTS:
            link = fs.agent_target_dir(agent) / entry.slug
            if link.is_symlink():
                if not _same_path(link, target) or not target.exists():
                    _append_once(broken, link)
            elif _is_owned_real_dir(link, owned_slugs):
                _append_once(owned, link)
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
            elif _is_owned_real_dir(child, owned_slugs):
                _append_once(owned, child)
            elif _looks_like_skill(child):
                _append_once(non_symlink, child)

    return Diagnostic(broken=broken, non_symlink=non_symlink, owned=owned)
