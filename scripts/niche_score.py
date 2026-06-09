#!/usr/bin/env python3
"""
niche_score.py — transparent demand-vs-competition scoring for KDP niches.

Parses a niche corpus (docs/niche-research.md by default, or live-scrape output in the
same shape) into structured records and ranks them by an opportunity score. This is the
deterministic core the research-niche skill uses; in fallback mode it runs entirely on the
existing corpus (no scrape needed), which is how it is verified.

Score model (transparent, all components reported):
  demand        = booktok*1.0 + revenue*1.2 + tier*0.8  (+1.0 if underserved)
  opportunity   = demand - competitiveness*1.5
  -> normalized to 0-100 across the scored set.

Zero-viable handling: with --min-score, if nothing clears the floor we DO NOT silently
pick the least-bad niche — we report "no viable niche" and surface the closest N.

Usage:
  python3 scripts/niche_score.py [corpus.md] [--niche SUBSTR] [--top N] [--min-score F] [--json]
Exit: 0 ok, 2 IO error, 3 zero-viable (with --min-score and nothing clears it).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BOOKTOK = {"massive": 5, "dominant": 5, "very high": 4, "high": 3, "moderate": 2, "low": 1}
COMPET = {"high": 3.0, "medium-high": 2.5, "medium": 2.0, "medium-low": 1.5, "low": 1.0}
REV_LO, REV_HI = 0.8, 2.5  # $/full-read range used to normalize revenue to 1..5

NICHE_RE = re.compile(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*$")
TIER_RE = re.compile(r"^###\s*TIER\s*(\d+)", re.IGNORECASE)
FIELD_RE = re.compile(r"^-\s*([\w /]+?):\s*(.+)$")


def first_key(text: str, table: dict[str, float | int]) -> tuple[str, float | int] | None:
    low = text.lower()
    # longest keys first so "medium-high" wins over "medium"/"high"
    for key in sorted(table, key=len, reverse=True):
        if key in low:
            return key, table[key]
    return None


def parse_revenue(text: str) -> float | None:
    nums = [float(x) for x in re.findall(r"\$(\d+(?:\.\d+)?)", text)]
    per = [n for n in nums if n <= 10]  # per-read dollars, not $5K/month figures
    if not per:
        return None
    mid = sum(per[:2]) / len(per[:2])
    scaled = 1 + 4 * (mid - REV_LO) / (REV_HI - REV_LO)
    return max(1.0, min(5.0, scaled))


def parse_corpus(text: str) -> list[dict]:
    niches: list[dict] = []
    tier = None
    cur: dict | None = None
    underserved = set()

    # collect underserved names (bonus)
    in_under = False
    for line in text.splitlines():
        if line.startswith("## UNDERSERVED"):
            in_under = True
            continue
        if in_under and line.startswith("## "):
            in_under = False
        if in_under:
            m = re.search(r"\*\*(.+?)\*\*", line)
            if m:
                underserved.add(m.group(1).split("/")[0].split("(")[0].strip().lower())

    for line in text.splitlines():
        tm = TIER_RE.match(line.strip())
        if tm:
            tier = int(tm.group(1))
            continue
        nm = NICHE_RE.match(line.strip())
        if nm:
            cur = {"rank": int(nm.group(1)), "name": nm.group(2).strip(),
                   "tier": tier, "fields": {}}
            niches.append(cur)
            continue
        if cur is not None:
            fm = FIELD_RE.match(line.strip())
            if fm:
                cur["fields"][fm.group(1).strip().lower()] = fm.group(2).strip()

    for n in niches:
        f = n["fields"]
        bt = first_key(f.get("booktok driver", ""), BOOKTOK)
        cp = first_key(f.get("competitiveness", ""), COMPET)
        rev = parse_revenue(f.get("revenue estimate", ""))
        tier_score = {1: 3, 2: 2, 3: 1}.get(n["tier"] or 3, 1)
        is_under = any(u in n["name"].lower() for u in underserved)

        n["booktok"] = bt[1] if bt else 1
        n["competitiveness"] = cp[1] if cp else 2.0
        n["revenue"] = rev if rev is not None else 2.5
        n["tier_score"] = tier_score
        n["underserved"] = is_under

        demand = n["booktok"] * 1.0 + n["revenue"] * 1.2 + tier_score * 0.8 + (1.0 if is_under else 0.0)
        n["demand"] = round(demand, 2)
        n["opportunity_raw"] = round(demand - n["competitiveness"] * 1.5, 2)

    if niches:
        raws = [n["opportunity_raw"] for n in niches]
        lo, hi = min(raws), max(raws)
        for n in niches:
            n["score"] = round(100 * (n["opportunity_raw"] - lo) / (hi - lo), 1) if hi > lo else 50.0
    return niches


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Score/rank KDP niches by demand vs competition.")
    ap.add_argument("corpus", nargs="?", default="docs/niche-research.md")
    ap.add_argument("--niche", help="score a single niche by name substring")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-score", type=float, default=None,
                    help="ABSOLUTE viability floor on opportunity_raw (demand - 1.5*competition; "
                         "e.g. 3.0), NOT the 0-100 display score. If nothing clears it, report "
                         "closest instead of silently picking the least-bad niche.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    p = Path(args.corpus)
    if not p.exists():
        print(f"error: corpus not found: {p}", file=sys.stderr)
        return 2
    niches = parse_corpus(p.read_text(encoding="utf-8", errors="replace"))
    if not niches:
        print("error: no niche records parsed", file=sys.stderr)
        return 2
    niches.sort(key=lambda n: n["score"], reverse=True)

    if args.niche:
        hits = [n for n in niches if args.niche.lower() in n["name"].lower()]
        if not hits:
            print(f"no niche matching '{args.niche}'. Closest by score:")
            for n in niches[:5]:
                print(f"  {n['score']:5.1f}  {n['name']}")
            return 0
        sel = hits[0]
        if args.json:
            print(json.dumps(sel, indent=2))
        else:
            print(f"{sel['name']} — score {sel['score']}/100")
            print(f"  demand {sel['demand']} (booktok {sel['booktok']}, revenue {sel['revenue']:.1f}, "
                  f"tier {sel['tier_score']}, underserved {sel['underserved']})")
            print(f"  competitiveness {sel['competitiveness']}  ->  opportunity_raw {sel['opportunity_raw']}")
        return 0

    ranked = niches[:args.top]
    if args.min_score is not None:
        # Floor is ABSOLUTE (opportunity_raw), not the normalized 0-100 score —
        # otherwise the top niche always normalizes to 100 and the guard never fires.
        viable = [n for n in niches if n["opportunity_raw"] >= args.min_score]
        if not viable:
            closest = niches[:max(3, args.top)]
            payload = {"viable": [], "zero_viable": True,
                       "min_opportunity": args.min_score,
                       "closest": [{"name": n["name"], "score": n["score"],
                                    "opportunity_raw": n["opportunity_raw"]} for n in closest]}
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"NO VIABLE NICHE with opportunity_raw >= {args.min_score}. "
                      f"Closest (not auto-selected):")
                for n in closest:
                    print(f"  raw {n['opportunity_raw']:5.2f}  (score {n['score']:5.1f})  {n['name']}")
            return 3
        ranked = viable[:args.top]

    if args.json:
        print(json.dumps([{k: n[k] for k in ("rank", "name", "tier", "score", "demand",
              "competitiveness", "booktok", "revenue", "underserved")} for n in ranked], indent=2))
    else:
        print(f"NICHE RANKING (top {len(ranked)} by opportunity score)")
        print("score | niche")
        print("------|------")
        for n in ranked:
            flag = " [underserved]" if n["underserved"] else ""
            print(f"{n['score']:5.1f} | {n['name']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
