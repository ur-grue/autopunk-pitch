# Changelog

All notable changes to ccwriter are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Every ship updates this file;
roadmap context lives in `ROADMAP.md`.

## [Unreleased]
### Fixed (D2 — writer under-length)
- `skills/phase-17-writer/SKILL.md` — Sub-Phase 4 (Draft synthesis) no longer treats the three
  sparse layers as a length ceiling. Reframed "not addition": the draft may and should deepen
  existing beats (sensory/interior/dialogue subtext) to reach `{chapter_length}`; "no addition"
  now applies only to plot/scenes, not depth. Word target made binding (±10%), and Sub-Phase 5
  (Revision) gained a length-preservation guard so polish can't cut the chapter back under target.
  Verified on the monster-romance ch1 test: draft went 1053 → 3091 words (32% → 93% of 3333), and
  `quality_gate.py` flips FAIL → PASS on all four checks.

### Added (Roadmap P0 — Survive & isolate)
- `docs/account-safety.md` — blast-radius model (the account, not the book, is the risk unit;
  one account / few pen names / low volume / high quality + disclosure), AI-disclosure posture,
  clean-read-profile rules, termination-pattern "never do" list, per-title pre-publish checklist.
- **Cadence enforcement** in `scripts/kdp_orchestrate.py`: a publish ledger + `publish-check`
  (refuses the 3rd publish in any 24h; optional stagger gap) and `record-publish`. Wired into the
  orchestrator's GATE 3 (publish-check must pass; AI disclosure = Yes). 2 unit tests.

### Planned (next, per ROADMAP.md M1)
- P1 mailing-list capture (back-matter CTA) + wide-distribution path (Draft2Digital/Kobo/Apple/Google).
- P2 AI-detection de-patterning gate; read-through reframe (length + chapter-end hook scoring).

## [0.2.0] - 2026-06-09
The autonomous KDP layer — ccwriter goes from "novel generator" to "research → generate →
quality-gate → cover → list → upload" pipeline with 3 human approval gates. Built, eng-reviewed,
and live-verified (a real KDP draft with a generated cover).

### Added
- `skills/research-niche/` + `scripts/niche_score.py` — niche-research stage: market-backed TOML
  filler with demand-vs-competition scoring, absolute viability floor, and a zero-viable guard.
- `skills/quality-gate/` + `scripts/quality_gate.py` — deterministic quality gate (per-chapter
  word-count ±15%, LLM-tell blacklist = 0, antithesis/list-negation = 0, completeness/no-truncation)
  with a bounded regen loop; LLM-judge score advisory only.
- `skills/kdp-orchestrator/` + `scripts/kdp_orchestrate.py` — the autonomous spine: single-title and
  series modes, 3 approval gates, resumable `orchestrator_state.json`; never auto-publishes.
- `skills/cover-generate/` + `scripts/generate_cover_api.py` — cover generation via OpenAI
  `gpt-image-1` (full illustrated cover with baked-in title, semi-realistic style); key from
  env/`.openai_key`, never printed.
- 13 unit tests across the deterministic cores (quality-gate, niche scorer, orchestrator spine).
- `ROADMAP.md` + this `CHANGELOG.md`.

### Changed
- `skills/kdp-upload/` — ported from (absent) Chrome DevTools MCP to gstack `browse`; verified-live
  KDP `data-{field}` selectors; preflight self-check; `upload_state.json` resume; velocity discipline
  (≤2/day, 5-min cooldown, 48h bursts); greenlight defaults to save-as-draft (publish only on typed
  "publish").
- `skills/cover-generate/` — switched the primary cover path to gpt-image-1 with baked-in typography
  (semi-realistic, on-2026-trend); ChatGPT-web path demoted to documented-unreliable fallback.
- `CLAUDE.md` — added the Health Stack; gitignored `.venv`, `.openai_key`, `__pycache__`.

### Fixed
- Quality-gate antithesis check anchored to a copula (cut false-positives on ordinary prose).
- Niche-scorer viability floor made absolute (`opportunity_raw`) so the zero-viable guard actually fires.

### Verified (live)
- KDP draft upload (manuscript + cover) via `browse`/CDP — stops at draft, never publishes.
- Orchestrator spine end-to-end with gates + resume.
- A gpt-image-1 illustrated cover placed on the real "Corner Office Crush" draft.

### Known issues (tracked in ROADMAP.md)
- Writer ships ~40% under word target (read-through/length — D2).
- KDP *cover* uploader resists `browse` automation → manual drag-drop fallback.
- ChatGPT-web image-gen not reliably automatable (use `gpt-image-1`).
- Niche research depends on fragile Amazon scraping (deferred; manual niche pick for now).

## [0.1.0] - 2026-04-03
Initial ccwriter: a 22-phase AI novel-generation pipeline that runs entirely inside Claude Code
(5-layer layered writer, pandoc DOCX assembly, KDP asset/prep skills), README, niche research, cover
scripts, and 20 niche series TOML configs.
