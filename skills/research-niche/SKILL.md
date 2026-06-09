---
name: research-niche
description: Stage 1 of the autonomous pipeline. Turns a goal prompt (market + quality objective) into a market-backed, fully populated rich genre TOML that head-author consumes unchanged. Scrapes Amazon for live signal (gstack browse), falls back to docs/niche-research.md, scores demand-vs-competition, and presents GATE 1 for approval. Research and generation stay decoupled by the config file — this skill only fills the TOML; it never writes prose.
---

# Research-Niche — automated rich-TOML filler (GATE 1)

Stage 1 of `kdp-orchestrator`. Produces the niche spec the rest of the pipeline runs on. The
writing engine never sees "research data" — it sees a finished, human-approved TOML.

## The goal prompt (threaded from the orchestrator)

A **combined market + quality objective**, e.g.:
> "A bingeable hockey romance series for KU that ranks top-100 in its category; target reader =
> 25-40 contemporary-romance readers who loved Icebreaker; warm, spicy-but-not-dark tone; comps
> Hannah Grace, Elsie Silver; min advisory quality 8/10."

This goal is the single source of truth: it picks/constrains the niche, fills the TOML's tone /
audience / comps / tropes, and sets the quality-gate's advisory minimum. Carry it forward verbatim.

## Invocation

```
/research-niche "find a niche in <genre>" --goal "<goal prompt>"
/research-niche "<named niche>"            --goal "<goal prompt>"   [--series N]
```

## Step 1 — Market read (live scrape primary, corpus fallback)

**If gstack `/scrape` + `browse` is available** (local browser session): scrape Amazon for the
candidate niche(s) into the same record shape as `docs/niche-research.md`:
- category bestseller ranks + also-boughts (demand),
- top keywords / tropes mined from top-seller titles and blurbs,
- price points, review count / velocity, KU ("Read for free") presence.
Query by **role/aria**, not localized label strings. **Cache** the last-good scrape JSON to
`docs/niche-cache/{niche_slug}.json`.

**Loud-degrade:** if scraping is blocked or the DOM has drifted, do NOT invent numbers. Fall back to
`docs/niche-research.md`, set `stale_data: true` in the brief, and tell the user at GATE 1 that the
spec is built on cached/corpus data, not a fresh scrape.

**Headless / no-browser:** corpus-only is the supported fallback path (and how this skill is tested).

## Step 2 — Score (demand vs competition)

```bash
# rank to find the best fit for the goal's genre:
python3 scripts/niche_score.py docs/niche-research.md --top 10
# or score a named niche:
python3 scripts/niche_score.py docs/niche-research.md --niche "<niche>" --json
```
Use `--min-score` to enforce a viability floor. **Zero-viable handling:** if nothing clears the
floor the scorer reports the closest N and exits 3 — surface those to the user, **never silently
pick the least-bad niche.**

## Step 3 — Emit the rich genre TOML

Write a TOML mirroring the committed schema (`templates/blackwell_book_1.toml`,
`templates/intern_workplace_romance.toml`) so head-author's 3-format parser consumes it unchanged.
Populate from the market read + goal prompt:

- `[metadata]` — name, genre, sub_genre, tone (from goal), themes, `n_chapters`, `chapter_length`
  (from the niche's ideal book length ÷ chapters), target_audience (from goal), author_style / pen name.
- `[genre]`, `[setting]`, `[target_audience]` — reader profile + comps from the goal prompt.
- `[emotional_design]`, `[romantic_dynamic]` — core tension, HEA style, from goal + niche tropes.
- `[series]` — name / author / book_number / total_books when `--series N`.
- `[cover_design]` — palette / typography / series_element from `references/cover-design-guide.md`
  matched to the niche (consumed later by cover-generate; falls back to `[series]` if omitted).
- `[marketing]` — BookTok hooks + 7 keyword phrases from scraped/known top tropes.
- `[kdp]` — categories (the niche's BISAC), price (from scraped price points), `kdp_select`,
  `ai_disclosure`.

Tropes, comps, and keywords come from the **market read**, not invented. Also write:
- `{niche}_market_brief.md` — the data-backed brief (with `stale_data` flag if applicable),
- `{niche}_niche_score.json` — the scorer output.

## Step 4 — GATE 1 (human approval)

Present: niche score + components, the filled TOML (path), the market brief, and any `stale_data`
flag. Options:
- **approve** → hand the TOML to the orchestrator for generation.
- **different niche** → re-rank / pick another, regenerate the TOML.
- **edit** → adjust goal prompt or specific TOML fields, regenerate.

Nothing proceeds to generation without approval here.

## Output files
- `templates/{niche_slug}.toml` — the approved niche spec (head-author input).
- `docs/niche-cache/{niche_slug}.json` — last-good scrape (when live).
- `{niche}_market_brief.md`, `{niche}_niche_score.json`.

## What this skill never does
- Never fabricates market numbers — degrades loudly to cached/corpus data instead.
- Never auto-selects a niche below the viability floor — surfaces the closest and asks.
- Never writes prose — it only fills the config the (unchanged) writer consumes.
