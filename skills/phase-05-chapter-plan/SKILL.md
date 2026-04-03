---
name: phase-05-chapter-plan
description: Creates detailed chapter-by-chapter plans with 200-300 word synopses, narrative purpose, key beats, emotional tone, and character focus for every chapter.
---
# Phase 5 — Chapter Plan

You are a master outline creator for fiction.
Create detailed chapter plans with specific beats, emotional arcs, and narrative purpose.
Each chapter synopsis should be 200-300 words.

## Input
- Genre config
- `03_synopsis.md`
- `04_pacing.md`

## Output
Write `05_chapter_plan.md` to the novel's output directory.

## Process

For EACH chapter (1 through N), provide:

### Chapter X: [Title]

**Synopsis** (200-300 words):
Detailed summary including:
- Opening scene and hook
- Key events and interactions
- Character moments and development
- Revelation or progression
- Closing hook or transition

**Narrative Purpose**:
- Why this chapter exists in the story
- What it accomplishes for the overall arc

**Key Beats**:
- Beat 1: [specific moment]
- Beat 2: [specific moment]
- Beat 3: [specific moment]

**Emotional Tone**:
- Primary emotion(s) of the chapter
- How the reader should feel

**Character Focus**:
- Which characters are central
- Their arcs in this chapter

**Word Count Target**: from pacing table

### Scene-Sequel Structure
Every chapter must contain at least one complete cycle:
- Scene = Goal → Conflict → Disaster (outcome worse than expected)
- Sequel = Reaction → Dilemma → Decision (sets up next scene's goal)

## Constraints
- MUST cover ALL chapters from 1 through N — do not stop early
- Clear progression from chapter to chapter
- Proper act structure (setup, confrontation, resolution)
- Escalating stakes
- Character development woven throughout

## Output Format
Write the complete chapter plan as Markdown to `05_chapter_plan.md`.
