# Autopunk Localize

**Broadcast Quality. Indie Pricing.**

AI-powered subtitle localization for independent producers, mid-size broadcasters, and content distributors. Upload a video, get broadcast-ready subtitles in multiple languages — transcription, translation, cultural adaptation, and QC in a single automated pipeline.

## The Problem

Professional localization costs €50–175/min per language and takes 2–5 weeks. Indie producers either skip international markets entirely or use consumer tools that get rejected by broadcasters and platforms.

## The Solution

Autopunk Localize delivers broadcast-compliant subtitles at **€5–15/min** (Western markets) and **€1–3/min** (South/SEA markets) — a 10x cost reduction with turnaround in hours, not weeks.

### Pipeline

```
Video Upload → Transcription → Translation → Cultural Adaptation → QC → Export
                (GPT-4o Mini)   (Claude Sonnet)  (Claude Sonnet)    (Claude Haiku)
```

- **Transcription** — Word-level timestamps via GPT-4o Mini Transcribe ($0.003/min)
- **Translation** — Context-aware, parallel multi-language translation via Claude Sonnet
- **Cultural Adaptation** — Flags idioms, cultural references, and units for review
- **QC Validation** — Automated reading speed, line length, timing, and shot-change checks
- **Export** — SRT, WebVTT, and EBU-STL with Netflix/BBC/YouTube profile compliance

### Cost Example

52-min documentary → 3 languages (FR, ES, HI):

| Component | Cost |
|-----------|------|
| Transcription | $0.16 |
| Translation (3 langs) | $1.53 |
| Cultural adaptation | $0.41 |
| QC (3 langs) | $0.24 |
| **Total API cost** | **$1.76** |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Celery + PostgreSQL |
| AI | GPT-4o Mini (transcription), Claude Sonnet (translation), Claude Haiku (QC) |
| Frontend | Next.js 14 + Tailwind CSS + Clerk Auth |
| Storage | S3-compatible (MinIO / AWS) |
| Deployment | Railway (backend) + Vercel (frontend) |

## Project Structure

```
backend/
  app/
    agents/         # Pipeline agents (transcription, translation, QC, formatting)
    api/v1/         # REST endpoints (jobs, projects, subtitles, export, billing)
    models/         # SQLAlchemy ORM (user, project, job, subtitle, invoice)
    formats/        # SRT, WebVTT, EBU-STL converters + validators
    services/       # Storage, audio extraction, billing
    tasks/          # Celery async pipeline tasks
  tests/            # Unit + integration tests (~2,500 lines)
  alembic/          # Database migrations

frontend/
  src/
    app/            # Next.js App Router pages
    components/     # UI components
    lib/            # API client + auth utilities
```

## Getting Started

```bash
# Backend
cd backend
pip install -e ".[dev]"
cp .env.example .env        # Add API keys
alembic upgrade head        # Create database tables
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

## Status

**Phase 1 (MVP)** — In development

- [x] Pipeline agents (transcription, translation, cultural adaptation, QC, formatting)
- [x] REST API (jobs, projects, subtitles, export, billing)
- [x] Database models + migrations
- [x] Format exporters (SRT, WebVTT, EBU-STL)
- [x] Auth (Clerk JWT)
- [x] Test suite
- [ ] Frontend completion (editor, upload flow)
- [ ] E2E integration testing
- [ ] Deployment

## Author

**Sebastian Nuss** — [autopunk.tv](https://autopunk.tv)

## License

Proprietary. All rights reserved.
