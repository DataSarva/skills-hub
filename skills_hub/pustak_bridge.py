"""Best-effort mirror of the Skills Hub index into Pustak wiki."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

from skills_hub import fs

_INDEX_NAME = "_index.json"
_NAMESPACE = "general/tooling"
_SLUG = "skills-hub-index"
_PAGE_NAME = f"{_SLUG}.md"
_SOURCE_URL = "https://github.com/datasarva/skills-hub"
_AGENT = "skills-hub-bridge"


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _load_index(hub_root: str | Path) -> dict[str, Any]:
    index_path = Path(hub_root).expanduser() / _INDEX_NAME
    return json.loads(index_path.read_text(encoding="utf-8"))


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _frontmatter() -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return [
        "---",
        f"id: {_SLUG}",
        f"slug: {_SLUG}",
        "aliases: []",
        f"namespace: {_NAMESPACE}",
        "sources: []",
        "tags: [skills-hub, index]",
        "version: 1",
        f"last_updated: {now}",
        f"authored_by: [{_AGENT}]",
        "deprecated: false",
        "---",
    ]


def _skill_rows(data: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        skills = []

    entries = [entry for entry in skills if isinstance(entry, dict)]
    entries.sort(key=lambda entry: str(entry.get("slug", "")))
    for entry in entries:
        slug = _escape_table_cell(str(entry.get("slug", "")))
        tier = _escape_table_cell(str(entry.get("tier", "")))
        description = _escape_table_cell(str(entry.get("description", "")))
        raw_tags = entry.get("tags", [])
        tags = (
            ", ".join(tag for tag in raw_tags if isinstance(tag, str))
            if isinstance(raw_tags, list)
            else ""
        )
        rows.append(f"| {slug} | {tier} | {description} | {_escape_table_cell(tags)} |")
    return rows


def render_wiki_page(hub_root: str | Path) -> str:
    """Render `_index.json` as the canonical Pustak wiki page."""
    data = _load_index(hub_root)
    rows = _skill_rows(data)
    lines = [
        *_frontmatter(),
        "",
        "# Skills Hub Index",
        "",
        "Auto-generated mirror of `_index.json` from the skills-hub repo. Do not edit",
        "this page by hand \u2014 edits are clobbered on the next `skills-hub install` or",
        "`skills-hub sync`.",
        "",
        "| slug | tier | description | tags |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
        f"Total skills: {len(rows)}",
        "",
        f"Source: {_SOURCE_URL}",
    ]
    return "\n".join(lines) + "\n"


def _wiki_root() -> Path:
    return Path.home() / ".pustak" / "wiki"


def _page_path() -> Path:
    return _wiki_root() / _NAMESPACE / _PAGE_NAME


def _comparable(text: str) -> str:
    patterns = (
        r"^id: .+$",
        r"^sources: .+$",
        r"^version: .+$",
        r"^last_updated: .+$",
    )
    comparable = text
    for pattern in patterns:
        comparable = re.sub(pattern, "__IGNORED__", comparable, flags=re.MULTILINE)
    return comparable.strip()


def _matches_existing(rendered: str, page_path: Path) -> bool:
    if not page_path.is_file():
        return False
    existing = page_path.read_text(encoding="utf-8")
    return _comparable(existing) == _comparable(rendered)


def _write_with_pustak(
    rendered: str, page_path: Path, cmd: list[str], cwd: str | None
) -> int:
    with TemporaryDirectory(prefix="skills-hub-pustak-") as temp_dir:
        content_file = Path(temp_dir) / _PAGE_NAME
        content_file.write_text(rendered, encoding="utf-8")
        result = subprocess.run(
            [
                *cmd,
                "wiki",
                "write",
                str(page_path),
                "--content-file",
                str(content_file),
                "--source-id",
                _SLUG,
                "--strict-new",
                "--agent",
                _AGENT,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        _warn(f"pustak wiki write failed{detail}")
    return 0


def mirror_index(hub_root: str | Path) -> int:
    """Mirror the generated hub index into Pustak when available.

    This bridge is deliberately best-effort: a missing Pustak install, missing
    wiki checkout, malformed index, or write failure should not block
    `skills-hub install` or `skills-hub sync`.
    """
    wiki_root = _wiki_root()
    if not wiki_root.is_dir():
        _warn(f"pustak wiki missing: {wiki_root}")
        return 0

    try:
        rendered = render_wiki_page(hub_root)
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"could not render pustak skills index: {exc}")
        return 0

    page_path = _page_path()
    try:
        if _matches_existing(rendered, page_path):
            return 0
    except OSError as exc:
        _warn(f"could not read existing pustak page: {exc}")

    repo = fs.pustak_repo_dir()
    if repo.is_dir() and (repo / "pyproject.toml").is_file():
        cmd = ["uv", "run", "pustak"]
        cwd = str(repo)
    elif shutil.which("pustak"):
        cmd = ["pustak"]
        cwd = None
    else:
        _warn("pustak CLI not found; skipping wiki mirror")
        return 0

    try:
        return _write_with_pustak(rendered, page_path, cmd, cwd)
    except FileNotFoundError:
        _warn("pustak CLI not found; skipping wiki mirror")
    except OSError as exc:
        _warn(f"could not run pustak wiki write: {exc}")
    return 0
