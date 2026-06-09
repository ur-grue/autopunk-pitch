# The ccwriter writing pipeline (22 phases)

A simple map of what each agent does. The **head-author** orchestrator runs all 22 in sequence and
resumes by skipping any phase whose output file already exists. Phases 0–17 are the "writers" (the
creative core, held fixed); 18–22 are mechanical/evaluative.

## Plan — build the blueprint before any prose
0. **Market Research** — comps, hot tropes, reader expectations for the genre
1. **Planner** — title, core concept, positioning, themes
2. **Brainstorm** — raw ideas, angles, what-ifs
3. **Synopsis** — the whole story told in beats
4. **Pacing** — per-chapter word-count + tension table
5. **Chapter Plan** — a 200–300 word summary per chapter
6. **Humanize** — self-critique pass: flags clichés/AI-tells in the plan
7. **Revise** — rewrites the chapter plan from that critique
8. **Characters** — cast bible: who they are, what they want, their voice
9. **Style Guide** — the prose voice/tone rules for this book
10. **Story Bible** — world, rules, continuity facts
11. **Three-Act** — maps structure (setups, midpoint, climax)
12. **Conflict & Obstacles** — what's in the way, escalating
13. **Plot Twists** — reversals and reveals
14. **Pacing Review** — checks the tension curve, fixes flat spots
15. **Scene Breakdown** — each chapter as Scene → Sequel beats
16. **Enhanced Story Bible** — consolidates everything for the writer

## Write — per chapter, 5 layered passes (the creative core, held fixed)
17. **Writer ×N chapters:**
    1. *Physical* — sensory detail only (no dialogue/thought)
    2. *Internal* — the POV character's inner world
    3. *Dialogue* — the spoken exchanges
    4. *Draft* — fuses the three layers into full prose
    5. *Revision* — polishes, strips AI-tells, matches the style guide

## Assemble
18. **Assembler** — stitches chapters + front/back matter into a KDP-ready DOCX (pandoc, no LLM)

## Publishing assets
19. **Publishing** — blurb, keywords, categories, cover prompts, HTML description

## Revise — post-draft quality passes (non-fatal)
20. **Beta Reader** — reads the book as 5 reader personas, grades + flags fixes
21. **Structural Revision** — arc/pacing/plot-hole analysis with a tension heat-map
22. **Targeted Revision** — surgically rewrites the worst-flagged chapters

---

Around this writing core sits the **autonomous KDP layer** (see `ROADMAP.md`): research-niche →
[GATE 1] → this pipeline → quality-gate → [GATE 2] → cover-generate → kdp-prepare → kdp-upload →
[GATE 3]. The human only approves at the 3 gates.
