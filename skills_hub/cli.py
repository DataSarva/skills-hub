"""Command-line interface for Skills Hub."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import fs

_INDEX_NAME = "_index.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skills-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize the skills hub")
    mode = init_parser.add_mutually_exclusive_group()
    mode.add_argument("--link", metavar="REPO", help="link the hub root to a repo")
    mode.add_argument("--copy", action="store_true", help="create plain directories")

    return parser


def _ensure_index(root: Path) -> None:
    index_path = root / _INDEX_NAME
    if index_path.exists():
        try:
            json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
        else:
            return
    index_path.write_text("{}\n", encoding="utf-8")


def _ensure_layout(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for tier in fs.TIERS:
        fs.tier_dir(tier).mkdir(parents=True, exist_ok=True)
    _ensure_index(root)


def _init_link(repo: str) -> None:
    root = fs.hub_root()
    target = Path(repo).expanduser().resolve()

    root.parent.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        if root.resolve() != target:
            raise FileExistsError(f"hub root already links elsewhere: {root}")
    elif root.exists():
        raise FileExistsError(f"hub root already exists: {root}")
    else:
        root.symlink_to(target, target_is_directory=True)

    _ensure_layout(root)


def _init_copy() -> None:
    _ensure_layout(fs.hub_root())


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        if args.link:
            _init_link(args.link)
        else:
            _init_copy()
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

