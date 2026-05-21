"""Unit tests for the use-case symlink module (`skills_hub.use_cases`).

This module is responsible for managing symlinks under `<hub>/use-cases/<name>`
that point at a use-case's own skill directory (e.g. ~/.investsarva/skills).
It must NEVER write to the underlying use-case dir — it only creates,
removes, and inspects symlinks within the hub.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skills_hub import fs as hub_fs
from skills_hub import use_cases


# ---------------------------------------------------------------------------
# DEFAULT_USE_CASES constant
# ---------------------------------------------------------------------------


def test_default_use_cases_covers_canonical_set() -> None:
    """The canonical default list on this Mac Mini."""
    assert set(use_cases.DEFAULT_USE_CASES) == {
        "investsarva",
        "pustak",
        "chakra",
        "memsarva",
        "pi",
        "feynman",
    }


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


def test_register_creates_symlink_to_target(tmp_hub_root: Path) -> None:
    """`register` creates `<hub>/use-cases/<name>` as a symlink to the target."""
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)
    target = tmp_hub_root.parent / "fake-usecase-skills"
    target.mkdir()

    use_cases.register("investsarva", target)

    link = hub_fs.tier_dir("use-cases") / "investsarva"
    assert link.is_symlink()
    assert link.resolve() == target.resolve()


def test_register_creates_parent_use_cases_tier_dir(tmp_hub_root: Path) -> None:
    """register() must succeed even if `<hub>/use-cases/` does not exist yet."""
    target = tmp_hub_root.parent / "skills-root"
    target.mkdir()

    use_cases.register("pustak", target)

    assert hub_fs.tier_dir("use-cases").is_dir()
    assert (hub_fs.tier_dir("use-cases") / "pustak").is_symlink()


def test_register_refuses_missing_target(tmp_hub_root: Path) -> None:
    """If target does not exist, register raises (does NOT create the dir)."""
    missing = tmp_hub_root.parent / "does-not-exist"
    with pytest.raises((FileNotFoundError, ValueError)):
        use_cases.register("ghost", missing)
    assert not missing.exists()
    assert not (hub_fs.tier_dir("use-cases") / "ghost").exists()


def test_register_refuses_non_directory_target(tmp_hub_root: Path) -> None:
    """Target must be a directory."""
    target_file = tmp_hub_root.parent / "not-a-dir.txt"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("hi")

    with pytest.raises((NotADirectoryError, ValueError)):
        use_cases.register("bad", target_file)


def test_register_refuses_malformed_name(tmp_hub_root: Path) -> None:
    """Use-case name must follow the same slug rules as fs._validate_slug."""
    target = tmp_hub_root.parent / "ok"
    target.mkdir()
    for bad in ["", "with/slash", "with\\back", ".", "..", "with space"]:
        with pytest.raises(ValueError):
            use_cases.register(bad, target)


def test_register_is_idempotent_for_same_target(tmp_hub_root: Path) -> None:
    """Re-registering the same name to the same target must not fail."""
    target = tmp_hub_root.parent / "twice"
    target.mkdir()

    use_cases.register("memsarva", target)
    use_cases.register("memsarva", target)  # second call

    link = hub_fs.tier_dir("use-cases") / "memsarva"
    assert link.is_symlink()
    assert link.resolve() == target.resolve()


def test_register_refuses_to_clobber_non_symlink(tmp_hub_root: Path) -> None:
    """If `<hub>/use-cases/<name>` exists as a real dir, register must refuse."""
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)
    occupied = hub_fs.tier_dir("use-cases") / "chakra"
    occupied.mkdir()

    target = tmp_hub_root.parent / "chakra-skills"
    target.mkdir()

    with pytest.raises((FileExistsError, ValueError)):
        use_cases.register("chakra", target)

    # The pre-existing real dir must remain untouched.
    assert occupied.is_dir() and not occupied.is_symlink()


def test_register_replaces_existing_symlink_pointing_elsewhere(
    tmp_hub_root: Path,
) -> None:
    """If a symlink already exists pointing elsewhere, register updates it atomically."""
    old_target = tmp_hub_root.parent / "old-target"
    old_target.mkdir()
    new_target = tmp_hub_root.parent / "new-target"
    new_target.mkdir()

    use_cases.register("pi", old_target)
    use_cases.register("pi", new_target)

    link = hub_fs.tier_dir("use-cases") / "pi"
    assert link.is_symlink()
    assert link.resolve() == new_target.resolve()


def test_register_never_writes_to_target_dir(tmp_hub_root: Path) -> None:
    """register() must only manipulate the link; never write into the target."""
    target = tmp_hub_root.parent / "untouched"
    target.mkdir()
    before = sorted(p.name for p in target.iterdir())

    use_cases.register("feynman", target)

    after = sorted(p.name for p in target.iterdir())
    assert before == after


# ---------------------------------------------------------------------------
# unregister()
# ---------------------------------------------------------------------------


def test_unregister_removes_symlink(tmp_hub_root: Path) -> None:
    target = tmp_hub_root.parent / "to-be-removed"
    target.mkdir()
    use_cases.register("memsarva", target)

    use_cases.unregister("memsarva")

    link = hub_fs.tier_dir("use-cases") / "memsarva"
    assert not link.exists()
    assert not link.is_symlink()


def test_unregister_does_not_touch_target(tmp_hub_root: Path) -> None:
    target = tmp_hub_root.parent / "preserved"
    target.mkdir()
    (target / "skill.md").write_text("body")
    use_cases.register("pustak", target)

    use_cases.unregister("pustak")

    assert target.is_dir()
    assert (target / "skill.md").read_text() == "body"


def test_unregister_missing_is_noop(tmp_hub_root: Path) -> None:
    """Unregistering something that isn't registered must be a quiet no-op."""
    # Should not raise.
    use_cases.unregister("nothing-here")


def test_unregister_refuses_to_remove_real_directory(tmp_hub_root: Path) -> None:
    """If the path exists but is a real directory (not a symlink), refuse."""
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)
    real_dir = hub_fs.tier_dir("use-cases") / "real"
    real_dir.mkdir()

    with pytest.raises((IsADirectoryError, ValueError, FileExistsError)):
        use_cases.unregister("real")

    assert real_dir.is_dir() and not real_dir.is_symlink()


# ---------------------------------------------------------------------------
# list_registered()
# ---------------------------------------------------------------------------


def test_list_registered_empty_when_nothing_registered(tmp_hub_root: Path) -> None:
    assert use_cases.list_registered() == {}


def test_list_registered_returns_name_to_resolved_target(tmp_hub_root: Path) -> None:
    t1 = tmp_hub_root.parent / "first"
    t1.mkdir()
    t2 = tmp_hub_root.parent / "second"
    t2.mkdir()

    use_cases.register("investsarva", t1)
    use_cases.register("pustak", t2)

    listed = use_cases.list_registered()
    assert set(listed) == {"investsarva", "pustak"}
    assert Path(listed["investsarva"]).resolve() == t1.resolve()
    assert Path(listed["pustak"]).resolve() == t2.resolve()


def test_list_registered_skips_non_symlink_entries(tmp_hub_root: Path) -> None:
    """A plain directory accidentally placed under use-cases must not appear."""
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)
    (hub_fs.tier_dir("use-cases") / "rogue").mkdir()

    target = tmp_hub_root.parent / "ok"
    target.mkdir()
    use_cases.register("good", target)

    listed = use_cases.list_registered()
    assert "rogue" not in listed
    assert "good" in listed


# ---------------------------------------------------------------------------
# discover()
# ---------------------------------------------------------------------------


def test_discover_registers_existing_default_use_cases(tmp_home: Path) -> None:
    """discover() scans ~/.<usecase>/skills/ for each canonical default."""
    # Stand up `skills/` for two of the six defaults.
    (tmp_home / ".investsarva" / "skills").mkdir(parents=True)
    (tmp_home / ".memsarva" / "skills").mkdir(parents=True)
    # Pre-create the hub.
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)

    registered = use_cases.discover()

    assert set(registered) == {"investsarva", "memsarva"}
    for name, root_dir in [("investsarva", tmp_home / ".investsarva" / "skills"),
                           ("memsarva", tmp_home / ".memsarva" / "skills")]:
        link = hub_fs.tier_dir("use-cases") / name
        assert link.is_symlink()
        assert link.resolve() == root_dir.resolve()


def test_discover_skips_missing_default_roots(tmp_home: Path) -> None:
    """If `~/.<usecase>/skills/` does not exist, discover ignores it."""
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)

    registered = use_cases.discover()
    assert registered == [] or registered == {}


def test_discover_skips_when_dot_dir_exists_but_skills_does_not(
    tmp_home: Path,
) -> None:
    """~/.investsarva exists but no `skills/` subdir → skip it."""
    (tmp_home / ".investsarva").mkdir()
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)

    registered = use_cases.discover()
    assert "investsarva" not in (registered or {})


def test_discover_is_idempotent(tmp_home: Path) -> None:
    (tmp_home / ".pi" / "skills").mkdir(parents=True)
    hub_fs.tier_dir("use-cases").mkdir(parents=True, exist_ok=True)

    first = use_cases.discover()
    second = use_cases.discover()

    assert set(first) == set(second) == {"pi"}


# ---------------------------------------------------------------------------
# Path authority — module must use skills_hub.fs for paths
# ---------------------------------------------------------------------------


def test_use_cases_module_does_not_hardcode_hub_path() -> None:
    """The module body must route through skills_hub.fs."""
    import inspect
    source = inspect.getsource(use_cases)
    # No literal `.skills-hub` and no literal `/use-cases/` joined manually.
    assert ".skills-hub" not in source
