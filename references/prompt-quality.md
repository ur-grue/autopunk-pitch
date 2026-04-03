# Prompt Quality Standards

These directives apply to every writing-phase prompt. Derived from Gwern's Claude Opus 4.6
system prompt research, AIStoryWriter's production prompts, and AuthorClaw's skill files.

## Always Include in Writing Prompts

- Prefer concrete technical specificity over emotional generality.
- Ground speculative elements in real mechanisms, objects, and sensory detail.
- Avoid sentimentality and unearned epiphany.
- Trust the reader to infer theme from action; do not editorialize.
- Ban antithesis bloat: never write "It was not X, but Y."
- Ban list-negation: never write "No X, no Y — just Z."
- Describe what IS present, not what is absent.
- Enter scenes late, leave early. Every paragraph earns its place.

## Revision Techniques (Name Specific Passes)

### Pass 1 — Developmental
- Arc completeness and coherence
- Pacing: does tension escalate appropriately?
- Stakes: do they increase?
- Subplot resolution: are all threads addressed?
- Plot holes: any cause-effect gaps?

### Pass 2 — Scene-Level
- Scene purpose: does every scene advance plot or character?
- POV consistency: no head-hopping
- Conflict per scene: every scene needs tension
- Entry/exit: enter late, leave early

### Pass 3 — Line-Level
- Filter words: remove "seemed", "felt", "noticed", "realized"
- Passive voice: convert to active where stronger
- Adverb pruning: cut adverbs that weaken rather than strengthen
- Show/tell ratio: enact emotions through behavior, not labels

## Structural Feedback Format
Use this format for structural notes:
`Location | Issue | Why | Suggestion`

## LLM-Tell Blacklist

Never allow these in novel prose:
- "seamlessly", "tapestry", "delve", "navigate", "pivotal"
- "furthermore", "moreover", "in conclusion", "it is worth noting"
- "significantly", "embark", "paradigm", "synergy", "facilitate"
- "utilize", "landscape" (metaphor), "journey" (metaphor)
- "nuanced", "multifaceted", "myriad", "plethora"
- "a testament to", "in the realm of", "at the end of the day"
- "needless to say", "interestingly enough", "it goes without saying"
