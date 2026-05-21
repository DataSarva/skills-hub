"""Shared pytest fixtures for skills-hub tests.

All tests MUST run against a tmp HOME and never touch the real `~`.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HOME to a tmp dir; clear HUB_ROOT so default resolution kicks in."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("HUB_ROOT", raising=False)
    return home


@pytest.fixture
def tmp_hub_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set HUB_ROOT to a tmp dir; also redirect HOME for agent target tests."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    root = tmp_path / "hub"
    monkeypatch.setenv("HUB_ROOT", str(root))
    return root
