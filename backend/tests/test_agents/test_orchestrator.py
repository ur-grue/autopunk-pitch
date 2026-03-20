"""Tests for the pipeline orchestrator."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.orchestrator import PipelineOrchestrator
from app.agents.schemas import (
    PipelineInput,
    PipelineOutput,
    TranscriptionOutput,
    TranscriptionSegment,
    TranslationOutput,
    TranslationSegment,
)


@pytest.fixture
def mock_transcription_output() -> TranscriptionOutput:
    """Create a mock transcription output."""
    return TranscriptionOutput(
        job_id=uuid.uuid4(),
        segments=[
            TranscriptionSegment(
                index=1, start_ms=0, end_ms=4200,
                text="Hello and welcome.",
            ),
            TranscriptionSegment(
                index=2, start_ms=4500, end_ms=9800,
                text="The ocean is vast.",
            ),
        ],
        language="en",
        duration_ms=9800,
        api_cost_usd=0.0015,
        api_usage={"model": "gpt-4o-mini-transcribe"},
    )


@pytest.fixture
def make_mock_translation_output():
    """Factory for mock translation outputs."""

    def _make(job_id: uuid.UUID, target_lang: str) -> TranslationOutput:
        return TranslationOutput(
            job_id=job_id,
            segments=[
                TranslationSegment(
                    index=1, start_ms=0, end_ms=4200,
                    original_text="Hello and welcome.",
                    translated_text=f"[{target_lang}] Hello and welcome.",
                ),
                TranslationSegment(
                    index=2, start_ms=4500, end_ms=9800,
                    original_text="The ocean is vast.",
                    translated_text=f"[{target_lang}] The ocean is vast.",
                ),
            ],
            source_language="en",
            target_language=target_lang,
            api_cost_usd=0.51,
            api_usage={"model": "claude-sonnet-4-6-20250514", "input_tokens": 500, "output_tokens": 200},
        )

    return _make


@pytest.fixture
def orchestrator(
    mock_transcription_output, make_mock_translation_output
) -> PipelineOrchestrator:
    """Create a PipelineOrchestrator with mocked agents."""
    orch = PipelineOrchestrator(
        openai_api_key="test-openai",
        anthropic_api_key="test-anthropic",
    )

    # Mock transcription agent
    orch._transcription_agent = MagicMock()
    orch._transcription_agent.process = AsyncMock(
        return_value=mock_transcription_output
    )

    # Mock translation agent — returns lang-specific output
    async def mock_translate(input):
        return make_mock_translation_output(
            input.job_id, input.target_language
        )

    orch._translation_agent = MagicMock()
    orch._translation_agent.process = AsyncMock(side_effect=mock_translate)

    return orch


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator.process()."""

    async def test_pipeline_single_language(self, orchestrator):
        """Pipeline with one target language completes successfully."""
        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr"],
        )

        result = await orchestrator.process(input_data)

        assert isinstance(result, PipelineOutput)
        assert result.transcription.language == "en"
        assert "fr" in result.translations
        assert len(result.translations["fr"].segments) == 2
        assert result.total_cost_usd > 0

    async def test_pipeline_multiple_languages_parallel(self, orchestrator):
        """Pipeline translates to multiple languages."""
        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr", "es", "de"],
        )

        result = await orchestrator.process(input_data)

        assert len(result.translations) == 3
        assert "fr" in result.translations
        assert "es" in result.translations
        assert "de" in result.translations

    async def test_pipeline_cost_aggregation(self, orchestrator):
        """Total cost includes transcription + all translations."""
        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr", "es"],
        )

        result = await orchestrator.process(input_data)

        expected = 0.0015 + (0.51 * 2)  # transcription + 2 translations
        assert abs(result.total_cost_usd - expected) < 0.001

    async def test_pipeline_usage_tracking(self, orchestrator):
        """API usage dict contains transcription and translation details."""
        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr"],
        )

        result = await orchestrator.process(input_data)

        assert "transcription" in result.total_api_usage
        assert "translations" in result.total_api_usage
        assert "fr" in result.total_api_usage["translations"]

    async def test_pipeline_calls_transcription_first(self, orchestrator):
        """Transcription runs before translation."""
        call_order = []

        original_transcribe = orchestrator._transcription_agent.process

        async def track_transcribe(input):
            call_order.append("transcribe")
            return await original_transcribe(input)

        original_translate = orchestrator._translation_agent.process

        async def track_translate(input):
            call_order.append(f"translate_{input.target_language}")
            return await original_translate(input)

        orchestrator._transcription_agent.process = AsyncMock(
            side_effect=track_transcribe
        )
        orchestrator._translation_agent.process = AsyncMock(
            side_effect=track_translate
        )

        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr"],
        )

        await orchestrator.process(input_data)

        assert call_order[0] == "transcribe"
        assert "translate_fr" in call_order[1:]

    async def test_pipeline_preserves_segment_count(self, orchestrator):
        """All segments from transcription appear in translations."""
        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr"],
        )

        result = await orchestrator.process(input_data)

        source_count = len(result.transcription.segments)
        for lang, translation in result.translations.items():
            assert len(translation.segments) == source_count

    async def test_pipeline_partial_translation_failure(self, orchestrator):
        """If one language fails, others still complete."""
        async def mock_translate(input):
            if input.target_language == "de":
                raise Exception("German translation failed")
            return TranslationOutput(
                job_id=input.job_id,
                segments=[
                    TranslationSegment(
                        index=1, start_ms=0, end_ms=4200,
                        original_text="Hello",
                        translated_text=f"[{input.target_language}] Hello",
                    ),
                    TranslationSegment(
                        index=2, start_ms=4500, end_ms=9800,
                        original_text="Ocean",
                        translated_text=f"[{input.target_language}] Ocean",
                    ),
                ],
                source_language="en",
                target_language=input.target_language,
                api_cost_usd=0.51,
                api_usage={},
            )

        orchestrator._translation_agent.process = AsyncMock(
            side_effect=mock_translate
        )

        input_data = PipelineInput(
            job_id=uuid.uuid4(),
            audio_file_path="/tmp/test.mp3",
            source_language="en",
            target_languages=["fr", "de", "es"],
        )

        result = await orchestrator.process(input_data)

        # fr and es succeed, de fails
        assert "fr" in result.translations
        assert "es" in result.translations
        assert "de" not in result.translations
