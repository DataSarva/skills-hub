"""Command-line interface for Skills Hub."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Sequence

from . import fs, linker, migrator, scanner, use_cases

_INDEX_NAME = "_index.json"
_ATTIC_NAME = ".attic"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skills-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize the skills hub")
    mode = init_parser.add_mutually_exclusive_group()
    mode.add_argument("--link", metavar="REPO", help="link the hub root to a repo")
    mode.add_argument("--copy", action="store_true", help="create plain directories")

    migrate_parser = subparsers.add_parser("migrate", help="migrate agent skills into the hub")
    migrate_mode = migrate_parser.add_mutually_exclusive_group()
    migrate_mode.add_argument("--dry-run", action="store_true", help="print the plan only")
    migrate_mode.add_argument("--apply", action="store_true", help="perform the migration")
    migrate_parser.add_argument(
        "--resolve",
        action="append",
        default=[],
        metavar="SLUG=AGENT",
        help="resolve a divergent slug by picking an agent variant",
    )

    use_case_parser = subparsers.add_parser(
        "use-case", help="manage registered use-case skill roots"
    )
    use_case_subparsers = use_case_parser.add_subparsers(
        dest="use_case_command", required=True
    )

    register_parser = use_case_subparsers.add_parser(
        "register", help="register a use-case skill root"
    )
    register_parser.add_argument("name", help="use-case name")
    register_parser.add_argument(
        "--root", required=True, metavar="PATH", help="use-case skills root"
    )

    unregister_parser = use_case_subparsers.add_parser(
        "unregister", help="unregister a use-case skill root"
    )
    unregister_parser.add_argument("name", help="use-case name")

    use_case_subparsers.add_parser("list", help="list registered use cases")
    use_case_subparsers.add_parser("discover", help="discover default use cases")

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


def _parse_resolutions(values: Sequence[str]) -> dict[str, str]:
    resolutions: dict[str, str] = {}
    for value in values:
        slug, sep, agent = value.partition("=")
        if not sep or not slug or not agent:
            raise ValueError(f"malformed resolution: {value!r}")
        resolutions[slug] = agent
    return resolutions


def _format_plan(plan: migrator.Plan) -> str:
    identical = [
        move for move in plan.moves if len(move.symlink_agents) > 1 and not move.attic_sources
    ]
    unique = [
        move for move in plan.moves if len(move.symlink_agents) == 1 and not move.attic_sources
    ]
    resolved = [move for move in plan.moves if move.attic_sources]

    lines = [
        "Migration plan",
        f"identical: {len(identical)}",
    ]
    lines.extend(f"  - {move.slug}: {', '.join(move.symlink_agents)}" for move in identical)
    lines.append(f"unique: {len(unique)}")
    lines.extend(f"  - {move.slug}: {', '.join(move.symlink_agents)}" for move in unique)
    lines.append(f"divergent: {len(plan.conflicts)}")
    for conflict in plan.conflicts:
        lines.append(f"  - {conflict.slug}: {', '.join(conflict.variants)}")
        diff = migrator.render_conflict_diff(conflict)
        if diff:
            lines.append(diff.rstrip("\n"))
    if resolved:
        lines.append(f"resolved: {len(resolved)}")
        for move in resolved:
            attic_agents = {source.agent for source in move.attic_sources}
            winners = ", ".join(agent for agent in move.symlink_agents if agent not in attic_agents)
            losers = ", ".join(source.agent for source in move.attic_sources)
            lines.append(f"  - {move.slug}: winner {winners}; attic {losers}")
    return "\n".join(lines) + "\n"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _attic_dest(timestamp: str, slug: str, agent: str) -> Path:
    return fs.hub_root() / _ATTIC_NAME / timestamp / f"{slug}-{agent}"


def _move_if_real_dir(src: Path, dest: Path) -> bool:
    if src.is_symlink() or not src.exists():
        return False
    linker.move_dir(src, dest)
    return True


def _apply_plan(plan: migrator.Plan, snapshot: list[migrator.AgentSkill]) -> None:
    source_by_agent = {(entry.slug, entry.agent): entry.source_dir for entry in snapshot}
    timestamp = _timestamp()

    for move in plan.moves:
        attic_agents = {source.agent for source in move.attic_sources}
        for source in move.attic_sources:
            _move_if_real_dir(source.source_dir, _attic_dest(timestamp, move.slug, source.agent))

        if not move.dest.exists():
            linker.move_dir(move.source_dir, move.dest)

        for agent in move.symlink_agents:
            source = source_by_agent.get(
                (move.slug, agent),
                fs.agent_target_dir(agent) / move.slug,
            )
            if agent in attic_agents or source == move.source_dir:
                continue
            _move_if_real_dir(source, _attic_dest(timestamp, move.slug, agent))

        for agent in move.symlink_agents:
            linker.write_symlink(move.dest, fs.agent_target_dir(agent) / move.slug)


def _run_migrate(args: argparse.Namespace) -> int:
    resolutions = _parse_resolutions(args.resolve)
    snapshot = scanner.scan_agents()
    plan = migrator.plan_migration(snapshot, resolve=resolutions)

    print(_format_plan(plan), end="")
    if args.apply:
        _ensure_layout(fs.hub_root())
        _apply_plan(plan, snapshot)
    return 0


def _use_case_command(args: argparse.Namespace) -> int:
    try:
        if args.use_case_command == "register":
            use_cases.register(args.name, args.root)
            return 0
        if args.use_case_command == "unregister":
            use_cases.unregister(args.name)
            return 0
        if args.use_case_command == "list":
            for name, target in use_cases.list_registered().items():
                print(f"{name}\t{target}")
            return 0
        if args.use_case_command == "discover":
            for name in use_cases.discover():
                print(name)
            return 0
    except (FileNotFoundError, NotADirectoryError, FileExistsError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    raise ValueError(f"unknown use-case command: {args.use_case_command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        if args.link:
            _init_link(args.link)
        else:
            _init_copy()
        return 0

    if args.command == "migrate":
        try:
            return _run_migrate(args)
        except ValueError as exc:
            parser.error(str(exc))

    if args.command == "use-case":
        return _use_case_command(args)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
