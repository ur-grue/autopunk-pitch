# ccwriter Session Handoff — 2026-04-03

## What Was Accomplished This Session

### QA Fixes (committed + pushed to GitHub)
- Unified scene break format (ornamental diamonds) across all files
- Fixed assemble-docx.sh page breaks (`---` to `\newpage`)
- Fixed Phase 18 contradictory H1/H2 heading guidance
- Made Phase 17 writer directives genre-agnostic (was romance-hardcoded)
- Made Phase 11 three-act structure genre-agnostic
- Added `[metadata]` shims to all 9 rich TOML config templates
- Fixed intern_workplace_romance.toml chapter_count type (string to integer)
- Updated head-author config parser to handle 3 template formats
- Synced CLAUDE.md docs (4 revision passes, docs/ directory, scene breaks)
- Added README.md to GitHub repo

### Blackwell Interns Series — Current State

| # | Title | Chapters | DOCX | Cover | KDP Assets | Status |
|---|-------|----------|------|-------|------------|--------|
| 1 | Corner Office Crush | 20/20 | YES | placeholder | NO | Needs Phase 19 + real cover |
| 2 | Styled by You | 20/20 | YES | placeholder | NO | Needs Phase 19 + real cover |
| 3 | Front Page Feelings | 20/20 | YES | placeholder | NO | Needs Phase 19 + real cover |
| 4 | Off the Record | 20/20 | YES | placeholder | YES | Needs real cover |
| 5 | Developed in the Dark | 20/20 | YES | placeholder | YES | Needs real cover |
| 6 | Event Horizon | 20/20 | YES | placeholder | NO | Needs Phase 19 + real cover |
| 7 | The Final Draft | 20/20 | YES | placeholder | YES | Needs real cover |

All novels are at: `novels/batch_blackwell_interns_20260326/`

### Tools Installed
- **pandoc** 3.9 via pypandoc_binary (path: `/Users/snu/Library/Python/3.9/lib/python/site-packages/pypandoc/files/pandoc`)
- **Pillow** 11.3.0 for cover image processing
- **Git** configured: user=ur-grue, email=sebastian.nuss@me.com

### Cover Generation Pipeline (proven, not yet automated as skill)
1. Prompt ChatGPT via Chrome automation with DALL-E scene description
2. Wait ~30-60 seconds for generation
3. Download via JavaScript injection (`a.click()` on img.src)
4. Resize to 1600x2560 + overlay title/author/series with `scripts/overlay-cover-text.py`
5. Save as KDP-ready JPEG

Scripts created:
- `scripts/generate-cover.py` — Pillow-only gradient covers (placeholder)
- `scripts/overlay-cover-text.py` — overlays title/author on any artwork image

### Niche Research
A background agent was researching lucrative Kindle niches. Results may be in:
`/private/tmp/claude-501/-Users-snu-Desktop-autopunk-ccwriter/6228815f-db30-4c76-b212-25531166f94f/tasks/a6c9dc4eb18b40a3a.output`

**WARNING**: This is a temp file that may not survive reboot. If the agent completed, save results to `docs/niche-research.md` before closing this session.

---

## Recommended Session Breakdown

### Session 1: Finish Blackwell (30 min)
1. Run Phase 19 (KDP assets) for Books 1, 2, 3, 6
2. Generate 7 real covers via ChatGPT (one at a time, ~5 min each)
3. Overlay text with `scripts/overlay-cover-text.py`
4. Run `/ccwriter:kdp-prepare` on all 7 novels

### Session 2: KDP Upload Blackwell (45 min)
1. Open Chrome, log into KDP
2. Run `/ccwriter:kdp-upload` for each of the 7 novels
3. Save as drafts, review, publish

### Session 3: Niche Research + Series Design (1 hour)
1. Research top 20 Kindle niches (if not already done)
2. Design 20 series (genre, tropes, book count, pen name per series)
3. Write TOML configs for all 20 series (140+ books)
4. Save to `templates/` directory

### Session 4: Batch Generation — Tranche 1 (long-running)
1. Pick first 5 series
2. Run batch-generate for each series (5-7 books per series = 25-35 novels)
3. Use parallel agents (3 concurrent) for speed
4. Monitor, resume if interrupted

### Session 5+: Repeat for remaining series
- Each session generates 25-35 novels
- 4 tranches of 5 series = 20 series = ~140 novels

### Session N: Scale to 3000
- After validating revenue from first 140 titles
- Expand to more niches and series
- Automate the full pipeline including cover gen + KDP upload

---

## Cover Generation Prompts (for Blackwell Series)

Use these in ChatGPT. Always end with: "CRITICAL: NO text, NO letters, NO words, NO typography anywhere."

### Book 1: Corner Office Crush
Scene: Stylish young woman from behind at floor-to-ceiling windows of a luxurious Manhattan corner office at twilight. NYC skyline below. Fitted blazer. Glass desk with magazine layouts and coffee cup. Warm amber desk lamp vs cool blue-violet city dusk. Contemporary romance mood.

### Book 2: Styled by You
Scene: Fashion design studio at golden hour. Mannequins draped in half-finished dresses. A young woman sketching at a drafting table, fabric swatches scattered. Through tall windows, NYC Fashion Week tents visible. Warm creative chaos. Pins and measuring tape. Intimate and aspirational.

### Book 3: Front Page Feelings
Scene: Laptop screen glowing in a dark office showing a viral social media post. A woman's hands on the keyboard, phone buzzing with notifications beside her. NYC at night through the window. The glow of the screen illuminates her face from below. Digital tension, modern romance.

### Book 4: Off the Record
Scene: Two wine glasses on a rooftop bar table, NYC skyline behind them. One glass has lipstick on the rim. A phone face-down on the table. City lights reflect in the dark wine. The mood is secrecy, intimacy, danger. Night, warm ambient lighting.

### Book 5: Developed in the Dark
Scene: A photography darkroom bathed in red safelight. Photographs hanging from clips on a line, dripping developer fluid. A camera sits on the counter. The silhouette of two people standing close together. Intimate, moody, artistic. Red and shadow dominate.

### Book 6: Event Horizon
Scene: A grand hotel ballroom being set up for a gala event. Crystal chandeliers, round tables with white linens, a woman directing caterers. Floor-to-ceiling windows show Manhattan at dusk. Gold and white color scheme. Elegant, buzzing with anticipation and unresolved tension.

### Book 7: The Final Draft
Scene: A massive glass-walled boardroom at the top of a skyscraper. An empty executive chair at the head of a long table. Through the windows, all of Manhattan stretches out at sunset — golden hour. On the table, a single document and a pen. The feeling is power, finality, and new beginnings.

---

## Key Config / Env Notes
- pandoc PATH must be set: `export PATH="/Users/snu/Library/Python/3.9/lib/python/site-packages/pypandoc/files:$PATH"`
- Git remote: `https://github.com/ur-grue/ccwriter.git` (renamed from autopunk-pitch)
- KDP interface is in German (account settings)
- KDP selectors documented in `skills/kdp-upload/SKILL.md` (tested March 2026)
