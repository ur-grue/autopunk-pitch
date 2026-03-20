"""TranscriptionAgent — transcribes audio using GPT-4o Mini Transcribe."""

import asyncio
from pathlib import Path

import openai
import structlog

from app.agents.schemas import (
    TranscriptionInput,
    TranscriptionOutput,
    TranscriptionSegment,
    WordTimestamp,
)
from app.exceptions import TranscriptionError

logger = structlog.get_logger(__name__)

# GPT-4o Mini Transcribe pricing: $0.003 per minute
COST_PER_MINUTE = 0.003
MODEL_NAME = "gpt-4o-mini-transcribe"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
API_TIMEOUT = 300


class TranscriptionAgent:
    """Extracts timestamped transcript from audio via GPT-4o Mini Transcribe.

    This agent is a pure function: it takes input and returns output
    without touching the database. The Celery task handles persistence.
    """

    def __init__(self, openai_api_key: str) -> None:
        self._client = openai.AsyncOpenAI(api_key=openai_api_key)
        self._logger = logger.bind(agent="transcription")

    async def process(self, input: TranscriptionInput) -> TranscriptionOutput:
        """Transcribe audio file and return structured segments.

        Args:
            input: Transcription input with audio path and language.

        Returns:
            Structured transcription output with segments and cost.

        Raises:
            TranscriptionError: If transcription fails after retries.
        """
        self._logger.info(
            "transcription_started",
            job_id=str(input.job_id),
            language=input.source_language,
            audio_path=input.audio_file_path,
        )

        response = await self._call_api(
            audio_path=input.audio_file_path,
            language=input.source_language,
            prompt=input.prompt,
        )

        segments = self._parse_segments(response)
        duration_seconds = getattr(response, "duration", 0.0) or 0.0
        duration_ms = int(duration_seconds * 1000)
        cost = self._calculate_cost(duration_seconds)

        self._logger.info(
            "transcription_completed",
            job_id=str(input.job_id),
            segment_count=len(segments),
            duration_ms=duration_ms,
            cost_usd=cost,
        )

        return TranscriptionOutput(
            job_id=input.job_id,
            segments=segments,
            language=input.source_language,
            duration_ms=duration_ms,
            api_cost_usd=cost,
            api_usage={
                "model": MODEL_NAME,
                "audio_duration_seconds": duration_seconds,
                "segment_count": len(segments),
            },
        )

    async def _call_api(
        self,
        audio_path: str,
        language: str,
        prompt: str | None = None,
    ) -> object:
        """Call OpenAI transcription API with retry logic.

        Retries up to MAX_RETRIES times with exponential backoff
        on transient errors (timeouts, 5xx responses).

        Args:
            audio_path: Path to the audio file.
            language: ISO 639-1 language code.
            prompt: Optional context prompt.

        Returns:
            OpenAI transcription response.

        Raises:
            TranscriptionError: After all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                audio_file = Path(audio_path)
                if not audio_file.exists():
                    raise TranscriptionError(
                        f"Audio file not found: {audio_path}"
                    )

                with open(audio_path, "rb") as f:
                    kwargs = {
                        "model": MODEL_NAME,
                        "file": f,
                        "response_format": "verbose_json",
                        "timestamp_granularities": ["segment", "word"],
                        "language": language,
                    }
                    if prompt:
                        kwargs["prompt"] = prompt

                    response = await asyncio.wait_for(
                        self._client.audio.transcriptions.create(**kwargs),
                        timeout=API_TIMEOUT,
                    )

                return response

            except TranscriptionError:
                raise
            except (
                openai.APITimeoutError,
                openai.APIConnectionError,
                openai.InternalServerError,
            ) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2**attempt)
                    self._logger.warning(
                        "transcription_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
            except asyncio.TimeoutError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2**attempt)
                    self._logger.warning(
                        "transcription_timeout_retry",
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                raise TranscriptionError(
                    f"Unexpected transcription error: {e}"
                ) from e

        raise TranscriptionError(
            f"Transcription failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def _parse_segments(self, api_response: object) -> list[TranscriptionSegment]:
        """Convert OpenAI response segments to internal format.

        Converts seconds (float) to milliseconds (int).
        Never silently drops segments — logs a warning if any
        segment can't be parsed.

        Args:
            api_response: OpenAI verbose_json transcription response.

        Returns:
            List of TranscriptionSegment objects.
        """
        raw_segments = getattr(api_response, "segments", None) or []
        raw_words = getattr(api_response, "words", None) or []

        # Build word-level timestamps indexed by approximate position
        segments: list[TranscriptionSegment] = []

        for i, seg in enumerate(raw_segments):
            try:
                start_ms = int(seg.get("start", 0) * 1000)
                end_ms = int(seg.get("end", 0) * 1000)
                text = seg.get("text", "").strip()

                # Collect words that fall within this segment's time range
                segment_words: list[WordTimestamp] = []
                for w in raw_words:
                    w_start = w.get("start", 0)
                    w_end = w.get("end", 0)
                    if w_start >= seg.get("start", 0) and w_end <= seg.get(
                        "end", float("inf")
                    ):
                        segment_words.append(
                            WordTimestamp(
                                word=w.get("word", ""),
                                start_ms=int(w_start * 1000),
                                end_ms=int(w_end * 1000),
                            )
                        )

                segments.append(
                    TranscriptionSegment(
                        index=i + 1,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        text=text,
                        confidence=seg.get("avg_logprob"),
                        words=segment_words if segment_words else None,
                    )
                )
            except Exception as e:
                self._logger.error(
                    "segment_parse_error",
                    segment_index=i,
                    error=str(e),
                    raw_segment=str(seg),
                )
                # Still include a flagged segment rather than dropping
                segments.append(
                    TranscriptionSegment(
                        index=i + 1,
                        start_ms=0,
                        end_ms=0,
                        text=str(seg.get("text", "")),
                        confidence=0.0,
                    )
                )

        if len(segments) != len(raw_segments):
            self._logger.warning(
                "segment_count_mismatch",
                expected=len(raw_segments),
                actual=len(segments),
            )

        return segments

    def _calculate_cost(self, duration_seconds: float) -> float:
        """Calculate API cost based on audio duration.

        GPT-4o Mini Transcribe: $0.003 per minute.

        Args:
            duration_seconds: Audio duration in seconds.

        Returns:
            Cost in USD.
        """
        minutes = duration_seconds / 60
        return round(minutes * COST_PER_MINUTE, 6)
