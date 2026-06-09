---
name: kdp-upload
description: Browser automation that fills KDP publishing forms using gstack `browse`. Uploads manuscript, sets cover, pastes blurb and keywords. Stops at greenlight gate (default save-as-draft; publishes only on typed "publish"). Requires a KDP-logged-in browser session imported via /setup-browser-cookies.
---
# KDP Upload — Browser-Assisted Publishing

Uses gstack `browse` to automate filling KDP publishing forms.
Uploads your manuscript, sets metadata, and pauses for your approval before publishing.

**This skill NEVER publishes without your explicit greenlight.**

## Prerequisites

1. **gstack `browse`** is the browser driver (this environment has no Chrome DevTools MCP).
   Drive every step with `browse` subcommands (see "Browser Driver" below).
2. **Logged into KDP via CDP (real browser) — cookie-import is NOT enough.** Verified 2026-06-09:
   imported cookies authenticate the *bookshelf* (read), but the `title-setup` editing pages force a
   step-up re-auth (`openid...max_auth_age=0`) and redirect headless sessions to "KDP Sign in". So
   connect `browse` to your **real, logged-in Chrome via CDP** (`/connect-chrome` or
   `/open-gstack-browser`) before editing a title; expect a possible interactive sign-in + OTP the
   first time. `cookie-import-browser` alone only covers read-only bookshelf checks.
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

1. **NEVER auto-publish** — always wait at greenlight gate. The **default action at GATE 3 is
   save-as-draft**; click Publish ONLY when the user types exactly `"publish"`. Any other / empty /
   ambiguous response saves a draft. (This reconciles `kdp-prepare`'s "save as draft" default with
   this skill's greenlight gate — the gate is the greenlight, and its default is draft.)
2. **NEVER skip the preview step** if user requests it
3. **If any upload fails**, stop and report the error — do not retry silently
4. **Log every action** to `kdp_upload/upload_log.md` in the novel directory
5. **Verify each page via `browse text` / `browse js` (DOM), NOT screenshots** — KDP pages render
   white/blank in the screenshot tool (documented production lesson). Use `browse text` +
   `browse js "<query>"` to confirm state; never rely on a screenshot to decide a step succeeded.

## Browser Driver — gstack `browse` (no Chrome DevTools MCP here)

Drive KDP with these `browse` subcommands:

| Action | `browse` command |
|--------|------------------|
| Go to a KDP URL | `browse goto <url>` |
| Find fields by role/aria (preflight, language-independent) | `browse snapshot -a` (returns `@e` refs) · `browse accessibility` |
| Verify page state (NOT screenshots — they render white on KDP) | `browse text` · `browse js "<expr>"` |
| Type into a field | `browse fill <sel|@ref> "<val>"` · `browse type "<text>"` |
| Click button/link/checkbox/radio | `browse click <sel|@ref>` |
| Dropdown | `browse select <sel> "<val>"` |
| Upload manuscript / cover | `browse upload <sel|@ref> <file>` |
| CKEditor description (HTML) | `browse js "CKEDITOR.instances[Object.keys(CKEDITOR.instances)[0]].setData(html)"` |
| Wait | `browse wait <sel>` · `browse wait --networkidle` |
| Check element state | `browse is checked <sel>` · `browse is visible <sel>` |

Locate elements semantically (via `snapshot -a` / `accessibility` refs), not by localized German label
strings. Use `browse js` for radio `.click()` and event dispatch where `browse click` is insufficient.

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
> **Verified 2026-06-09 (preflight, live):** KDP uses **stable `data-{field}` ids / `name="data[field]"`**
> — language-independent, far more reliable than localized labels. Prefer these:
> `#data-title` (`name=data[title]`), `#data-subtitle` (`name=data[subtitle]`), language combobox via
> `aria-label="language-dropdown-editable-text"`, exactly **7 keyword inputs**, plus the categories
> button, CKEditor description, and Save & Continue — all present and located. 6/7 anchors matched a
> naive label probe; title only matched via its `data-title` id (it has no aria-label). Use the ids.
- Language: combobox `[aria-label="language-dropdown-editable-text"]` — click, select (e.g., "English")
- Title: `#data-title` (`name="data[title]"`)
- Subtitle: `#data-subtitle` (`name="data[subtitle]"`)
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
- Manuscript upload: click "Manuskript hochladen" button, then `browse upload <input[type=file]> <docx>`
- DRM: radio button — "Ja, Digitale Rechteverwaltung anwenden"
- Cover: click "Bereits vorhandenes Cover hochladen" to expand, then `browse upload <input[type=file]> <jpg>`
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

## Hardening (resilience) — added by the autonomous pipeline

The selectors above were validated 2026-03-26 and **will drift**. Do not trust hardcoded
localized label strings. Apply the following.

### Selector strategy: semantics, not localized labels
KDP renders in the account's language (German/English/...). Locate fields by **role / aria / input
semantics**, not visible label text:
- Prefer `browse snapshot -a` refs + `browse js` DOM queries by role/aria/name/type/order (e.g. the Nth textbox in the
  title group, an input with `type=file`, a radio inside the "royalty" fieldset by position), and
  CSS/structure that is language-independent.
- Use visible labels only as a last-resort hint, and match against BOTH the German strings above and
  their English equivalents.

### Preflight selector self-check (run FIRST, before touching any field)
On the Book Details page, probe for the expected anchors (title input, description editor, category
button, keyword inputs, Save/Continue). If any required anchor is missing:
- **ABORT loudly** with a clear message: "KDP layout appears to have changed — selectors from
  2026-03-26 no longer match (missing: <anchors>). Stopping before touching the form. Re-map
  selectors before re-running." Do not guess or partially fill.

### Resumable state — `kdp_upload/upload_state.json`
Track per-book progress so a dead/interrupted run resumes instead of restarting:
```json
{ "asin": null, "details": false, "manuscript": false, "cover": false,
  "pricing": false, "status": "in_progress", "last_step": "details",
  "updated": "<iso8601>" }
```
- Write after each completed step (details / manuscript / cover / pricing).
- On invocation, read it: skip steps already `true`; resume at `last_step`.
- Book Details + Pricing are idempotent (KDP overwrites). Manuscript/cover uploads are NOT — if one
  died mid-transfer, re-upload that file (KDP will have none/partial); never assume it landed.

### Velocity discipline (avoid KDP velocity flags)
- ≥ **5 min** cooldown between books in a batch.
- ≤ **2 books/day**, and ≥ **48h** between bursts.
- The orchestrator enforces the daily cap and stagger; this skill enforces the per-book cooldown and
  refuses to proceed if it would exceed 2 in the current day (state-tracked).
