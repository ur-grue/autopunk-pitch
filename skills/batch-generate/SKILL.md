---
name: batch-generate
description: Generate multiple novels in one session from a single genre config. Runs N complete pipelines consecutively, each producing a unique novel with distinct characters, plot, and title. Invoke with count and genre config.
---
# Batch Generate — Multiple Novel Production

You generate multiple complete novels from a single genre configuration.
Each novel gets unique characters, plot, title, and KDP assets.

## Invocation

```
/batch-generate 10 templates/romance-genre.toml
/batch-generate 5 templates/example-genre.toml
/batch-generate 3 "A dark enemies-to-lovers romance set in 1920s Paris"
```

Format: `/batch-generate <count> <genre_config_or_concept>`

## Process

### Step 1: Setup

Parse the genre config once. Create a master output directory:
```
novels/batch_{genre}_{YYYYMMDD_HHMMSS}/
```

### Step 2: Generate Each Novel

For each novel (1 through N):

1. **Announce**: Print batch progress header
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     NOVEL 3 / 10
     Genre: Contemporary Romance
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

2. **Seed variation**: Before starting each novel, prepend a variation directive
   to the Phase 1 (Planner) prompt:
   ```
   VARIATION DIRECTIVE: This is novel #{n} of {total} in a batch generation.
   You MUST create a completely unique story that differs from the previous novels
   in this batch. Use different:
   - Protagonist name, background, and occupation
   - Setting (different city, workplace, or environment)
   - Central conflict and obstacles
   - Supporting cast
   - Plot structure and twists
   - Title

   Previous titles in this batch: {list of titles so far}

   Do NOT reuse any character names, settings, or plot structures from previous novels.
   ```

3. **Run full pipeline**: Execute all 22 phases via the head-author skill.
   Each novel outputs to its own subdirectory:
   ```
   novels/batch_{genre}_{timestamp}/
   ├── 01_Novel_Title_One/
   │   ├── 01_plan.md
   │   ├── ... (all phase outputs)
   │   ├── complete_novel.docx
   │   └── 19_kdp_assets.md
   ├── 02_Novel_Title_Two/
   │   └── ...
   └── 10_Novel_Title_Ten/
       └── ...
   ```

4. **Track progress**: Maintain a running summary after each novel completes.

### Step 3: Batch Summary

After all novels are complete, write `batch_summary.md` to the batch directory:

```markdown
# Batch Generation Summary

- **Genre**: {genre_name}
- **Novels Generated**: {count}
- **Total Words**: {sum of all novel word counts}
- **Generated**: {date and time}

## Novels

| # | Title | Author | Chapters | Words | DOCX |
|---|-------|--------|----------|-------|------|
| 1 | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... |
...

## KDP Assets Quick Reference

| # | Title | Subtitle | Top Keyword |
|---|-------|----------|-------------|
| 1 | ... | ... | ... |
...
```

### Step 4: Report

Print final batch summary to console:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BATCH COMPLETE: 10 / 10 NOVELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Genre:        Contemporary Romance
  Total Words:  ~600,000
  Output:       novels/batch_romance_20260326_153000/
  Summary:      batch_summary.md

  1. "Breaking Brief"      — 62,340 words
  2. "Opposing Counsel"     — 58,920 words
  3. "Motion to Dismiss"    — 61,100 words
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Uniqueness Guarantees

Each novel MUST differ in:
- Title (tracked and enforced — no duplicates)
- Protagonist name and background
- Setting / location
- Central conflict
- Supporting characters
- Plot twists

The variation directive grows with each novel — later novels in the batch
have more "previous titles" to avoid, ensuring increasing diversity.

## Resume Support

If the batch is interrupted:
- Completed novel directories are detected and skipped
- The batch resumes from the next incomplete novel
- Partially complete novels resume at the phase level (same as single-novel resume)

To resume: run the same command again. The batch directory is detected by timestamp pattern.

## Parallel Execution (Advanced)

For faster batch generation, the orchestrator can spawn parallel agents:
- Each agent handles one novel independently
- Use `Agent` tool with different names: `novel-1`, `novel-2`, etc.
- Maximum recommended parallel: 3 novels (to avoid context pressure)
- Each parallel agent receives the full variation directive

Note: Parallel mode uses more resources but completes faster.
Sequential mode is the default and more reliable.

## Constraints
- Each novel is fully independent — no shared characters or plot elements
- All 22 phases run for each novel (non-fatal phases still non-fatal)
- KDP assets generated per novel (unique blurb, keywords, covers for each)
- Maximum batch size: 20 novels per run (practical limit)
