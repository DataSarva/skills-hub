"""Unit tests for `skills_hub.pustak_bridge`.

The bridge:
  * reads `_index.json` from a hub root,
  * renders a deterministic markdown wiki page,
  * shells out to `pustak wiki write` (never writes the wiki directly),
  * is idempotent (no-op when rendered body matches existing page),
  * is best-effort (logs warning and returns 0 when pustak/wiki missing).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from skills_hub import pustak_bridge


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pustak_bridge"


def _home() -> Path:
    return Path(os.environ["HOME"])


def _seed_index(hub_root: Path) -> Path:
    hub_root.mkdir(parents=True, exist_ok=True)
    payload = (FIXTURES / "_index.json").read_text(encoding="utf-8")
    target = hub_root / "_index.json"
    target.write_text(payload, encoding="utf-8")
    return target


def _seed_wiki_dir() -> Path:
    wiki = _home() / ".pustak" / "wiki" / "general" / "tooling"
    wiki.mkdir(parents=True, exist_ok=True)
    return wiki


def _normalize(text: str) -> str:
    """Mask `id`, `version`, `last_updated` so golden compare is stable."""
    text = re.sub(r"^id: .+$", "id: __ID__", text, flags=re.MULTILINE)
    text = re.sub(r"^version: .+$", "version: __VERSION__", text, flags=re.MULTILINE)
    text = re.sub(
        r"^last_updated: .+$", "last_updated: __LAST_UPDATED__", text, flags=re.MULTILINE
    )
    return text


# ---------------------------------------------------------------------------
# render_wiki_page — pure markdown rendering
# ---------------------------------------------------------------------------


def test_render_matches_golden_fixture(tmp_hub_root: Path) -> None:
    _seed_index(tmp_hub_root)
    body = pustak_bridge.render_wiki_page(tmp_hub_root)
    golden = (FIXTURES / "skills-hub-index.md").read_text(encoding="utf-8")
    assert _normalize(body) == golden


def test_render_includes_required_frontmatter_keys(tmp_hub_root: Path) -> None:
    _seed_index(tmp_hub_root)
    body = pustak_bridge.render_wiki_page(tmp_hub_root)
    for key in (
        "id:",
        "slug: skills-hub-index",
        "namespace: general/tooling",
        "version:",
        "last_updated:",
        "authored_by:",
        "deprecated: false",
    ):
        assert key in body, f"missing key {key!r} in:\n{body}"


def test_render_table_has_one_row_per_skill(tmp_hub_root: Path) -> None:
    _seed_index(tmp_hub_root)
    body = pustak_bridge.render_wiki_page(tmp_hub_root)
    data = json.loads((tmp_hub_root / "_index.json").read_text(encoding="utf-8"))
    for entry in data["skills"]:
        assert f"| {entry['slug']} |" in body


def test_render_is_deterministic(tmp_hub_root: Path) -> None:
    _seed_index(tmp_hub_root)
    a = _normalize(pustak_bridge.render_wiki_page(tmp_hub_root))
    b = _normalize(pustak_bridge.render_wiki_page(tmp_hub_root))
    assert a == b


# ---------------------------------------------------------------------------
# mirror_index — orchestrates render + subprocess + idempotency
# ---------------------------------------------------------------------------


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.returncode = 0

    def __call__(self, cmd, *args, **kwargs):  # noqa: ANN001
        text_input = kwargs.get("input", "")
        self.calls.append({"cmd": list(cmd), "kwargs": kwargs, "input": text_input})

        class _Result:
            returncode = self.returncode  # noqa: B023

        return _Result()


def test_mirror_index_invokes_pustak_cli(
    tmp_hub_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_index(tmp_hub_root)
    _seed_wiki_dir()
    recorder = _Recorder()
    monkeypatch.setattr(pustak_bridge.subprocess, "run", recorder)

    rc = pustak_bridge.mirror_index(tmp_hub_root)

    assert rc == 0
    assert recorder.calls, "expected pustak subprocess to be invoked"
    call = recorder.calls[0]
    joined = " ".join(call["cmd"])
    assert "pustak" in joined
    assert "wiki" in joined
    assert "write" in joined
    # Path argument must reference our slug under namespace.
    assert any("skills-hub-index" in part for part in call["cmd"])
    assert any("general/tooling" in part for part in call["cmd"])


def test_mirror_index_skips_when_pustak_missing(
    tmp_hub_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _seed_index(tmp_hub_root)
    _seed_wiki_dir()

    def _raise(*_args, **_kwargs):
        raise FileNotFoundError("pustak")

    monkeypatch.setattr(pustak_bridge.subprocess, "run", _raise)
    rc = pustak_bridge.mirror_index(tmp_hub_root)
    assert rc == 0
    captured = capsys.readouterr()
    assert "pustak" in (captured.err + captured.out).lower()


def test_mirror_index_skips_when_wiki_dir_missing(
    tmp_hub_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _seed_index(tmp_hub_root)
    # NOTE: do NOT create ~/.pustak/wiki/
    recorder = _Recorder()
    monkeypatch.setattr(pustak_bridge.subprocess, "run", recorder)

    rc = pustak_bridge.mirror_index(tmp_hub_root)

    assert rc == 0
    assert recorder.calls == [], "must not shell out when wiki dir missing"
    captured = capsys.readouterr()
    assert "pustak" in (captured.err + captured.out).lower()


def test_mirror_index_is_no_op_when_content_matches(
    tmp_hub_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_index(tmp_hub_root)
    wiki_dir = _seed_wiki_dir()
    # Pre-seed the wiki page with the body the bridge would write — only
    # `version` and `last_updated` differ. Idempotency should skip the call.
    body = pustak_bridge.render_wiki_page(tmp_hub_root)
    existing = body.replace("__VERSION__", "5").replace("__LAST_UPDATED__", "2024-01-01T00:00:00Z")
    # The render returns real values; we need to mimic real content with
    # different version/last_updated. Use the same body but tweak those.
    existing = re.sub(r"^version: .+$", "version: 5", body, flags=re.MULTILINE)
    existing = re.sub(
        r"^last_updated: .+$", "last_updated: 2024-01-01T00:00:00Z", existing, flags=re.MULTILINE
    )
    (wiki_dir / "skills-hub-index.md").write_text(existing, encoding="utf-8")

    recorder = _Recorder()
    monkeypatch.setattr(pustak_bridge.subprocess, "run", recorder)

    rc = pustak_bridge.mirror_index(tmp_hub_root)
    assert rc == 0
    assert recorder.calls == [], "expected no subprocess call when content unchanged"


def test_mirror_index_writes_when_content_differs(
    tmp_hub_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_index(tmp_hub_root)
    wiki_dir = _seed_wiki_dir()
    (wiki_dir / "skills-hub-index.md").write_text(
        "---\nslug: skills-hub-index\n---\n\nstale\n", encoding="utf-8"
    )

    recorder = _Recorder()
    monkeypatch.setattr(pustak_bridge.subprocess, "run", recorder)

    rc = pustak_bridge.mirror_index(tmp_hub_root)
    assert rc == 0
    assert len(recorder.calls) == 1
