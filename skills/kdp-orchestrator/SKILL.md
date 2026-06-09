---
name: kdp-orchestrator
description: The autonomous spine for ccwriter. Drives a goal prompt through research → generate → quality-gate → cover → list → upload for a single title or a whole series, stopping only at 3 human approval gates. Resumable via orchestrator_state.json. Holds the writing engine fixed — it only chains existing skills and the new bookend skills; it never edits prose.
---

# KDP Orchestrator — autonomous research → generate → publish

One command takes a **goal prompt** to KDP drafts. The human only approves at 3 gates; everything
between gates runs unattended. The writing engine (phases 0/1–17 + assembler 18) is never modified —
this skill only chains skills.

## The goal prompt (single source of truth)

A **combined market + quality objective** authored once at the top and threaded **verbatim** into
every stage. Example:
> "A bingeable hockey-romance series for KU that ranks top-100 in its category; reader = 25-40
> contemporary-romance fans who loved Icebreaker; warm, spicy-not-dark; comps Hannah Grace, Elsie
> Silver; min advisory quality 8/10; 6 books; $4.99, KDP Select."

It picks/constrains the niche (research-niche), fills tone/audience/comps/tropes in the TOML
(consumed by the unchanged writer), and sets the quality-gate advisory minimum.

## Invocation

```
/kdp-orchestrator single "<goal prompt>"
/kdp-orchestrator series N "<goal prompt>"
/kdp-orchestrator --resume <state_dir>
```

## State — `orchestrator_state.json`

Written to the run dir; makes the whole pipeline resumable.
```json
{ "mode": "single|series", "goal": "<goal prompt verbatim>", "total_books": N,
  "stage": "research|generate|quality|cover|prepare|upload|done",
  "gates": { "g1_niche": false, "g2_manuscripts": false, "g3_publish": false },
  "books": [ { "title": null, "dir": null, "generated": false,
              "quality_passed": false, "cover_done": false, "uploaded": "none|draft|published" } ],
  "updated": "<iso8601>" }
```
On `--resume`, read it and continue from `stage` / the first incomplete book. Each sub-skill also
has its own resume file (`upload_state.json`, `cover_state.json`, head-author chapter resume), so a
death anywhere resumes at the finest available granularity.

## Pipeline

```
 research-niche ─[G1]─▶ head-author / batch-generate ─▶ quality-gate ─[G2]─▶ phase19 ─▶ cover-generate ─▶ kdp-prepare ─▶ kdp-upload ─[G3]─▶ draft/publish
```

1. **research-niche** (`/research-niche … --goal "<goal>"`) → fills the rich TOML + niche score +
   market brief. **GATE 1:** approve niche/spec (or pick different / edit). Series: approve concept once.
2. **Generate** — single: `/ccwriter:head-author <toml>`; series: `/ccwriter:batch-generate N <toml>`
   (variation directive + batch resume). Writers unchanged.
3. **quality-gate** (`/quality-gate <novel_dir>`) → deterministic checks + advisory score; auto-regen
   failing chapters (≤2) via `head-author --resume` + re-assemble. **GATE 2:** approve manuscripts.
   Series: one **batched** manuscript-quality review across all books.
4. **Listing assets** — `/ccwriter:phase-19` (blurb, keywords, categories, HTML description).
5. **cover-generate** (`/cover-generate <novel_dir>`) → text-free artwork + `overlay-cover-text.py`
   typography + cover-QA. Cover preview shown at G2/G3.
6. **kdp-prepare** → `kdp_upload/` package + (series) staggered release schedule.
7. **kdp-upload** (`/kdp-upload <novel_dir> --cover …`) → fills KDP, **GATE 3** greenlight. Default
   action = **save-as-draft**; publishes only on typed `"publish"`.
   **P0 survival guard (mandatory — see `docs/account-safety.md`):** before clicking Publish at GATE 3,
   run `python3 scripts/kdp_orchestrate.py publish-check`. If it exits non-zero (BLOCKED — ≤2/24h cap),
   **refuse to publish** and tell the user to wait. After a successful publish, run
   `python3 scripts/kdp_orchestrate.py record-publish "<title>"`. Always set **AI disclosure = Yes**
   (text + cover). One flagged title can terminate the whole account + withhold accrued royalties, so
   cadence + disclosure are non-negotiable survival controls, not preferences.

## Single vs. series

- **single:** one pass; 3 gates for the one title.
- **series (N books):** **3 series-level gates total** — (G1) approve the series concept/niche once;
  (G2) one batched review of all N manuscripts + covers; (G3) one publish/stagger-schedule approval.
  Generation uses `batch-generate` (unique title/plot per book, shared series bible). Per the velocity
  rules, drafts go up ≤2/day and publishing staggers 2–3 days between books (from kdp-prepare's
  stagger guide) for "new release" visibility.

## Resume & failure handling
- `--resume <state_dir>` continues from `orchestrator_state.json`.
- A stage that escalates (quality-gate chapter past regen cap, kdp-upload selector drift, cover UI
  drift) **stops at its gate / aborts loudly** — the orchestrator surfaces it and waits; it never
  silently skips or fabricates.
- research stale-data, zero-viable niche, mid-upload death: handled by the respective sub-skills and
  surfaced to the human (see their SKILL.md).

## What this skill never does
- Never auto-publishes (GATE 3 default = draft; publish only on typed "publish").
- Never edits prose or modifies phases 0/1–17 + 18 — it only chains skills and re-invokes the writer.
- Never advances a gate without explicit human approval.
