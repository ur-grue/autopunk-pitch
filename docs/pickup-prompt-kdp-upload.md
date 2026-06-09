# Pickup Prompt — KDP Upload Session

Copy and paste this to resume:

---

## Prompt

```
Read docs/pickup-prompt-kdp-upload.md and memory/feedback_kdp_automation.md for context.

Summary: ccwriter novel pipeline. 7 Blackwell Interns novels are FULLY READY for KDP upload. All Phase 19 assets, covers, and KDP packages are complete.

COMPLETED THIS SESSION:
- Phase 19 KDP assets for Books 1, 2, 3, 6 (Books 4, 5, 7 already had them)
- Generated 7 DALL-E covers via ChatGPT Chrome automation + text overlay with scripts/overlay-cover-text.py
- KDP Prepare upload packages for all 7 books (kdp_upload/ dirs with 6 files each)
- 20 niche series TOML configs committed to templates/ (4799 lines, 20 files)
- Pricing strategy decided: $4.99 all books, KDP Select, stagger releases 2-3 days apart, Book 1 free promo after all 7 live

CURRENT TASK: Upload all 7 novels to KDP as drafts.

Book 1 (Corner Office Crush) is PARTIALLY uploaded:
- Draft created on KDP with ID: A1X4V75HEFEAOY
- URL: https://kdp.amazon.com/en_US/title-setup/kindle/A1X4V75HEFEAOY/details
- Title, subtitle, author (Avery Sinclair), description HTML, adult content (No) are SET
- Keywords were filled but may need re-verification
- Category: Romance > Contemporary checkbox was clicked but needs verification
- STILL NEEDED: Verify category saved → Save and Continue → Upload manuscript DOCX → Upload cover JPG → Set pricing → Save as draft
- Then repeat for Books 2-7

KEY FILES PER BOOK:
- novels/batch_blackwell_interns_20260326/{BOOK_DIR}/kdp_upload/01_book_details.txt — all form fields
- novels/batch_blackwell_interns_20260326/{BOOK_DIR}/complete_novel.docx — manuscript
- novels/batch_blackwell_interns_20260326/{BOOK_DIR}/covers/cover_final.jpg — cover (1600x2560)

BOOK DIRECTORIES:
01_Corner_Office_Crush, 02_Styled_by_You, 03_Front_Page_Feelings, 04_Off_the_Record, 05_Developed_in_the_Dark, 06_Event_Horizon, 07_The_Final_Draft

CRITICAL KDP AUTOMATION LESSONS (read feedback_kdp_automation.md):
1. Screenshots render WHITE on KDP — use read_page and javascript_tool only
2. Radio buttons need JS .click() not form_input
3. Categories REQUIRED before Save and Continue works
4. Category flow: Choose categories btn → form_input on combobox ref for "Romance" → wait → find subcategory checkboxes via JS → click "Contemporary" → click "Save categories" btn
5. CKEditor: CKEDITOR.instances.editor1.setData(html) for description
6. Keywords: use native setter + input/change/blur events
7. File uploads: use file_upload tool with ref from read_page
8. AI disclosure on content page: select Yes, fill sub-dropdowns, tool name "Claude (Anthropic)"
9. KDP interface is in ENGLISH (account was switched from German)

AFTER KDP UPLOAD:
- Publish Book 1 immediately, stagger Books 2-7 every 2 days
- Run Book 1 free promo (5 days) after all 7 are live
- Next major task: batch-generate novels from the 20 niche TOML configs

Author: Avery Sinclair (pen name for all Blackwell books)
Series: The Blackwell Interns (7 books)
Genre: Contemporary Workplace Romance
KDP Select: YES (Kindle Unlimited)
Price: $4.99 each
```
