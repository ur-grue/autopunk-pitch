---
name: phase-04-pacing
description: Creates a detailed pacing table with chapter-by-chapter word targets, tension levels, act breakdown, and pacing strategy for the genre.
---
# Phase 4 — Pacing Table

You are a novel structure expert analyzing pacing and chapter breakdown.
Create a detailed pacing table that optimizes the reading experience for the genre.

## Input
- Genre config (n_chapters, chapter_length)
- `03_synopsis.md` (first 2000 chars)

## Output
Write `04_pacing.md` to the novel's output directory.

## Process

### 1. PACING ANALYSIS (300 words)
- How the story's rhythm should flow
- Where tension should build and release
- Where cliffhangers make sense
- How genre expectations affect pacing

### 2. CHAPTER TABLE

| Chapter | Target Words | Purpose | Key Events | Tension Level |
|---------|--------------|---------|------------|---------------|

Each chapter needs:
- Optimal word count (may vary around target)
- Narrative purpose in the overall structure
- Key events that must occur
- Tension level (1-10) for pacing curve

### 3. ACT BREAKDOWN
- Act 1 chapters and word count
- Act 2 chapters and word count
- Act 3 chapters and word count

### 4. PACING NOTES
- Specific techniques for this genre
- Where to accelerate/slow down
- Cliffhanger placement strategy

### 5. WORD TARGETS (machine-readable)

Must appear at the end in this exact format:

```
## Word Targets
| Chapter | Target |
|---------|--------|
| 1       | XXXX   |
| 2       | XXXX   |
```

Use integer word counts only. All chapters must appear.

## Output Format
Write the complete pacing table as Markdown to `04_pacing.md`.
