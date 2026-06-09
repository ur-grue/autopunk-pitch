#!/usr/bin/env python3
"""Tests for kdp_orchestrate.py spine. Run: python3 scripts/test_kdp_orchestrate.py (or pytest)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kdp_orchestrate as ko  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def _fixture(d: Path):
    # one on-target chapter so the quality stage passes, plus the downstream artifacts
    (d / "chapter01.md").write_text("## Chapter 1\n\n" + ("word " * 2500).strip() + ".", encoding="utf-8")
    (d / "complete_novel.docx").write_bytes(b"PK\x03\x04stub")
    (d / "complete_novel.md").write_text("# Novel\n", encoding="utf-8")
    (d / "covers").mkdir()
    (d / "covers" / "cover_final.jpg").write_bytes(b"\xff\xd8\xff\xe0stub")
    (d / "kdp_upload").mkdir()


def test_pipeline_walks_gates_and_never_publishes():
    cfg = "templates/blackwell_book_1.toml"
    assert (REPO / cfg).exists(), "fixture config must exist in repo"
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        _fixture(d)
        assert ko.main(["init", str(d), "--config", cfg, "--mode", "single"]) == 0

        # run #1 -> research ok, stop at GATE 1
        assert ko.main(["run", str(d)]) == 3
        st = ko.load(d)
        assert st["stage"] == "awaiting:g1"
        assert st["gates"] == {"g1": False, "g2": False, "g3": False}

        # approve g1 -> generate + quality -> stop at GATE 2
        assert ko.main(["approve", str(d), "g1"]) == 0
        assert ko.main(["run", str(d)]) == 3
        st = ko.load(d)
        assert st["stage"] == "awaiting:g2"
        assert st["quality"]["pass"] is True            # on-target single chapter passes

        # approve g2 -> cover + prepare + upload -> stop at GATE 3 (never auto-publish)
        assert ko.main(["approve", str(d), "g2"]) == 0
        assert ko.main(["run", str(d)]) == 3
        st = ko.load(d)
        assert st["stage"] == "awaiting:g3"
        assert st["upload"] == "draft"                  # default draft, never published
        assert st["gates"]["g3"] is False               # G3 not auto-approved

        # resume is idempotent: re-run still halts at G3
        assert ko.main(["run", str(d)]) == 3


def test_missing_artifact_halts_stage():
    cfg = "templates/blackwell_book_1.toml"
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)  # no artifacts at all
        ko.main(["init", str(d), "--config", cfg])
        ko.main(["approve", str(d), "g1"])
        # research passes (config exists), generate fails (no chapters/docx) -> halt
        assert ko.main(["run", str(d)]) == 3
        assert ko.load(d)["stage"] == "generate"


def test_publish_cadence_cap():
    now = 1_000_000.0
    assert ko.can_publish([], now)[0] is True                       # empty -> ok
    led = ko.record_publish([], "A", now - 3600)                    # 1h ago
    assert ko.can_publish(led, now)[0] is True                      # 1 in 24h -> ok
    led = ko.record_publish(led, "B", now - 7200)                   # 2h ago
    ok, reason = ko.can_publish(led, now)                           # 2 in 24h -> blocked
    assert ok is False and "cap" in reason
    old = [{"title": "X", "ts": now - 30 * 3600}, {"title": "Y", "ts": now - 26 * 3600}]
    assert ko.can_publish(old, now)[0] is True                      # >24h ago doesn't count


def test_publish_min_gap():
    now = 1_000_000.0
    led = [{"title": "A", "ts": now - 1800}]                        # 0.5h ago
    assert ko.can_publish(led, now, max_per_day=2, min_gap_hours=4)[0] is False
    assert ko.can_publish(led, now, max_per_day=2, min_gap_hours=0)[0] is True


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
