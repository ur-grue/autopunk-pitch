"""Pydantic schemas shared across pipeline agents.

These define the contract between agents — TranscriptionAgent outputs
TranscriptionOutput, which downstream agents (TranslationAgent, QCAgent)
consume.
"""

import uuid

from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    """Word-level timestamp from transcription."""

    word: str
    start_ms: int
    end_ms: int


class TranscriptionSegment(BaseModel):
    """A single transcribed segment with timing.

    All timing is in milliseconds (integers) to avoid float precision issues.
    """

    index: int = Field(ge=1, description="1-based cue sequence number")
    start_ms: int = Field(ge=0, description="Start time in milliseconds")
    end_ms: int = Field(ge=0, description="End time in milliseconds")
    text: str = Field(min_length=0, description="Transcribed text")
    confidence: float | None = Field(
        default=None, description="Avg log probability from transcription (negative values expected)"
    )
    words: list[WordTimestamp] | None = Field(
        default=None, description="Word-level timestamps if available"
    )


class TranscriptionInput(BaseModel):
    """Input to the TranscriptionAgent."""

    job_id: uuid.UUID
    audio_file_path: str = Field(description="Local temp path to extracted audio")
    source_language: str = Field(
        min_length=2, max_length=10, description="ISO 639-1 language code"
    )
    prompt: str | None = Field(
        default=None,
        description="Optional context prompt for better accuracy",
    )


class TranscriptionOutput(BaseModel):
    """Output from the TranscriptionAgent."""

    job_id: uuid.UUID
    segments: list[TranscriptionSegment]
    language: str
    duration_ms: int = Field(ge=0, description="Total audio duration in ms")
    api_cost_usd: float = Field(ge=0.0, description="API cost for this call")
    api_usage: dict = Field(
        default_factory=dict,
        description="Detailed usage: model, duration, etc.",
    )


# --- Translation schemas ---


class TranslationSegment(BaseModel):
    """A single translated subtitle segment with preserved timing."""

    index: int = Field(ge=1, description="1-based cue sequence number")
    start_ms: int = Field(ge=0, description="Start time in milliseconds")
    end_ms: int = Field(ge=0, description="End time in milliseconds")
    original_text: str = Field(description="Source language text")
    translated_text: str = Field(description="Translated text")
    flags: list[str] = Field(
        default_factory=list,
        description="Issues: untranslated, low_confidence, cultural_ref",
    )


class TranslationInput(BaseModel):
    """Input to the TranslationAgent."""

    job_id: uuid.UUID
    segments: list[TranscriptionSegment] = Field(
        description="Source segments from transcription"
    )
    source_language: str = Field(
        min_length=2, max_length=10, description="Source ISO 639-1 code"
    )
    target_language: str = Field(
        min_length=2, max_length=10, description="Target ISO 639-1 code"
    )


class TranslationOutput(BaseModel):
    """Output from the TranslationAgent for a single language."""

    job_id: uuid.UUID
    segments: list[TranslationSegment]
    source_language: str
    target_language: str
    api_cost_usd: float = Field(ge=0.0, description="API cost for this call")
    api_usage: dict = Field(
        default_factory=dict,
        description="Detailed usage: model, tokens, etc.",
    )


# --- Pipeline orchestrator schemas ---


class PipelineInput(BaseModel):
    """Input to the full localization pipeline."""

    job_id: uuid.UUID
    audio_file_path: str = Field(description="Local temp path to extracted audio")
    source_language: str = Field(min_length=2, max_length=10)
    target_languages: list[str] = Field(
        min_length=1, description="Target ISO 639-1 codes"
    )


class PipelineOutput(BaseModel):
    """Output from the full localization pipeline."""

    job_id: uuid.UUID
    transcription: TranscriptionOutput
    translations: dict[str, TranslationOutput] = Field(
        description="Keyed by target language code"
    )
    total_cost_usd: float = Field(ge=0.0)
    total_api_usage: dict = Field(default_factory=dict)


# --- QC schemas ---


class QCIssueSchema(BaseModel):
    """A quality control issue identified by the QCAgent."""

    cue_index: int = Field(ge=1)
    severity: str = Field(description="error, warning, or info")
    rule: str = Field(description="Rule identifier")
    message: str
    suggestion: str | None = Field(
        default=None, description="Suggested fix from AI"
    )


class QCInput(BaseModel):
    """Input to the QCAgent."""

    job_id: uuid.UUID
    segments: list[TranslationSegment] = Field(
        description="Translated segments to validate"
    )
    source_language: str
    target_language: str


class QCOutput(BaseModel):
    """Output from the QCAgent."""

    job_id: uuid.UUID
    target_language: str
    issues: list[QCIssueSchema]
    score: int = Field(ge=0, le=100, description="Quality score 0-100")
    api_cost_usd: float = Field(ge=0.0)
    api_usage: dict = Field(default_factory=dict)


# --- Cultural adaptation schemas ---


class CulturalAdaptationItem(BaseModel):
    """A single cultural item flagged for human review.

    Represents a subtitle cue that contains culturally specific content
    requiring adaptation for the target audience.
    """

    cue_index: int = Field(ge=1, description="1-based cue sequence number")
    category: str = Field(
        description=(
            "Item type: idiom, measurement, date_format, currency, "
            "proper_noun, cultural_ref, humor, formality"
        )
    )
    original_text: str = Field(description="Full original cue text")
    flagged_text: str = Field(
        description="Specific substring that triggered the flag"
    )
    suggestion: str | None = Field(
        default=None,
        description="Suggested culturally adapted replacement, if applicable",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Agent confidence that this genuinely requires adaptation",
    )


class CulturalAdaptationInput(BaseModel):
    """Input to the CulturalAdaptationAgent."""

    job_id: uuid.UUID
    segments: list[TranslationSegment] = Field(
        description="Translated segments to analyse for cultural items"
    )
    source_language: str = Field(
        min_length=2, max_length=10, description="Source ISO 639-1 code"
    )
    target_language: str = Field(
        min_length=2, max_length=10, description="Target ISO 639-1 code"
    )


class CulturalAdaptationOutput(BaseModel):
    """Output from the CulturalAdaptationAgent."""

    job_id: uuid.UUID
    target_language: str
    items: list[CulturalAdaptationItem]
    item_count: int = Field(ge=0, description="Total flagged items")
    api_cost_usd: float = Field(ge=0.0, description="API cost for this call")
    api_usage: dict = Field(
        default_factory=dict,
        description="Detailed usage: model, tokens, batches.",
    )


# --- Formatting schemas ---


class FormattingInput(BaseModel):
    """Input to the FormattingAgent."""

    job_id: uuid.UUID
    segments: list[TranslationSegment] | list[TranscriptionSegment]
    language: str
    format: str = Field(description="srt or webvtt")


class FormattingOutput(BaseModel):
    """Output from the FormattingAgent."""

    job_id: uuid.UUID
    language: str
    format: str
    content: str = Field(description="Formatted subtitle file content")
