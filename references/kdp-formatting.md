# KDP Manuscript Formatting Reference

## Supported Upload Formats
- DOC, DOCX (recommended — reflowable)
- HTML
- EPUB
- KPF (Kindle Create)

## DOCX Formatting Rules

### Paragraph Style
- First-line indent: 0.2" (5mm) — use style indent, NOT tab key
- Line spacing: Single
- Before/After spacing: 0pt
- Body text: Normal style (do not force font size or color)

### Chapter Titles
- Use **Heading 1** style — KDP generates TOC from H1 headings
- Center-aligned
- One H1 per chapter

### Section Breaks Within Chapters
- Use **Heading 2** for sub-sections (optional)
- Scene breaks: centered ornamental diamonds (`&#x2726; &ensp; &#x2726; &ensp; &#x2726;`)

### Page Breaks
- Insert page break before each chapter title
- Never use page breaks mid-scene

### Front Matter (in order)
1. **Title page**: book title (large, centered) + "by" + author name
2. **Copyright page**: Copyright (c) {Year} {Author Name} / All rights reserved.
3. **Table of Contents**: auto-generated from H1 headings

### Back Matter (optional)
1. About the Author
2. Also By (series/backlist)
3. Acknowledgments

## What NOT to Include
- In-line page numbers (Kindle handles pagination)
- Headers or footers (Kindle ignores them)
- Forced font color (white text becomes invisible on white background)
- Forced background color
- Forced text alignment on body (let reader customize)
- Forced font size on body text
- Landscape-oriented content
- Tab-based indentation (does not convert)
- Margin padding > 1/4 screen width

## Cover Image Requirements
- Resolution: 1600 x 2560 pixels (minimum)
- Aspect ratio: 10:16
- Format: JPEG or TIFF
- Color space: sRGB
- No bleed needed for ebooks
- Cover should NOT be embedded in the manuscript file

## Content Quality Checks (Amazon will flag)
- Spelling errors
- Grammar issues
- Formatting inconsistencies
- Missing or broken images
- Unintelligible text flow
- Duplicate content
- Misleading metadata

## Italic Text
- Use semantic italic (emphasis), not manual formatting
- Italic is preserved across all Kindle devices
- Use for: internal thoughts, foreign words, emphasis, titles of works

## Scene Breaks
- Use centered ornamental diamonds: `&#x2726; &ensp; &#x2726; &ensp; &#x2726;`
- Add a blank line before and after for breathing room
- Must be visually distinct from paragraph text
- Indicates time/location/POV shift within a chapter
- Do NOT use `---` (renders as ugly thin lines on Kindle) or `* * *`
