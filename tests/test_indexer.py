"""Unit tests for `skills_hub.indexer`.

Indexer is PURE: it walks a hub directory and returns an in-memory Index.
No symlink or rename syscalls are allowed in this module.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import indexer as hub_indexer


SKILL_TEMPLATE = """---
name: {name}
description: {description}
tier: {tier}
tags: [{tags}]
version: {version}
---

# {name}

{description}
"""


def _write_skill(
    hub: Path,
    tier: str,
    slug: str,
    *,
    name: str | None = None,
    description: str = "",
    tags: list[str] | None = None,
    version: int = 1,
) -> Path:
    tier_dir = hub / tier
    tier_dir.mkdir(parents=True, exist_ok=True)
    skill_dir = tier_dir / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    md.write_text(
        SKILL_TEMPLATE.format(
            name=name or slug,
            description=description,
            tier=tier,
            tags=", ".join(tags or []),
            version=version,
        ),
        encoding="utf-8",
    )
    return skill_dir


def _build_fixture_hub(hub: Path) -> None:
    hub.mkdir(parents=True, exist_ok=True)
    for tier in ("general", "tools", "use-cases"):
        (hub / tier).mkdir(parents=True, exist_ok=True)
    _write_skill(
        hub,
        "general",
        "caveman",
        description="Ultra-compressed communication",
        tags=["style", "communication"],
        version=1,
    )
    _write_skill(
        hub,
        "general",
        "oracle",
        description="Predictive coding oracle",
        tags=["coding"],
        version=2,
    )
    _write_skill(
        hub,
        "tools",
        "release-peekaboo",
        description="Release-cut helper",
        tags=["release"],
        version=1,
    )


# ---------------------------------------------------------------------------
# build_index returns an Index with Entry items
# ---------------------------------------------------------------------------


def test_build_index_returns_entries_for_each_skill(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)

    index = hub_indexer.build_index(hub)
    slugs = {entry.slug for entry in index.entries}
    assert slugs == {"caveman", "oracle", "release-peekaboo"}


def test_entry_fields_capture_frontmatter(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)

    index = hub_indexer.build_index(hub)
    by_slug = {entry.slug: entry for entry in index.entries}

    caveman = by_slug["caveman"]
    assert caveman.tier == "general"
    assert caveman.name == "caveman"
    assert caveman.description == "Ultra-compressed communication"
    assert "style" in caveman.tags
    assert "communication" in caveman.tags
    assert caveman.version == 1
    assert caveman.path == hub / "general" / "caveman"
    assert isinstance(caveman.sha, str) and len(caveman.sha) >= 16


def test_entries_sorted_by_tier_then_slug(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)
    index = hub_indexer.build_index(hub)
    keys = [(e.tier, e.slug) for e in index.entries]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# Tiers walked
# ---------------------------------------------------------------------------


def test_build_index_walks_all_three_tiers(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)
    _write_skill(hub, "use-cases", "investsarva-news", description="Wire news", tags=[])
    index = hub_indexer.build_index(hub)
    tiers = {e.tier for e in index.entries}
    assert tiers == {"general", "tools", "use-cases"}


def test_build_index_skips_non_skill_dirs(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)
    # A subdir with no SKILL.md must be ignored.
    (hub / "general" / "no-skill-doc").mkdir()
    index = hub_indexer.build_index(hub)
    slugs = {e.slug for e in index.entries}
    assert "no-skill-doc" not in slugs


def test_build_index_skips_hidden_and_underscore_dirs(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    _build_fixture_hub(hub)
    # `.attic` and `_index.json` should not show up as skills.
    (hub / "general" / ".attic").mkdir()
    (hub / "general" / "_meta").mkdir()
    index = hub_indexer.build_index(hub)
    slugs = {e.slug for e in index.entries}
    assert ".attic" not in slugs
    assert "_meta" not in slugs


def test_build_index_handles_missing_tier_dirs(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    hub.mkdir()
    # No tier dirs at all — empty index, no crash.
    index = hub_indexer.build_index(hub)
    assert index.entries == []


# ---------------------------------------------------------------------------
# Index.to_dict / round-trip
# ---------------------------------------------------------------------------


def test_index_to_dict_is_json_serializable(tmp_path: Path) -> None:
    import json

    hub = tmp_path / "hub"
    _build_fixture_hub(hub)
    index = hub_indexer.build_index(hub)
    payload = index.to_dict()
    json.dumps(payload)  # must not raise
    assert "skills" in payload
    assert isinstance(payload["skills"], list)
    assert len(payload["skills"]) == 3
    first = payload["skills"][0]
    assert {"slug", "tier", "name", "description", "tags", "version", "sha"} <= set(first)


# ---------------------------------------------------------------------------
# Purity guard: indexer must NOT call symlink/rename APIs
# ---------------------------------------------------------------------------


def test_indexer_module_has_no_symlink_or_rename_calls() -> None:
    import inspect

    src = inspect.getsource(hub_indexer)
    for forbidden in ("os.symlink", "os.rename", "os.replace", "shutil.move"):
        assert forbidden not in src, f"indexer must be pure, found {forbidden!r}"
