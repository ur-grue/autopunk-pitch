"""Tests for the QCAgent."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.agents.qc import QCAgent
from app.agents.schemas import QCInput, QCOutput, TranslationSegment


@pytest.fixture
def translated_segments() -> list[TranslationSegment]:
    """Create sample translated segments for QC tests."""
    return [
        TranslationSegment(
            index=1, start_ms=0, end_ms=4200,
            original_text="Hello and welcome.",
            translated_text="Bonjour et bienvenue.",
        ),
        TranslationSegment(
            index=2, start_ms=4500, end_ms=9800,
            original_text="The ocean is vast.",
            translated_text="L'océan est vaste.",
        ),
        TranslationSegment(
            index=3, start_ms=10200, end_ms=18500,
            original_text="Many species remain undiscovered.",
            translated_text="De nombreuses espèces restent inconnues.",
        ),
    ]


@pytest.fixture
def mock_haiku_response() -> MagicMock:
    """Create a mock Claude Haiku response with QC issues."""
    issues_json = json.dumps([
        {
            "cue_index": 2,
            "severity": "info",
            "rule": "style",
            "message": "Consider using 'immense' instead of 'vaste' for more natural phrasing.",
            "suggestion": "L'océan est immense.",
        },
    ])

    response = MagicMock()
    response.content = [MagicMock(type="text", text=issues_json)]
    response.usage = MagicMock(input_tokens=300, output_tokens=100)
    return response


@pytest.fixture
def mock_haiku_clean_response() -> MagicMock:
    """Mock Haiku response with no issues."""
    response = MagicMock()
    response.content = [MagicMock(type="text", text="[]")]
    response.usage = MagicMock(input_tokens=300, output_tokens=10)
    return response


@pytest.fixture
def agent(mock_haiku_response) -> QCAgent:
    """Create a QCAgent with mocked Anthropic client."""
    agent = QCAgent(anthropic_api_key="test-key")
    agent._client = MagicMock()
    agent._client.messages = MagicMock()
    agent._client.messages.create = AsyncMock(return_value=mock_haiku_response)
    return agent


@pytest.fixture
def qc_input(translated_segments) -> QCInput:
    """Create a valid QCInput."""
    return QCInput(
        job_id=uuid.uuid4(),
        segments=translated_segments,
        source_language="en",
        target_language="fr",
    )


class TestQCAgentProcess:
    """Tests for QCAgent.process()."""

    async def test_process_returns_qc_output(self, agent, qc_input):
        """Happy path: QC returns output with score."""
        result = await agent.process(qc_input)

        assert isinstance(result, QCOutput)
        assert result.job_id == qc_input.job_id
        assert result.target_language == "fr"
        assert 0 <= result.score <= 100

    async def test_process_includes_rule_and_ai_issues(self, agent, qc_input):
        """Output includes both rule-based and AI-identified issues."""
        result = await agent.process(qc_input)

        # AI found 1 style suggestion
        ai_issues = [i for i in result.issues if i.rule == "style"]
        assert len(ai_issues) >= 1

    async def test_process_clean_subtitles_high_score(
        self, agent, qc_input, mock_haiku_clean_response
    ):
        """Well-formed subtitles with no AI issues get high score."""
        agent._client.messages.create = AsyncMock(
            return_value=mock_haiku_clean_response
        )

        result = await agent.process(qc_input)

        assert result.score >= 90

    async def test_process_tracks_cost(self, agent, qc_input):
        """API cost is tracked."""
        result = await agent.process(qc_input)

        assert result.api_cost_usd > 0
        assert result.api_usage["model"] == "claude-haiku-4-5-20251001"
        assert result.api_usage["input_tokens"] == 300
        assert result.api_usage["output_tokens"] == 100


class TestQCRuleValidation:
    """Tests for rule-based validation within QCAgent."""

    async def test_line_length_violation_detected(self, agent):
        """QC detects line length violations."""
        segments = [
            TranslationSegment(
                index=1, start_ms=0, end_ms=4200,
                original_text="Short.",
                translated_text="A" * 50,  # 50 chars > 42 max
            ),
        ]
        qc_input = QCInput(
            job_id=uuid.uuid4(),
            segments=segments,
            source_language="en",
            target_language="fr",
        )

        result = await agent.process(qc_input)

        line_issues = [i for i in result.issues if i.rule == "line_length"]
        assert len(line_issues) >= 1

    async def test_overlap_detected(self, agent):
        """QC detects overlapping cues."""
        segments = [
            TranslationSegment(
                index=1, start_ms=0, end_ms=5000,
                original_text="First.", translated_text="Premier.",
            ),
            TranslationSegment(
                index=2, start_ms=4000, end_ms=8000,
                original_text="Second.", translated_text="Deuxième.",
            ),
        ]
        qc_input = QCInput(
            job_id=uuid.uuid4(),
            segments=segments,
            source_language="en",
            target_language="fr",
        )

        result = await agent.process(qc_input)

        overlap_issues = [i for i in result.issues if i.rule == "overlap"]
        assert len(overlap_issues) >= 1


class TestQCAIValidation:
    """Tests for AI-powered validation within QCAgent."""

    async def test_ai_failure_falls_back_to_rules(self, agent, qc_input):
        """If AI QC fails, rule-based QC still runs."""
        agent._client.messages.create = AsyncMock(
            side_effect=anthropic.APITimeoutError(request=MagicMock())
        )

        with patch("app.agents.qc.asyncio.sleep", new_callable=AsyncMock):
            result = await agent.process(qc_input)

        # Should still return a result (from rule-based validation)
        assert isinstance(result, QCOutput)
        assert result.api_usage["ai_issues"] == 0

    async def test_ai_invalid_json_handled(self, agent, qc_input):
        """Invalid JSON from AI is handled gracefully."""
        bad_response = MagicMock()
        bad_response.content = [MagicMock(type="text", text="not json")]
        bad_response.usage = MagicMock(input_tokens=100, output_tokens=10)
        agent._client.messages.create = AsyncMock(return_value=bad_response)

        result = await agent.process(qc_input)

        assert isinstance(result, QCOutput)
        # Only rule-based issues, no AI issues
        assert result.api_usage["ai_issues"] == 0

    async def test_ai_suggestions_preserved(self, agent, qc_input):
        """AI suggestions are included in issue objects."""
        result = await agent.process(qc_input)

        suggestions = [i for i in result.issues if i.suggestion is not None]
        assert len(suggestions) >= 1
        assert "immense" in suggestions[0].suggestion


class TestQCCostCalculation:
    """Tests for QC cost calculation."""

    def test_cost_haiku(self):
        """Claude Haiku 4.5: $1/MTok input, $5/MTok output."""
        agent = QCAgent(anthropic_api_key="test-key")
        cost = agent._calculate_cost(30_000, 10_000)
        expected = round((30_000 / 1_000_000) * 1.0 + (10_000 / 1_000_000) * 5.0, 6)
        assert cost == expected

    def test_cost_zero(self):
        agent = QCAgent(anthropic_api_key="test-key")
        assert agent._calculate_cost(0, 0) == 0.0
