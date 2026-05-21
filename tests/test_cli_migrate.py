"""Integration tests for `skills-hub migrate`.

These tests build a synthetic agent-skill scatter under a tmp HOME, run the
CLI, and assert the resulting hub layout + symlinks. The real `~` is never
touched.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs


FIXTURES = Path(__file__).parent / "fixtures" / "migration"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_agent_skill(home: Path, agent: str, slug: str, src: Path) -> Path:
    """Copy a fixture skill dir into the given agent's skills dir under tmp HOME."""
    suffix = hub_fs.AGENTS[agent]  # e.g. ".claude/skills"
    target = home / suffix / slug
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, target)
    return target


def _seed_identical_caveman(home: Path) -> None:
    src = FIXTURES / "identical" / "caveman"
    for agent in ("claude", "codex", "gemini"):
        _seed_agent_skill(home, agent, "caveman", src)


def _seed_divergent_oracle(home: Path) -> None:
    _seed_agent_skill(home, "claude", "oracle", FIXTURES / "divergent" / "oracle.claude")
    _seed_agent_skill(home, "codex", "oracle", FIXTURES / "divergent" / "oracle.codex")


def _seed_unique_release_peekaboo(home: Path) -> None:
    _seed_agent_skill(
        home, "gemini", "release-peekaboo", FIXTURES / "unique" / "release-peekaboo"
    )


# ---------------------------------------------------------------------------
# `skills-hub migrate --dry-run`
# ---------------------------------------------------------------------------


def test_dry_run_classifies_and_prints_counts(
    tmp_hub_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = Path(os.environ["HOME"])
    _seed_identical_caveman(home)
    _seed_divergent_oracle(home)
    _seed_unique_release_peekaboo(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--dry-run"])
    assert rc == 0

    out = capsys.readouterr().out.lower()
    # Should mention counts for identical / divergent / unique
    assert "identical" in out
    assert "divergent" in out
    assert "unique" in out
    # Slug names should appear somewhere in the plan output
    assert "caveman" in out
    assert "oracle" in out
    assert "release-peekaboo" in out
    # Diff context for divergent slug
    assert "claude" in out and "codex" in out


def test_dry_run_does_not_move_anything(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_identical_caveman(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--dry-run"])
    assert rc == 0

    # Originals still in place, not symlinks
    for agent in ("claude", "codex", "gemini"):
        p = home / hub_fs.AGENTS[agent] / "caveman"
        assert p.is_dir()
        assert not p.is_symlink()
    # Hub still empty (no caveman dir)
    assert not (tmp_hub_root / "general" / "caveman").exists()


# ---------------------------------------------------------------------------
# `skills-hub migrate --apply` — identical case
# ---------------------------------------------------------------------------


def test_apply_moves_identical_skill_and_symlinks_all_agents(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_identical_caveman(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--apply"])
    assert rc == 0

    hub_skill = tmp_hub_root / "general" / "caveman"
    assert hub_skill.is_dir()
    assert (hub_skill / "SKILL.md").is_file()

    for agent in ("claude", "codex", "gemini"):
        link = home / hub_fs.AGENTS[agent] / "caveman"
        assert link.is_symlink(), f"{agent} should now be a symlink"
        assert link.resolve() == hub_skill.resolve()


def test_apply_unique_skill_is_moved_and_symlinked(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_unique_release_peekaboo(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--apply"])
    assert rc == 0

    hub_skill = tmp_hub_root / "general" / "release-peekaboo"
    assert hub_skill.is_dir()
    link = home / hub_fs.AGENTS["gemini"] / "release-peekaboo"
    assert link.is_symlink()
    assert link.resolve() == hub_skill.resolve()


# ---------------------------------------------------------------------------
# Divergent skill: skipped without --resolve, attic'd with it
# ---------------------------------------------------------------------------


def test_apply_skips_divergent_skill_without_resolve(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_divergent_oracle(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--apply"])
    assert rc == 0

    # Hub did NOT receive oracle (it was skipped).
    assert not (tmp_hub_root / "general" / "oracle").exists()
    # Originals untouched (still real dirs, not symlinks).
    for agent in ("claude", "codex"):
        p = home / hub_fs.AGENTS[agent] / "oracle"
        assert p.is_dir()
        assert not p.is_symlink()


def test_apply_with_resolve_promotes_winner_and_attics_losers(
    tmp_hub_root: Path,
) -> None:
    home = Path(os.environ["HOME"])
    _seed_divergent_oracle(home)
    hub_cli.main(["init"])

    rc = hub_cli.main(["migrate", "--apply", "--resolve", "oracle=codex"])
    assert rc == 0

    hub_skill = tmp_hub_root / "general" / "oracle"
    assert hub_skill.is_dir()
    # Winner content (codex variant) is what landed in the hub.
    assert "codex variant" in (hub_skill / "SKILL.md").read_text()

    # Both agents symlinked at the winner.
    for agent in ("claude", "codex"):
        link = home / hub_fs.AGENTS[agent] / "oracle"
        assert link.is_symlink()
        assert link.resolve() == hub_skill.resolve()

    # Loser variant stashed under .attic/, not deleted.
    attic_root = tmp_hub_root / ".attic"
    assert attic_root.is_dir()
    attic_entries = list(attic_root.rglob("oracle-claude"))
    assert attic_entries, "loser variant should be stashed under .attic/<ts>/oracle-claude"
    # Attic copy preserves the original claude content
    attic_skill_md = attic_entries[0] / "SKILL.md"
    assert attic_skill_md.is_file()
    assert "claude variant" in attic_skill_md.read_text()


# ---------------------------------------------------------------------------
# Idempotency: re-running --apply is a no-op
# ---------------------------------------------------------------------------


def test_apply_is_idempotent(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_identical_caveman(home)
    _seed_unique_release_peekaboo(home)
    hub_cli.main(["init"])

    assert hub_cli.main(["migrate", "--apply"]) == 0
    # Snapshot link inodes
    link = home / hub_fs.AGENTS["claude"] / "caveman"
    inode_before = os.lstat(link).st_ino

    assert hub_cli.main(["migrate", "--apply"]) == 0
    inode_after = os.lstat(link).st_ino

    assert link.is_symlink()
    assert inode_before == inode_after


# ---------------------------------------------------------------------------
# Safety: migrate never deletes — only moves or symlinks
# ---------------------------------------------------------------------------


def test_apply_never_deletes_divergent_content(tmp_hub_root: Path) -> None:
    home = Path(os.environ["HOME"])
    _seed_divergent_oracle(home)
    hub_cli.main(["init"])

    claude_md = home / hub_fs.AGENTS["claude"] / "oracle" / "SKILL.md"
    codex_md = home / hub_fs.AGENTS["codex"] / "oracle" / "SKILL.md"
    claude_text_before = claude_md.read_text()
    codex_text_before = codex_md.read_text()

    hub_cli.main(["migrate", "--apply"])

    # Both files still readable, content unchanged.
    assert claude_md.read_text() == claude_text_before
    assert codex_md.read_text() == codex_text_before


def test_resolve_attics_loser_then_apply_still_finds_winner_content(
    tmp_hub_root: Path,
) -> None:
    """Even after attic'ing the loser, its content is still on disk somewhere."""
    home = Path(os.environ["HOME"])
    _seed_divergent_oracle(home)
    hub_cli.main(["init"])

    hub_cli.main(["migrate", "--apply", "--resolve", "oracle=codex"])

    # Loser (claude) content must exist somewhere under .attic
    attic_root = tmp_hub_root / ".attic"
    found = list(attic_root.rglob("SKILL.md"))
    assert any("claude variant" in p.read_text() for p in found)
