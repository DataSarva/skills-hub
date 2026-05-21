"""Pure index builder for Skills Hub."""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib
from pathlib import Path
from typing import Any

from . import fs

_SKILL_DOC = "SKILL.md"
_FRONTMATTER_DELIMITER = "---"


@dataclass(frozen=True)
class Entry:
    slug: str
    tier: str
    path: Path
    name: str
    description: str
    tags: list[str]
    version: int
    sha: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "tier": self.tier,
            "path": str(self.path),
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
            "version": self.version,
            "sha": self.sha,
        }


@dataclass(frozen=True)
class Index:
    entries: list[Entry]

    def to_dict(self) -> dict[str, Any]:
        return {"skills": [entry.to_dict() for entry in self.entries]}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in inner.split(",")]
    if value[0] in {"'", '"'} and value[-1:] == value[0]:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
        return parsed if isinstance(parsed, str) else value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def _parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        return {}

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_DELIMITER:
            end = index
            break
    if end is None:
        return {}

    values: dict[str, Any] = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, raw = line.partition(":")
        if not separator:
            continue
        values[key.strip()] = _parse_scalar(raw)
    return values


def _sha_for(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_slug(slug: str, tier: str) -> bool:
    try:
        fs.skill_dir(tier, slug)
    except ValueError:
        return False
    return True


def _string_value(values: dict[str, Any], key: str, default: str) -> str:
    value = values.get(key, default)
    return value if isinstance(value, str) else default


def _int_value(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    return value if isinstance(value, int) else default


def _tags_value(values: dict[str, Any]) -> list[str]:
    value = values.get("tags", [])
    if not isinstance(value, list):
        return []
    return [tag for tag in value if isinstance(tag, str)]


def _entry_for_skill(tier: str, skill_dir: Path) -> Entry | None:
    skill_doc = skill_dir / _SKILL_DOC
    if not skill_doc.is_file():
        return None

    text = skill_doc.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(text)
    slug = skill_dir.name
    return Entry(
        slug=slug,
        tier=tier,
        path=skill_dir,
        name=_string_value(frontmatter, "name", slug),
        description=_string_value(frontmatter, "description", ""),
        tags=_tags_value(frontmatter),
        version=_int_value(frontmatter, "version", 1),
        sha=_sha_for(skill_doc),
    )


def build_index(hub_root: str | Path) -> Index:
    """Walk a hub root and return an in-memory index."""
    root = Path(hub_root).expanduser()
    entries: list[Entry] = []

    for tier in fs.TIERS:
        tier_root = root / tier
        if not tier_root.is_dir():
            continue
        for child in sorted(tier_root.iterdir(), key=lambda path: path.name):
            if child.name.startswith((".", "_")):
                continue
            if not child.is_dir() or not _valid_slug(child.name, tier):
                continue
            entry = _entry_for_skill(tier, child)
            if entry is not None:
                entries.append(entry)

    return Index(entries=sorted(entries, key=lambda entry: (entry.tier, entry.slug)))
