"""Pydantic request/response schemas for API v1."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.agents.schemas import TranscriptionSegment, TranslationSegment


# --- Projects ---


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(min_length=1, max_length=255)
    source_language: str = Field(min_length=2, max_length=10)
    target_languages: list[str] = Field(min_length=1, max_length=10)


class ProjectResponse(BaseModel):
    """Response for a project."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    source_language: str
    target_languages: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Response for a project with jobs."""

    jobs: list["JobResponse"] = []


# --- Jobs ---


class JobResponse(BaseModel):
    """Response for a job."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: str
    duration_seconds: float | None = None
    cost_usd: float | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TranscriptResponse(BaseModel):
    """Response for a completed transcription."""

    job_id: uuid.UUID
    language: str
    duration_ms: int
    segments: list[TranscriptionSegment]


class TranslatedSubtitlesResponse(BaseModel):
    """Response for translated subtitles in a specific language."""

    job_id: uuid.UUID
    source_language: str
    target_language: str
    duration_ms: int
    segments: list[TranslationSegment]


class PipelineLanguagesResponse(BaseModel):
    """Response listing available languages for a completed pipeline job."""

    job_id: uuid.UUID
    source_language: str
    target_languages: list[str]


# --- Subtitle Editor ---


class SubtitleResponse(BaseModel):
    """Response for a single subtitle cue."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    index: int
    start_ms: int
    end_ms: int
    text: str
    language: str
    speaker: str | None = None
    confidence: float | None = None
    flags: list[str] | None = None


class SubtitleUpdate(BaseModel):
    """Request body for updating a subtitle cue."""

    text: str | None = None
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)
    speaker: str | None = None


class SubtitleBatchUpdate(BaseModel):
    """Request body for batch-updating multiple subtitle cues."""

    updates: list["SubtitleBatchItem"] = Field(min_length=1, max_length=500)


class SubtitleBatchItem(BaseModel):
    """A single item in a batch subtitle update."""

    id: uuid.UUID
    text: str | None = None
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)


class SubtitleSplitRequest(BaseModel):
    """Request to split a subtitle cue at a given position."""

    split_at_ms: int = Field(ge=0, description="Timecode to split at (ms)")
    first_text: str = Field(description="Text for the first half")
    second_text: str = Field(description="Text for the second half")


class SubtitleListResponse(BaseModel):
    """Response for listing subtitles for a job+language."""

    job_id: uuid.UUID
    language: str
    total: int
    subtitles: list[SubtitleResponse]


# --- Billing ---


class CheckoutRequest(BaseModel):
    """Request to start a checkout session for a job."""

    job_id: uuid.UUID


class CheckoutResponse(BaseModel):
    """Response with Stripe checkout URL."""

    checkout_url: str
    invoice_id: uuid.UUID


class InvoiceResponse(BaseModel):
    """Response for an invoice record."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID | None = None
    amount_usd: float
    duration_minutes: float
    status: str
    description: str | None = None
    created_at: datetime


class UsageResponse(BaseModel):
    """Response for user usage summary."""

    plan: str
    monthly_minutes_used: int
    monthly_minutes_limit: int
    total_spent_usd: float
    invoice_count: int


# --- Platform Profiles ---


class PlatformProfileResponse(BaseModel):
    """Response for a platform QC profile."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    display_name: str
    description: str | None = None
    max_chars_per_line: int
    max_lines_per_cue: int
    max_cps: float
    min_duration_ms: int
    min_gap_ms: int
    settings: dict | None = None
