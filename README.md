<p align="center">
  <img src="https://img.shields.io/badge/engine-Claude%20Code-7C3AED?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQyIDAtOC0zLjU4LTgtOHMzLjU4LTggOC04IDggMy41OCA4IDgtMy41OCA4LTggNHoiLz48L3N2Zz4=" alt="Claude Code">
  <img src="https://img.shields.io/badge/output-KDP%20Ready-FF9900?style=for-the-badge&logo=amazon&logoColor=white" alt="KDP Ready">
  <img src="https://img.shields.io/badge/phases-22-blue?style=for-the-badge" alt="22 Phases">
  <img src="https://img.shields.io/badge/genre-any-green?style=for-the-badge" alt="Any Genre">
</p>

# ccwriter

**A 22-phase AI novel generation pipeline that runs entirely inside Claude Code.**

No Python. No external LLM clients. No API keys to manage. Claude Code *is* the writing engine. Point it at a genre config, walk away, come back to a KDP-ready manuscript with marketing assets.

---

## What It Does

ccwriter takes a genre specification (TOML file or plain-text concept) and produces:

- A **complete novel** (50,000-80,000 words) as KDP-ready `.docx`
- **3 AI cover image prompts** (1600x2560px, Midjourney/DALL-E ready)
- A **high-converting blurb**, **7 SEO keywords**, and **Amazon HTML description**
- **Ad copy** for Amazon AMS, BookBub, Facebook/Instagram
- A **social media kit** for BookTok, Instagram, X/Twitter
- **Beta reader feedback**, **structural notes**, and **revision logs**

Or batch-generate an entire series overnight.

---

## Quick Start

```bash
# Generate a single novel
/ccwriter:head-author templates/example-genre.toml

# Generate from a prose concept
/ccwriter:head-author "A cozy mystery set in a haunted bookshop in Cornwall"

# Batch generate a 7-book series
/ccwriter:batch-generate 7 templates/blackwell_book_1.toml

# Resume an interrupted run
/ccwriter:head-author templates/romance-genre.toml --resume novels/My_Novel/
```

### Prerequisites

- **Claude Code** (CLI, desktop app, or IDE extension)
- **Claude Opus 4.6** recommended for writing phases (Sonnet works for planning)
- **pandoc** for DOCX assembly: `brew install pandoc` (macOS) or `apt install pandoc` (Linux)

---

## The Pipeline

Every novel passes through 22 sequential phases. Each phase is a self-contained Claude Code skill that reads upstream outputs and generates its own artifact.

```
                         PLANNING                              PREPARATION
    ┌─────────────────────────────────────┐   ┌──────────────────────────────────────────┐
    │                                     │   │                                          │
    │  00  Market Research                │   │  06  Humanize (cliche audit)             │
    │  01  Planner (title, concept)       │   │  07  Revise Chapter Plan                 │
    │  02  Brainstorm                     │   │  08  Deep Character Profiles              │
    │  03  Synopsis                       │   │  09  Style Guide                          │
    │  04  Pacing                         │   │  10  Story Bible                          │
    │  05  Chapter Plan                   │   │  11  Three-Act Structure                  │
    │                                     │   │  12  Conflict & Obstacles                 │
    └─────────────────────────────────────┘   │  13  Plot Twists                          │
                                              │  14  Pacing Review                        │
                                              │  15  Scene Breakdown                      │
                                              │  16  Enhanced Story Bible                 │
                                              └──────────────────────────────────────────┘

                          WRITING                                FINISHING
    ┌─────────────────────────────────────┐   ┌──────────────────────────────────────────┐
    │                                     │   │                                          │
    │  17  Writer (5 sub-phases/chapter)  │   │  18  DOCX Assembler (pandoc)             │
    │      x N chapters                   │   │  19  Publishing Assets (KDP)              │
    │                                     │   │  20  Beta Reader Feedback                 │
    │      Physical ──► Internal          │   │  21  Structural Revision Notes            │
    │          │            │             │   │  22  Targeted Revision Log                │
    │      Dialogue ──► First Draft       │   │                                          │
    │                    │                │   └──────────────────────────────────────────┘
    │                 Revision            │
    │                                     │
    └─────────────────────────────────────┘
```

### Phase Details

| # | Phase | Output | Notes |
|---|-------|--------|-------|
| 0 | Market Research | `00_market_research.md` | Skippable with `--no-research` |
| 1 | Planner | `01_plan.md` | Extracts title; renames output directory |
| 2 | Brainstorm | `02_preparation.md` | Characters, plot, world-building brainstorm |
| 3 | Synopsis | `03_synopsis.md` | 1-2 page synopsis with full arc |
| 4 | Pacing | `04_pacing.md` | Act structure, turning points, climax beats |
| 5 | Chapter Plan | `05_chapter_plan.md` | Beat-by-beat breakdown per chapter |
| 6 | Humanize | `06_humanize.md` | LLM self-critiques for worn tropes and cliches |
| 7 | Revise | `07_revised_chapter_plan.md` | Strengthens unique elements from humanize pass |
| 8 | Characters | `08_characters.md` | Wound, want, need, arc, voice per character |
| 9 | Style Guide | `09_style_guide.md` | Voice, tone, prose rules, recurring imagery |
| 10 | Story Bible | `10_story_bible.md` | Locations, timelines, side characters, objects |
| 11 | Three-Act | `11_three_act_structure.md` | Chapter ranges, beats, emotional shifts per act |
| 12 | Conflict | `12_conflict_obstacles.md` | Obstacles per chapter, stakes escalation |
| 13 | Plot Twists | `13_plot_twists.md` | Surprise reversals, reader expectations subverted |
| 14 | Pacing Review | `14_pacing_analysis.md` | Tension curve analysis, dead zone identification |
| 15 | Scene Breakdown | `15_scene_breakdown.md` | Scene-Sequel structure per chapter |
| 16 | Enhanced Bible | `16_enhanced_story_bible.md` | Synthesizes all prep phases for the writer |
| 17 | **Writer** | `chapter01.md` ... `chapterNN.md` | **5 sub-phases per chapter** (see below) |
| 18 | Assembler | `complete_novel.docx` | No LLM needed -- pure pandoc conversion |
| 19 | Publishing | `19_kdp_assets.md` | Blurb, keywords, cover prompts, ad copy |
| 20 | Beta Reader | `20_beta_feedback.md` | Non-fatal; simulated beta reader feedback |
| 21 | Structural Rev. | `21_structural_notes.md` | Non-fatal; plot holes, pacing, consistency |
| 22 | Targeted Rev. | `22_revision_log.md` | Non-fatal; line-level polish suggestions |

---

## The Writer Engine (Phase 17)

The heart of ccwriter. Each chapter passes through **5 sequential generation layers**, producing prose that is textured, grounded, and indistinguishable from skilled human writing.

```
    SENSORY FOUNDATION          EMOTIONAL DEPTH            VOICE
    ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
    │   Physical   │    +     │   Internal   │    +     │   Dialogue   │
    │              │          │              │          │              │
    │ sights       │          │ thoughts     │          │ speech       │
    │ sounds       │          │ memories     │          │ subtext      │
    │ textures     │          │ reactions    │          │ beats        │
    │ scents       │          │ associations │          │ rhythm       │
    │ temperature  │          │ commentary   │          │ silence      │
    └──────┬───────┘          └──────┬───────┘          └──────┬───────┘
           │                         │                         │
           └────────────────┬────────┘─────────────────────────┘
                            ▼
                   ┌──────────────┐
                   │  First Draft │  ← synthesize all three layers
                   │  Synthesis   │    into seamless, living prose
                   └──────┬───────┘
                          ▼
                   ┌──────────────┐
                   │   Revision   │  ← strip LLM-tells, check bible,
                   │   Polish     │    match author_style, tighten
                   └──────────────┘
```

**Why layered writing?** Traditional single-pass generation produces flat prose that reads like a summary. By separating sensory, emotional, and verbal layers, each gets full attention before synthesis. The result is prose with depth -- you can *feel* the room before the character speaks.

### Intermediate Files

Each chapter produces 5 files:
```
chapter03_1_physical.md    ← raw sensory texture
chapter03_2_internal.md    ← viewpoint character's inner world
chapter03_3_dialogue.md    ← spoken exchanges only
chapter03_4_draft.md       ← synthesized first draft
chapter03.md               ← final revised chapter
```

---

## Genre Configuration

ccwriter supports any genre through TOML configuration files. Two formats:

### Simple (Flat)

Quick setup for any genre:

```toml
name = "Cozy Mystery"
description = "A retired librarian solves murders in a seaside village"
tone = "warm, witty, suspenseful"
themes = ["community", "justice", "secrets"]
n_chapters = 20
chapter_length = 3000
target_audience = "adult mystery readers"
author_style = "Agatha Christie"
```

### Rich (Nested)

Deep commercial specifications for maximum reader impact:

```toml
[metadata]
name = "Contemporary Romance"
description = "A driven corporate lawyer forced to co-counsel with her ex-boyfriend"
tone = "witty, emotionally charged, tension-filled with moments of tenderness"
themes = ["vulnerability as strength", "second chances", "ambition vs. connection"]
n_chapters = 24
chapter_length = 3500
target_audience = "women 25-45, romance readers, BookTok audience"
author_style = "Emily Henry"
tropes = ["second chance romance", "forced proximity", "workplace rivals"]

[emotional_design]
core_tension = "professional ambition vs. unresolved love"
emotional_arc = "guarded -> cracking -> vulnerable -> shattered -> rebuilt"
heat_level = "closed door with high emotional intimacy"

[pacing]
act1_percent = 25
act2_percent = 50
act3_percent = 25
cliffhanger_frequency = "every chapter except the last"

[characters.protagonist]
name_suggestion = "Maya Chen"
age_range = "30-34"
wound = "abandonment — chose career over everything, including him"
want = "make partner at the firm"
need = "let someone in without it feeling like losing"
```

### Included Templates

| Template | Description |
|----------|-------------|
| `example-genre.toml` | Minimal cozy mystery starter |
| `romance-genre.toml` | Rich contemporary romance with full emotional design |
| `intern_workplace_romance.toml` | Detailed boss-intern workplace romance spec |
| `blackwell_book_1.toml` - `_7.toml` | Complete 7-book series ("The Blackwell Interns") |

---

## Batch Generation

Generate multiple unique novels from a single genre config:

```bash
/ccwriter:batch-generate 10 templates/romance-genre.toml
```

Each novel gets unique characters, plot, title, and KDP assets. The batch controller enforces uniqueness across the entire batch -- no duplicate names, settings, or plot structures.

```
novels/batch_romance_20260326/
  01_Breaking_Brief/
    complete_novel.docx
    19_kdp_assets.md
    chapter01.md ... chapter24.md
  02_Opposing_Counsel/
  03_Hostile_Witness/
  ...
  batch_summary.md          ← word counts, titles, keywords for all novels
```

**Features:**
- Uniqueness enforced across all novels in the batch
- Resume support -- interrupted batches pick up where they left off
- Parallel option: spawn up to 3 concurrent novel agents
- Batch summary with word counts, titles, and keywords
- Maximum recommended: 20 novels per run

---

## KDP Publishing Workflow

Two-step workflow with mandatory approval gates. Nothing goes live without explicit confirmation.

### Step 1: Prepare Upload Package

```bash
/ccwriter:kdp-prepare novels/My_Novel/
/ccwriter:kdp-prepare novels/batch_romance_20260326/    # entire batch
```

Generates a `kdp_upload/` folder per novel:

```
kdp_upload/
  01_book_details.txt         ← every KDP form field, ready to paste
  02_manuscript.docx          ← copy of the final DOCX
  03_cover_prompts.txt        ← 3 image gen prompts (1600x2560px)
  04_pricing_notes.txt        ← pricing strategy recommendations
  05_greenlight_checklist.md  ← review checklist before publishing
```

For batches, also generates a staggered release schedule (2-3 days between books for maximum "new release" visibility on Amazon).

### Step 2: Browser-Assisted Upload (Optional)

```bash
/ccwriter:kdp-upload novels/My_Novel/ --cover ~/covers/cover.jpg
```

Uses Chrome DevTools to fill KDP forms automatically:
1. Fills Book Details (title, author, blurb, keywords, categories)
2. Uploads manuscript DOCX
3. Uploads cover image
4. Sets pricing
5. **Saves as draft** -- you review and publish from KDP bookshelf

---

## Writing Quality Standards

These directives are embedded in every writing-phase skill to ensure the output reads like skilled human prose, not AI slop.

### Always

- Prefer concrete technical specificity over emotional generality
- Ground speculative elements in real mechanisms, objects, and sensory detail
- Avoid sentimentality and unearned epiphany
- Trust the reader to infer theme from action; do not editorialize
- Enter scenes late, leave early -- every paragraph earns its place

### Never

- Antithesis bloat: "It was not X, but Y"
- List-negation: "No X, no Y -- just Z"
- Describing what is absent instead of what is present

### LLM-Tell Blacklist

These words and phrases are banned from all novel output. The revision phase actively strips them:

> "seamlessly", "tapestry", "delve", "navigate", "pivotal", "furthermore",
> "moreover", "in conclusion", "it is worth noting", "significantly",
> "embark", "paradigm", "synergy", "facilitate", "utilize", "landscape" (metaphor),
> "journey" (metaphor), "nuanced", "multifaceted", "myriad", "plethora",
> "a testament to", "in the realm of", "needless to say"

### Dialogue Rules

- Default to "said" as dialogue tag (it's invisible to readers)
- Use action beats instead of tags when possible
- Never use: "exclaimed", "retorted", "queried", "said softly"
- Subtext techniques: Deflection, Contradiction, Silence, Interruption, Non-sequitur

### Scene-Sequel Structure

Every chapter follows the Scene-Sequel pattern:

```
SCENE:  Goal ──► Conflict ──► Disaster (outcome worse than expected)
                     │
SEQUEL: Reaction ──► Dilemma ──► Decision (sets up next scene's goal)
```

### Revision Passes

The revision phase applies 4 structured passes:

1. **Developmental** -- arc, pacing, stakes, subplot resolution, plot holes
2. **Scene-level** -- scene purpose, POV consistency, conflict per scene
3. **Line-level** -- filter words, passive voice, adverb pruning, show/tell
4. **Polish** -- read-aloud rhythm, sentence variety, dialogue distinction, hooks

---

## Project Structure

```
ccwriter/
  CLAUDE.md                    ← pipeline spec (what Claude Code reads)
  README.md                    ← you are here
  docs/                        ← series design specs and planning docs
  skills/                      ← 27 SKILL.md files (one per phase + orchestrators)
    head-author/               ← master orchestrator
    batch-generate/            ← multi-novel batch controller
    kdp-prepare/               ← upload package generator
    kdp-upload/                ← browser-assisted KDP form filler
    phase-00-market-research/
    phase-01-planner/
    ...
    phase-22-targeted-revision/
  references/                  ← shared technique docs loaded by skills
    kdp-formatting.md          ← Amazon KDP DOCX submission standards
    prompt-quality.md          ← writing quality directives + LLM-tell blacklist
    revision-passes.md         ← 4-pass revision framework + 9 rewrite techniques
    scene-sequel.md            ← Scene-Sequel story structure rules
    subtext-techniques.md      ← 5 dialogue subtext techniques
  templates/                   ← genre config files (TOML)
    example-genre.toml
    romance-genre.toml
    intern_workplace_romance.toml
    blackwell_book_1.toml - blackwell_book_7.toml
  scripts/
    assemble-docx.sh           ← pandoc-based DOCX assembly utility
  novels/                      ← generated output (gitignored)
```

---

## Resume Support

ccwriter checks for existing output files before running each phase. If the file exists, the phase is skipped.

```bash
# Resume an interrupted novel
/ccwriter:head-author templates/romance-genre.toml --resume novels/My_Novel/

# Force re-run a specific phase: delete its output file
rm novels/My_Novel/08_characters.md
/ccwriter:head-author templates/romance-genre.toml --resume novels/My_Novel/
```

For the writer phase, individual chapters are checked:
- `chapter05.md` exists? Skip chapter 5.
- `chapter05_3_dialogue.md` exists but `chapter05.md` doesn't? Resume from sub-phase 4.

---

## Architecture

ccwriter has no runtime, no server, no dependencies beyond pandoc. The entire system is **27 markdown files** that Claude Code interprets as skills.

```
User invocation
  |
  v
Parse genre config (TOML or prose)
  |
  v
Create output dir: novels/{timestamp}_{genre}/
  |
  v
Run Phase 0-22 sequentially
  |  (skip existing outputs on resume)
  |
  v
After Phase 1: rename dir to novels/{Title}_{wordcount}_{timestamp}/
  |
  v
Phase 17: 5 sub-phases x N chapters = 100+ LLM calls
  |
  v
Phase 18: pandoc converts markdown -> KDP DOCX
  |
  v
Phases 19-22: marketing assets, beta feedback, revision notes
  |
  v
Output: complete_novel.docx + kdp_assets + revision logs
```

**Model routing:** The head-author suggests model tiers per phase:
- `fast` (haiku/default) -- market research, pacing, assembler
- `mid` (sonnet) -- planning, characters, structure, revision notes
- `best` (opus) -- writer phase, beta reader, targeted revision

---

## What's Been Generated

The Blackwell Interns series (7 contemporary workplace romances):

| # | Title | Words | Status |
|---|-------|-------|--------|
| 1 | Corner Office Crush | ~50,000 | Chapters complete |
| 2 | Styled by You | ~50,000 | Chapters complete |
| 3 | Front Page Feelings | ~50,000 | Chapters complete |
| 4 | Off the Record | ~50,000 | DOCX + KDP assets |
| 5 | Developed in the Dark | ~50,000 | DOCX + KDP assets |
| 6 | Event Horizon | ~35,000 | In progress (ch 14/20) |
| 7 | The Final Draft | ~50,000 | DOCX + KDP assets |

---

<p align="center">
  <sub>Built with Claude Code. No Python was harmed in the making of these novels.</sub>
</p>
