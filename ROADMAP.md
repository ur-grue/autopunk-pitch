# ccwriter Roadmap

> Living document. Built 2026-06-09 from: a repo retro, a /health baseline (8.8/10), cited
> market research (KDP/KU economics, enforcement, tooling, covers), a last-30-days sentiment
> scan, and an adversarial pressure-test. Updated as bets resolve. Pairs with `CHANGELOG.md`.

## Context

ccwriter is an **autonomous publishing pipeline** that runs inside Claude Code: point it at a genre
and it researches a niche → generates a full novel (22-phase, 5-layer writer) → quality-gates it →
generates an illustrated cover (gpt-image-1) → lists + uploads to Amazon KDP as a draft, with the
human approving at 3 gates. The pipeline was built and live-verified on 2026-06-09 (a real KDP draft
with a generated cover). No sales yet. Solo operator.

**The hard truth from the research + pressure-test:** the binding constraint is **distribution,
account-survival, and platform risk — not production.** We built a factory for a market that is
actively hunting factories (AI-detection takedowns, KU read-pattern bans, reader backlash). "Good
book + right niche = sells" is false for an unknown author: Amazon discovery runs on early-sales
velocity, reviews, ads, and also-boughts — none of which the pipeline currently touches. So the
roadmap's job is **survive + get discovered + compound an owned asset**, with production quality as
necessary-but-not-sufficient.

**Prime directive:** *compound an owned audience without getting nuked.*

## Strategic decisions (resolved 2026-06-09)

- **D1 — Business model → CONTENT-OP ONLY.** ccwriter is used solely by the operator to generate
  their own Amazon KDP books and series. The pipeline is **not** productized, sold, or offered as a
  service. **P5 (productize) is cut.** Everything below serves one goal: the operator shipping their
  own profitable, survivable KDP catalog.
- **D2 — Writer length → READ-THROUGH + a small fix.** Right-size each book's target to what gets
  *fully read* (KU pays on pages read; a tight fully-read book beats a padded one with 40% drop-off).
  Add a **bounded** generation-level expansion only where a book is materially incomplete. The
  writer's prose logic otherwise stays fixed.

## Pillars (re-sequenced by the pressure-test: survival + audience first)

| # | Pillar | Why / why here | Status |
|---|--------|----------------|--------|
| **P0** | **Survive & isolate** — account-survival as *architecture*: pen-name/account isolation + blast-radius design (one flagged title can nuke the whole account *and* withhold accrued royalties = correlated tail risk), AI disclosure posture, human-paced cadence (≤2/day + stagger), clean-read-profile awareness (KU bot-farm sweeps catch innocents). **Precondition — before any more uploads.** | partial (velocity in `kdp-upload`; isolation architecture missing) |
| **P1** | **Own the audience** — the actual growth engine, starting at **book #1**: back-matter CTA → reader magnet → mailing list (the one asset Amazon can't terminate); **wide distribution after the KU window** (Draft2Digital → Kobo/Apple/Google) to de-risk single-platform dependence; a minimal launch mechanic. | **not built — top gap** |
| **P2** | **Quality that survives + sells** — de-pattern prose for **AI-detection survival** (Pangram-style "100% AI" flags pulped a Big Five book in 2026; the LLM-tell/antithesis checks become load-bearing and must go further); reframe under-length → read-through (D2); current-trope fit (yearning/slow-burn rising, high-spice cooling); on-trend illustrated covers (✅ done via gpt-image-1). | quality-gate + cover built; de-pattern + read-through pending |
| **P3** | **Pick ONE niche manually + ship** — for M1–M2, hand-pick an underserved niche (monster/alien romance, why-choose, cozy fantasy, omegaverse, dark academia) and ship. **Defer the scraping/scoring automation** — it's premature before any niche is validated. | research-niche exists; intentionally deferred |
| **P4** | **Close the loop** — post-publish KDP sales/KU read-through → niche scoring; needs M2 volume to be a real signal. The controlled ramp (5–8 titles, one pen name) provides signal without flooding. | not built |
| ~~P5~~ | ~~Pipeline-as-product~~ — **CUT (D1: content-op only).** | — |

## Milestones (the M1 gate is *process* validation — read-through needs M2 scale)

- **M0 — Pipeline built (DONE, 2026-06-09).** Autonomous pipeline + 13 tests live-verified; one
  gpt-image-1 cover on a real KDP draft.
- **M1 — "Machine validated + audience seeded" (near-term).** P0 isolation architecture in place; **1
  hand-picked-niche book** that is de-patterned (survives an AI-detector sniff), right-sized for
  read-through, on-trend illustrated cover, KDP-compliant, **published with a back-matter list CTA**.
  *Gate = process validation* (compliant · non-AI-flagged · fully-readable · list-capture works) +
  qualitative (beta read, also-bought placement). **Not** statistical read-through (impossible at n=1).
- **M2 — "Controlled ramp + first real signal."** 5–8 titles, **one pen name, one niche**, velocity-safe,
  **wide after the KU window.** Now read-through + KU page-reads become a real signal → feed P4. *Gate =
  read-through trend + account health + list growth.*
- **M3 — "Brand compounding."** The pen-name brand + mailing list + series read-through is a durable,
  backlash-resistant asset. (Final milestone — content-op only, per D1.)

## Near-term backlog (M1 — spec-level, build-actionable)

- [ ] **P0-1 Isolation architecture** — decide pen-name/account structure + blast radius; document in a
      `docs/account-safety.md`; encode the rule "AI disclosure = Yes; one account per N pen names" into
      `kdp-orchestrator`. *Verify: a written isolation model + orchestrator refuses to exceed cadence.*
- [ ] **P0-2 Cadence enforcement** — orchestrator hard-caps ≤2 publishes/day, staggers releases, warns on
      bursty read patterns. *Verify: attempt 3/day → blocked.*
- [ ] **P1-1 Mailing-list capture** — back-matter CTA + reader-magnet generation added to phase-19/assembler
      (front/back matter), pointing at a list provider. *Verify: a generated book ends with a working CTA.*
- [ ] **P1-2 Wide-distribution path** — add a Draft2Digital (or direct Kobo/Apple/Google) export/upload
      track parallel to KDP, triggered after the KU exclusivity window. *Verify: one title exported wide.*
- [ ] **P2-1 AI-detection de-patterning gate** — extend `quality_gate.py` beyond the blacklist: flag
      AI-tell patterns (adjective-per-noun density, simile-for-action, rule-of-three runs, repeated-word
      clusters) and gate/regenerate. *Verify: a deliberately patterned chapter is flagged.*
- [ ] **P2-2 Read-through reframe (D2)** — set the per-book target to a read-through-optimal length;
      add chapter-end hook scoring to the gate. *Verify: gate reports a hook score per chapter.*
- [ ] **P3-1 Manual niche pick** — choose one underserved niche for the first title; fill its TOML by hand
      (no scraper). *Verify: a validated niche TOML + market rationale.*

## What already exists (reuse, don't rebuild)
- 22-phase writer + assembler (held fixed); `kdp-orchestrator` (3 gates, resume); `quality_gate.py`
  (word-count/blacklist/antithesis/completeness + 13 tests); `cover-generate` (gpt-image-1, illustrated,
  baked-in title — verified live); `kdp-upload` (browse driver, verified KDP selectors, velocity caps);
  `research-niche` + `niche_score.py` + `docs/niche-research.md` corpus.

## NOT in scope (explicitly deferred)
- Niche-research **automation** (P3 manual until a niche is validated).
- Multi-pen-name *scale* before M2 process validation.
- Touching the 5-layer writer's prose logic beyond the bounded D2 expansion fix.
- Productizing / selling / offering the pipeline as a service (P5 cut — content-op only, per D1).

## Kill-risks (inversion — what ends this)
1. **Account nuke + royalty clawback** (one AI-flagged title → whole account + accrued earnings gone).
   → P0 isolation *architecture*; wide distribution (P1) reduces single-point-of-failure.
2. **AI-detection takedown / review-bombing** (Shy Girl was pulped). → P2 de-patterning + heavy
   human-signature; disclosure handled but note the disclosure-vs-ranking tension.
3. **No discovery** (great book into a void). → P1 audience + launch mechanics are now first-class.
4. **Validation paradox** (need volume to measure, forbid volume until validated). → controlled ramp
   at M2; M1 gates on process, not statistics.
5. **The "writer works well" illusion** (it underproduces 40%). → D2 forces an explicit decision.

## Sources (terrain)
- KU economics / KENP: [Global Fund payout tracker](https://www.writtenwordmedia.com/kdp-global-fund-payouts/) (Apr 2026 US rate ~$0.0048/pg), [Kindlepreneur KENP](https://kindlepreneur.com/kenp-calculator/)
- AI-detection takedowns: [Shy Girl / Hachette (Slate, Mar 2026)](https://slate.com/culture/2026/03/shy-girl-mia-ballard-novel-a-i-book-horror-reddit-hachette-canceled.html), [Commonwealth Prize AI flag (The Conversation)](https://theconversation.com/what-do-the-commonwealth-writers-prize-ai-allegations-mean-for-prizes-and-short-stories-283470)
- Enforcement (behavioral): [KU bot-farm bans catch innocents (The Digital Reader)](https://the-digital-reader.com/authors-are-getting-caught-up-in-amazons-fight-against-ku-bot-farms/)
- Tooling landscape: [Kindlepreneur AI tools](https://kindlepreneur.com/best-ai-writing-tools/), [mylifenote 11 tools](https://blog.mylifenote.ai/the-11-best-ai-tools-for-writing-fiction-in-2026/)
- Covers 2026: [book cover trends (Miblart)](https://miblart.com/blog/book-cover-trends-this-year/), [k-lytics romance](https://k-lytics.com/romance/)
- Trends/distribution: [BookTok yearning trend](https://romancingthephone.substack.com/p/the-first-booktok-trend-roundup-of), [wide vs KU (Scribe Count)](https://scribecount.com/author-resource/publishing-a-book/wide-vs-kindle-unlimited)
