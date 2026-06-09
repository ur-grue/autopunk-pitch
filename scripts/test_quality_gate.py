#!/usr/bin/env python3
"""Tests for quality_gate.py. Run: python3 scripts/test_quality_gate.py  (or pytest)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quality_gate as qg  # noqa: E402


def test_antithesis_copula_matches():
    # describe-by-negation bloat anchored to a copula
    assert qg.ANTITHESIS_RE.search("The room was not silent, but careful.")
    assert qg.ANTITHESIS_RE.search("It is not anger, but fear.")


def test_antithesis_ignores_plain_not_but():
    # ordinary prose must NOT be flagged (the A2 false-positive the review caught)
    assert not qg.ANTITHESIS_RE.search("She tried not to listen, but he kept talking.")
    assert not qg.ANTITHESIS_RE.search("He told her not to move, but she ran.")


def test_word_count_strips_heading():
    assert qg.word_count("## Chapter 1: Signal\n\nword word word") == 3


def test_is_truncated():
    assert qg.is_truncated("a sentence that ends abruptly")          # no terminal punctuation
    assert not qg.is_truncated('He smiled. "We are done."')          # ends in close-quote
    assert not qg.is_truncated("She left.")


def test_blacklist_whole_word_and_phrase():
    h = qg.whole_word_hits("This is significantly better, a testament to skill", qg.HARD_BLACKLIST)
    assert h.get("significantly") == 1
    assert h.get("a testament to") == 1
    # "embark" must not match inside "embarked"? whole-word: "embark" only
    assert "embark" not in qg.whole_word_hits("They embarked early", qg.HARD_BLACKLIST)


def test_parse_word_targets_and_run():
    with tempfile.TemporaryDirectory() as d:
        nd = Path(d)
        (nd / "04_pacing.md").write_text(
            "## Word Targets\n| Chapter | Target |\n|--|--|\n| 1 | 100 |\n| 2 | 100 |\n",
            encoding="utf-8")
        targets = qg.parse_word_targets(nd / "04_pacing.md")
        assert targets == {1: 100, 2: 100}

        # ch1 on-target (100 words), ch2 way under (10 words)
        (nd / "chapter01.md").write_text("## Chapter 1\n\n" + ("word " * 100).strip() + ".", encoding="utf-8")
        (nd / "chapter02.md").write_text("## Chapter 2\n\n" + ("word " * 10).strip() + ".", encoding="utf-8")
        report = qg.run(nd, default_target=100, tol=0.15, n_chapters=2)
        assert report["pass"] is False
        assert report["failing_chapters"] == [2]          # only ch2 fails word count
        assert report["checks"]["completeness"]["pass"] is True


def test_truncated_chapter_fails():
    with tempfile.TemporaryDirectory() as d:
        nd = Path(d)
        (nd / "chapter01.md").write_text("## Chapter 1\n\n" + ("word " * 100) + "and then", encoding="utf-8")
        report = qg.run(nd, default_target=100, tol=0.5, n_chapters=1)
        assert 1 in report["checks"]["completeness"]["truncated"]
        assert report["pass"] is False


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
