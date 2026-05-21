"""Unit tests for `skills_hub.migrator`.

The migrator is a PURE function over a typed snapshot:

    plan_migration(snapshot, resolve=None) -> Plan

Snapshot is produced by `skills_hub.scanner` from the real filesystem. The
migrator itself never calls `os.walk`, `Path.exists`, `os.symlink`, etc.
These tests build snapshots in memory and assert the resulting plan.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import migrator as hub_migrator
from skills_hub import fs as hub_fs


# ---------------------------------------------------------------------------
# Snapshot builder helpers
# ---------------------------------------------------------------------------


def _entry(slug: str, agent: str, content_hash: str, source: str) -> hub_migrator.AgentSkill:
    """Build an AgentSkill snapshot row for testing."""
    return hub_migrator.AgentSkill(
        slug=slug,
        agent=agent,
        source_dir=Path(source),
        content_hash=content_hash,
    )


# ---------------------------------------------------------------------------
# Classification: identical / divergent / unique
# ---------------------------------------------------------------------------


def test_identical_skill_across_agents_yields_single_move_and_symlinks(
    tmp_hub_root: Path,
) -> None:
    """Same content_hash across multiple agents => one Move, symlinks for each agent."""
    snapshot = [
        _entry("caveman", "claude", "h1", "/home/u/.claude/skills/caveman"),
        _entry("caveman", "codex", "h1", "/home/u/.codex/skills/caveman"),
        _entry("caveman", "gemini", "h1", "/home/u/.gemini/skills/caveman"),
    ]

    plan = hub_migrator.plan_migration(snapshot)

    assert len(plan.moves) == 1
    move = plan.moves[0]
    assert move.slug == "caveman"
    assert move.tier == "general"
    assert move.dest == hub_fs.skill_dir("general", "caveman")
    # All three agents get a symlink back.
    assert set(move.symlink_agents) == {"claude", "codex", "gemini"}
    # The source picked to move (the "winner") must be one of the inputs.
    assert move.source_dir in {Path(e.source_dir) for e in snapshot}
    assert plan.conflicts == []


def test_unique_skill_present_in_one_agent_is_moved_and_symlinked(
    tmp_hub_root: Path,
) -> None:
    snapshot = [
        _entry("solo", "claude", "h1", "/home/u/.claude/skills/solo"),
    ]

    plan = hub_migrator.plan_migration(snapshot)

    assert len(plan.moves) == 1
    move = plan.moves[0]
    assert move.slug == "solo"
    assert move.tier == "general"
    assert move.symlink_agents == ("claude",)
    assert plan.conflicts == []


def test_divergent_skill_yields_conflict_not_move(tmp_hub_root: Path) -> None:
    """Different content_hash across agents => Conflict, no Move (unless resolved)."""
    snapshot = [
        _entry("oracle", "claude", "hA", "/home/u/.claude/skills/oracle"),
        _entry("oracle", "codex", "hB", "/home/u/.codex/skills/oracle"),
    ]

    plan = hub_migrator.plan_migration(snapshot)

    assert plan.moves == []
    assert len(plan.conflicts) == 1
    conflict = plan.conflicts[0]
    assert conflict.slug == "oracle"
    assert set(conflict.variants) == {"claude", "codex"}
    # The conflict carries the variant source dirs (for diffing later).
    assert conflict.variants["claude"] == Path("/home/u/.claude/skills/oracle")
    assert conflict.variants["codex"] == Path("/home/u/.codex/skills/oracle")


def test_mixed_snapshot_classifies_each_slug_independently(tmp_hub_root: Path) -> None:
    snapshot = [
        # identical across two agents
        _entry("caveman", "claude", "h1", "/home/u/.claude/skills/caveman"),
        _entry("caveman", "codex", "h1", "/home/u/.codex/skills/caveman"),
        # unique to gemini
        _entry("solo", "gemini", "h2", "/home/u/.gemini/skills/solo"),
        # divergent
        _entry("oracle", "claude", "hA", "/home/u/.claude/skills/oracle"),
        _entry("oracle", "codex", "hB", "/home/u/.codex/skills/oracle"),
    ]

    plan = hub_migrator.plan_migration(snapshot)

    moved = {m.slug for m in plan.moves}
    assert moved == {"caveman", "solo"}
    conflicted = {c.slug for c in plan.conflicts}
    assert conflicted == {"oracle"}


# ---------------------------------------------------------------------------
# --resolve <slug>=<agent>: HITL arbitration of divergent variants
# ---------------------------------------------------------------------------


def test_resolve_promotes_chosen_variant_to_move(tmp_hub_root: Path) -> None:
    snapshot = [
        _entry("oracle", "claude", "hA", "/home/u/.claude/skills/oracle"),
        _entry("oracle", "codex", "hB", "/home/u/.codex/skills/oracle"),
    ]

    plan = hub_migrator.plan_migration(snapshot, resolve={"oracle": "codex"})

    assert len(plan.moves) == 1
    move = plan.moves[0]
    assert move.slug == "oracle"
    assert move.source_dir == Path("/home/u/.codex/skills/oracle")
    # ALL original agents get re-symlinked at the chosen winner.
    assert set(move.symlink_agents) == {"claude", "codex"}
    # Conflict no longer present (it was resolved).
    assert plan.conflicts == []
    # Losing variants are attic'd (never deleted).
    assert len(move.attic_sources) == 1
    attic = move.attic_sources[0]
    assert attic.agent == "claude"
    assert attic.source_dir == Path("/home/u/.claude/skills/oracle")


def test_resolve_rejects_unknown_winner_agent(tmp_hub_root: Path) -> None:
    """If the resolver names an agent that didn't actually have the slug, raise."""
    snapshot = [
        _entry("oracle", "claude", "hA", "/home/u/.claude/skills/oracle"),
        _entry("oracle", "codex", "hB", "/home/u/.codex/skills/oracle"),
    ]
    with pytest.raises(ValueError):
        hub_migrator.plan_migration(snapshot, resolve={"oracle": "gemini"})


def test_resolve_for_non_divergent_slug_is_ignored_silently(tmp_hub_root: Path) -> None:
    """Resolving a slug that isn't conflicted should not blow up."""
    snapshot = [
        _entry("caveman", "claude", "h1", "/home/u/.claude/skills/caveman"),
    ]
    # No error, plan still has the single move
    plan = hub_migrator.plan_migration(snapshot, resolve={"caveman": "claude"})
    assert len(plan.moves) == 1
    assert plan.conflicts == []


# ---------------------------------------------------------------------------
# Purity: migrator must NOT touch the filesystem
# ---------------------------------------------------------------------------


def test_migrator_does_not_call_filesystem(monkeypatch: pytest.MonkeyPatch) -> None:
    """plan_migration is a pure function of its input snapshot."""
    import os
    import shutil

    forbidden_attrs = [
        (os, "walk"),
        (os, "symlink"),
        (os, "rename"),
        (os, "replace"),
        (os, "remove"),
        (os, "unlink"),
        (os, "mkdir"),
        (os, "makedirs"),
        (shutil, "move"),
        (shutil, "copytree"),
        (shutil, "rmtree"),
    ]

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("migrator must not touch the filesystem")

    for module, attr in forbidden_attrs:
        if hasattr(module, attr):
            monkeypatch.setattr(module, attr, _boom)

    snapshot = [
        hub_migrator.AgentSkill(
            slug="caveman",
            agent="claude",
            source_dir=Path("/nope/.claude/skills/caveman"),
            content_hash="h1",
        ),
        hub_migrator.AgentSkill(
            slug="caveman",
            agent="codex",
            source_dir=Path("/nope/.codex/skills/caveman"),
            content_hash="h1",
        ),
    ]
    plan = hub_migrator.plan_migration(snapshot)
    assert len(plan.moves) == 1


# ---------------------------------------------------------------------------
# Determinism: same input -> same plan (no time-based / random sources)
# ---------------------------------------------------------------------------


def test_plan_is_deterministic_for_a_given_snapshot(tmp_hub_root: Path) -> None:
    snapshot = [
        _entry("caveman", "claude", "h1", "/home/u/.claude/skills/caveman"),
        _entry("caveman", "codex", "h1", "/home/u/.codex/skills/caveman"),
        _entry("solo", "gemini", "h2", "/home/u/.gemini/skills/solo"),
    ]
    p1 = hub_migrator.plan_migration(snapshot)
    p2 = hub_migrator.plan_migration(list(snapshot))

    s1 = sorted((m.slug, str(m.source_dir), tuple(sorted(m.symlink_agents))) for m in p1.moves)
    s2 = sorted((m.slug, str(m.source_dir), tuple(sorted(m.symlink_agents))) for m in p2.moves)
    assert s1 == s2


# ---------------------------------------------------------------------------
# Diff rendering (for the dry-run output) — pure function on a Conflict
# ---------------------------------------------------------------------------


def test_render_conflict_diff_returns_unified_diff_text(tmp_path: Path) -> None:
    """`render_conflict_diff(conflict)` returns text containing both agent names."""
    # Build a real on-disk pair so the diff has something to compare.
    a = tmp_path / "a" / "oracle"
    a.mkdir(parents=True)
    (a / "SKILL.md").write_text("line one\nline two-A\n")
    b = tmp_path / "b" / "oracle"
    b.mkdir(parents=True)
    (b / "SKILL.md").write_text("line one\nline two-B\n")

    conflict = hub_migrator.Conflict(
        slug="oracle",
        variants={"claude": a, "codex": b},
    )
    out = hub_migrator.render_conflict_diff(conflict)
    assert "claude" in out
    assert "codex" in out
    assert "line two-A" in out or "line two-B" in out
