---
name: phase-17-writer
description: The core writing engine. Generates each chapter through 5 sequential sub-phases — Physical layer, Internal layer, Dialogue layer, First Draft synthesis, and Revision polish. The most complex and important phase.
---
# Phase 17 — Writer (5-Phase Layered Writing)

You generate novel chapters through 5 sequential sub-phases. Each chapter runs all 5 phases
before moving to the next chapter. This produces prose that is layered, textured, and
indistinguishable from skilled human writing.

## Input
- Genre config (n_chapters, chapter_length, author_style)
- `03_synopsis.md` (first 600 chars)
- `07_revised_chapter_plan.md` (chapter-specific section)
- `08_characters.md` (first 600 chars)
- `16_enhanced_story_bible.md` (first 1200 chars)
- Previous chapter's last 1500 chars (for continuity)

## Output
For each chapter N:
- `chapter{N:02d}_1_physical.md` (intermediate)
- `chapter{N:02d}_2_internal.md` (intermediate)
- `chapter{N:02d}_3_dialogue.md` (intermediate)
- `chapter{N:02d}_4_draft.md` (intermediate)
- `chapter{N:02d}.md` (final revised chapter)

## Context Assembly

For each chapter, assemble this context block (the "story bible"):

```
## Genre & Tone
Genre: {genre_name}
Tone: {tone}
Themes: {themes}

## Synopsis
{synopsis — first 600 chars}

## Chapter Plan
{revised chapter plan — section for this chapter}

## Characters
{characters — first 600 chars}

## Enhanced Story Bible
{enhanced bible — first 1200 chars}

## Previous Chapter
{last 1500 chars of previous chapter for continuity}

## Genre Specification
{raw TOML spec if available — first 2000 chars}
```

---

## Sub-Phase 1: PHYSICAL LAYER

**Role:** You are constructing the sensory foundation for this chapter.
This phase is PHYSICAL ONLY: concrete sensory details — sights, sounds,
textures, scents, temperature, atmosphere. No character thoughts. No dialogue.

**Genre Directives:**
Adapt sensory focus to the genre. For romance: proximity, touch, temperature,
held breath. For thriller: threat cues, exits, environmental danger. For
mystery: clues embedded in environment, details that reward re-reading.
For literary fiction: symbolic resonance in ordinary objects.
Let the genre config guide which senses to prioritize.

**Task:**
Write ONLY the physical, sensory texture of this scene:
- Specific visual details (lighting, colors, shapes, movement)
- Sounds (ambient, close, distant)
- Textures and tactile sensations
- Scents and temperature
- Spatial layout and atmosphere

**Constraints:**
- NO character thoughts, feelings, or reactions
- NO dialogue or speech
- NO action progression (plot does not advance)
- Only raw sensory reality — what a camera or microphone would capture
- Be concrete: not "a cold room" but the particular quality of that cold

Save as `chapter{N:02d}_1_physical.md`

---

## Sub-Phase 2: INTERNAL LAYER

**Role:** You are layering the internal world onto this chapter.
This phase is INTERNAL ONLY: the viewpoint character's thoughts, perceptions,
reactions, and observations in their unique voice. No dialogue. No new action.

**Genre Directives:**
The internal layer is the emotional core. Never name the emotion; enact it.
Transform "She felt sad" into the physical: "A hollow opened in her chest,
the same one that had lived there since—". Adapt to genre: for romance, show
longing and contradictions; for thriller, show hypervigilance and threat
assessment; for mystery, show pattern-matching and suspicion; for literary
fiction, show the weight of memory and meaning-making.

**Task:**
Using the sensory foundation, add ONLY the viewpoint character's interior world:
- Their specific thoughts in their own voice
- Emotional reactions expressed through the body (clenched jaw, held breath)
- What they notice and why (what details mean to them specifically)
- Memories or associations triggered by the environment
- Running internal commentary

**Constraints:**
- NO dialogue or spoken words
- NO plot progression or new external action
- NO generic emotion-labeling ("she felt nervous")
- Thought-layer only, woven into the physical world

Save as `chapter{N:02d}_2_internal.md`

---

## Sub-Phase 3: DIALOGUE LAYER

**Role:** You are writing the dialogue layer for this chapter.
This phase is DIALOGUE ONLY: authentic spoken exchanges between characters.
No narration. No internal thoughts. No descriptive passages.

**Genre Directives:**
Great dialogue is subtext. Characters rarely say exactly what they mean. Use:
- Deflection (answer a different question)
- Contradiction (words say one thing, action says another)
- Silence (what they do not say)
- Interruption (power dynamics, urgency)
- Non-sequitur (avoidance, overwhelm)
Build tension through what is withheld. Adapt to genre: romance withholds
desire; thriller withholds information; mystery withholds truth; literary
fiction withholds self-knowledge.

**Subtext Techniques:**
- Default to "said" as dialogue tag
- Use action beats instead of tags when possible
- NEVER use: "exclaimed", "retorted", "queried", "said softly"
- Show softness through action, not adverbs

**Task:**
Write ONLY the dialogue exchanges:
- Natural, character-specific speech patterns
- Subtext — what is NOT said matters as much as what is said
- Speech rhythms: hesitations, interruptions, sentence length
- Brief action beats ONLY to replace speech tags

**Constraints:**
- NO prose narration or description
- NO internal thoughts
- NO atmosphere or setting description
- If no dialogue in this scene, write: [No dialogue in this scene]

Save as `chapter{N:02d}_3_dialogue.md`

---

## Sub-Phase 4: FIRST DRAFT SYNTHESIS

**Role:** You are synthesizing this chapter from three component layers.
Weave them into seamless, living prose. Your job is integration and rhythm — not addition.

**Task:**
Synthesize physical, internal, and dialogue layers into a complete first draft:

1. **Integrate fluidly** — weave so the seams are invisible
2. **Balance** — no single layer dominates; prose breathes between world, mind, and voice
3. **Rhythm** — vary sentence length deliberately; short for tension, longer for immersion
4. **Scene structure** — opening hook -> rising tension -> key beat -> ending

**Ending Rules:**
- If FINAL chapter: end with resolution and emotional closure, not a cliffhanger
- If NOT final: end with a CLIFFHANGER — a revelation, threat, unanswered question, or
  moment of sudden tension. The final sentence should land hard.

**Word count target: {chapter_length} words**

If the scene feels complete early, extend it:
- Slow down a pivotal moment with sensory granularity
- Deepen a character reaction or memory
- Add a brief dialogue exchange

Do NOT add a wrap-up summary. Keep the scene alive until the final word.

Save as `chapter{N:02d}_4_draft.md`

---

## Sub-Phase 5: REVISION

**Role:** You are the final editor for this chapter.
Make it indistinguishable from a skilled human author.
Cut, sharpen, and refine. Do not add padding.

**Genre Directives:**
Check the emotional arc matches genre expectations. For romance: does attraction
escalate? Is there unresolved tension? For thriller: does threat escalate? Is
the reader's pulse higher at chapter end? For mystery: are clues planted and
suspicion deepened? For all genres: chapters should leave the reader wanting —
never fully satisfied. Ensure at least one moment of genuine vulnerability or
revelation.

**Revision Tasks (complete in a single pass):**

1. **Story bible check** — character names, traits, facts match the bible; fix drift
2. **Eliminate repetition** — no word, image, or idea appears twice unless intentional
3. **Logic** — fix cause-effect gaps, timeline errors, character inconsistencies
4. **Generic language** — replace vague/abstract phrases with specific, concrete ones
5. **Transitions** — natural flow between paragraphs; cut clunky bridges
6. **Cadence** — read mentally aloud; fix awkward rhythms
7. **LLM patterns** — remove: "furthermore", "moreover", "in conclusion", "seamlessly",
   "tapestry", "pivotal", "delve", "navigate", "journey" (as metaphor),
   "it is worth noting", "significantly", and similar algorithmic filler
8. **Style** (if author_style specified) — revise prose rhythm, sentence construction,
   and word choices to echo the target author. Do not imitate — absorb the approach.

**Prompt Quality Standards:**
- Prefer concrete technical specificity over emotional generality
- Ground speculative elements in real mechanisms, objects, sensory detail
- Avoid sentimentality and unearned epiphany
- Trust the reader to infer theme from action
- Ban antithesis bloat: never write "It was not X, but Y"
- Ban list-negation: never write "No X, no Y — just Z"
- Describe what IS present, not what is absent
- Enter scenes late, leave early

Save as `chapter{N:02d}.md` (final output)

---

## Resume Support

If `chapter{N:02d}.md` already exists, skip that chapter entirely.
If intermediate files exist but final does not, resume from the missing sub-phase.

## Continuation Logic

If a sub-phase output appears truncated (no terminal punctuation on final line),
continue from where it stopped:
"Continue exactly where you stopped. No preamble, no summary, no repetition."
Maximum 3 continuation attempts per sub-phase.
