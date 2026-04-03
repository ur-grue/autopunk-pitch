---
name: kdp-prepare
description: Generates a complete KDP upload-ready package per novel — pre-formatted text for every KDP form field, organized for fast copy-paste upload. Run after phase 19 or after batch-generate.
---
# KDP Prepare — Upload-Ready Package

Generates a complete upload package for each novel, with every KDP form field
pre-formatted and ready to paste. Eliminates guesswork during upload.

## Invocation

```
# Single novel
/kdp-prepare novels/My_Novel/

# All novels in a batch
/kdp-prepare novels/batch_romance_20260326/
```

## Process

For each novel directory found, read `19_kdp_assets.md` and `01_plan.md`,
then generate a `kdp_upload/` folder inside the novel directory.

### Output Structure

```
novels/My_Novel/
├── ... (existing phase outputs)
└── kdp_upload/
    ├── README.md                    ← step-by-step upload instructions
    ├── 01_book_details.txt          ← all KDP "Book Details" form fields
    ├── 02_manuscript.docx           ← copy of complete_novel.docx
    ├── 03_cover_prompts.txt         ← 3 image generation prompts
    ├── 04_pricing_notes.txt         ← pricing recommendations
    └── 05_greenlight_checklist.md   ← review checklist before publishing
```

### File Contents

#### `01_book_details.txt`

Pre-formatted for direct copy-paste into KDP's "Book Details" page:

```
═══════════════════════════════════════════
  KDP BOOK DETAILS — Ready to Paste
═══════════════════════════════════════════

LANGUAGE: English

BOOK TITLE: {title}

SUBTITLE: {subtitle}

SERIES: {series_name if applicable, otherwise leave blank}

EDITION NUMBER: 1

AUTHOR: {author_name}

CONTRIBUTORS: (none)

DESCRIPTION:
{Amazon HTML description from Section E of 19_kdp_assets.md}
(paste this into the HTML editor on KDP)

PUBLISHING RIGHTS: I own the copyright

KEYWORDS (paste one per field):
1. {keyword_1}
2. {keyword_2}
3. {keyword_3}
4. {keyword_4}
5. {keyword_5}
6. {keyword_6}
7. {keyword_7}

CATEGORIES:
- Primary: {recommended BISAC category}
- Secondary: {recommended BISAC category}

AGE AND GRADE RANGE: Not applicable (adult fiction)

RELEASE DATE: {today's date or "I want to release my book now"}

PRE-ORDER: No
```

#### `03_cover_prompts.txt`

Three detailed prompts ready to paste into Midjourney, DALL-E, or any image generator:

```
═══════════════════════════════════════════
  COVER IMAGE PROMPTS
  Spec: 1600 x 2560 px (10:16 ratio)
═══════════════════════════════════════════

OPTION 1 — {concept name}
{full prompt} --ar 10:16

OPTION 2 — {concept name}
{full prompt} --ar 10:16

OPTION 3 — {concept name}
{full prompt} --ar 10:16

AFTER GENERATING:
- Save as JPEG or TIFF
- Minimum resolution: 1600 x 2560 px
- Color space: sRGB
- Do NOT embed the cover in the DOCX — upload separately on KDP
```

#### `04_pricing_notes.txt`

```
═══════════════════════════════════════════
  PRICING RECOMMENDATIONS
═══════════════════════════════════════════

EBOOK:
- Kindle Unlimited: ENROLL (recommended for romance/genre fiction)
- List Price: $4.99 (sweet spot for genre fiction)
- Royalty: 70% ($3.49 per sale)
- Territories: All territories

ALTERNATIVE PRICING:
- Launch price: $0.99 or $2.99 (first 3 days for ranking boost)
- Regular price: $4.99
- Sale price: $2.99 (for BookBub promotions)

KDP SELECT:
- Enroll for 90 days (required for Kindle Unlimited)
- Gives access to Kindle Countdown Deals and Free Book Promotions
- Exclusivity requirement: ebook cannot be sold elsewhere during enrollment
```

#### `05_greenlight_checklist.md`

```markdown
# Pre-Publish Greenlight Checklist

Review each item before publishing. Check off when verified.

## Manuscript
- [ ] Downloaded and opened complete_novel.docx — no formatting errors
- [ ] Previewed in Kindle Previewer (free download from Amazon)
- [ ] Table of contents links work correctly
- [ ] No blank pages or missing chapters
- [ ] Scene breaks (ornamental diamonds) display correctly
- [ ] Italic text preserved where intended
- [ ] First and last chapters read well

## Book Details
- [ ] Title and subtitle are correct and compelling
- [ ] Author name is the desired pen name
- [ ] Description HTML renders correctly in KDP preview
- [ ] All 7 keywords are entered (one per field)
- [ ] Categories are appropriate for the genre
- [ ] No typos in any metadata field

## Cover
- [ ] Cover image is 1600 x 2560 px minimum
- [ ] Text on cover is readable at thumbnail size
- [ ] Genre conventions are met (readers know what kind of book this is)
- [ ] Title on cover matches title in book details exactly

## Pricing
- [ ] Price is set ($4.99 recommended for genre fiction)
- [ ] Royalty plan selected (70% for $2.99-$9.99 range)
- [ ] Territories selected (worldwide recommended)
- [ ] KDP Select enrollment decision made

## Final Approval
- [ ] GREENLIGHT: Ready to publish

Date reviewed: ___________
Approved by: ___________
```

### Batch Mode

When run on a batch directory, generates `kdp_upload/` for every novel subdirectory.
Also creates a master `batch_upload_guide.md` at the batch root:

```markdown
# Batch Upload Guide — {N} Novels

Upload order (recommended — stagger releases for maximum visibility):

| # | Title | Upload Date | Status |
|---|-------|-------------|--------|
| 1 | ... | Day 1 | [ ] Uploaded [ ] Reviewed [ ] Published |
| 2 | ... | Day 3 | [ ] Uploaded [ ] Reviewed [ ] Published |
| 3 | ... | Day 5 | [ ] Uploaded [ ] Reviewed [ ] Published |
...

Staggering releases 2-3 days apart maximizes each book's "new release"
visibility window on Amazon.
```

## Publishing Flow

The automation flow is: **fill all 3 KDP tabs, save as draft, user reviews and publishes from KDP bookshelf.**

- The `/kdp-upload` skill fills Book Details, Content, and Pricing tabs in sequence
- After all tabs are complete, it clicks "Als Entwurf speichern" (Save as Draft)
- The user reviews the draft on the KDP bookshelf and publishes manually when ready
- There is no greenlight gate in automation — the user controls publishing from KDP directly

**Cooldown period**: Wait at least 5 minutes between uploading books in a batch.
Amazon may flag rapid successive uploads as suspicious activity.

## Constraints
- Automation saves as draft only — user publishes from KDP bookshelf
- All text is pre-formatted for KDP's specific form fields
- Cover prompts only — actual image generation is manual (or via image tools)
- Pricing is advisory — user makes final pricing decisions
