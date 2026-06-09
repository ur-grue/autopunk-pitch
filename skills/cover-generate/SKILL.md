---
name: cover-generate
description: Generate professional book covers via ChatGPT (GPT-4o) with integrated typography. Produces niche-appropriate illustrated covers with title and author name rendered directly in the image. Uses Chrome automation to interact with ChatGPT.
---

# Cover Generation — GPT-4o Illustrated Covers

Generates professional book covers using ChatGPT's image generation (GPT-4o).
Title and author name are included in the prompt so typography is part of the composition.

## Prerequisites

1. **Chrome open** with ChatGPT logged in at chatgpt.com
2. **Novel with Phase 19 assets** (`19_kdp_assets.md` with title, author, blurb)
3. **Genre TOML config** (for tone, tropes, character details)

## Invocation

```
/cover-generate novels/My_Novel/
/cover-generate novels/batch_romance/01_First_Book/ --style illustrated
/cover-generate novels/batch_romance/ --batch    # all books in batch dir
```

## Process

### Step 1: Read Novel Context

Read from the novel directory:
- `19_kdp_assets.md` — title, subtitle, author, blurb, cover prompts
- `08_characters.md` — character physical descriptions
- `01_plan.md` — setting, tone, themes
- Genre TOML if available

Extract:
- **Title** and **subtitle**
- **Author name** (pen name)
- **Two main characters**: ethnicity, hair, clothing style, distinguishing features
- **Primary setting**: specific room/location for the cover scene
- **Emotional core**: the central romantic tension (forbidden, rivals, secret, etc.)
- **Tropes**: for visual shorthand (grumpy/sunshine = contrast in body language)

### Step 2: Build Cover Prompt

Use the template from `references/cover-design-guide.md` to construct a prompt.

**Required elements in every prompt:**
1. **Style: rich SEMI-REALISTIC painterly / digital-painting** (glossy, cinematic, detailed, like
   bestselling KU romance covers). NOT flat-vector, NOT minimal — that style reads as amateur here.
2. Specific character descriptions (ethnicity, clothing, hair, props) + genre body language / tension
3. Scene setting with concrete props (e.g. office: MANUSCRIPT pages, EDITOR IN CHIEF nameplate,
   skyline through windows, golden-hour light)
4. Color palette + warm cinematic lighting — from `[cover_design].palette` ‖ `[series]` ‖ the genre
   row in `references/cover-design-guide.md`
5. **Title + author painted INTO the image as typography.** gpt-image-1 renders text well, so let the
   model paint the title (e.g. large elegant gold brush-script) + author name. This looks far better
   than a mechanical overlay. (The old "no text, overlay later" rule was for legacy DALL-E that
   garbled text — obsolete for gpt-image-1.)
6. Aspect ratio: tall portrait book-cover; thumbnail-legible at 200x300

### Step 3 (PRIMARY): Generate the FULL cover via the OpenAI Images API (gpt-image-1)

The reliable, autonomous path — no browser, scriptable. Generates the **complete cover INCLUDING the
painted title + author typography** (semi-realistic style). No overlay step needed.
```bash
.venv/bin/python scripts/generate_cover_api.py novels/{book}/covers/cover.png \
  --prompt "<semi-realistic prompt from Step 2, WITH the title+author baked in>" \
  --size 1024x1536 --quality high
```
- Stdlib-only (urllib) — no `openai` package needed; `.venv/bin/python` for consistency.
- Key: set `OPENAI_API_KEY`, or put it in `./.openai_key` / `~/.openai_key` (gitignored). Never printed.
- Resize to 1600x2560 for KDP if needed. Skip the overlay (Step 3.5) unless the model garbled the text.
- This replaces scripting chatgpt.com, which is NOT reliably automatable (see below).

### Step 3 (FALLBACK): Generate via ChatGPT browser

Only if no API key is available, and knowing it is unreliable. Using gstack `browse` (this
environment has no Chrome DevTools MCP). **CDP (real browser) is required
for ChatGPT — cookie-import is NOT enough.** Verified 2026-06-09: headless `browse` hitting
`chatgpt.com` gets a Cloudflare **403** even with valid imported cookies. Connect to your real,
logged-in Chrome via CDP (`/connect-chrome` or `/open-gstack-browser`) so the genuine session +
fingerprint passes Cloudflare. If CDP isn't available, fall back to the **overlay-only path**: drop a
manually-generated artwork into `covers/artwork.png` and run the overlay step (V1-proven) — the
deterministic typography is the same.

> **Verified 2026-06-09 (live, CDP):** even past Cloudflare with a logged-in session, driving ChatGPT
> image-gen through the web UI is UNRELIABLE — the prompt submits (a user turn appears) but no
> assistant turn / image is produced (no error, just nothing), across multiple attempts. The web UI
> is not a dependable automation surface for generation. **Recommendation:** for autonomy, generate
> artwork via a **programmatic image API** (e.g. OpenAI `gpt-image-1`) rather than scripting
> chatgpt.com; otherwise use the **overlay-only path** above. The overlay → 1600x2560 step is proven
> reliable (V1) and produced the actual cover uploaded to KDP in V3.
1. `browse goto https://chatgpt.com`
2. Start a new conversation (`browse click` the new-chat affordance via `browse snapshot -a`)
3. Enter the **text-free artwork** prompt from Step 2: `browse fill <composer> "<prompt>"` then `browse press Enter`
4. `browse wait --networkidle` (image gen ~30-90s; poll for the result `<img>`)
5. Pull the generated image src via JS (screenshots are unreliable):
   `browse js "document.querySelector('main img[src*=\"oaiusercontent\"]').src"` then download that URL
6. Save artwork to `novels/{book}/covers/artwork.png`

### Step 3.5: Overlay typography (deterministic — replaces baked-in text)

Render title / series line / author onto the artwork with crisp, correctly-spelled type:
```bash
.venv/bin/python scripts/overlay-cover-text.py \
  novels/{book}/covers/artwork.png \
  novels/{book}/covers/cover_final.jpg \
  "{title}" "{series_line}" "{author}" "{accent_hex}"
```
- `title` / `author` from `19_kdp_assets.md`; `series_line` + `accent_hex` from `[cover_design]` ‖ `[series]`.
- Output is resized to KDP spec **1600x2560**. Pillow lives in the project venv (`.venv`); the script
  needs it, so invoke via `.venv/bin/python` (set up once: `python3 -m venv .venv && .venv/bin/pip install Pillow`).
- **Verified 2026-06-09:** overlay produces a crisp, correctly-spelled 1600x2560 cover from text-free artwork.
- Because text comes from the overlay, **spelling is deterministic** — the warped/misspelled-title
  failure mode is gone.

### Step 4: Cover-QA (gate before listing)

Score `cover_final.jpg`; on fail, regenerate (new artwork) up to N attempts, then escalate:
1. Dimensions == 1600x2560, 10:16.
2. Thumbnail legibility at 200x300 — the (overlaid) title is readable; artwork has a strong shape.
3. **AI-artifact check on the artwork** — extra/warped fingers, uncanny faces, melted props.
4. Series-consistency — palette/typography/series_element match `[cover_design]` and prior books.
5. Title/author spelling — deterministic via overlay (verify the overlay rendered, not garbled).
Report to user (GATE 2 / GATE 3 cover preview).

### Step 5: Iterate if Needed

If the cover needs adjustment:
- Regenerate with modified prompt
- Try "keep the same style but change X" for refinements
- Generate 2-3 variants, let user pick

## Series Consistency

For multi-book series:
- Use a **series template** that locks: illustration style, color palette family, font styles, layout structure
- Only vary: characters, scene, accent color, emotional tone
- Save series template to `references/cover-template-{series_name}.md`

## Batch Mode

For batch generation (`--batch` flag):
1. Read all book directories in the batch folder
2. Load series template if it exists
3. Generate covers sequentially (one ChatGPT conversation per cover)
4. 30-second pause between generations to avoid rate limits
5. Save each cover and create thumbnail
6. Produce a visual summary for user review

## Output Files

Per book:
- `covers/artwork.png` — the text-free ChatGPT/DALL-E artwork
- `covers/cover_final.jpg` — artwork + overlaid typography, 1600x2560 (the cover KDP uploads)
- `covers/cover_final_thumb.jpg` — 200x300px thumbnail for QA
- `covers/cover_prompt.txt` — the exact artwork prompt used (for reproducibility)
- `covers/cover_state.json` — per-cover resume state (artwork / overlay / qa flags, attempt count)

## Hardening (resilience) — Chrome automation

Same fragility class as `kdp-upload`. Apply:
- **Selectors:** locate ChatGPT's composer / send / generated-image by role/aria/DOM semantics, not
  localized label text or screenshots (screenshots are unreliable; pull the `<img>` src via JS).
- **Preflight self-check:** before sending, confirm the composer + send affordance exist; if the
  ChatGPT UI has drifted, **abort loudly** ("ChatGPT UI changed — re-map before re-running") rather
  than guessing.
- **Resume:** `cover_state.json` tracks artwork-done / overlay-done / qa-passed so an interrupted run
  resumes instead of regenerating from scratch.
- **Pacing:** ≥30s between generations in batch mode (existing) to avoid rate limits.

## Quality Checklist

Before approving a cover:
- [ ] Title readable at 200x300px thumbnail
- [ ] Characters match novel descriptions (ethnicity, clothing, features)
- [ ] Emotional tone matches the book's romantic tension
- [ ] Color palette is genre-appropriate
- [ ] No AI artifacts (extra fingers, warped text, uncanny faces)
- [ ] Author name legible and correctly spelled
- [ ] Consistent with other books in the series
- [ ] Would blend in (not stand out as amateur) on Amazon's bestseller shelf
