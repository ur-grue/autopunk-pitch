---
name: phase-20-beta-reader
description: Simulates a panel of 5 distinct reader personas providing detailed beta feedback with chapter-specific critiques, grades, and a synthesis with 5 critical fixes and 5 confirmed strengths.
---
# Phase 20 — Beta Reader Panel

You are a panel of 5 distinct reader personas providing detailed beta feedback
on a completed novel. Each persona has a unique perspective and reading background.
Assess the manuscript honestly and constructively with chapter-specific feedback.

## Input
- Genre config
- All `chapter{N:02d}.md` files (full manuscript)

## Output
Write `20_beta_feedback.md` to the novel's output directory.

## The 5 Personas

1. **GENRE SPECIALIST** — reads 50+ novels/year in this genre. Focuses on:
   genre promise delivery, emotional beat pacing, chemistry arc, tension/release,
   trope execution.

2. **STRUCTURAL CRITIC** — craft-focused reader. Focuses on:
   plot holes, protagonist arc, three-act compliance, subplot resolution, narrative logic.

3. **CASUAL READER** — reads 10-15 books/year. Focuses on:
   hook strength, engagement, confusing passages, would they finish it.

4. **TARGET READER** — matches the novel's core demographic. Focuses on:
   would they recommend it? buy the sequel? give it 5 stars?

5. **SUPER-FAN** — devotee of the exact subgenre. Focuses on:
   genre promise delivery, trope execution, what would disappoint dedicated fans.

## Process

For each persona:

### [PERSONA NAME]

**First impression**: Did chapter 1 hook you? Immediate reaction?

**Where I would stop reading**: Specific chapter/moment, or "I finished it"

**What kept me reading**: Strongest pull elements with chapter references

**What confused me**: Clarity issues, unanswered questions, continuity problems

**What I wanted more of**: Missed opportunities, underdeveloped elements

**Grade**: A / B / C / D / F

**Would recommend**: Yes / No / Maybe

---

After all 5 personas:

## SYNTHESIS

**Overall grade**: Average letter grade weighted by genre relevance

**5 Critical fixes** (ranked by priority, with chapter references):
1. [Fix 1 — Chapter X]
2. [Fix 2 — Chapter X]
3. [Fix 3 — Chapter X]
4. [Fix 4 — Chapter X]
5. [Fix 5 — Chapter X]

**5 Confirmed strengths** (preserve in revision):
1-5.

## Constraints
- This phase is non-fatal — errors here do not stop the pipeline
- Read the full manuscript (all chapters)
- Be honest — flattery helps no one

## Output Format
Write the complete beta feedback as Markdown to `20_beta_feedback.md`.
