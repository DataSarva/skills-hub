"""Guard test: NO hardcoded path string outside `skills_hub/fs.py`.

`hub-fs` is the single path authority. Any other module that needs a path
must import from `skills_hub.fs`. This test greps the repo and fails if a
forbidden literal shows up anywhere else.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

# Path-shaped string literals that may ONLY appear in skills_hub/fs.py
FORBIDDEN_PATTERNS = [
    re.compile(r"\.skills-hub"),
    re.compile(r"\.claude/skills"),
    re.compile(r"\.codex/skills"),
    re.compile(r"\.gemini/skills"),
    re.compile(r"\.pi/agent/skills"),
    re.compile(r"\.feynman/agent/skills"),
    re.compile(r"\.agents/skills"),
]

# Files that are allowed to contain these literals.
ALLOWED_FILES = {
    REPO_ROOT / "skills_hub" / "fs.py",
    REPO_ROOT / "README.md",
    REPO_ROOT / "tests" / "test_fs.py",
    REPO_ROOT / "tests" / "test_cli_init.py",
    REPO_ROOT / "tests" / "test_path_authority.py",
}

# Directories to skip entirely (vendor / VCS / caches).
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".claude",
}


def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    # Guard scans production code under skills_hub/ plus the bin shim and
    # pyproject. Tests are allowed to use literal paths in fixtures/assertions.
    scan_roots = [
        REPO_ROOT / "skills_hub",
        REPO_ROOT / "bin",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix in {".py", ".toml", ".sh", ".json"} or path.name in {
                "skills-hub",
            }:
                files.append(path)
    pyproject = REPO_ROOT / "pyproject.toml"
    if pyproject.exists():
        files.append(pyproject)
    return files


def test_no_hardcoded_hub_paths_outside_fs_module() -> None:
    offenders: list[tuple[Path, int, str]] = []
    for path in _iter_source_files():
        if path in ALLOWED_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    offenders.append((path.relative_to(REPO_ROOT), lineno, line.strip()))
                    break
    assert not offenders, (
        "Hardcoded hub paths found outside skills_hub/fs.py:\n"
        + "\n".join(f"  {p}:{ln}: {txt}" for p, ln, txt in offenders)
    )
