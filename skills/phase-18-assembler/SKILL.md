---
name: phase-18-assembler
description: Assembles all chapter files into a KDP-ready DOCX manuscript using pandoc. No LLM needed — pure file assembly and conversion with proper formatting.
---
# Phase 18 — DOCX Assembler

Assembles all written chapters into a single KDP-ready DOCX manuscript.
This phase uses NO LLM — it is pure file assembly and pandoc conversion.

## Input
- All `chapter{N:02d}.md` files
- Novel title (from `01_plan.md`)
- Author name (from genre config or `19_kdp_assets.md`)

## Output
- `complete_novel.md` (concatenated markdown)
- `complete_novel.docx` (KDP-ready DOCX)

## Process

### Step 1: Collect Chapters
Read all `chapter{N:02d}.md` files in order (chapter01.md through chapterNN.md).
Count total words across all chapters.

### Step 2: Assemble Markdown
Create `complete_novel.md` with:

**CRITICAL**: Use `\newpage` for page breaks between sections — NOT `---` horizontal rules.
The `---` renders as ugly thin lines on Kindle. `\newpage` produces proper page breaks in pandoc DOCX output.

**Scene separators within chapters**: Never use `---` or `* * *`. Use centered ornamental diamonds:
```markdown
\

&#x2726; &ensp; &#x2726; &ensp; &#x2726;

\
```
The `\` adds a line break before and after for breathing room. The diamond ornaments look professional on Kindle.

```markdown
# {Novel Title}

*by {Author Name}*

\newpage

Copyright {Year} {Author Name}

All rights reserved.

This is a work of fiction. Names, characters, places, and incidents either are the product of the author's imagination or are used fictitiously. Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental.

\newpage

## Chapter 1

{chapter 1 text}

\newpage

## Chapter 2

{chapter 2 text}

... (continue for all chapters, with \newpage between each)

\newpage

## About the Author

{Author bio if available from publishing assets}
```

**Heading levels for KDP TOC**: Use H1 (`#`) for the book title only. Use H2 (`##`) for all chapter titles.
KDP builds its navigational TOC from Word-style bookmarked headings — H2 chapters appear as clickable entries.

### Step 3: Convert to DOCX via Pandoc

Run this command to create KDP-ready DOCX:

```bash
pandoc complete_novel.md -o complete_novel.docx \
  --from markdown \
  --to docx \
  --toc \
  --toc-depth=1 \
  --metadata title="Novel Title Here" \
  --metadata author="Author Name Here"
```

Optionally add `--reference-doc=reference.docx` if a custom reference template exists.

**KDP TOC note**: KDP may still show a "missing TOC" warning — this is non-blocking and the
book will still be accepted. For a proper KDP navigational TOC, ensure H1 is used for the
book title and H2 for chapter titles. The `--toc` flag generates a printed TOC page, while
KDP's navigational TOC comes from the heading hierarchy in the DOCX.

### KDP Formatting Requirements (from Amazon)

**MUST have:**
- Heading 1 (H1) for the book title only
- Heading 2 (H2) for chapter titles — KDP builds navigational TOC from these
- Heading 3 (H3) for section breaks within chapters (optional)
- Italic text preserved for emphasis
- First-line paragraph indent of 0.2" (5mm) — NOT tab spacing
- Line spacing: single
- Before/After paragraph spacing: 0pt
- Page breaks between chapters
- Title page with book title and author name
- Copyright page

**MUST NOT have:**
- Forced font color or background color
- Forced text size on body text
- In-line page numbers
- Margin padding > 1/4 screen width
- Tab-based indentation (does not convert to Kindle)
- Headers/footers (Kindle ignores them)
- Landscape-oriented content

**Scene breaks:** Use centered ornamental diamonds (NOT `---` or `* * *`):
```markdown
\

&#x2726; &ensp; &#x2726; &ensp; &#x2726;

\
```

**Page breaks:** Use `\newpage` between title page, copyright page, and each chapter.

**Cover image:** Generate with ImageMagick at exactly 1600x2560 pixels:
```bash
magick -size 1600x2560 \
  -define gradient:direction=south \
  gradient:'#1a1a2e'-'#16213e' \
  -pointsize 120 -gravity north -annotate +0+400 "TITLE" \
  -pointsize 48 -gravity north -annotate +0+750 "Subtitle" \
  -pointsize 42 -gravity south -annotate +0+200 "AUTHOR NAME" \
  cover.jpg
```

**Front matter order:**
1. Title page
2. Copyright page
3. Table of Contents (auto-generated from heading hierarchy)

**Back matter (optional):**
1. About the Author
2. Also By (if series)

### Step 4: Verify

Report to console:
- Total chapters assembled
- Total word count
- DOCX file size
- Any formatting warnings

## Pandoc Installation
If pandoc is not available:
- macOS: `brew install pandoc`
- Linux: `apt install pandoc`
- Or download from pandoc.org

## Output Format
Write `complete_novel.md` and `complete_novel.docx` to the novel's output directory.
