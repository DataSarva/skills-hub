"""Migration planning for scattered agent skills.

The planner is intentionally pure: it classifies an in-memory snapshot into
hub moves and unresolved conflicts without inspecting or mutating disk.
"""

from __future__ import annotations

from dataclasses import dataclass
import difflib
from pathlib import Path

from . import fs as hub_fs

_DEFAULT_TIER = "general"
_SKILL_DOC = "SKILL.md"


@dataclass(frozen=True)
class AgentSkill:
    slug: str
    agent: str
    source_dir: Path
    content_hash: str


@dataclass(frozen=True)
class AtticSource:
    agent: str
    source_dir: Path


@dataclass(frozen=True)
class Move:
    slug: str
    tier: str
    source_dir: Path
    dest: Path
    symlink_agents: tuple[str, ...]
    attic_sources: tuple[AtticSource, ...] = ()


@dataclass(frozen=True)
class Conflict:
    slug: str
    variants: dict[str, Path]


@dataclass(frozen=True)
class Plan:
    moves: list[Move]
    conflicts: list[Conflict]


def _agent_order(agent: str) -> tuple[int, str]:
    try:
        index = tuple(hub_fs.AGENTS).index(agent)
    except ValueError:
        index = len(hub_fs.AGENTS)
    return index, agent


def _sorted_entries(entries: list[AgentSkill]) -> list[AgentSkill]:
    return sorted(entries, key=lambda entry: (_agent_order(entry.agent), str(entry.source_dir)))


def _move_for_entries(
    slug: str,
    entries: list[AgentSkill],
    winner: AgentSkill,
    attic_sources: tuple[AtticSource, ...] = (),
) -> Move:
    ordered = _sorted_entries(entries)
    return Move(
        slug=slug,
        tier=_DEFAULT_TIER,
        source_dir=winner.source_dir,
        dest=hub_fs.skill_dir(_DEFAULT_TIER, slug),
        symlink_agents=tuple(entry.agent for entry in ordered),
        attic_sources=attic_sources,
    )


def plan_migration(snapshot: list[AgentSkill], resolve: dict[str, str] | None = None) -> Plan:
    """Classify a scanned snapshot into moves and unresolved conflicts."""
    resolutions = resolve or {}
    by_slug: dict[str, list[AgentSkill]] = {}
    for entry in snapshot:
        by_slug.setdefault(entry.slug, []).append(entry)

    moves: list[Move] = []
    conflicts: list[Conflict] = []

    for slug in sorted(by_slug):
        entries = _sorted_entries(by_slug[slug])
        hashes = {entry.content_hash for entry in entries}
        if len(hashes) == 1:
            moves.append(_move_for_entries(slug, entries, entries[0]))
            continue

        variants = {entry.agent: entry.source_dir for entry in entries}
        winner_agent = resolutions.get(slug)
        if winner_agent is None:
            conflicts.append(Conflict(slug=slug, variants=variants))
            continue
        if winner_agent not in variants:
            raise ValueError(f"resolution for {slug!r} names unknown agent: {winner_agent!r}")

        winner = next(entry for entry in entries if entry.agent == winner_agent)
        attic_sources = tuple(
            AtticSource(agent=entry.agent, source_dir=entry.source_dir)
            for entry in entries
            if entry.agent != winner_agent
        )
        moves.append(_move_for_entries(slug, entries, winner, attic_sources))

    return Plan(moves=moves, conflicts=conflicts)


def _read_skill_doc(source_dir: Path) -> list[str]:
    path = source_dir / _SKILL_DOC
    try:
        return path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return []


def render_conflict_diff(conflict: Conflict) -> str:
    """Render unified diffs between each variant's skill document."""
    agents = sorted(conflict.variants, key=_agent_order)
    if len(agents) < 2:
        return ""

    chunks: list[str] = []
    previous = agents[0]
    previous_lines = _read_skill_doc(conflict.variants[previous])
    for agent in agents[1:]:
        current_lines = _read_skill_doc(conflict.variants[agent])
        diff = difflib.unified_diff(
            previous_lines,
            current_lines,
            fromfile=f"{previous}/{_SKILL_DOC}",
            tofile=f"{agent}/{_SKILL_DOC}",
        )
        chunks.extend(diff)
        if chunks and not chunks[-1].endswith("\n"):
            chunks[-1] = f"{chunks[-1]}\n"
        previous = agent
        previous_lines = current_lines

    return "".join(chunks)
