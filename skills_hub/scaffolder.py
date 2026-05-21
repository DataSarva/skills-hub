"""Skill scaffolding helpers."""

from __future__ import annotations

import json
from pathlib import Path

from . import fs

_SKILL_DOC = "SKILL.md"


def _format_string(value: str) -> str:
    if value == "":
        return '""'
    if any(char in value for char in (":", "#", "[", "]", "{", "}", '"', "'")):
        return json.dumps(value)
    return value


def _format_tags(tags: list[str]) -> str:
    if not tags:
        return "[]"
    return "[" + ", ".join(_format_string(tag) for tag in tags) + "]"


def scaffold_skill(
    hub_root: str | Path,
    slug: str,
    tier: str,
    *,
    description: str = "",
    name: str | None = None,
    tags: list[str] | None = None,
    version: int = 1,
) -> Path:
    """Create a new skill document and return its path."""
    fs.skill_dir(tier, slug)
    root = Path(hub_root).expanduser()
    skill_dir = root / tier / slug
    if skill_dir.exists() or skill_dir.is_symlink():
        raise FileExistsError(f"skill already exists: {skill_dir}")

    skill_name = name or slug
    skill_tags = list(tags or [])
    skill_dir.mkdir(parents=True)
    skill_doc = skill_dir / _SKILL_DOC
    skill_doc.write_text(
        "\n".join(
            [
                "---",
                f"name: {_format_string(skill_name)}",
                f"description: {_format_string(description)}",
                f"tier: {tier}",
                f"tags: {_format_tags(skill_tags)}",
                f"version: {version}",
                "---",
                "",
                f"# {skill_name}",
                "",
                description,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return skill_doc
