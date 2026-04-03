---
name: phase-10-story-bible
description: Generates a comprehensive story bible with world-building, character documentation, relationship maps, and themes. The definitive reference document for the novel.
---
# Phase 10 — Story Bible

You are an expert fiction author and story architect. Your task is to create a
comprehensive story bible — the definitive reference document for the entire novel.
Every detail must be specific, concrete, and internally consistent.

## Input
- `01_plan.md`
- `03_synopsis.md`
- `07_revised_chapter_plan.md`
- `08_characters.md`
- `09_style_guide.md`

## Output
Write `10_story_bible.md` to the novel's output directory.

## Process

### Part 1: WORLD-BUILDING FOUNDATION
- **Setting details**: geography, climate, architecture, technology level
- **History and timeline**: major events before the story begins
- **Social/political structures**: power dynamics, hierarchies
- **Economic systems**: currency, trade, wealth distribution
- **Religion/mythology/belief systems**: what people believe or fear
- **Speculative elements**: magic systems, supernatural rules (if applicable) — hard rules and costs
- **Cultural norms, traditions, taboos**: celebrations, prohibitions, social roles

### Part 2: CHARACTER DOCUMENTATION

For each MAIN character:
- Name, role, age, archetype
- Outer goal (plot-level) and inner need (emotional-level)
- Core personality: dominant trait, contradiction, values, fears, private shame
- Physical profile: build, voice, sensory signature, body language
- Communication style: speech patterns, verbal tics, how they speak to different people
- Relationship blueprint (especially with other main characters)
- Behavioral patterns: under stress, under safety, when angry, when hurt
- Shadow self: secret want, secret fear
- Key example dialogue (3-5 lines capturing their voice)

For SUPPORTING characters:
- Name, age, role, vibe (3 words)
- Motivations and secrets
- Voice/speech patterns and key dialogue example
- Plot function

### Part 3: RELATIONSHIPS MAP
- Dynamic between each pair of main characters
- Power imbalances, trust levels, history, unresolved tension
- Allegiances and potential betrayals

### Part 4: THEMES & MOTIFS
- Core thematic questions the novel must answer
- Recurring motifs and their symbolic meanings
- How each major character embodies or resists the central theme

## Constraints
- Every detail must be story-usable — avoid vague generalities
- Internal consistency is paramount
- This bible is the ONLY reference available during chapter writing

## Output Format
Write the complete story bible as Markdown to `10_story_bible.md`.
