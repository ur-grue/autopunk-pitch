"""Audio extraction service using ffmpeg."""

import asyncio
import json

import structlog

from app.exceptions import AudioExtractionError

logger = structlog.get_logger(__name__)


class AudioService:
    """Extracts audio from video files using ffmpeg subprocess."""

    async def extract_audio(
        self,
        video_path: str,
        output_path: str,
        bitrate: str = "64k",
    ) -> float:
        """Extract audio track from video file as mp3.

        Args:
            video_path: Path to the input video file.
            output_path: Path for the output audio file.
            bitrate: Audio bitrate (64k is sufficient for speech).

        Returns:
            Duration in seconds.

        Raises:
            AudioExtractionError: If ffmpeg fails.
        """
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",               # No video
            "-acodec", "libmp3lame",
            "-ab", bitrate,
            "-ar", "16000",      # 16kHz sample rate (optimal for speech)
            "-ac", "1",          # Mono
            "-y",                # Overwrite output
            output_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(
                process.communicate(), timeout=600
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                raise AudioExtractionError(
                    f"ffmpeg failed with code {process.returncode}: {error_msg}"
                )

            duration = await self.get_duration(video_path)
            logger.info(
                "audio_extracted",
                video_path=video_path,
                output_path=output_path,
                duration_seconds=duration,
            )
            return duration

        except asyncio.TimeoutError:
            raise AudioExtractionError(
                "Audio extraction timed out after 600 seconds"
            )
        except AudioExtractionError:
            raise
        except Exception as e:
            raise AudioExtractionError(
                f"Unexpected error during audio extraction: {e}"
            ) from e

    async def get_duration(self, file_path: str) -> float:
        """Get media duration in seconds using ffprobe.

        Args:
            file_path: Path to the media file.

        Returns:
            Duration in seconds.

        Raises:
            AudioExtractionError: If ffprobe fails.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(
                process.communicate(), timeout=30
            )

            if process.returncode != 0:
                raise AudioExtractionError(
                    f"ffprobe failed for {file_path}"
                )

            data = json.loads(stdout.decode("utf-8"))
            duration = float(data["format"]["duration"])
            return duration

        except AudioExtractionError:
            raise
        except Exception as e:
            raise AudioExtractionError(
                f"Failed to get duration: {e}"
            ) from e
