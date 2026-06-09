#!/usr/bin/env python3
"""
quality_gate.py — deterministic quality gate for ccwriter novels (Phase 18.5).

Runs AFTER the assembler (Phase 18). Reads the final chapter files and the pacing
table; never edits prose. Emits a hard pass/fail on scriptable checks plus a
machine-readable list of failing chapters that the regen loop consumes.

Checks (hard, gating):
  1. word_count   — each chapter within +/- TOL of its target
  2. blacklist    — zero hard LLM-tell terms (references/prompt-quality.md)
  3. antithesis   — zero "not X, but Y" / "No X, no Y — just Z" constructions
  4. completeness — exactly n_chapters files, none truncated mid-sentence

Soft (reported, non-gating):
  - context-dependent words (journey/landscape/navigate as metaphor) -> warnings

The LLM-judge advisory score is NOT computed here; the quality-gate SKILL adds it
on top of this deterministic core and never lets it override a hard fail.

Usage:
  python3 scripts/quality_gate.py NOVEL_DIR [--target-words N] [--tolerance 0.15]
                                  [--n-chapters N] [--json]
Exit code: 0 = PASS, 1 = FAIL, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- LLM-tell blacklist (mirrors references/prompt-quality.md) ----------------
# HARD: unambiguous AI-tells. Any hit fails the gate.
HARD_BLACKLIST = [
    "seamlessly", "tapestry", "delve", "pivotal", "furthermore", "moreover",
    "in conclusion", "it is worth noting", "significantly", "embark", "paradigm",
    "synergy", "facilitate", "utilize", "nuanced", "multifaceted", "myriad",
    "plethora", "a testament to", "in the realm of", "at the end of the day",
    "needless to say", "interestingly enough", "it goes without saying",
]
# SOFT: legitimate in literal use; reported as warnings, do not gate.
SOFT_BLACKLIST = ["journey", "landscape", "navigate"]

# Antithesis bloat: "it WAS not X, but Y" — anchored to a copula so we catch the
# describe-by-negation construction without false-flagging ordinary prose like
# "she tried not to listen, but he kept talking".
ANTITHESIS_RE = re.compile(
    r"\b(?:was|were|is|are|am|be|been|being|it's|its|that's|there's|he's|she's|they're)"
    r"\s+not\s+[\w'-]+(?:\s+[\w'-]+){0,4}\s*,\s*but\s+\w",
    re.IGNORECASE,
)
# List-negation: "No X, no Y — just Z" / "no X, no Y, just Z"
LIST_NEG_RE = re.compile(r"\bno\s+[\w''-]+\s*,\s*no\s+[\w''-]+\s*[—,-]\s*(?:just\s+)?\w", re.IGNORECASE)

TERMINAL_CHARS = set('.!?"”’…)')  # . ! ? " ” ’ … )
CHAPTER_RE = re.compile(r"^chapter(\d+)\.md$")


def word_count(text: str) -> int:
    # Strip the leading "## Chapter N: Title" heading line so it doesn't pad the count.
    lines = text.splitlines()
    body = [ln for ln in lines if not ln.lstrip().startswith("#")]
    return len(" ".join(body).split())


def parse_word_targets(pacing_path: Path) -> dict[int, int]:
    """Parse the '## Word Targets' table (| N | target |) from 04_pacing.md."""
    targets: dict[int, int] = {}
    if not pacing_path.exists():
        return targets
    in_targets = False
    row = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|")
    for line in pacing_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().lower().startswith("## word targets"):
            in_targets = True
            continue
        if in_targets and line.startswith("## "):  # next section
            break
        m = row.match(line.strip())
        if m:
            targets[int(m.group(1))] = int(m.group(2))
    return targets


def whole_word_hits(text: str, terms: list[str]) -> dict[str, int]:
    low = text.lower()
    hits: dict[str, int] = {}
    for term in terms:
        # word-boundary match; multi-word phrases matched as substrings with spaces
        if " " in term:
            n = low.count(term)
        else:
            n = len(re.findall(rf"\b{re.escape(term)}\b", low))
        if n:
            hits[term] = n
    return hits


def is_truncated(text: str) -> bool:
    nonempty = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    if not nonempty:
        return True
    last = nonempty[-1].rstrip("*_`> ")  # strip trailing markdown emphasis
    return bool(last) and last[-1] not in TERMINAL_CHARS


def run(novel_dir: Path, default_target: int, tol: float, n_chapters: int | None) -> dict:
    chapters = {}
    for p in sorted(novel_dir.glob("chapter*.md")):
        m = CHAPTER_RE.match(p.name)
        if m:
            chapters[int(m.group(1))] = p
    targets = parse_word_targets(novel_dir / "04_pacing.md")

    expected = n_chapters or (max(chapters) if chapters else 0)

    per_chapter = []
    failing = set()
    blacklist_hits, soft_hits, antithesis, list_neg, truncated = {}, {}, [], [], []

    for num in sorted(chapters):
        text = chapters[num].read_text(encoding="utf-8", errors="replace")
        wc = word_count(text)
        target = targets.get(num, default_target)
        lo, hi = int(target * (1 - tol)), int(target * (1 + tol))
        wc_ok = lo <= wc <= hi

        hard = whole_word_hits(text, HARD_BLACKLIST)
        soft = whole_word_hits(text, SOFT_BLACKLIST)
        anti = [m.group(0) for m in ANTITHESIS_RE.finditer(text)]
        lneg = [m.group(0) for m in LIST_NEG_RE.finditer(text)]
        trunc = is_truncated(text)

        chapter_pass = wc_ok and not hard and not anti and not lneg and not trunc
        if not chapter_pass:
            failing.add(num)
        if hard:
            blacklist_hits[num] = hard
        if soft:
            soft_hits[num] = soft
        if anti:
            antithesis.append({"chapter": num, "matches": anti[:5]})
        if lneg:
            list_neg.append({"chapter": num, "matches": lneg[:5]})
        if trunc:
            truncated.append(num)

        per_chapter.append({
            "chapter": num, "words": wc, "target": target,
            "range": [lo, hi], "word_count_ok": wc_ok,
            "blacklist": hard, "soft": soft,
            "antithesis": len(anti), "list_negation": len(lneg),
            "truncated": trunc, "pass": chapter_pass,
        })

    missing = [n for n in range(1, expected + 1) if n not in chapters] if expected else []
    completeness_ok = (not missing) and expected > 0 and not truncated

    checks = {
        "word_count": {"pass": all(c["word_count_ok"] for c in per_chapter),
                       "tolerance": tol},
        "blacklist": {"pass": not blacklist_hits, "hits": blacklist_hits},
        "antithesis": {"pass": not antithesis and not list_neg,
                       "antithesis": antithesis, "list_negation": list_neg},
        "completeness": {"pass": completeness_ok, "expected": expected,
                         "found": len(chapters), "missing": missing,
                         "truncated": truncated},
    }
    overall = all(c["pass"] for c in checks.values()) and bool(per_chapter)

    return {
        "novel": novel_dir.name,
        "pass": overall,
        "checks": checks,
        "failing_chapters": sorted(failing),
        "soft_warnings": soft_hits,
        "per_chapter": per_chapter,
    }


def human_report(r: dict) -> str:
    out = [f"QUALITY GATE — {r['novel']}", "=" * 48]
    status = "PASS" if r["pass"] else "FAIL"
    out.append(f"VERDICT: {status}")
    out.append("")
    c = r["checks"]
    def mark(b): return "OK  " if b else "FAIL"
    out.append(f"[{mark(c['word_count']['pass'])}] word count (+/-{int(c['word_count']['tolerance']*100)}%)")
    out.append(f"[{mark(c['blacklist']['pass'])}] LLM-tell blacklist")
    out.append(f"[{mark(c['antithesis']['pass'])}] antithesis / list-negation")
    out.append(f"[{mark(c['completeness']['pass'])}] completeness "
               f"({c['completeness']['found']}/{c['completeness']['expected']} chapters)")
    if r["failing_chapters"]:
        out.append("")
        out.append("Failing chapters (regen targets): " +
                   ", ".join(str(n) for n in r["failing_chapters"]))
        for pc in r["per_chapter"]:
            if not pc["pass"]:
                reasons = []
                if not pc["word_count_ok"]:
                    reasons.append(f"words {pc['words']} vs {pc['target']} {pc['range']}")
                if pc["blacklist"]:
                    reasons.append("blacklist " + ", ".join(pc["blacklist"]))
                if pc["antithesis"]:
                    reasons.append(f"antithesis x{pc['antithesis']}")
                if pc["list_negation"]:
                    reasons.append(f"list-negation x{pc['list_negation']}")
                if pc["truncated"]:
                    reasons.append("truncated")
                out.append(f"  ch{pc['chapter']:02d}: " + "; ".join(reasons))
    if c["completeness"]["missing"]:
        out.append("Missing chapters: " + ", ".join(str(n) for n in c["completeness"]["missing"]))
    if r["soft_warnings"]:
        out.append("")
        out.append("Soft warnings (context-dependent, non-gating):")
        for ch, hits in sorted(r["soft_warnings"].items()):
            out.append(f"  ch{ch:02d}: " + ", ".join(f"{k}x{v}" for k, v in hits.items()))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Deterministic quality gate for a ccwriter novel dir.")
    ap.add_argument("novel_dir")
    ap.add_argument("--target-words", type=int, default=2500,
                    help="fallback per-chapter target if 04_pacing.md has no table")
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--n-chapters", type=int, default=None,
                    help="expected chapter count; inferred from files if omitted")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    novel_dir = Path(args.novel_dir)
    if not novel_dir.is_dir():
        print(f"error: not a directory: {novel_dir}", file=sys.stderr)
        return 2

    report = run(novel_dir, args.target_words, args.tolerance, args.n_chapters)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(human_report(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
