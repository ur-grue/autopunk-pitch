# Pickup Prompt — Signal & Noise Novel Generation

Copy and paste this to start a fresh session:

---

```
Read CLAUDE.md, then read docs/pickup-prompt-signal-noise-generation.md and memory files for context.

TASK: Generate 12 novels for the "Signal & Noise" series — neurodivergent heroines × AI romance. Upper YA / Clean NA.

12 individual book TOMLs are ready at templates/signal-and-noise-book-01.toml through -12.toml. The master series TOML is templates/signal-and-noise-ai-romance.toml.

Run /ccwriter:head-author for each book sequentially, starting with Book 1:
  /ccwriter:head-author templates/signal-and-noise-book-01.toml

After Book 1 completes, review quality (check chapter 1 + plan), then continue with Books 2-12.

Output goes to novels/ directory. Each book: 24 chapters × 2500 words = ~60,000 words.

The assemble-docx.sh script has been fixed to include page breaks before each chapter title.

After all 12 novels are generated:
1. Generate 12 covers via ChatGPT (use the cover template at references/cover-template-signal-and-noise.md)
2. Upload all 12 to KDP as drafts using the WebSocket relay method for file uploads

Series details:
- Pen name: Seren Voss
- Price: $4.99 each, KDP Select, 70% royalty
- Categories: Science Fiction Romance, Clean & Wholesome Romance
- AI disclosure: Yes, entire work with extensive editing, tool: Claude (Anthropic)
- Cover style: Dark navy + neon glow + solo heroine + webtoon aesthetic (proven with Book 1 "Static" test cover)

Book order:
1. Static (social anxiety, voice AI)
2. Pattern Recognition (autism late-dx, smart home AI)
3. Noise Cancelling (ADHD, coding rival AI)
4. Chromatic (synesthesia, music composer AI)
5. Quiet Room (sensory processing, wellness AI)
6. Burnout (autistic burnout, AI therapist)
7. Detour (dyscalculia, navigation AI)
8. Placeholder (ADHD+anxiety, hologram boyfriend AI)
9. Unmasked (autism masking, social coach AI)
10. Reboot (PTSD+dissociation, reactivated AI)
11. Proxy (selective mutism, voice avatar AI)
12. Frequency (intersecting conditions, series finale + courtroom)
```
