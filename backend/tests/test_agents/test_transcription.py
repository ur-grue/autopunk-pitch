"""Tests for the TranscriptionAgent."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from app.agents.schemas import TranscriptionInput, TranscriptionOutput
from app.agents.transcription import TranscriptionAgent
from app.exceptions import TranscriptionError


@pytest.fixture
def agent(mock_openai_client) -> TranscriptionAgent:
    """Create a TranscriptionAgent with mocked OpenAI client."""
    agent = TranscriptionAgent(openai_api_key="test-key")
    agent._client = mock_openai_client
    return agent


@pytest.fixture
def transcription_input(tmp_path) -> TranscriptionInput:
    """Create a valid TranscriptionInput with a temp audio file."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio content")
    return TranscriptionInput(
        job_id=uuid.uuid4(),
        audio_file_path=str(audio_file),
        source_language="en",
    )


class TestTranscriptionAgentProcess:
    """Tests for TranscriptionAgent.process()."""

    async def test_process_valid_audio_returns_segments(
        self, agent, transcription_input
    ):
        """Happy path: valid audio returns structured segments."""
        result = await agent.process(transcription_input)

        assert isinstance(result, TranscriptionOutput)
        assert result.job_id == transcription_input.job_id
        assert result.language == "en"
        assert len(result.segments) == 5
        assert result.duration_ms > 0
        assert result.api_cost_usd > 0

    async def test_process_preserves_all_segments_no_drops(
        self, agent, transcription_input
    ):
        """Critical rule: never silently drop subtitle cues."""
        result = await agent.process(transcription_input)

        # The fixture has 5 segments — all must be present
        assert len(result.segments) == 5
        indices = [s.index for s in result.segments]
        assert indices == [1, 2, 3, 4, 5]

    async def test_process_calculates_cost_correctly(
        self, agent, transcription_input, mock_openai_response
    ):
        """Cost should be $0.003/min based on audio duration."""
        mock_openai_response.duration = 3120.0  # 52 minutes
        result = await agent.process(transcription_input)

        expected_cost = round((3120.0 / 60) * 0.003, 6)
        assert result.api_cost_usd == expected_cost

    async def test_process_segments_have_millisecond_timestamps(
        self, agent, transcription_input
    ):
        """Verify seconds -> milliseconds conversion is correct."""
        result = await agent.process(transcription_input)

        first = result.segments[0]
        # Fixture segment 0: start=0.0, end=4.2
        assert first.start_ms == 0
        assert first.end_ms == 4200

        second = result.segments[1]
        # Fixture segment 1: start=4.5, end=9.8
        assert second.start_ms == 4500
        assert second.end_ms == 9800

    async def test_process_includes_word_timestamps(
        self, agent, transcription_input
    ):
        """Word-level timestamps stored in segment data."""
        result = await agent.process(transcription_input)

        first = result.segments[0]
        assert first.words is not None
        assert len(first.words) > 0
        assert first.words[0].word.strip() == "Hello"
        assert first.words[0].start_ms == 0
        assert first.words[0].end_ms == 500

    async def test_process_returns_api_usage_metadata(
        self, agent, transcription_input
    ):
        """API usage dict includes model and duration info."""
        result = await agent.process(transcription_input)

        assert result.api_usage["model"] == "gpt-4o-mini-transcribe"
        assert "audio_duration_seconds" in result.api_usage
        assert "segment_count" in result.api_usage


class TestTranscriptionAgentCallAPI:
    """Tests for TranscriptionAgent._call_api() retry behavior."""

    async def test_call_api_retries_on_timeout(
        self, agent, transcription_input, mock_openai_response
    ):
        """API timeout triggers retry up to 3 times."""
        agent._client.audio.transcriptions.create = AsyncMock(
            side_effect=[
                openai.APITimeoutError(request=MagicMock()),
                mock_openai_response,
            ]
        )

        with patch("app.agents.transcription.asyncio.sleep", new_callable=AsyncMock):
            result = await agent.process(transcription_input)

        assert isinstance(result, TranscriptionOutput)
        assert agent._client.audio.transcriptions.create.call_count == 2

    async def test_call_api_retries_on_server_error(
        self, agent, transcription_input, mock_openai_response
    ):
        """5xx server error triggers retry."""
        agent._client.audio.transcriptions.create = AsyncMock(
            side_effect=[
                openai.InternalServerError(
                    message="Server error",
                    response=MagicMock(status_code=500),
                    body=None,
                ),
                mock_openai_response,
            ]
        )

        with patch("app.agents.transcription.asyncio.sleep", new_callable=AsyncMock):
            result = await agent.process(transcription_input)

        assert isinstance(result, TranscriptionOutput)

    async def test_call_api_raises_on_persistent_failure(
        self, agent, transcription_input
    ):
        """3 consecutive failures raise TranscriptionError."""
        agent._client.audio.transcriptions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=MagicMock())
        )

        with patch("app.agents.transcription.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TranscriptionError, match="failed after 3 attempts"):
                await agent.process(transcription_input)

        assert agent._client.audio.transcriptions.create.call_count == 3

    async def test_call_api_raises_on_missing_file(self, agent):
        """Missing audio file raises TranscriptionError immediately."""
        input_data = TranscriptionInput(
            job_id=uuid.uuid4(),
            audio_file_path="/nonexistent/audio.mp3",
            source_language="en",
        )

        with pytest.raises(TranscriptionError, match="Audio file not found"):
            await agent.process(input_data)


class TestTranscriptionAgentParseSegments:
    """Tests for TranscriptionAgent._parse_segments()."""

    def test_parse_segments_empty_audio_returns_empty(self):
        """Silent audio returns empty segment list, not error."""
        agent = TranscriptionAgent(openai_api_key="test-key")
        response = MagicMock()
        response.segments = []
        response.words = []

        segments = agent._parse_segments(response)
        assert segments == []

    def test_parse_segments_handles_missing_fields(self):
        """Segments with missing optional fields are still parsed."""
        agent = TranscriptionAgent(openai_api_key="test-key")
        response = MagicMock()
        response.segments = [
            {"start": 1.0, "end": 2.0, "text": "Test"}
        ]
        response.words = []

        segments = agent._parse_segments(response)
        assert len(segments) == 1
        assert segments[0].text == "Test"
        assert segments[0].start_ms == 1000
        assert segments[0].end_ms == 2000


class TestCalculateCost:
    """Tests for TranscriptionAgent._calculate_cost()."""

    def test_cost_30_second_clip(self):
        """30s clip: (30/60) * 0.003 = $0.0015."""
        agent = TranscriptionAgent(openai_api_key="test-key")
        assert agent._calculate_cost(30.0) == 0.0015

    def test_cost_52_minute_documentary(self):
        """52-min doc: (3120/60) * 0.003 = $0.156."""
        agent = TranscriptionAgent(openai_api_key="test-key")
        assert agent._calculate_cost(3120.0) == 0.156

    def test_cost_zero_duration(self):
        """Zero duration returns zero cost."""
        agent = TranscriptionAgent(openai_api_key="test-key")
        assert agent._calculate_cost(0.0) == 0.0
