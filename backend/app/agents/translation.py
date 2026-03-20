"""TranslationAgent — translates subtitle segments using Claude Sonnet 4.6.

Processes segments in batches of ~40-50 cues per API call. Translations
run in parallel across languages via asyncio.gather() in the orchestrator.
This agent handles a single source→target language pair.
"""

import asyncio
import json

import anthropic
import structlog

from app.agents.schemas import (
    TranscriptionSegment,
    TranslationInput,
    TranslationOutput,
    TranslationSegment,
)
from app.exceptions import TranslationError

logger = structlog.get_logger(__name__)

MODEL_NAME = "claude-sonnet-4-6-20250514"
# Claude Sonnet 4.6: $3/MTok input, $15/MTok output
COST_PER_INPUT_MTOK = 3.0
COST_PER_OUTPUT_MTOK = 15.0
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
API_TIMEOUT = 120
BATCH_SIZE = 40

SYSTEM_PROMPT = """You are a professional subtitle translator. Your task is to translate subtitle segments from {source_language} to {target_language}.

CRITICAL RULES:
1. Preserve the exact number of segments — translate every segment, never skip or merge.
2. Keep translations concise: max 42 characters per line, max 2 lines per segment.
3. Preserve meaning, tone, and register. Adapt idioms naturally to the target language.
4. Do NOT translate proper nouns, brand names, or technical terms that are commonly kept in the original language.
5. Flag any segment where translation is uncertain or involves cultural references that may need adaptation.

OUTPUT FORMAT:
Return a JSON array where each element has:
- "index": the segment index (must match input)
- "translated_text": the translated text
- "flags": array of flags (empty if none). Valid flags: "cultural_ref", "untranslated", "uncertain", "proper_noun"

Return ONLY the JSON array, no other text."""

USER_PROMPT_TEMPLATE = """Translate these subtitle segments from {source_language} to {target_language}:

{segments_json}"""


class TranslationAgent:
    """Translates subtitle segments using Claude Sonnet 4.6.

    Pure function agent: takes TranslationInput, returns TranslationOutput.
    Does not access the database. The Celery task handles persistence.
    """

    def __init__(self, anthropic_api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self._logger = logger.bind(agent="translation")

    async def process(self, input: TranslationInput) -> TranslationOutput:
        """Translate all segments from source to target language.

        Segments are chunked into batches of ~40 for API calls.
        Results are merged and validated for completeness.

        Args:
            input: Translation input with segments and language pair.

        Returns:
            Structured translation output with all segments translated.

        Raises:
            TranslationError: If translation fails after retries.
        """
        self._logger.info(
            "translation_started",
            job_id=str(input.job_id),
            source=input.source_language,
            target=input.target_language,
            segment_count=len(input.segments),
        )

        # Chunk segments into batches
        batches = self._chunk_segments(input.segments, BATCH_SIZE)
        all_translated: list[TranslationSegment] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for batch_idx, batch in enumerate(batches):
            self._logger.info(
                "translating_batch",
                batch=batch_idx + 1,
                total_batches=len(batches),
                batch_size=len(batch),
            )

            translated, usage = await self._translate_batch(
                segments=batch,
                source_language=input.source_language,
                target_language=input.target_language,
            )
            all_translated.extend(translated)
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)

        # Validate completeness — never silently drop cues
        if len(all_translated) != len(input.segments):
            self._logger.warning(
                "translation_segment_count_mismatch",
                expected=len(input.segments),
                actual=len(all_translated),
            )
            # Fill in any missing segments with untranslated flags
            all_translated = self._fill_missing_segments(
                input.segments, all_translated
            )

        cost = self._calculate_cost(total_input_tokens, total_output_tokens)

        self._logger.info(
            "translation_completed",
            job_id=str(input.job_id),
            target=input.target_language,
            segment_count=len(all_translated),
            cost_usd=cost,
        )

        return TranslationOutput(
            job_id=input.job_id,
            segments=all_translated,
            source_language=input.source_language,
            target_language=input.target_language,
            api_cost_usd=cost,
            api_usage={
                "model": MODEL_NAME,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "batches": len(batches),
            },
        )

    async def _translate_batch(
        self,
        segments: list[TranscriptionSegment],
        source_language: str,
        target_language: str,
    ) -> tuple[list[TranslationSegment], dict]:
        """Translate a single batch of segments via Claude API.

        Args:
            segments: Batch of source segments.
            source_language: Source ISO 639-1 code.
            target_language: Target ISO 639-1 code.

        Returns:
            Tuple of (translated segments, token usage dict).

        Raises:
            TranslationError: After all retries exhausted.
        """
        segments_json = json.dumps(
            [
                {"index": s.index, "text": s.text}
                for s in segments
            ],
            ensure_ascii=False,
        )

        system = SYSTEM_PROMPT.format(
            source_language=source_language,
            target_language=target_language,
        )
        user_msg = USER_PROMPT_TEMPLATE.format(
            source_language=source_language,
            target_language=target_language,
            segments_json=segments_json,
        )

        response = await self._call_api(system=system, user_message=user_msg)

        # Parse response
        translated = self._parse_response(response, segments)
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return translated, usage

    async def _call_api(
        self, system: str, user_message: str
    ) -> anthropic.types.Message:
        """Call Claude API with retry logic.

        Args:
            system: System prompt.
            user_message: User message with segments to translate.

        Returns:
            Claude API response.

        Raises:
            TranslationError: After all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await asyncio.wait_for(
                    self._client.messages.create(
                        model=MODEL_NAME,
                        max_tokens=4096,
                        temperature=0.3,
                        system=system,
                        messages=[{"role": "user", "content": user_message}],
                    ),
                    timeout=API_TIMEOUT,
                )
                return response

            except (
                anthropic.APITimeoutError,
                anthropic.APIConnectionError,
                anthropic.InternalServerError,
                anthropic.RateLimitError,
            ) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2**attempt)
                    self._logger.warning(
                        "translation_retry",
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
                        "translation_timeout_retry",
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                raise TranslationError(
                    f"Unexpected translation error: {e}"
                ) from e

        raise TranslationError(
            f"Translation failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def _parse_response(
        self,
        response: anthropic.types.Message,
        source_segments: list[TranscriptionSegment],
    ) -> list[TranslationSegment]:
        """Parse Claude's JSON response into TranslationSegment objects.

        Never silently drops segments — if parsing fails for a segment,
        it's included with an 'untranslated' flag.

        Args:
            response: Claude API response.
            source_segments: Original source segments for timing data.

        Returns:
            List of TranslationSegment objects.
        """
        # Extract text content from response
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        # Strip markdown code fences if present
        text_content = text_content.strip()
        if text_content.startswith("```"):
            lines = text_content.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text_content = "\n".join(lines)

        try:
            translated_list = json.loads(text_content)
        except json.JSONDecodeError as e:
            self._logger.error(
                "translation_json_parse_error",
                error=str(e),
                raw_response=text_content[:500],
            )
            # Return all segments flagged as untranslated
            return [
                TranslationSegment(
                    index=s.index,
                    start_ms=s.start_ms,
                    end_ms=s.end_ms,
                    original_text=s.text,
                    translated_text=s.text,
                    flags=["untranslated"],
                )
                for s in source_segments
            ]

        # Build lookup by index
        source_by_index = {s.index: s for s in source_segments}
        translated_by_index = {t["index"]: t for t in translated_list}

        result: list[TranslationSegment] = []
        for seg in source_segments:
            t = translated_by_index.get(seg.index)
            if t:
                result.append(
                    TranslationSegment(
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        original_text=seg.text,
                        translated_text=t.get("translated_text", seg.text),
                        flags=t.get("flags", []),
                    )
                )
            else:
                self._logger.warning(
                    "missing_translation_for_segment",
                    index=seg.index,
                )
                result.append(
                    TranslationSegment(
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        original_text=seg.text,
                        translated_text=seg.text,
                        flags=["untranslated"],
                    )
                )

        return result

    def _fill_missing_segments(
        self,
        source_segments: list[TranscriptionSegment],
        translated_segments: list[TranslationSegment],
    ) -> list[TranslationSegment]:
        """Fill in missing segments with untranslated flags.

        Args:
            source_segments: All original source segments.
            translated_segments: Translated segments (may be incomplete).

        Returns:
            Complete list of TranslationSegment objects.
        """
        translated_by_index = {s.index: s for s in translated_segments}
        result: list[TranslationSegment] = []

        for seg in source_segments:
            if seg.index in translated_by_index:
                result.append(translated_by_index[seg.index])
            else:
                result.append(
                    TranslationSegment(
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        original_text=seg.text,
                        translated_text=seg.text,
                        flags=["untranslated"],
                    )
                )

        return result

    def _chunk_segments(
        self, segments: list[TranscriptionSegment], size: int
    ) -> list[list[TranscriptionSegment]]:
        """Split segments into batches of given size.

        Args:
            segments: All source segments.
            size: Maximum batch size.

        Returns:
            List of segment batches.
        """
        return [segments[i : i + size] for i in range(0, len(segments), size)]

    def _calculate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate API cost based on token usage.

        Claude Sonnet 4.6: $3/MTok input, $15/MTok output.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD.
        """
        input_cost = (input_tokens / 1_000_000) * COST_PER_INPUT_MTOK
        output_cost = (output_tokens / 1_000_000) * COST_PER_OUTPUT_MTOK
        return round(input_cost + output_cost, 6)
