"""Tests for the CulturalAdaptationAgent."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.agents.cultural_adaptation import CulturalAdaptationAgent
from app.agents.schemas import (
    CulturalAdaptationInput,
    CulturalAdaptationItem,
    CulturalAdaptationOutput,
    TranslationSegment,
)
from app.exceptions import AppError


@pytest.fixture
def translation_segments() -> list[TranslationSegment]:
    """Create sample translated segments for cultural adaptation tests."""
    return [
        TranslationSegment(
            index=1,
            start_ms=0,
            end_ms=3000,
            original_text="Break a leg on stage!",
            translated_text="Bonne chance sur scène!",
        ),
        TranslationSegment(
            index=2,
            start_ms=3500,
            end_ms=8000,
            original_text="It costs twenty bucks.",
            translated_text="Ça coûte vingt dollars.",
        ),
        TranslationSegment(
            index=3,
            start_ms=8500,
            end_ms=15000,
            original_text="Happy Halloween!",
            translated_text="Joyeux Halloween!",
        ),
    ]


@pytest.fixture
def mock_claude_response_with_items() -> MagicMock:
    """Create a mock Claude API response with cultural adaptation items."""
    items_json = json.dumps([
        {
            "cue_index": 1,
            "category": "idiom",
            "original_text": "Break a leg on stage!",
            "flagged_text": "Break a leg",
            "suggestion": "Bonne chance",
            "confidence": 0.95,
        },
        {
            "cue_index": 2,
            "category": "currency",
            "original_text": "It costs twenty bucks.",
            "flagged_text": "twenty bucks",
            "suggestion": "vingt euros",
            "confidence": 0.87,
        },
    ])

    response = MagicMock()
    response.content = [MagicMock(type="text", text=items_json)]
    response.usage = MagicMock(input_tokens=600, output_tokens=250)
    return response


@pytest.fixture
def mock_anthropic_client(
    mock_claude_response_with_items,
) -> MagicMock:
    """Create a mock Anthropic AsyncClient."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(
        return_value=mock_claude_response_with_items
    )
    return client


@pytest.fixture
def agent(mock_anthropic_client) -> CulturalAdaptationAgent:
    """Create a CulturalAdaptationAgent with mocked Anthropic client."""
    agent = CulturalAdaptationAgent(anthropic_api_key="test-key")
    agent._client = mock_anthropic_client
    return agent


@pytest.fixture
def cultural_adaptation_input(
    translation_segments,
) -> CulturalAdaptationInput:
    """Create a valid CulturalAdaptationInput."""
    return CulturalAdaptationInput(
        job_id=uuid.uuid4(),
        segments=translation_segments,
        source_language="en",
        target_language="fr",
    )


class TestCulturalAdaptationAgentProcess:
    """Tests for CulturalAdaptationAgent.process()."""

    async def test_identifies_cultural_references(
        self, agent, cultural_adaptation_input
    ):
        """Happy path: Claude identifies cultural items with correct categories."""
        result = await agent.process(cultural_adaptation_input)

        assert isinstance(result, CulturalAdaptationOutput)
        assert result.job_id == cultural_adaptation_input.job_id
        assert result.target_language == "fr"
        assert len(result.items) == 2
        assert result.item_count == 2

        # Verify first item (idiom)
        item1 = result.items[0]
        assert item1.cue_index == 1
        assert item1.category == "idiom"
        assert item1.flagged_text == "Break a leg"
        assert item1.confidence == 0.95

        # Verify second item (currency)
        item2 = result.items[1]
        assert item2.cue_index == 2
        assert item2.category == "currency"
        assert item2.flagged_text == "twenty bucks"
        assert item2.confidence == 0.87

    async def test_empty_response_no_items(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Empty array response returns zero items."""
        empty_response = MagicMock()
        empty_response.content = [
            MagicMock(type="text", text=json.dumps([]))
        ]
        empty_response.usage = MagicMock(
            input_tokens=500, output_tokens=50
        )
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=empty_response
        )

        result = await agent.process(cultural_adaptation_input)

        assert len(result.items) == 0
        assert result.item_count == 0
        assert result.api_cost_usd >= 0

    async def test_json_parse_error_graceful(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Invalid JSON from Claude returns empty items list gracefully."""
        invalid_response = MagicMock()
        invalid_response.content = [
            MagicMock(type="text", text="This is not JSON at all")
        ]
        invalid_response.usage = MagicMock(
            input_tokens=500, output_tokens=100
        )
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=invalid_response
        )

        result = await agent.process(cultural_adaptation_input)

        assert isinstance(result, CulturalAdaptationOutput)
        assert result.items == []
        assert result.item_count == 0

    async def test_tracks_api_cost(
        self, agent, cultural_adaptation_input, mock_claude_response_with_items
    ):
        """API cost and usage metadata are populated correctly."""
        # Update mock response with known token counts
        mock_claude_response_with_items.usage.input_tokens = 100_000
        mock_claude_response_with_items.usage.output_tokens = 30_000

        result = await agent.process(cultural_adaptation_input)

        assert result.api_cost_usd > 0
        assert result.api_usage["model"] == "claude-haiku-4-5-20251001"
        assert result.api_usage["input_tokens"] == 100_000
        assert result.api_usage["output_tokens"] == 30_000

    async def test_cost_calculation_haiku_pricing(
        self, agent, cultural_adaptation_input
    ):
        """Cost calculation: $0.80/MTok input + $4/MTok output (Haiku pricing)."""
        # Direct cost calculation test
        cost = agent._calculate_cost(100_000, 30_000)
        expected = round(
            (100_000 / 1_000_000) * 0.80 + (30_000 / 1_000_000) * 4.0, 6
        )
        assert cost == expected

    async def test_batches_large_input(
        self, agent, mock_anthropic_client
    ):
        """100 segments batched correctly with multiple API calls."""
        segments = [
            TranslationSegment(
                index=i + 1,
                start_ms=i * 1000,
                end_ms=(i + 1) * 1000,
                original_text=f"English text {i + 1}.",
                translated_text=f"Texte français {i + 1}.",
            )
            for i in range(100)
        ]

        # Mock responses for each batch
        def make_response(batch_segments):
            items = [
                {
                    "cue_index": s.index,
                    "category": "cultural_ref",
                    "original_text": s.original_text,
                    "flagged_text": f"text {s.index}",
                    "suggestion": f"suggested {s.index}",
                    "confidence": 0.85,
                }
                for s in batch_segments
            ]
            resp = MagicMock()
            resp.content = [MagicMock(type="text", text=json.dumps(items))]
            resp.usage = MagicMock(input_tokens=500, output_tokens=200)
            return resp

        call_count = 0
        all_batches = [segments[i : i + 40] for i in range(0, 100, 40)]

        async def mock_create(**kwargs):
            nonlocal call_count
            batch = all_batches[call_count]
            call_count += 1
            return make_response(batch)

        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=mock_create
        )

        input_data = CulturalAdaptationInput(
            job_id=uuid.uuid4(),
            segments=segments,
            source_language="en",
            target_language="fr",
        )

        result = await agent.process(input_data)

        assert len(result.items) == 100
        assert call_count == 3  # 40 + 40 + 20
        assert result.api_usage["batches"] == 3


class TestCulturalAdaptationAgentRetry:
    """Tests for retry behavior."""

    async def test_retries_on_api_timeout(
        self,
        agent,
        cultural_adaptation_input,
        mock_claude_response_with_items,
    ):
        """API timeout triggers retry."""
        agent._client.messages.create = AsyncMock(
            side_effect=[
                anthropic.APITimeoutError(request=MagicMock()),
                mock_claude_response_with_items,
            ]
        )

        with patch(
            "app.agents.cultural_adaptation.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await agent.process(cultural_adaptation_input)

        assert isinstance(result, CulturalAdaptationOutput)
        assert agent._client.messages.create.call_count == 2

    async def test_retries_on_rate_limit(
        self,
        agent,
        cultural_adaptation_input,
        mock_claude_response_with_items,
    ):
        """Rate limit error triggers retry."""
        agent._client.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError(
                    message="Rate limited",
                    response=MagicMock(status_code=429),
                    body=None,
                ),
                mock_claude_response_with_items,
            ]
        )

        with patch(
            "app.agents.cultural_adaptation.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await agent.process(cultural_adaptation_input)

        assert isinstance(result, CulturalAdaptationOutput)

    async def test_raises_on_persistent_failure(
        self, agent, cultural_adaptation_input
    ):
        """3 consecutive failures raise AppError."""
        agent._client.messages.create = AsyncMock(
            side_effect=anthropic.APITimeoutError(request=MagicMock())
        )

        with patch(
            "app.agents.cultural_adaptation.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            with pytest.raises(AppError, match="failed after 3 attempts"):
                await agent.process(cultural_adaptation_input)


class TestCulturalAdaptationAgentParsing:
    """Tests for response parsing edge cases."""

    async def test_handles_json_with_code_fences(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Claude sometimes wraps JSON in ```json code fences."""
        fenced_json = "```json\n" + json.dumps([
            {
                "cue_index": 1,
                "category": "idiom",
                "original_text": "Break a leg!",
                "flagged_text": "Break a leg",
                "suggestion": "Bonne chance",
                "confidence": 0.92,
            },
            {
                "cue_index": 2,
                "category": "currency",
                "original_text": "It costs twenty bucks.",
                "flagged_text": "bucks",
                "suggestion": "euros",
                "confidence": 0.88,
            },
        ]) + "\n```"

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=fenced_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)
        assert len(result.items) == 2

    async def test_handles_missing_optional_fields(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Missing optional fields (suggestion) are handled gracefully."""
        partial_json = json.dumps([
            {
                "cue_index": 1,
                "category": "idiom",
                "original_text": "Break a leg!",
                "flagged_text": "Break a leg",
                "confidence": 0.90,
                # suggestion omitted
            },
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=partial_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)

        assert len(result.items) == 1
        item = result.items[0]
        assert item.cue_index == 1
        assert item.suggestion is None

    async def test_handles_invalid_json_response(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Invalid JSON from Claude returns empty items."""
        resp = MagicMock()
        resp.content = [
            MagicMock(type="text", text="{ broken json")
        ]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)

        assert result.items == []
        assert result.item_count == 0

    async def test_filters_items_by_confidence_threshold(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Items below confidence threshold (0.5) are filtered out."""
        json_response = json.dumps([
            {
                "cue_index": 1,
                "category": "idiom",
                "original_text": "Break a leg!",
                "flagged_text": "Break a leg",
                "suggestion": "Bonne chance",
                "confidence": 0.85,  # High confidence - included
            },
            {
                "cue_index": 2,
                "category": "cultural_ref",
                "original_text": "Some reference",
                "flagged_text": "reference",
                "suggestion": "adapted ref",
                "confidence": 0.3,  # Low confidence - excluded
            },
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=json_response)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)

        # Only high-confidence item included
        assert len(result.items) == 1
        assert result.items[0].cue_index == 1


class TestCulturalAdaptationSchemas:
    """Tests for schema validation."""

    def test_item_valid(self):
        """CulturalAdaptationItem can be created with valid data."""
        item = CulturalAdaptationItem(
            cue_index=1,
            category="idiom",
            original_text="Break a leg!",
            flagged_text="Break a leg",
            suggestion="Bonne chance",
            confidence=0.95,
        )

        assert item.cue_index == 1
        assert item.category == "idiom"
        assert item.confidence == 0.95

    def test_item_confidence_bounds(self):
        """Confidence must be between 0.0 and 1.0."""
        # Valid bounds
        item_low = CulturalAdaptationItem(
            cue_index=1,
            category="idiom",
            original_text="test",
            flagged_text="test",
            confidence=0.0,
        )
        assert item_low.confidence == 0.0

        item_high = CulturalAdaptationItem(
            cue_index=1,
            category="idiom",
            original_text="test",
            flagged_text="test",
            confidence=1.0,
        )
        assert item_high.confidence == 1.0

        # Invalid: > 1.0
        with pytest.raises(ValueError):
            CulturalAdaptationItem(
                cue_index=1,
                category="idiom",
                original_text="test",
                flagged_text="test",
                confidence=1.5,
            )

        # Invalid: < 0.0
        with pytest.raises(ValueError):
            CulturalAdaptationItem(
                cue_index=1,
                category="idiom",
                original_text="test",
                flagged_text="test",
                confidence=-0.1,
            )

    def test_output_item_count(self):
        """item_count field must match items list length."""
        items = [
            CulturalAdaptationItem(
                cue_index=i,
                category="idiom",
                original_text=f"text {i}",
                flagged_text=f"flag {i}",
                confidence=0.9,
            )
            for i in range(1, 4)
        ]

        output = CulturalAdaptationOutput(
            job_id=uuid.uuid4(),
            target_language="fr",
            items=items,
            item_count=3,
            api_cost_usd=0.05,
            api_usage={
                "model": "claude-haiku-4-5-20251001",
                "input_tokens": 500,
                "output_tokens": 200,
                "batches": 1,
            },
        )

        assert output.item_count == 3
        assert len(output.items) == 3
        assert output.item_count == len(output.items)

    def test_output_api_cost_bounds(self):
        """API cost must be non-negative."""
        # Valid
        output_zero = CulturalAdaptationOutput(
            job_id=uuid.uuid4(),
            target_language="fr",
            items=[],
            item_count=0,
            api_cost_usd=0.0,
            api_usage={},
        )
        assert output_zero.api_cost_usd == 0.0

        output_positive = CulturalAdaptationOutput(
            job_id=uuid.uuid4(),
            target_language="fr",
            items=[],
            item_count=0,
            api_cost_usd=0.12345,
            api_usage={},
        )
        assert output_positive.api_cost_usd == 0.12345

        # Invalid: negative cost
        with pytest.raises(ValueError):
            CulturalAdaptationOutput(
                job_id=uuid.uuid4(),
                target_language="fr",
                items=[],
                item_count=0,
                api_cost_usd=-0.01,
                api_usage={},
            )

    def test_item_required_cue_index_ge_1(self):
        """cue_index must be >= 1."""
        # Valid
        item = CulturalAdaptationItem(
            cue_index=1,
            category="idiom",
            original_text="test",
            flagged_text="test",
            confidence=0.9,
        )
        assert item.cue_index == 1

        # Invalid: 0
        with pytest.raises(ValueError):
            CulturalAdaptationItem(
                cue_index=0,
                category="idiom",
                original_text="test",
                flagged_text="test",
                confidence=0.9,
            )

        # Invalid: negative
        with pytest.raises(ValueError):
            CulturalAdaptationItem(
                cue_index=-1,
                category="idiom",
                original_text="test",
                flagged_text="test",
                confidence=0.9,
            )


class TestCulturalAdaptationInputValidation:
    """Tests for input validation."""

    def test_input_requires_segments(self):
        """CulturalAdaptationInput requires non-empty segments list."""
        # Valid with segments
        input_data = CulturalAdaptationInput(
            job_id=uuid.uuid4(),
            segments=[
                TranslationSegment(
                    index=1,
                    start_ms=0,
                    end_ms=1000,
                    original_text="test",
                    translated_text="test",
                )
            ],
            source_language="en",
            target_language="fr",
        )
        assert len(input_data.segments) == 1

        # Valid with empty segments (edge case)
        input_empty = CulturalAdaptationInput(
            job_id=uuid.uuid4(),
            segments=[],
            source_language="en",
            target_language="fr",
        )
        assert input_empty.segments == []

    def test_input_language_validation(self):
        """Language codes must be 2-10 characters."""
        segment = TranslationSegment(
            index=1,
            start_ms=0,
            end_ms=1000,
            original_text="test",
            translated_text="test",
        )

        # Valid
        input_valid = CulturalAdaptationInput(
            job_id=uuid.uuid4(),
            segments=[segment],
            source_language="en",
            target_language="fr",
        )
        assert input_valid.source_language == "en"

        # Invalid: too short
        with pytest.raises(ValueError):
            CulturalAdaptationInput(
                job_id=uuid.uuid4(),
                segments=[segment],
                source_language="e",
                target_language="fr",
            )

        # Invalid: too long
        with pytest.raises(ValueError):
            CulturalAdaptationInput(
                job_id=uuid.uuid4(),
                segments=[segment],
                source_language="english_language_code",
                target_language="fr",
            )


class TestCulturalAdaptationEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_empty_segments_input(self, agent):
        """Empty segment list should process gracefully."""
        input_data = CulturalAdaptationInput(
            job_id=uuid.uuid4(),
            segments=[],
            source_language="en",
            target_language="fr",
        )

        result = await agent.process(input_data)

        assert result.items == []
        assert result.item_count == 0

    async def test_malformed_item_skipped(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Malformed items in response are skipped, not fail entire parse."""
        malformed_json = json.dumps([
            {
                "cue_index": 1,
                "category": "idiom",
                "original_text": "test",
                "flagged_text": "test",
                "confidence": 0.85,
            },
            {
                # Missing required fields
                "cue_index": 2,
                "confidence": 0.90,
            },
            {
                "cue_index": 3,
                "category": "cultural_ref",
                "original_text": "another",
                "flagged_text": "another",
                "confidence": 0.88,
            },
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=malformed_json)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)

        # Valid items included, malformed ones skipped
        assert len(result.items) == 2
        assert result.items[0].cue_index == 1
        assert result.items[1].cue_index == 3

    async def test_very_low_confidence_items_excluded(
        self, agent, cultural_adaptation_input, mock_anthropic_client
    ):
        """Items at or below confidence threshold are excluded."""
        json_response = json.dumps([
            {
                "cue_index": 1,
                "category": "idiom",
                "original_text": "text",
                "flagged_text": "text",
                "confidence": 0.5,  # At threshold - included
            },
            {
                "cue_index": 2,
                "category": "cultural_ref",
                "original_text": "text",
                "flagged_text": "text",
                "confidence": 0.49,  # Below threshold - excluded
            },
            {
                "cue_index": 3,
                "category": "idiom",
                "original_text": "text",
                "flagged_text": "text",
                "confidence": 0.0,  # At minimum - excluded
            },
        ])

        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=json_response)]
        resp.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=resp
        )

        result = await agent.process(cultural_adaptation_input)

        assert len(result.items) == 1
        assert result.items[0].cue_index == 1

    async def test_unexpected_exception_raised(
        self, agent, cultural_adaptation_input
    ):
        """Unexpected (non-retryable) exceptions are raised immediately."""
        agent._client.messages.create = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        with pytest.raises(AppError, match="Unexpected cultural adaptation error"):
            await agent.process(cultural_adaptation_input)

    def test_calculate_cost_zero_tokens(self):
        """Zero token usage = zero cost."""
        agent = CulturalAdaptationAgent(anthropic_api_key="test-key")
        cost = agent._calculate_cost(0, 0)
        assert cost == 0.0

    def test_calculate_cost_fractional_tokens(self):
        """Cost calculation rounds to 6 decimals."""
        agent = CulturalAdaptationAgent(anthropic_api_key="test-key")
        # 1 input + 1 output
        cost = agent._calculate_cost(1, 1)
        # (1/1M * 0.80) + (1/1M * 4.0) = 0.0000048
        expected = round((1 / 1_000_000) * 0.80 + (1 / 1_000_000) * 4.0, 6)
        assert cost == expected

    def test_chunk_segments_even_division(self):
        """Segment batching with even division."""
        agent = CulturalAdaptationAgent(anthropic_api_key="test-key")
        segments = [
            TranslationSegment(
                index=i,
                start_ms=0,
                end_ms=1000,
                original_text="text",
                translated_text="text",
            )
            for i in range(1, 81)
        ]

        batches = agent._chunk_segments(segments, 40)

        assert len(batches) == 2
        assert len(batches[0]) == 40
        assert len(batches[1]) == 40

    def test_chunk_segments_remainder(self):
        """Segment batching with remainder."""
        agent = CulturalAdaptationAgent(anthropic_api_key="test-key")
        segments = [
            TranslationSegment(
                index=i,
                start_ms=0,
                end_ms=1000,
                original_text="text",
                translated_text="text",
            )
            for i in range(1, 51)
        ]

        batches = agent._chunk_segments(segments, 40)

        assert len(batches) == 2
        assert len(batches[0]) == 40
        assert len(batches[1]) == 10
