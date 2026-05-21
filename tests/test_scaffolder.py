"""Unit tests for `skills_hub.scaffolder`.

Produces a SKILL.md whose frontmatter round-trips to a dict.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import cli as hub_cli
from skills_hub import fs as hub_fs
from skills_hub import indexer as hub_indexer
from skills_hub import scaffolder as hub_scaffolder


def test_scaffold_creates_skill_md(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    path = hub_scaffolder.scaffold_skill(tmp_hub_root, "new-skill", "general")
    assert path.is_file()
    assert path == tmp_hub_root / "general" / "new-skill" / "SKILL.md"
    assert path.read_text().startswith("---")


def test_scaffolded_frontmatter_roundtrips(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    hub_scaffolder.scaffold_skill(
        tmp_hub_root,
        "round-trip",
        "general",
        description="A round-trip test skill",
    )
    index = hub_indexer.build_index(tmp_hub_root)
    by_slug = {e.slug: e for e in index.entries}
    entry = by_slug["round-trip"]
    assert entry.tier == "general"
    assert entry.name == "round-trip"
    assert entry.description == "A round-trip test skill"
    assert entry.tags == []
    assert entry.version == 1


def test_scaffold_rejects_unknown_tier(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    with pytest.raises(ValueError):
        hub_scaffolder.scaffold_skill(tmp_hub_root, "slug", "not-a-tier")


def test_scaffold_refuses_existing(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    hub_scaffolder.scaffold_skill(tmp_hub_root, "dup", "general")
    with pytest.raises(FileExistsError):
        hub_scaffolder.scaffold_skill(tmp_hub_root, "dup", "general")


def test_scaffold_supports_use_cases_tier(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    path = hub_scaffolder.scaffold_skill(tmp_hub_root, "isv-news", "use-cases")
    assert path.parent == tmp_hub_root / "use-cases" / "isv-news"


def test_cli_new_subcommand(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    rc = hub_cli.main(["new", "my-skill", "--tier", "general"])
    assert rc == 0
    assert (tmp_hub_root / "general" / "my-skill" / "SKILL.md").is_file()


def test_cli_new_rejects_bad_tier(tmp_hub_root: Path) -> None:
    hub_cli.main(["init"])
    with pytest.raises(SystemExit):
        hub_cli.main(["new", "my-skill", "--tier", "bogus"])
