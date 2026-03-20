"""Tests for the TranslationAgent."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.agents.schemas import (
    TranscriptionSegment,
    TranslationInput,
    TranslationOutput,
)
from app.agents.translation import TranslationAgent
from app.exceptions import TranslationError


@pytest.fixture
def source_segments() -> list[TranscriptionSegment]:
    """Create sample source segments for translation tests."""
    return [
        TranscriptionSegment(
            index=1,
            start_ms=0,
            end_ms=4200,
            text="Hello and welcome to this documentary about marine life.",
        ),
        TranscriptionSegment(
            index=2,
            start_ms=4500,
            end_ms=9800,
            text="The ocean covers over 70 percent of our planet.",
        ),
        TranscriptionSegment(
            index=3,
            start_ms=10200,
            end_ms=18500,
            text="It is home to millions of species, many of which remain undiscovered.",
        ),
    ]


@pytest.fixture
def mock_claude_response() -> MagicMock:
    """Create a mock Claude API response with translated segments."""
    translated_json = json.dumps([
        {
            "index": 1,
            "translated_text": "Bonjour et bienvenue dans ce documentaire sur la vie marine.",
            "flags": [],
        },
        {
            "index": 2,
            "translated_text": "L'océan couvre plus de 70 pour cent de notre planète.",
            "flags": [],
        },
        {
            "index": 3,
            "translated_text": "Il abrite des millions d'espèces, dont beaucoup restent encore inconnues.",
            "flags": [],
        },
    ])

    response = MagicMock()
    response.content = [MagicMock(type="text", text=translated_json)]
    response.usage = MagicMock(input_tokens=500, output_tokens=200)
    return response


@pytest.fixture
def mock_anthropic_client(mock_claude_response) -> MagicMock:
    """Create a mock Anthropic AsyncClient."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=mock_claude_response)
    return client


@pytest.fixture
def agent(mock_anthropic_client) -> TranslationAgent:
    """Create a TranslationAgent with mocked Anthropic client."""
    agent = TranslationAgent(anthropic_api_key="test-key")
    agent._client = mock_anthropic_client
    return agent


@pytest.fixture
def translation_input(source_segments) -> TranslationInput:
    """Create a valid TranslationInput."""
    return TranslationInput(
        job_id=uuid.uuid4(),
        segments=source_segments,
        source_language="en",
        target_language="fr",
    )


class TestTranslationAgentProcess:
    """Tests for TranslationAgent.process()."""

    async def test_process_valid_segments_returns_translations(
        self, agent, translation_input
    ):
        """Happy path: source segments translated to target language."""
        result = await agent.process(translation_input)

        assert isinstance(result, TranslationOutput)
        assert result.job_id == translation_input.job_id
        assert result.source_language == "en"
        assert result.target_language == "fr"
        assert len(result.segments) == 3
        assert result.api_cost_usd > 0

    async def test_process_preserves_all_segments_no_drops(
        self, agent, translation_input
    ):
        """Critical rule: never silently drop subtitle cues."""
        result = await agent.process(translation_input)

        assert len(result.segments) == len(translation_input.segments)
        indices = [s.index for s in result.segments]
        assert indices == [1, 2, 3]

    async def test_process_preserves_timing(
        self, agent, translation_input
    ):
        """Translated segments must keep original timing."""
        result = await agent.process(translation_input)

        for i, seg in enumerate(result.segments):
            assert seg.start_ms == translation_input.segments[i].start_ms
            assert seg.end_ms == translation_input.segments[i].end_ms

    async def test_process_includes_original_text(
        self, agent, translation_input
    ):
        """Each translated segment includes the original source text."""
        result = await agent.process(translation_input)

        for i, seg in enumerate(result.segments):
            assert seg.original_text == translation_input.segments[i].text

    async def test_process_translated_text_differs_from_source(
        self, agent, translation_input
    ):
        """Translated text should differ from source (it's a translation)."""
        result = await agent.process(translation_input)

        for seg in result.segments:
            assert seg.translated_text != seg.original_text

    async def test_process_tracks_api_usage(
        self, agent, translation_input
    ):
        """API usage metadata includes model and token counts."""
        result = await agent.process(translation_input)

        assert result.api_usage["model"] == "claude-sonnet-4-6-20250514"
        assert result.api_usage["input_tokens"] == 500
        assert result.api_usage["output_tokens"] == 200
        assert result.api_usage["batches"] == 1

    async def test_process_calculates_cost_correctly(
        self, agent, translation_input, mock_claude_response
    ):
        """Cost calculation: $3/MTok input + $15/MTok output."""
        mock_claude_response.usage.input_tokens = 100_000
        mock_claude_response.usage.output_tokens = 30_000

        result = await agent.process(translation_input)

        expected_cost = round(
            (100_000 / 1_000_000) * 3.0 + (30_000 / 1_000_000) * 15.0, 6
        )
        assert result.api_cost_usd == expected_cost


class TestTranslationAgentBatching:
    """Tests for segment batching."""

    async def test_large_input_batched(
        self, agent, mock_anthropic_client, mock_claude_response
    ):
        """100 segments should be split into 3 batches of 40/40/20."""
        segments = [
            TranscriptionSegment(
                index=i + 1,
                start_ms=i * 1000,
                end_ms=(i + 1) * 1000,
                text=f"Segment {i + 1} text.",
            )
            for i in range(100)
        ]

        # Mock responses for each batch — return matching indices
        def make_response(batch_segments):
            translated = [
                {"index": s.index, "translated_text": f"Traduit {s.index}", "flags": []}
                for s in batch_segments
            ]
            resp = MagicMock()
            resp.content = [MagicMock(type="text", text=json.dumps(translated))]
            resp.usage = MagicMock(input_tokens=500, output_tokens=200)
            return resp

        call_count = 0
        all_batches = [segments[i:i+40] for i in range(0, 100, 40)]

        async def mock_create(**kwargs):
            nonlocal call_count
            batch = all_batches[call_count]
            call_count += 1
            return make_response(batch)

        mock_anthropic_client.messages.create = AsyncMock(side_effect=mock_create)

        input_data = TranslationInput(
            job_id=uuid.uuid4(),
            segments=segments,
            source_language="en",
            target_language="fr",
        )

        result = await agent.process(input_data)

        assert len(result.segments) == 100
        assert call_count == 3  # 40 + 40 + 20
        assert result.api_usage["batches"] == 3


class TestTranslationAgentRetry:
    """Tests for retry behavior."""

    async def test_retries_on_api_timeout(
        self, agent, translation_input, mock_claude_response
    ):
        """API timeout triggers retry."""
        agent._client.messages.create = AsyncMock(
            side_effect=[
                anthropic.APITimeoutError(request=MagicMock()),
                mock_claude_response,
            ]
        )

        with patch("app.agents.translation.asyncio.sleep", new_callable=AsyncMock):
            result = await agent.process(translation_input)

        assert isinstance(result, TranslationOutput)
        assert agent._client.messages.create.call_count == 2

    async def test_retries_on_rate_limit(
        self, agent, translation_input, mock_claude_response
    ):
        """Rate limit error triggers retry."""
        agent._client.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError(
                    message="Rate limited",
                    response=MagicMock(status_code=429),
                    body=None,
                ),
                mock_claude_response,
            ]
        )

        with patch("app.agents.translation.asyncio.sleep", new_callable=AsyncMock):
            result = await agent.process(translation_input)

        assert isinstance(result, TranslationOutput)

    async def test_raises_on_persistent_failure(
        self, agent, translation_input
    ):
        """3 consecutive failures raise TranslationError."""
        agent._client.messages.create = AsyncMock(
            side_effect=anthropic.APITimeoutError(request=MagicMock())
        )

        with patch("app.agents.translation.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TranslationError, match="failed after 3 attempts"):
                await agent.process(translation_input)


class TestTranslationAgentParsing:
    """Tests for response parsing edge cases."""

    async def test_handles_json_with_code_fences(
        self, agent, translation_input
    ):
        """Claude sometimes wraps JSON in ```json code fences."""
        fenced_json = '```json\n' + json.dumps([
            {"index": 1, "translated_text": "Bonjour", "flags": []},
            {"index": 2, "translated_text": "L'océan", "flags": []},
            {"index": 3, "translated_text": "Il abrite", "flags": []},
        ]) + '\n```'

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=fenced_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        agent._client.messages.create = AsyncMock(return_value=resp)

        result = await agent.process(translation_input)
        assert len(result.segments) == 3

    async def test_handles_missing_segment_in_response(
        self, agent, translation_input
    ):
        """Missing segment in Claude response is flagged, not dropped."""
        partial_json = json.dumps([
            {"index": 1, "translated_text": "Bonjour", "flags": []},
            # index 2 missing
            {"index": 3, "translated_text": "Il abrite", "flags": []},
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=partial_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        agent._client.messages.create = AsyncMock(return_value=resp)

        result = await agent.process(translation_input)

        assert len(result.segments) == 3
        missing_seg = result.segments[1]
        assert "untranslated" in missing_seg.flags
        assert missing_seg.translated_text == missing_seg.original_text

    async def test_handles_invalid_json_response(
        self, agent, translation_input
    ):
        """Invalid JSON from Claude flags all segments as untranslated."""
        resp = MagicMock()
        resp.content = [MagicMock(type="text", text="This is not JSON")]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        agent._client.messages.create = AsyncMock(return_value=resp)

        result = await agent.process(translation_input)

        assert len(result.segments) == 3
        for seg in result.segments:
            assert "untranslated" in seg.flags

    async def test_flags_propagated(
        self, agent, translation_input
    ):
        """Flags from Claude (cultural_ref, etc.) are preserved."""
        flagged_json = json.dumps([
            {"index": 1, "translated_text": "Bonjour", "flags": ["cultural_ref"]},
            {"index": 2, "translated_text": "L'océan", "flags": ["uncertain"]},
            {"index": 3, "translated_text": "Il abrite", "flags": []},
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=flagged_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        agent._client.messages.create = AsyncMock(return_value=resp)

        result = await agent.process(translation_input)

        assert "cultural_ref" in result.segments[0].flags
        assert "uncertain" in result.segments[1].flags
        assert result.segments[2].flags == []


class TestCalculateCost:
    """Tests for cost calculation."""

    def test_cost_typical_translation(self):
        """65K in + 21K out for one language of a 52-min doc."""
        agent = TranslationAgent(anthropic_api_key="test-key")
        # $3/MTok input + $15/MTok output
        cost = agent._calculate_cost(65_000, 21_000)
        expected = round((65_000 / 1_000_000) * 3.0 + (21_000 / 1_000_000) * 15.0, 6)
        assert cost == expected

    def test_cost_zero_tokens(self):
        """Zero tokens = zero cost."""
        agent = TranslationAgent(anthropic_api_key="test-key")
        assert agent._calculate_cost(0, 0) == 0.0
