# PRD: Autopunk Localize — AI Agent for Media Localization

**Version:** 1.0.0
**Author:** Sebastian Nuß
**Date:** 2026-03-20
**Status:** Ready for Claude Code

---

## 1. Problem Statement

### The problem

Independent production companies (5–50 employees), mid-size broadcasters, and content distributors need to localize audiovisual content (subtitles, dubbing scripts, cultural adaptation) for international markets. Today this process costs €50–175/min per language for dubbing and €5–26/min per language for subtitling, takes 2–5 weeks per project, and requires coordinating multiple specialized vendors (transcription, translation, timing, QC, formatting).

Most indie producers cannot afford this. They either skip localization entirely — leaving international revenue on the table — or use cheap consumer tools (DeepL + SRT editor) that produce output rejected by broadcasters and platforms.

### Who has this problem

- **Independent producers** exporting content internationally (UK: £2.02B TV exports in 2024/25; India: 1,800+ films/year across 20+ languages)
- **Content distributors and sales agents** managing localization for catalog titles across 5–20+ territories
- **Mid-size broadcasters** under pressure from the European Accessibility Act (June 2025), UK Media Act 2024, and FCC/CVAA requirements to provide subtitles and accessibility features at scale
- **Corporate video producers** localizing training, marketing, and communications content

### Why now

1. AI transcription (Whisper-class) has reached broadcast-acceptable accuracy
2. LLM translation quality now exceeds traditional MT for most language pairs
3. No competitor offers an agentic end-to-end workflow combining transcription → translation → cultural adaptation → QC → broadcast-format delivery
4. Regulatory mandates (EAA, UK Media Act, FCC) create compliance-driven urgency
5. FAST channel proliferation (76% growth since 2023) demands cost-effective localization at scale

### What exists today (and why it's not enough)

- **Enterprise AI dubbing** (Deepdub, Flawless AI): Studio-grade, but enterprise pricing ($20K+ per project), inaccessible to independents
- **Creator tools** (Rask AI, HeyGen, ElevenLabs): Fast and cheap ($1/min), but no broadcast format compliance, no QC automation, no cultural adaptation
- **Workflow platforms** (OOONA, ZOO Digital): Handle project management and formats, but not AI-powered, not self-serve
- **Open-source pipelines** (Whisper + subtitle editors): Competent components, but no broadcast formatting (EBU-STL, TTML), no QC, no cultural adaptation, no orchestration
- **Traditional vendors** (Iyuno, Deluxe, VSI): High quality, but $50–175/min, 2–5 week turnaround, relationship-gated

**The gap:** No platform bridges broadcast-grade quality with indie-accessible pricing through an automated, agentic workflow.

---

## 2. Goals and Success Metrics

### Product goals

| ID | Goal | Success metric | Timeline |
|----|------|---------------|----------|
| G-01 | Deliver broadcast-quality subtitles at 1/10th traditional cost | Output passes Netflix Timed Text Style Guide validation; pricing at €5–15/min/language vs. €50–150 traditional | MVP |
| G-02 | Reduce localization turnaround from weeks to hours | 52-min documentary subtitled into 3 languages in <4 hours (vs. 2–4 weeks traditional) | MVP |
| G-03 | Support broadcast-standard export formats | EBU-STL, SRT, WebVTT, TTML output passing format validation | MVP |
| G-04 | Achieve QC pass rate >90% without human intervention | Automated QC catches >90% of issues (line length, reading speed, timing) before human review | MVP+1 |
| G-05 | Validate product-market fit with 10 paying customers | 10 production companies or distributors on paid plans within 6 months of launch | Month 6 |
| G-06 | Generate €5K MRR within 12 months | Combination of per-minute and subscription revenue | Month 12 |
| G-07 | Expand to dubbing script generation | Lip-sync-aware dubbing scripts with speaker identification and timing | Phase 2 |

### Business constraints

- **Solo developer** (Sebastian) with ~5–8h/week dev capacity alongside ARTE role and family obligations (alternating custody). This is a **vibe coding project** — Claude Code does the heavy lifting, Sebastian steers. Expect 3–5x velocity multiplier vs. manual coding, but only during focused sessions.
- **No external funding** — must be bootstrapped; API costs must stay below 30% of revenue
- **ARTE role must remain invisible** — no reference to ARTE in product, marketing, or sales
- **Target markets explicitly exclude DACH** — focus on UK/Australia, SEA/India, USA/Canada
- **Autopunk brand positioning:** "AI Agents for Media Operations" — localization is first module, not the brand identity
- **Multi-market pricing required** — Western markets (UK/US/AU) and South/Southeast Asian markets have fundamentally different price expectations ($5–15/min vs. $1–3/min). Pricing must be region-aware.

---

## 3. User Stories

### Persona: Indie Producer (primary)

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| US-001 | As an indie producer, I want to upload a video file and receive broadcast-quality subtitles in multiple languages, so that I can sell my documentary internationally without hiring a localization vendor. | 1. Upload accepts MP4, MOV, MXF up to 10GB. 2. User selects source language and 1–10 target languages. 3. System returns SRT files per language within 4 hours for a 52-min file. 4. Subtitles comply with max 42 chars/line, max 2 lines, min 1-second duration, max 200ms gap from shot changes. 5. User can download all files as ZIP. |
| US-002 | As an indie producer, I want to review and edit AI-generated subtitles in a browser-based interface before exporting, so that I can fix errors without specialized software. | 1. Web-based subtitle editor displays video with synced subtitles. 2. User can edit text, adjust timing, split/merge cues. 3. Flagged segments (low confidence, cultural references, proper nouns) are highlighted. 4. Changes auto-save. 5. Export updated files in selected format. |
| US-003 | As an indie producer, I want the system to detect and flag cultural references, idioms, and measurement units that may need adaptation, so that my content works in the target culture. | 1. System identifies culture-specific items (dates, currencies, idioms, units, proper nouns). 2. Each flagged item shows original, suggested adaptation, and confidence score. 3. User can accept, reject, or edit each suggestion. 4. Flagged items are counted in QC report. |
| US-004 | As an indie producer, I want to export subtitles in broadcast-standard formats, so that I can deliver to any platform or broadcaster. | 1. Export supports SRT, WebVTT, EBU-STL, TTML (Netflix profile). 2. Each format passes format-specific validation (character encoding, timecode format, metadata fields). 3. User can set target platform profile (Netflix, BBC, YouTube) and format adjusts automatically. |
| US-005 | As an indie producer, I want to see a detailed QC report for each language before export, so that I know the quality level without manually checking every subtitle. | 1. Report shows: reading speed distribution (CPM), line length violations, timing violations, shot-change conflicts, untranslated segments, flagged cultural items. 2. Overall quality score (0–100). 3. Individual issues are clickable, jumping to the relevant timecode in the editor. |

### Persona: Content Distributor

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| US-006 | As a content distributor, I want to batch-process multiple titles in a single job, so that I can localize my catalog efficiently. | 1. User can queue up to 20 titles per batch. 2. Each title has independent language and format settings. 3. Progress dashboard shows per-title status. 4. Batch completes without requiring per-title manual intervention (unless flagged items exceed threshold). |
| US-007 | As a content distributor, I want to manage a glossary of brand-specific terms and recurring translations, so that consistency is maintained across my catalog. | 1. User can create/edit glossary entries (source term → target term per language). 2. Glossary is applied during translation. 3. Violations (term translated differently than glossary) are flagged in QC. 4. Glossary is persistent across projects. |

### Persona: Mid-Size Broadcaster

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| US-008 | As a broadcaster, I want to generate accessibility-compliant subtitles (SDH/CC) from existing content, so that I can meet EAA and Ofcom requirements. | 1. System generates SDH subtitles including speaker identification, sound effects, and music descriptions. 2. Output meets Ofcom/EAA subtitle quality standards. 3. SDH-specific formatting (speaker labels, sound cues in brackets) is applied automatically. |

### Persona: All Users

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| US-009 | As a user, I want to see transparent per-minute pricing before starting a job, so that I can budget accurately. | 1. Price estimate shown before processing starts, based on content duration and selected languages. 2. Estimate is binding (±10% tolerance). 3. No hidden fees. 4. Payment via Stripe (credit card). |
| US-010 | As a user, I want to try the service with a free tier before committing, so that I can evaluate quality on my own content. | 1. Free tier: 10 minutes/month, 3 languages, SRT export only. 2. No credit card required for free tier. 3. Full QC and review features available in free tier. 4. Clear upgrade path shown when limits are reached. |

### Persona: Indian/SEA Producer

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| US-011 | As an Indian producer, I want to localize between Indian regional languages (Hindi ↔ Tamil, Telugu, Malayalam, Bengali, Kannada), so that I can reach audiences across India's linguistic markets. | 1. System supports all 22 scheduled Indian languages as both source and target. 2. Transliteration between scripts (Devanagari, Tamil, Telugu, etc.) is handled correctly. 3. Song/poetry segments are flagged for manual review rather than machine-translated. 4. Honorific systems and formality registers are preserved per language. |
| US-012 | As an Indian/SEA producer, I want pricing in my local currency at rates competitive with local vendors, so that AI localization is financially viable for my market. | 1. Pricing displayed in INR, THB, IDR, PHP, MYR alongside USD. 2. SEA/India tier: $1–3/min/language (vs. $5–15 Western tier). 3. Payment supports Razorpay (India) and regional payment methods alongside Stripe. 4. Volume discounts for >500 min/month. |
| US-013 | As an Indian/SEA producer, I want to target OTT platform specifications for JioHotstar, ZEE5, Viu, and iQIYI, so that my subtitles are accepted without rework. | 1. Platform profiles include JioHotstar, ZEE5, Viu, iQIYI, Netflix India, Amazon Prime Video India. 2. Each profile enforces platform-specific rules (character limits, font encoding, metadata). 3. Profile selection adjusts QC rules automatically. |
| US-014 | As a SEA distributor handling Korean drama for Thai/Vietnamese/Indonesian markets, I want to localize Korean → multiple SEA languages in a single batch, so that I can serve the K-drama distribution pipeline efficiently. | 1. Korean source language fully supported with accurate romanization handling. 2. Thai, Vietnamese, Indonesian, Filipino, Malay as target languages. 3. Batch supports Korean → 5 SEA languages simultaneously. 4. Honorific/politeness systems mapped correctly across Korean → SEA pairs. |

---

## 4. Technical Requirements

### Tech stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.12+ | Best AI/ML ecosystem, fastest prototyping with Claude Code |
| **Web framework** | FastAPI | Async-native, auto-generated OpenAPI docs, lightweight |
| **Frontend** | Next.js 14 (App Router) | React ecosystem, SSR, Vercel deployment, strong Claude Code support |
| **Database** | PostgreSQL 16 + SQLAlchemy | Proven, JSONB for flexible metadata, good ORM support |
| **Task queue** | Celery + Redis | Async job processing for long-running localization tasks |
| **File storage** | S3-compatible (AWS S3 or Backblaze B2) | Video upload/download, subtitle file storage |
| **AI — Transcription** | GPT-4o Mini Transcribe ($0.003/min) or Whisper API ($0.006/min) | Mini for cost; Whisper as fallback for difficult audio. Self-hosted faster-whisper deferred to Phase 3 |
| **AI — Translation** | Claude API (claude-sonnet-4-6) | Superior context-aware translation, cultural adaptation; $3/$15 per MTok |
| **AI — QC** | Claude API (claude-haiku-4-5-20251001) | Fast, cheap QC validation; $1/$5 per MTok |
| **AI — Orchestration** | Custom Python agent framework | Lightweight orchestrator chaining transcription → translation → QC → export |
| **Auth** | Clerk | Managed auth, social login, API keys, Next.js-native |
| **Payments** | Stripe + Razorpay | Stripe for Western markets, Razorpay for India |
| **Hosting — Backend** | Railway (initially), AWS later | Low-ops for FastAPI + Celery + Redis + Postgres |
| **Hosting — Frontend** | Vercel | Native Next.js deployment, global CDN, free tier generous |
| **CI/CD** | GitHub Actions | Standard, free for public repos |

### Architecture overview

```
[Client Browser]
    ↓
[Next.js 14 Frontend — Vercel]
    ↓
[FastAPI Backend — Railway]
    ├── /api/v1/projects — CRUD for localization projects
    ├── /api/v1/jobs — Submit, monitor, cancel jobs
    ├── /api/v1/export — Download finished subtitle files
    └── /api/v1/billing — Usage tracking, payments
    ↓
[Celery Task Queue + Redis]
    ↓
[Agent Orchestrator]
    ├── TranscriptionAgent → GPT-4o Mini Transcribe API
    ├── TranslationAgent → Claude API (per language, parallel)
    ├── CulturalAdaptationAgent → Claude API
    ├── QCAgent → Claude API (Haiku)
    └── FormattingAgent → Python (pycaption/pysrt)
    ↓
[PostgreSQL] ←→ [S3 Storage]
```

### Hard constraints

- All video files processed and deleted within 72 hours (privacy)
- No video content stored permanently — only subtitle/metadata outputs
- API rate limits: max 10 concurrent jobs per account (free), 50 (paid)
- All subtitle outputs must be valid UTF-8
- Source video never leaves the processing region (EU for EU customers, etc.)

---

## 5. MVP Scope

### In scope (Phase 1 — MVP)

| Feature | Priority | Notes |
|---------|----------|-------|
| Video upload (MP4, MOV) | P0 | MXF deferred to Phase 2 |
| AI transcription (source language) | P0 | GPT-4o Mini Transcribe, 10+ languages |
| AI translation to target languages | P0 | Claude-powered, 15 languages at launch |
| Subtitle timing and segmentation | P0 | Shot-change detection, reading speed enforcement |
| SRT + WebVTT export | P0 | Two most common formats |
| Basic web-based subtitle review/edit | P0 | Text editing + timing adjustment, no video playback in v1 |
| QC report (automated) | P0 | Reading speed, line length, timing violations |
| Per-minute pricing + Stripe payment | P0 | Western pricing tier only in MVP |
| Free tier (10 min/month) | P0 | Lead generation |
| User auth + project dashboard | P0 | Clerk, email + Google login |
| Cultural adaptation flagging | P1 | Flags items for review; no auto-adaptation in MVP |
| EBU-STL export | P1 | Add within 4 weeks of MVP |
| Platform profiles (Netflix, YouTube) | P1 | Rules-based QC adjustment |

### Out of scope (deferred)

| Feature | Deferred to | Reason |
|---------|-------------|--------|
| MXF upload | Phase 2 | Requires FFmpeg pipeline complexity |
| TTML/Netflix profile export | Phase 2 | Complex spec, needs validation testing |
| AI dubbing scripts | Phase 2 | Separate agent, lip-sync timing |
| Video playback in review editor | Phase 2 | Significant frontend complexity |
| Razorpay / Indian payment methods | Phase 2 | Regulatory overhead (GST, etc.) |
| SEA/India pricing tier | Phase 2 | Need market validation from Western launch first |
| Batch processing (20+ titles) | Phase 2 | MVP validates single-title workflow first |
| Glossary management | Phase 2 | Nice-to-have, not core loop |
| SDH/CC accessibility subtitles | Phase 2 | Requires speaker diarization + sound event detection |
| API access (headless) | Phase 3 | Enterprise feature |
| Self-hosted Whisper | Phase 3 | Cost optimization once volume justifies |

---

## 6. File Structure

```
autopunk-localize/
├── CLAUDE.md                          # Project context for Claude Code
├── .claude/
│   ├── agents/
│   │   ├── backend-architect.md       # FastAPI + DB design decisions
│   │   ├── agent-orchestrator.md      # Localization pipeline logic
│   │   ├── test-writer.md             # Pytest, integration tests
│   │   └── frontend-dev.md            # UI components, state management
│   ├── rules/
│   │   ├── python-backend.md          # Python conventions, paths: backend/**
│   │   ├── frontend.md                # JS/TS conventions, paths: frontend/**
│   │   └── subtitle-formats.md        # Format specs, paths: **/formats/**
│   └── settings.json
├── docs/
│   ├── PRD.md                         # This document
│   ├── ARCHITECTURE.md                # System design decisions
│   └── API.md                         # Endpoint specifications
├── backend/
│   ├── pyproject.toml
│   ├── alembic/                       # DB migrations
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings, env vars
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── job.py
│   │   │   └── subtitle.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── projects.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── export.py
│   │   │   │   └── billing.py
│   │   ├── agents/                    # Localization agent pipeline
│   │   │   ├── orchestrator.py        # Main pipeline coordinator
│   │   │   ├── transcription.py       # Whisper integration
│   │   │   ├── translation.py         # Claude translation agent
│   │   │   ├── cultural_adaptation.py # Cultural flagging agent
│   │   │   ├── qc.py                  # Quality control agent
│   │   │   └── formatting.py          # Subtitle format converters
│   │   ├── formats/                   # Subtitle format handlers
│   │   │   ├── srt.py
│   │   │   ├── webvtt.py
│   │   │   ├── ebu_stl.py
│   │   │   └── validators.py
│   │   ├── services/                  # Business logic
│   │   │   ├── job_service.py
│   │   │   ├── billing_service.py
│   │   │   └── storage_service.py
│   │   └── tasks/                     # Celery async tasks
│   │       └── localization_tasks.py
│   └── tests/
│       ├── test_agents/
│       ├── test_api/
│       ├── test_formats/
│       └── fixtures/
│           └── sample_subtitles/      # Known-good SRT/VTT for validation
├── frontend/                          # Next.js 14 (App Router) — deployed on Vercel
│   ├── package.json
│   └── src/
│       ├── app/                       # App Router pages
│       │   ├── layout.tsx
│       │   ├── page.tsx               # Landing / marketing
│       │   ├── dashboard/
│       │   │   ├── page.tsx           # Project list
│       │   │   └── [projectId]/
│       │   │       └── page.tsx       # Project detail + subtitle review
│       │   └── api/                   # Next.js API routes (auth callbacks, webhooks)
│       ├── components/
│       │   ├── upload/
│       │   ├── editor/                # Subtitle review/edit components
│       │   ├── dashboard/
│       │   └── shared/
│       └── lib/
│           ├── api-client.ts          # FastAPI backend client
│           └── auth.ts                # Clerk integration
├── infrastructure/
│   ├── docker-compose.yml             # Local dev (Postgres, Redis, MinIO)
│   ├── Dockerfile
│   └── railway.toml                   # or fly.toml
└── scripts/
    ├── seed_languages.py              # Seed supported language pairs
    └── test_pipeline.py               # End-to-end smoke test
```

---

## 7. Commands

### Development

```bash
# Setup
git clone https://github.com/ur-grue/autopunk-localize.git
cd autopunk-localize
cp .env.example .env                   # Add API keys
docker-compose up -d                   # Postgres, Redis, MinIO
cd backend && pip install -e ".[dev]"  # Install with dev deps
alembic upgrade head                   # Run migrations

# Run
uvicorn app.main:app --reload --port 8000   # Backend
cd frontend && npm run dev                    # Next.js on :3000

# Test
pytest backend/tests/ -v --cov=app           # Backend tests
pytest backend/tests/test_formats/ -v        # Format validation only

# Database
alembic revision --autogenerate -m "description"  # New migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback last

# Pipeline smoke test
python scripts/test_pipeline.py --input sample.mp4 --languages en,fr,es
```

### Deployment

```bash
# Frontend (Vercel — auto-deploys from main branch)
cd frontend && vercel

# Backend (Railway)
railway up

# Docker (production, self-hosted)
docker build -t autopunk-localize .
docker push registry/autopunk-localize:latest
```

---

## 8. Testing Requirements

### Framework and tooling

| Tool | Purpose |
|------|---------|
| pytest | Backend unit + integration tests |
| pytest-asyncio | Async endpoint testing |
| pytest-cov | Coverage reporting (target: 80% for agents/, formats/) |
| httpx | Async API client for endpoint tests |
| factory_boy | Test data factories for models |
| Playwright or Cypress | E2E frontend tests (Phase 2) |

### Test categories

| Category | Location | What it covers | When it runs |
|----------|----------|---------------|-------------|
| Unit — Agents | `tests/test_agents/` | Each agent in isolation with mocked API calls | Every commit |
| Unit — Formats | `tests/test_formats/` | SRT/WebVTT/EBU-STL parsing, generation, validation against known-good fixtures | Every commit |
| Integration — Pipeline | `tests/test_pipeline/` | Full orchestrator flow: upload → transcription → translation → QC → export | Pre-merge |
| Integration — API | `tests/test_api/` | Endpoint request/response contracts, auth, error handling | Every commit |
| Fixture validation | `tests/fixtures/sample_subtitles/` | Known-good subtitle files in each format; tests verify our output matches spec | Every commit |
| Smoke test | `scripts/test_pipeline.py` | Real API calls against a short (30s) test clip; validates end-to-end in staging | Pre-deploy |

### Critical test scenarios

1. **Format compliance:** Generate SRT for a 52-min file → validate every cue has ≤42 chars/line, ≤2 lines, reading speed ≤25 CPS
2. **Language pairs:** Test Hindi→Tamil, English→French, Korean→Thai translation output for correct script, encoding, directionality
3. **Edge cases:** Empty audio segments, overlapping speakers, music-only passages, on-screen text
4. **Idempotency:** Same input produces same output structure (content may vary due to LLM, but format/timing must be stable)
5. **Error handling:** API timeout mid-job → job resumes or fails gracefully with partial output preserved

---

## 9. Boundaries

### The system must NEVER

- Store or log video content beyond the 72-hour processing window
- Send user video content to any third party other than declared AI providers (OpenAI, Anthropic)
- Auto-publish or distribute subtitle files without explicit user confirmation
- Silently drop subtitle cues — if a segment can't be translated, it must be flagged, not deleted
- Expose one user's content, subtitles, or glossary to another user
- Make API calls to AI providers without metering them against the user's usage quota

### Performance requirements

| Metric | Target | Hard limit |
|--------|--------|-----------|
| Transcription speed | ≤0.3x real-time (52 min → <16 min) | ≤0.5x |
| Translation speed per language | ≤0.2x real-time (52 min → <11 min) | ≤0.4x |
| Total pipeline (3 languages) | ≤4 hours for 52-min file | ≤6 hours |
| API response (non-processing) | ≤200ms p95 | ≤500ms |
| Upload speed | Limited by user bandwidth, not server | — |
| Concurrent jobs per instance | 10 | 20 |

### Security requirements

- All data in transit: TLS 1.3
- All data at rest: AES-256 encryption on S3 storage
- API authentication: Bearer tokens (Clerk JWT)
- No API keys or secrets in client-side code
- CORS restricted to frontend domain only
- Rate limiting: 100 requests/min per authenticated user, 10/min unauthenticated

### Cost guardrails

**Reference scenario:** 52-min documentary, EN → 3 languages (FR, ES, HI)

| Component | Model | Tokens (in/out) | Cost |
|-----------|-------|-----------------|------|
| Transcription | GPT-4o Mini Transcribe | 52 min audio | $0.16 |
| Translation (3 languages) | Claude Sonnet 4.6 ($3/$15 per MTok) | 195K in / 63K out | $1.53 |
| Cultural adaptation flagging | Claude Sonnet 4.6 | 60K in / 15K out | $0.41 |
| QC validation (3 languages) | Claude Haiku 4.5 ($1/$5 per MTok) | 90K in / 30K out | $0.24 |
| Prompt caching savings (~40%) | — | — | -$0.58 |
| **Total API cost** | | | **$1.76** |
| **Cost per minute of content** | | | **$0.034** |

| Pricing tier | Price/min | API cost/min | Gross margin | Break-even (hosting $87/mo) |
|-------------|-----------|-------------|-------------|---------------------------|
| Western (UK/US/AU) | $5.00 | $0.034 | **99.3%** | 17 min/month |
| India/SEA | $1.50 | $0.034 | **97.7%** | 58 min/month |
| Aggressive India | $0.75 | $0.034 | **95.5%** | 116 min/month |

**Monthly hosting (fixed):** ~$62–87 (Railway $34, Vercel $20, Backblaze $3, Clerk $0–25, misc $5)

**€5K MRR target path:** ~4 Western customers at 250 min/month each, or ~22 Indian customers at 300 min/month each, or any mix.

**Cost optimization roadmap:**
- Phase 1: Prompt caching (40% savings), GPT-4o Mini Transcribe (50% cheaper than Whisper)
- Phase 2: Batch API for non-urgent jobs (50% off Claude), Haiku for simple language pairs (~70% savings)
- Phase 3: Self-hosted faster-whisper (~95% transcription savings), DeepSeek for simple QC (~85% savings)

**Budget ceiling (first 6 months):** $500/month total API spend. At current margins, this supports ~14,700 minutes of processed content — far beyond expected early volume.

---

## 10. Implementation Phases

### Phase 1: Core Pipeline (Weeks 1–8)

**Goal:** Working vertical slice — upload a video, get subtitles in 3 languages, download SRT files.

| Week | Focus | Deliverable | Verification |
|------|-------|------------|-------------|
| 1–2 | Project scaffolding + TranscriptionAgent | FastAPI skeleton, Postgres models, Whisper integration. Upload MP4 → get timestamped transcript JSON. | `pytest test_agents/test_transcription.py` passes; 30s test clip transcribed correctly. |
| 3–4 | TranslationAgent + basic pipeline | Claude-powered translation for EN→FR, EN→ES, EN→DE. Orchestrator chains transcription → translation. | `pytest test_agents/test_translation.py` passes; output is valid subtitle-ready text with timing preserved. |
| 5–6 | SRT/WebVTT formatting + QCAgent | Format generators with line-length, reading-speed, timing enforcement. QC agent validates and reports. | `pytest test_formats/` passes; generated SRT matches fixture structure. QC report generated. |
| 7–8 | Minimal frontend + auth + upload/download | Project creation, file upload to S3, job submission, status polling, download ZIP. Clerk auth. | Manual smoke test: upload video → wait → download subtitles. Free tier functional. |

**Phase 1 exit criteria:** A real 52-min documentary can be uploaded, subtitled into 3 languages, and the SRT files downloaded — all within 4 hours.

### Phase 2: Review + Polish (Weeks 9–14)

| Week | Focus | Deliverable |
|------|-------|------------|
| 9–10 | Web-based subtitle editor | Text editing, timing adjustment, flagged segment highlighting. No video playback yet. |
| 11–12 | Cultural adaptation flagging + EBU-STL export | CulturalAdaptationAgent identifies items for review. EBU-STL output passes format validation. |
| 13–14 | Billing (Stripe) + platform profiles | Per-minute pricing, Stripe checkout, usage dashboard. Netflix/YouTube/BBC QC profiles. |

**Phase 2 exit criteria:** 5 beta users (from Sebastian's network) have completed real projects and provided feedback. Stripe payments functional.

### Phase 3: Market Expansion (Weeks 15–24)

| Week | Focus | Deliverable |
|------|-------|------------|
| 15–17 | Indian language support (Hindi, Tamil, Telugu, Malayalam, Bengali) | Script-aware translation, honorific handling, JioHotstar/ZEE5 platform profiles. |
| 18–20 | SEA language support (Korean→Thai/Vietnamese/Indonesian) + Razorpay | K-drama pipeline, SEA platform profiles, India pricing tier, Razorpay integration. |
| 21–22 | Batch processing + glossary management | Multi-title queue, persistent glossaries, distributor workflow. |
| 23–24 | Dubbing script generation (basic) | Speaker-identified scripts with timing cues, lip-sync duration markers. No voice synthesis. |

**Phase 3 exit criteria:** 10 paying customers across at least 2 geographic markets. €5K MRR trajectory visible.

### Phase 4: Scale (Weeks 25+)

- TTML/Netflix profile export
- SDH/CC accessibility subtitles
- Self-hosted Whisper for margin improvement
- API access for headless integration
- Video playback in review editor
- Agent Teams feature: metadata agent, compliance agent alongside localization
