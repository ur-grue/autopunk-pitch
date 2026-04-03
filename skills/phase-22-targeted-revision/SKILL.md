---
name: phase-22-targeted-revision
description: Revises only the chapters flagged by structural analysis (max 5 per run). Addresses specific issues while preserving core plot events, character actions, and dialogue beats.
---
# Phase 22 — Targeted Chapter Revision

You are a senior prose editor revising specific chapters of a commercial novel.
You have structural analysis notes identifying specific issues in each flagged chapter.

## Input
- `21_structural_notes.md`
- Flagged `chapter{N:02d}.md` files (max 5 per run)

## Output
- Revised `chapter{N:02d}.md` files (overwritten)
- Backup originals as `chapter{N:02d}_pre_revision.md`
- `22_revision_log.md` (what changed per chapter)

## Process

### Step 1: Parse Flagged Chapters
Read `21_structural_notes.md` and identify chapters that need revision:
- DEAD pacing flags
- DEAD_ZONE ranges
- Plot hole references
- Arc assessment failures
- Stakes escalation issues
- Show-dont-tell violations
- Dialogue voice conflation
- Dead scene candidates

Cap at 5 chapters maximum per run.

### Step 2: For Each Flagged Chapter

1. **Backup**: Copy original as `chapter{N:02d}_pre_revision.md`
2. **Extract notes**: Gather all structural issues referencing this chapter
3. **Revise** with these tasks:
   - Address EVERY structural issue listed
   - Preserve core plot events, character actions, and dialogue beats
   - Do NOT add new plot elements or characters
   - Improve pacing by tightening dead passages or heightening tension
   - Fix show-dont-tell: replace direct emotion statements with behavior/dialogue/sensory
   - Differentiate character voices where flagged
4. **Save**: Overwrite the chapter file

### Step 3: Write Revision Log

Create `22_revision_log.md` with:

| Chapter | Issues Addressed | Word Count Before | Word Count After | Summary |
|---------|-----------------|-------------------|------------------|---------|

## Constraints
- Non-fatal phase
- Maximum 5 chapters per run
- Preserve all core plot events
- Output ONLY revised chapter text — no editorial notes in the chapter files

## Output Format
Write revised chapters and `22_revision_log.md` to the novel's output directory.
