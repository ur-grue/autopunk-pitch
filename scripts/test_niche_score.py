#!/usr/bin/env python3
"""Tests for niche_score.py. Run: python3 scripts/test_niche_score.py  (or pytest)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import niche_score as ns  # noqa: E402

CORPUS = """\
## RANKED TOP 20 NICHES

### TIER 1 -- Proven
**1. Romantasy**
- Competitiveness: HIGH
- BookTok driver: DOMINANT
- Revenue estimate: $2.00-$2.50 per full read

**2. Cozy Mystery**
- Competitiveness: MEDIUM
- BookTok driver: Low
- Revenue estimate: $0.85-$1.20 per read; top authors earn $5K-$20K/month

## UNDERSERVED BUT HIGH-DEMAND (Best Opportunities)
1. **Cozy Mystery** -- few series.
"""


def test_parse_and_revenue_not_polluted_by_monthly_figures():
    niches = ns.parse_corpus(CORPUS)
    by = {n["name"]: n for n in niches}
    # "$5K-$20K/month" must NOT pollute the per-read revenue (first-2 + <=10 guard)
    assert by["Cozy Mystery"]["revenue"] < 3.0
    assert by["Romantasy"]["revenue"] > by["Cozy Mystery"]["revenue"]


def test_underserved_flag():
    niches = ns.parse_corpus(CORPUS)
    by = {n["name"]: n for n in niches}
    assert by["Cozy Mystery"]["underserved"] is True
    assert by["Romantasy"]["underserved"] is False


def test_normalized_score_range():
    niches = ns.parse_corpus(CORPUS)
    scores = sorted(n["score"] for n in niches)
    assert scores[0] == 0.0 and scores[-1] == 100.0  # normalized endpoints


def test_min_score_floor_is_absolute_not_normalized():
    # A3: the floor must be on opportunity_raw, so a floor of 100 must NOT pass
    # just because the top niche normalizes to 100.
    niches = ns.parse_corpus(CORPUS)
    raws = [n["opportunity_raw"] for n in niches]
    assert max(raws) < 100  # absolute opportunity is small; 100 can never be cleared
    # and a reasonable absolute floor admits the strong niche
    viable = [n for n in niches if n["opportunity_raw"] >= -10]
    assert viable


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
