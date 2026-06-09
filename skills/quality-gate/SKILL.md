---
name: quality-gate
description: Objective, deterministic quality gate that runs after Phase 18 (assembler) and before Phase 19 (publishing). Scores a finished novel on hard scriptable checks, auto-regenerates failing chapters via head-author --resume (bounded), and presents GATE 2 for human approval. Never edits prose — it only reads outputs and re-invokes the writer + assembler.
---

# Quality Gate — Phase 18.5 (deterministic-first)

Runs **after Phase 18 (assembler)**, **before Phase 19 (publishing assets)**. This is the
objective pass/fail the pipeline was missing — phases 20/22 only produce letter grades and prose
feedback, which never gated anything.

**Hard rule:** this skill NEVER edits prose. It reads outputs, and on failure re-invokes the
existing writer (`head-author --resume`) and the assembler. The writing agents (phases 0/1–17 + 18)
are out of scope to change.

## Invocation

```
/quality-gate novels/My_Novel/
/quality-gate novels/My_Novel/ --tolerance 0.15 --max-regen 2
```

## Inputs

- `novels/{Novel}/complete_novel.md`, `chapter{NN}.md`, `04_pacing.md` (word targets table).
- The **goal prompt** (combined market + quality objective, from the orchestrator): supplies the
  target reader, tone, comps, and the **minimum advisory score** to report against. Quality targets
  (per-chapter word counts) come from `04_pacing.md`; fallback `metadata.chapter_length`.

## Step 1 — Deterministic checks (the actual gate)

Run the deterministic scorer. It is the source of truth for pass/fail:

```bash
python3 scripts/quality_gate.py novels/{Novel}/ --json
```

Hard checks (all must pass):
1. **Word count** — each chapter within **±15%** of its `04_pacing.md` target.
2. **LLM-tell blacklist = 0** — hard terms from `references/prompt-quality.md`
   (soft/context terms like "journey"/"landscape" are reported as warnings, not failures).
3. **Antithesis / list-negation = 0** — "not X, but Y" and "No X, no Y — just Z".
4. **Completeness** — exactly `n_chapters` files, none truncated mid-sentence.

The script's `failing_chapters` array is the regen work-list. Exit 0 = PASS, 1 = FAIL.

## Step 2 — Advisory LLM score (non-gating)

Read 2–3 representative chapters and map the Phase-20 persona rubric to a single **0–10** read,
framed against the goal prompt's target reader and comps. **This score is advisory only** — it is
shown in the GATE 2 report and logged, but it NEVER passes a novel the deterministic checks failed,
and never fails one they passed. Report it alongside the goal prompt's stated minimum, e.g.
`advisory 7/10 (goal min 8)`.

## Step 3 — Bounded auto-regen loop (on deterministic FAIL)

For each chapter in `failing_chapters`, up to **--max-regen (default 2)** attempts:

1. **Move aside** (do not delete) the chapter and its intermediates so `--resume` regenerates them:
   ```bash
   mkdir -p novels/{Novel}/_regen_attic
   mv novels/{Novel}/chapter{NN}.md            novels/{Novel}/_regen_attic/chapter{NN}.r{attempt}.md
   mv novels/{Novel}/chapter{NN}_?_*.md         novels/{Novel}/_regen_attic/ 2>/dev/null || true
   ```
2. **Regenerate with a length directive** (A1 decision — the regen path is allowed to steer the
   writer toward the target; the writer's prose logic is otherwise untouched). Because the writer
   reproducibly underproduces (~40% short), a bare `--resume` would just reproduce the shortfall, so
   the regen MUST pass an explicit per-chapter directive that head-author injects into the phase-17
   context for the regenerated chapter only:
   > `REGEN DIRECTIVE — chapter {NN}: target {target} words (current {words}, ~{pct}% short). Expand
   >  existing scene beats with more sensory/interior detail and dialogue; do NOT pad, repeat, or add
   >  new plot. Also fix: {blacklist/antithesis/truncation reasons}.`
   Invoke `/ccwriter:head-author {config} --resume novels/{Novel}/` (it rewrites only the moved-aside
   chapters; the directive rides along for those chapters). **Word-count stays a HARD gate** — with
   the directive, regen can actually move length, so it is not demoted to a warning.
3. **Re-run the assembler** so `complete_novel.md/.docx` reflect the new chapters:
   `/ccwriter:phase-18 {config} novels/{Novel}/` (or `scripts/assemble-docx.sh`).
4. **Re-score** with `scripts/quality_gate.py`. Drop chapters that now pass.

Stop when the novel passes or a chapter has used its `--max-regen` attempts. Any chapter still
failing after the cap → **escalate to GATE 2** (do not loop further; this prevents the infinite-regen
failure mode). If the deterministic scorer output is malformed/unparseable, treat as **fail-to-human**
— never auto-pass.

## Step 4 — GATE 2 (human approval)

Present a compact report and stop for approval:

```
QUALITY GATE — {Novel}
VERDICT: PASS | FAIL (after N regen attempts)
  word count    | OK/FAIL  (chapters off-target: …)
  blacklist     | OK/FAIL  (hits: …)
  antithesis    | OK/FAIL
  completeness  | OK/FAIL  (NN/NN chapters)
Advisory score: X/10  (goal min: Y)
Cover preview:  {covers/cover_final.jpg if present}
Escalated chapters (still failing after cap): …
```

User options at GATE 2:
- **proceed** → continue to Phase 19 / listing.
- **regen <chapters>** → run another bounded pass on named chapters.
- **accept-with-notes** → proceed despite a soft/advisory concern (logged).
- **stop** → halt the orchestrator at this title.

For a **series**, the orchestrator batches GATE 2: run this skill per book, collect all reports, and
present one batched manuscript-quality review (per the 3-series-gate decision).

## Output files
- `novels/{Novel}/quality_report.json` — deterministic + advisory results (the orchestrator reads this).
- `novels/{Novel}/_regen_attic/` — superseded chapter versions (audit trail; safe to delete).

## What this skill never does
- Never edits prose directly. Only `head-author --resume` regenerates; only the assembler re-builds.
- Never lets the advisory LLM score override a deterministic hard fail.
- Never loops a chapter past `--max-regen` — it escalates to the human instead.
