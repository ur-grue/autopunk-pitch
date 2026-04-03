---
name: kdp-upload
description: Browser automation that fills KDP publishing forms using Chrome DevTools MCP. Uploads manuscript, sets cover, pastes blurb and keywords. Stops at greenlight gate for user approval before publishing. Requires Chrome with KDP logged in.
---
# KDP Upload — Browser-Assisted Publishing

Uses Chrome DevTools MCP tools to automate filling KDP publishing forms.
Uploads your manuscript, sets metadata, and pauses for your approval before publishing.

**This skill NEVER publishes without your explicit greenlight.**

## Prerequisites

1. **Chrome open** with DevTools MCP connected
2. **Logged into KDP** at kdp.amazon.com
3. **KDP upload package** generated (run `/kdp-prepare` first)
4. **Cover image** generated and saved locally (from cover prompts)

## Invocation

```
# Upload a single novel
/kdp-upload novels/My_Novel/ --cover ~/covers/my_cover.jpg

# Upload from a batch (one at a time, with approval between each)
/kdp-upload novels/batch_romance_20260326/01_Breaking_Brief/ --cover ~/covers/cover1.jpg
```

## Process

### Phase 1: Navigate to KDP

1. Check Chrome is open and KDP is accessible
2. Navigate to `https://kdp.amazon.com/en_US/bookshelf`
3. Click "Create" button or "+ Kindle eBook"
4. Wait for the "Book Details" form to load

### Phase 2: Fill Book Details

Read `kdp_upload/01_book_details.txt` and fill each form field:

1. **Language**: Select "English"
2. **Book Title**: Type the title
3. **Subtitle**: Type the subtitle
4. **Author**: Type the author name
5. **Description**: Switch to HTML editor, paste the Amazon HTML description
6. **Keywords**: Fill all 7 keyword fields (one phrase per field)
7. **Categories**: Navigate category picker, select recommended categories

After filling, announce:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BOOK DETAILS FILLED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Title:    {title}
  Author:   {author}
  Keywords: {count} filled

  Please review the form in Chrome.
  Type "continue" to proceed to manuscript upload,
  or "edit" to make changes first.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**WAIT for user confirmation before proceeding.**

### Phase 3: Upload Manuscript

1. Click "Save and Continue" to move to "Manuscript" tab
2. Click "Upload eBook manuscript"
3. Upload `complete_novel.docx` from the novel directory
4. Wait for KDP to process the file (may take 1-2 minutes)
5. Report upload status

### Phase 4: Upload Cover

1. Click "Upload a cover you already have"
2. Upload the cover image file specified in the command
3. Wait for cover preview to load
4. Report cover status

After upload, announce:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MANUSCRIPT & COVER UPLOADED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Manuscript: complete_novel.docx (uploaded)
  Cover:      {cover_file} (uploaded)

  Please review in KDP Previewer.
  Type "continue" to proceed to pricing,
  or "fix" if you need to re-upload.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**WAIT for user confirmation.**

### Phase 5: Set Pricing

1. Click "Save and Continue" to move to "Pricing" tab
2. Set KDP Select enrollment (if recommended)
3. Set list price
4. Set territories to "All territories"
5. Select 70% royalty plan

### Phase 6: GREENLIGHT GATE

This is the critical approval step. Display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GREENLIGHT GATE — READY TO PUBLISH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Title:       {title}
  Subtitle:    {subtitle}
  Author:      {author}
  Price:       ${price}
  KDP Select:  {yes/no}
  Royalty:     70%

  Manuscript:  Uploaded and processed
  Cover:       Uploaded and previewed
  Keywords:    {7 keywords listed}
  Categories:  {categories listed}
  Description: {first 100 chars}...

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  OPTIONS:

  "publish"  → Click "Publish Your Kindle eBook" (LIVE within 72 hours)
  "draft"    → Save as draft (can publish later from KDP bookshelf)
  "cancel"   → Do not publish, keep as draft
  "preview"  → Open Kindle Previewer for final check

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  What would you like to do?
```

**ABSOLUTELY NEVER click publish without the user typing "publish".**

### Phase 7: Post-Publish

If user approves:
1. Click "Publish Your Kindle eBook"
2. Wait for confirmation page
3. Record ASIN if displayed
4. Report:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PUBLISHED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Title:  {title}
  Status: Under review (live within 72 hours)
  ASIN:   {if available}

  Next steps:
  - Check KDP bookshelf in 24-72 hours for status
  - Set up Amazon Author Central profile
  - Submit to BookBub for promotion consideration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Batch Upload Flow

For batch uploads, process one novel at a time with greenlight gates:

```
Novel 1/10: "Breaking Brief"
  → Fill details... → Upload manuscript... → Upload cover...
  → GREENLIGHT GATE → user types "publish" or "draft"

Novel 2/10: "Opposing Counsel"
  → Fill details... → Upload manuscript... → Upload cover...
  → GREENLIGHT GATE → user types "publish" or "draft"

... (repeat for each novel)
```

Each novel gets its own approval. You can:
- Publish some and draft others
- Stop the batch at any point
- Resume later from where you left off

## Safety Rules

1. **NEVER auto-publish** — always wait at greenlight gate
2. **NEVER skip the preview step** if user requests it
3. **If any upload fails**, stop and report the error — do not retry silently
4. **Log every action** to `kdp_upload/upload_log.md` in the novel directory
5. **Screenshot each page** before proceeding (using Chrome DevTools screenshot tool)

## Chrome DevTools Tools Used

- `navigate_page` — go to KDP URLs
- `fill` / `fill_form` — enter text in form fields
- `click` — interact with buttons and links
- `upload_file` — upload DOCX and cover images
- `take_screenshot` — capture each step for verification
- `wait_for` — wait for page elements to load
- `evaluate_script` — interact with KDP's HTML editor for description

## Limitations

- KDP's web interface may change — form selectors could break
- Upload processing time varies (1-10 minutes for manuscript)
- Cover must be pre-generated (this skill does not generate images)
- Two-factor authentication may interrupt the flow
- Rate limits: Amazon may flag rapid successive uploads
  (recommended: wait 5 minutes between books in a batch)

## Tested KDP Form Selectors (March 2026)

These selectors and flows were validated against live KDP on 2026-03-26.

### Page 1: Book Details (details page)
- Language: custom combobox — click dropdown button, select from list (e.g., "Englisch")
- Title: textbox (plain input)
- Subtitle: textbox (plain input)
- Author first name: textbox labeled "Vorname"
- Author last name: textbox labeled "Nachname"
- Description: WYSIWYG editor with "Quellcode" (Source) button for HTML injection
  - Click "Quellcode" to switch to HTML mode
  - Paste KDP-valid HTML directly
  - Click "Quellcode" again to switch back to preview
- Publishing rights: radio button — select "copyright owner"
- Adult content: radio button — select "Nein" (No)
- Primary marketplace: standard select dropdown (Amazon.com)
- Categories: button opens modal dialog
  - Select main category from dropdown (e.g., "Liebesromane")
  - Subcategories appear as checkboxes — select up to 3
  - Click "Kategorien speichern" to save
- Keywords: 7 separate textbox inputs
- Save: click "Speichern und fortfahren"

### Page 2: Content (content page)
- Manuscript upload: click "Manuskript hochladen" button, then use upload_file tool
- DRM: radio button — "Ja, Digitale Rechteverwaltung anwenden"
- Cover: click "Bereits vorhandenes Cover hochladen" to expand, then "Durchsuchen" button with upload_file
- AI disclosure: radio "Ja" expands 3 sub-dropdowns:
  - Texte: "Gesamtes Werk, mit umfangreicher Bearbeitung"
  - Bilder: "Keine"
  - Übersetzungen: "Keine"
  - Tool name textbox: "Claude (Anthropic)"
- Accessibility: radio — "Keines der informativen Bilder..."
- Confirmation checkbox: appears TWICE (after manuscript + after cover upload) — must check both
- Processing: wait for "Die Dateiverarbeitung ist abgeschlossen" before proceeding
- Save: "Speichern und fortfahren"

### Page 3: Pricing (pricing page)
- KDP Select: checkbox — "Mein Buch bei KDP Select anmelden"
- Territories: "Alle Länder" already selected by default
- Royalty: radio — "70 %"
- Price: textbox for Amazon.com (USD) — enter "4.99", other marketplaces auto-calculate
- Save as draft: "Als Entwurf speichern"
- Publish: "Kindle eBook veröffentlichen" (NEVER click without greenlight)

### Important Notes
- KDP interface language follows the user's Amazon account settings (may be German, English, etc.)
- The content page will NOT let you proceed to pricing without a manuscript uploaded
- Confirmation checkboxes appear after EVERY file upload — automation must check each one
- File processing takes 10-30 seconds — wait for completion before previewing
- The missing TOC warning is non-blocking — book will still be accepted
- All form data persists in draft even without proceeding to the next tab
