"""Tests for the AudioService."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import AudioExtractionError
from app.services.audio_service import AudioService


@pytest.fixture
def audio_service() -> AudioService:
    """Create an AudioService instance."""
    return AudioService()


class TestExtractAudio:
    """Tests for AudioService.extract_audio()."""

    async def test_extract_audio_valid_video(self, audio_service, tmp_path):
        """Successful extraction returns duration and creates output file."""
        video_path = str(tmp_path / "test.mp4")
        output_path = str(tmp_path / "audio.mp3")

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with (
            patch(
                "app.services.audio_service.asyncio.create_subprocess_exec",
                return_value=mock_process,
            ),
            patch.object(
                audio_service,
                "get_duration",
                return_value=30.5,
            ),
        ):
            duration = await audio_service.extract_audio(video_path, output_path)

        assert duration == 30.5

    async def test_extract_audio_ffmpeg_failure_raises(
        self, audio_service, tmp_path
    ):
        """ffmpeg returning non-zero exit code raises AudioExtractionError."""
        video_path = str(tmp_path / "test.mp4")
        output_path = str(tmp_path / "audio.mp3")

        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: invalid input")
        )

        with patch(
            "app.services.audio_service.asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            with pytest.raises(AudioExtractionError, match="ffmpeg failed"):
                await audio_service.extract_audio(video_path, output_path)

    async def test_extract_audio_timeout_raises(self, audio_service, tmp_path):
        """ffmpeg timeout raises AudioExtractionError."""
        video_path = str(tmp_path / "test.mp4")
        output_path = str(tmp_path / "audio.mp3")

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch(
            "app.services.audio_service.asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            with pytest.raises(
                AudioExtractionError, match="timed out"
            ):
                await audio_service.extract_audio(video_path, output_path)


class TestGetDuration:
    """Tests for AudioService.get_duration()."""

    async def test_get_duration_returns_seconds(self, audio_service, tmp_path):
        """ffprobe returns correct duration in seconds."""
        file_path = str(tmp_path / "test.mp4")

        ffprobe_output = json.dumps(
            {"format": {"duration": "30.500000"}}
        ).encode()

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(ffprobe_output, b"")
        )

        with patch(
            "app.services.audio_service.asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            duration = await audio_service.get_duration(file_path)

        assert duration == 30.5

    async def test_get_duration_ffprobe_failure_raises(
        self, audio_service, tmp_path
    ):
        """ffprobe failure raises AudioExtractionError."""
        file_path = str(tmp_path / "bad_file.xyz")

        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error"))

        with patch(
            "app.services.audio_service.asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            with pytest.raises(AudioExtractionError, match="ffprobe failed"):
                await audio_service.get_duration(file_path)
