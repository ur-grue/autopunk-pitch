# ccwriter Pickup Prompt

Copy-paste this into a new Claude Code session to resume work.

---

## Prompt

```
Read docs/HANDOFF.md and docs/niche-research.md to understand current state.

Summary: ccwriter is a 22-phase AI novel generation pipeline. 7 Blackwell Interns novels are complete (all have DOCX manuscripts). The scaling goal is 3000 KDP titles across 20 series in lucrative niches.

Remaining work (in order):

1. BLACKWELL FINISH: Run Phase 19 (KDP publishing assets) for Books 1, 2, 3, 6 — they're missing blurbs, keywords, cover prompts. Books 4, 5, 7 already have these. Use /ccwriter:phase-19 or follow skills/phase-19-publishing/SKILL.md.

2. COVERS: Generate 7 real covers via ChatGPT/DALL-E using the prompts in docs/HANDOFF.md. Pipeline: prompt ChatGPT in Chrome → wait for image → download via JS injection → resize+overlay text with scripts/overlay-cover-text.py. Placeholder covers exist but aren't publish-quality.

3. KDP UPLOAD: Run /ccwriter:kdp-prepare on all 7 novels, then /ccwriter:kdp-upload with Chrome automation. KDP interface is in German. Selectors documented in skills/kdp-upload/SKILL.md.

4. NICHE SERIES DESIGN: Using docs/niche-research.md (20 ranked niches), design 20 series with TOML configs. Each series needs: pen name, series name, book count, tropes, tone, emotional design. Write configs to templates/ directory.

5. BATCH GENERATION: Run /ccwriter:batch-generate for each series. Use parallel agents (3 concurrent). ~140 novels in first tranche.

pandoc is at: /Users/snu/Library/Python/3.9/lib/python/site-packages/pypandoc/files/pandoc
Git: ur-grue / sebastian.nuss@me.com
Repo: https://github.com/ur-grue/ccwriter.git
```
