# ccwriter — Claude Code Novel Generator

ccwriter is a 22-phase AI novel generation pipeline that runs entirely inside Claude Code.
No Python. No external LLM clients. Claude Code IS the writing engine.

## Quick Start

```bash
# Generate a novel from a genre config
/ccwriter:head-author templates/example-genre.toml

# Run a single phase (e.g., just the planner)
/ccwriter:phase-01 templates/example-genre.toml

# Resume an interrupted novel
/ccwriter:head-author templates/example-genre.toml --resume novels/My_Novel/

# Batch generate 10 novels overnight
/ccwriter:batch-generate 10 templates/romance-genre.toml

# Batch from a prose concept
/ccwriter:batch-generate 5 "A dark enemies-to-lovers romance set in 1920s Paris"
```

## How It Works

Each phase is a Claude Code skill that:
1. Reads the genre config and any previous phase outputs
2. Generates its output using Claude as the LLM (no external API needed)
3. Writes the result to `novels/{Novel_Title}/`
4. Reports progress verbosely to the console

The **head-author** orchestrator runs all 22 phases in sequence. Resume works by
checking which output files already exist — completed phases are skipped.

## Pipeline — 22 Phases

```
Phase 0   Market Research    → 00_market_research.md    (skippable with --no-research)
Phase 1   Planner            → 01_plan.md               (title extracted; output dir renamed)
Phase 2   Brainstorm         → 02_preparation.md
Phase 3   Synopsis           → 03_synopsis.md
Phase 4   Pacing             → 04_pacing.md
Phase 5   Chapter Plan       → 05_chapter_plan.md
Phase 6   Humanize           → 06_humanize.md           (LLM self-critiques for cliches)
Phase 7   Revise             → 07_revised_chapter_plan.md
Phase 8   Characters         → 08_characters.md
Phase 9   Style Guide        → 09_style_guide.md
Phase 10  Story Bible        → 10_story_bible.md
Phase 11  Three-Act          → 11_three_act_structure.md
Phase 12  Conflict           → 12_conflict_obstacles.md
Phase 13  Plot Twists        → 13_plot_twists.md
Phase 14  Pacing Review      → 14_pacing_analysis.md
Phase 15  Scene Breakdown    → 15_scene_breakdown.md
Phase 16  Enhanced Bible     → 16_enhanced_story_bible.md
Phase 17  Writer x N         → chapter01.md ... chapterNN.md  (5 sub-phases each)
Phase 18  Assembler          → complete_novel.docx       (no LLM — pandoc conversion)
Phase 19  Publishing         → 19_kdp_assets.md
Phase 20  Beta Reader        → 20_beta_feedback.md       (non-fatal)
Phase 21  Structural Rev.    → 21_structural_notes.md    (non-fatal)
Phase 22  Targeted Rev.      → 22_revision_log.md        (non-fatal)
```

## Writer Phase — 5-Phase Layered Writing

The most complex phase. Each chapter runs 5 sequential generation passes:

1. **Physical** — sensory detail only (no dialogue, no thought)
2. **Internal** — viewpoint character's inner world layered onto physical
3. **Dialogue** — spoken exchanges only
4. **First Draft** — synthesises all three layers into full prose
5. **Revision** — polish pass; strips LLM-tells; optionally mimics author_style

Intermediate files: `chapter{N:02d}_1_physical.md` through `_4_draft.md`.
Final output: `chapter{N:02d}.md`.

## Genre Config — TOML Format

Two formats supported:

**Simple** (flat):
```toml
name = "Cozy Mystery"
description = "A small-town murder mystery"
tone = "warm, witty, suspenseful"
themes = ["community", "justice", "secrets"]
n_chapters = 20
chapter_length = 3000
target_audience = "adult mystery readers"
author_style = "Agatha Christie"
```

**Rich** (nested — for detailed commercial specs):
```toml
[metadata]
name = "Dark Romance"
tone = "intense, atmospheric"

[emotional_design]
core_tension = "forbidden desire vs. self-preservation"
# ... extensive nested configuration
```

Rich configs must include a `[metadata]` section with the standard fields (`name`,
`n_chapters`, `chapter_length`, etc.) for the head-author to parse. The full rich
config is also serialized and injected into every phase prompt as context.

## Model Preferences

ccwriter uses Claude Code's own model. For best results:
- Use **Claude Opus 4.6** for writing phases (17) — highest creative quality
- Use **Claude Sonnet 4.6** for planning phases — fast and capable
- The head-author orchestrator handles model suggestions per phase

For multi-model support, the head-author can spawn subagents with specific model overrides.

## DOCX Assembly (Phase 18)

Uses **pandoc** to convert assembled markdown to KDP-ready DOCX:
- Heading 1 for book title only; Heading 2 for chapter titles (triggers KDP TOC)
- Heading 2 for section breaks within chapters
- Italic text preserved for emphasis
- First-line indent 0.2" (5mm) on body paragraphs
- No forced font size, color, or alignment on body text
- Page breaks between chapters
- Front matter: title page, copyright page
- No in-line page numbers
- Scene breaks as centered ornamental diamonds (`&#x2726; &ensp; &#x2726; &ensp; &#x2726;`)

KDP upload format: `.docx` (reflowable). The DOCX must pass KDP's quality checks.

If pandoc is not installed: `brew install pandoc` (macOS) or `apt install pandoc` (Linux).

## Publishing Assets (Phase 19)

Generates:
- **3 cover image prompts** — detailed image generation prompts for Midjourney/DALL-E
  (KDP ebook spec: 1600x2560 px, 10:16 aspect ratio)
- **1 high-converting blurb** — 150-250 words, third-person present tense
- **7 SEO keywords** — long-tail trope-stacking phrases
- **Title + Subtitle** — optimized for KDP search
- **Author name** — pen name suggestion fitting the genre
- **Amazon HTML description** — KDP-valid HTML (b, em, br tags only)
- **Ad copy pack** — Amazon AMS, BookBub, Facebook/Instagram variants
- **Social media kit** — Instagram, X/Twitter, TikTok, email newsletter

## Prompt Quality Standards

These directives are embedded in every writing-phase skill:

**Always:**
- Prefer concrete technical specificity over emotional generality
- Ground speculative elements in real mechanisms, objects, and sensory detail
- Avoid sentimentality and unearned epiphany
- Trust the reader to infer theme from action; do not editorialize
- Enter scenes late, leave early — every paragraph earns its place

**Never:**
- "It was not X, but Y" (antithesis bloat)
- "No X, no Y — just Z" (list-negation)
- Describe what is absent instead of what is present

**Revision passes must name specific techniques:**
- Pass 1 (Developmental): arc, pacing, stakes, subplot resolution, plot holes
- Pass 2 (Scene-level): scene purpose, POV consistency, conflict per scene
- Pass 3 (Line-level): filter words, passive voice, adverb pruning, show/tell
- Pass 4 (Polish): read-aloud rhythm, sentence variety, dialogue distinction, hooks

**Dialogue must specify subtext techniques:**
- Deflection, Contradiction, Silence, Interruption, Non-sequitur
- Default to "said" as tag; use action beats instead when possible
- Never: "exclaimed", "retorted", "queried", "said softly"

## LLM-Tell Blacklist

These words/phrases must never appear in novel output:
"seamlessly", "tapestry", "delve", "navigate", "pivotal", "furthermore",
"moreover", "in conclusion", "it is worth noting", "significantly",
"embark", "paradigm", "synergy", "facilitate", "utilize", "landscape" (metaphor),
"journey" (metaphor), "nuanced", "multifaceted", "myriad", "plethora"

## Scene-Sequel Structure

Injected into Chapter Plan and Scene Breakdown phases:
- Scene = Goal → Conflict → Disaster (outcome worse than expected)
- Sequel = Reaction → Dilemma → Decision (sets up next scene's goal)
- Every chapter contains at least one complete Scene-Sequel cycle

## File Organization

```
ccwriter/
├── CLAUDE.md              ← you are here
├── docs/                  ← series design specs and planning docs
├── skills/                ← one SKILL.md per phase + orchestrator
│   ├── head-author/
│   ├── phase-00-market-research/
│   ├── phase-01-planner/
│   │   └── SKILL.md
│   ├── ... (phases 02-22)
│   ├── phase-22-targeted-revision/
│   ├── batch-generate/
│   ├── kdp-prepare/
│   └── kdp-upload/
├── references/            ← shared reference docs loaded by skills
│   ├── kdp-formatting.md
│   ├── prompt-quality.md
│   ├── subtext-techniques.md
│   ├── revision-passes.md
│   └── scene-sequel.md
├── templates/             ← example genre configs
│   ├── example-genre.toml
│   └── romance-genre.toml
├── scripts/               ← utility scripts
│   └── assemble-docx.sh
└── novels/                ← generated output
```

## Resume Support

Resume works by checking the output directory for existing files:
- If `01_plan.md` exists → skip Phase 1
- If `chapter05.md` exists → skip writing Chapter 5
- The head-author checks each phase's output file before running it

To force re-run a phase, delete its output file and run the orchestrator again.

## Batch Generation

Generate multiple novels from one genre config:
```
/ccwriter:batch-generate 10 templates/romance-genre.toml
```

Each novel gets unique characters, plot, title, and KDP assets. Output structure:
```
novels/batch_romance_20260326/
├── 01_Breaking_Brief/
│   ├── complete_novel.docx
│   └── 19_kdp_assets.md
├── 02_Opposing_Counsel/
├── ...
└── batch_summary.md
```

Features:
- **Uniqueness enforced**: each novel tracks previous titles to avoid duplication
- **Resume**: interrupted batches resume from the next incomplete novel
- **Parallel option**: spawn up to 3 concurrent novel agents for speed
- **Batch summary**: word counts, titles, keywords for all novels in one table

Maximum recommended batch: 20 novels per run.

## KDP Publishing Workflow

Two-step publishing with mandatory approval gates:

### Step 1: Prepare Upload Package
```
/ccwriter:kdp-prepare novels/My_Novel/
/ccwriter:kdp-prepare novels/batch_romance_20260326/    # all novels in batch
```

Generates `kdp_upload/` per novel with:
- `01_book_details.txt` — every KDP form field pre-formatted for copy-paste
- `03_cover_prompts.txt` — 3 image generation prompts (1600x2560px)
- `04_pricing_notes.txt` — pricing strategy recommendations
- `05_greenlight_checklist.md` — review checklist before publishing

For batches, also generates a staggered release schedule (2-3 days between books
for maximum "new release" visibility).

### Step 2: Browser-Assisted Upload (Optional)
```
/ccwriter:kdp-upload novels/My_Novel/ --cover ~/covers/cover.jpg
```

Uses Chrome DevTools to fill KDP forms automatically:
1. Fills Book Details (title, author, blurb, keywords, categories)
2. Uploads manuscript DOCX
3. Uploads cover image
4. Sets pricing

**Greenlight gate**: Stops before publishing and shows a full summary.
You type `"publish"`, `"draft"`, or `"cancel"` for each book.
Nothing goes live without your explicit approval.

For batch uploads, each novel gets its own greenlight gate.

## Running Individual Phases

Each phase can be run standalone. Read the corresponding SKILL.md for details.
The skill will tell you what input files it needs (from previous phases) and what it outputs.

## Output Verbose Mode

All phases print verbose progress to the Claude Code console:
- Phase name and number
- What input files are being read
- Generation progress
- Word counts
- Quality metrics (after writing phase)
- Time elapsed per phase
