"""Tests for the FormattingAgent."""

import uuid

import pytest

from app.agents.formatting import FormattingAgent
from app.agents.schemas import (
    FormattingInput,
    FormattingOutput,
    TranscriptionSegment,
    TranslationSegment,
)
from app.exceptions import ValidationError


@pytest.fixture
def formatter() -> FormattingAgent:
    return FormattingAgent()


@pytest.fixture
def translation_segments() -> list[TranslationSegment]:
    return [
        TranslationSegment(
            index=1, start_ms=0, end_ms=4200,
            original_text="Hello.", translated_text="Bonjour.",
        ),
        TranslationSegment(
            index=2, start_ms=4500, end_ms=9800,
            original_text="World.", translated_text="Monde.",
        ),
    ]


@pytest.fixture
def transcription_segments() -> list[TranscriptionSegment]:
    return [
        TranscriptionSegment(
            index=1, start_ms=0, end_ms=4200, text="Hello.",
        ),
        TranscriptionSegment(
            index=2, start_ms=4500, end_ms=9800, text="World.",
        ),
    ]


class TestFormattingAgentSRT:
    """Tests for SRT output."""

    async def test_generate_srt_from_translations(
        self, formatter, translation_segments
    ):
        """Generate SRT from TranslationSegment objects."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=translation_segments,
            language="fr",
            format="srt",
        )

        result = await formatter.process(input_data)

        assert isinstance(result, FormattingOutput)
        assert result.format == "srt"
        assert "Bonjour." in result.content
        assert "Monde." in result.content
        assert "00:00:00,000 --> 00:00:04,200" in result.content

    async def test_generate_srt_from_transcription(
        self, formatter, transcription_segments
    ):
        """Generate SRT from TranscriptionSegment objects."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=transcription_segments,
            language="en",
            format="srt",
        )

        result = await formatter.process(input_data)

        assert "Hello." in result.content
        assert "00:00:04,500 --> 00:00:09,800" in result.content


class TestFormattingAgentWebVTT:
    """Tests for WebVTT output."""

    async def test_generate_webvtt(self, formatter, translation_segments):
        """Generate WebVTT from TranslationSegment objects."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=translation_segments,
            language="fr",
            format="webvtt",
        )

        result = await formatter.process(input_data)

        assert result.format == "webvtt"
        assert result.content.startswith("WEBVTT")
        assert "Bonjour." in result.content
        assert "00:00:00.000 --> 00:00:04.200" in result.content

    async def test_webvtt_uses_dot_timecodes(
        self, formatter, translation_segments
    ):
        """WebVTT uses dots, not commas in timecodes."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=translation_segments,
            language="fr",
            format="webvtt",
        )

        result = await formatter.process(input_data)

        assert "," not in result.content.split("\n")[3]  # timecode line


class TestFormattingAgentValidation:
    """Tests for input validation."""

    async def test_unsupported_format_raises(
        self, formatter, translation_segments
    ):
        """Unsupported format raises ValidationError."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=translation_segments,
            language="fr",
            format="ass",
        )

        with pytest.raises(ValidationError, match="Unsupported format"):
            await formatter.process(input_data)

    async def test_empty_segments(self, formatter):
        """Empty segment list produces minimal valid output."""
        input_data = FormattingInput(
            job_id=uuid.uuid4(),
            segments=[],
            language="fr",
            format="srt",
        )

        result = await formatter.process(input_data)
        assert result.content.strip() == ""
