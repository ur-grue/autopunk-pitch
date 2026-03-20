"""CulturalAdaptationAgent — identifies culturally specific content in translations.

Processes segments in batches of ~40-50 cues per API call. Uses Claude Haiku 4.5
to identify idioms, cultural references, measurements, currencies, and other
culturally-specific items that may require human review or adaptation.

This agent analyzes a single translated language pair and returns flagged items.
"""

import asyncio
import json

import anthropic
import structlog

from app.agents.schemas import (
    CulturalAdaptationInput,
    CulturalAdaptationItem,
    CulturalAdaptationOutput,
    TranslationSegment,
)
from app.exceptions import AppError

logger = structlog.get_logger(__name__)

MODEL_NAME = "claude-haiku-4-5-20251001"
# Claude Haiku 4.5: $0.80/MTok input, $4/MTok output
COST_PER_INPUT_MTOK = 0.80
COST_PER_OUTPUT_MTOK = 4.0
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
API_TIMEOUT = 120
BATCH_SIZE = 40
CONFIDENCE_THRESHOLD = 0.5

SYSTEM_PROMPT = """You are a cultural adaptation expert. Your task is to identify culturally specific content in translated subtitle segments that may require localization or adaptation for the target audience.

Analyze each segment for:
- Idioms and expressions that don't translate directly
- Measurements (imperial vs metric, temperatures)
- Dates and time formats
- Currency references
- Proper nouns that are culturally significant
- Cultural references, holidays, or traditions
- Humor that may not translate
- Formal/informal registers

OUTPUT FORMAT:
Return a JSON array where each element has:
- "cue_index": the segment index (1-based)
- "category": one of: idiom, measurement, date_format, currency, proper_noun, cultural_ref, humor, formality
- "original_text": the full original source text
- "flagged_text": the specific substring that triggered the flag
- "suggestion": optional suggested adaptation or replacement
- "confidence": a score 0.0-1.0 indicating confidence that this genuinely requires adaptation

Return ONLY the JSON array, no other text. Only include items you are confident about (confidence >= 0.5)."""

USER_PROMPT_TEMPLATE = """Identify cultural items in these subtitle segments from {source_language} translated to {target_language}:

{segments_json}"""


class CulturalAdaptationAgent:
    """Identifies culturally specific content in translations using Claude Haiku.

    Pure function agent: takes CulturalAdaptationInput, returns
    CulturalAdaptationOutput. Does not access the database. The Celery task
    handles persistence.
    """

    def __init__(self, anthropic_api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self._logger = logger.bind(agent="cultural_adaptation")

    async def process(
        self, input: CulturalAdaptationInput
    ) -> CulturalAdaptationOutput:
        """Identify cultural items in translated segments.

        Segments are chunked into batches of ~40 for API calls.
        Results are merged and filtered by confidence threshold.

        Args:
            input: Cultural adaptation input with segments and language pair.

        Returns:
            Structured cultural adaptation output with flagged items.

        Raises:
            AppError: If identification fails after retries.
        """
        self._logger.info(
            "cultural_adaptation_started",
            job_id=str(input.job_id),
            source=input.source_language,
            target=input.target_language,
            segment_count=len(input.segments),
        )

        # Chunk segments into batches
        batches = self._chunk_segments(input.segments, BATCH_SIZE)
        all_items: list[CulturalAdaptationItem] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for batch_idx, batch in enumerate(batches):
            self._logger.info(
                "analyzing_batch",
                batch=batch_idx + 1,
                total_batches=len(batches),
                batch_size=len(batch),
            )

            items, usage = await self._analyze_batch(
                segments=batch,
                source_language=input.source_language,
                target_language=input.target_language,
            )
            all_items.extend(items)
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)

        cost = self._calculate_cost(total_input_tokens, total_output_tokens)

        self._logger.info(
            "cultural_adaptation_completed",
            job_id=str(input.job_id),
            target=input.target_language,
            item_count=len(all_items),
            cost_usd=cost,
        )

        return CulturalAdaptationOutput(
            job_id=input.job_id,
            target_language=input.target_language,
            items=all_items,
            item_count=len(all_items),
            api_cost_usd=cost,
            api_usage={
                "model": MODEL_NAME,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "batches": len(batches),
            },
        )

    async def _analyze_batch(
        self,
        segments: list[TranslationSegment],
        source_language: str,
        target_language: str,
    ) -> tuple[list[CulturalAdaptationItem], dict]:
        """Analyze a single batch of segments via Claude API.

        Args:
            segments: Batch of translated segments.
            source_language: Source ISO 639-1 code.
            target_language: Target ISO 639-1 code.

        Returns:
            Tuple of (cultural items, token usage dict).

        Raises:
            AppError: After all retries exhausted.
        """
        segments_json = json.dumps(
            [
                {
                    "index": s.index,
                    "original_text": s.original_text,
                    "translated_text": s.translated_text,
                }
                for s in segments
            ],
            ensure_ascii=False,
        )

        system = SYSTEM_PROMPT
        user_msg = USER_PROMPT_TEMPLATE.format(
            source_language=source_language,
            target_language=target_language,
            segments_json=segments_json,
        )

        response = await self._call_api(system=system, user_message=user_msg)

        # Parse response
        items = self._parse_response(response)
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return items, usage

    async def _call_api(
        self, system: str, user_message: str
    ) -> anthropic.types.Message:
        """Call Claude API with retry logic.

        Args:
            system: System prompt.
            user_message: User message with segments to analyze.

        Returns:
            Claude API response.

        Raises:
            AppError: After all retries exhausted.
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
                        "cultural_adaptation_retry",
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
                        "cultural_adaptation_timeout_retry",
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                raise AppError(
                    f"Unexpected cultural adaptation error: {e}"
                ) from e

        raise AppError(
            f"Cultural adaptation analysis failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def _parse_response(
        self,
        response: anthropic.types.Message,
    ) -> list[CulturalAdaptationItem]:
        """Parse Claude's JSON response into CulturalAdaptationItem objects.

        Args:
            response: Claude API response.

        Returns:
            List of CulturalAdaptationItem objects, filtered by confidence
            threshold.
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
            items_list = json.loads(text_content)
        except json.JSONDecodeError as e:
            self._logger.error(
                "cultural_adaptation_json_parse_error",
                error=str(e),
                raw_response=text_content[:500],
            )
            # Return empty list on parse error
            return []

        # Convert to CulturalAdaptationItem objects and filter by confidence
        result: list[CulturalAdaptationItem] = []
        for item_data in items_list:
            try:
                confidence = item_data.get("confidence", 0.5)
                if confidence >= CONFIDENCE_THRESHOLD:
                    item = CulturalAdaptationItem(
                        cue_index=item_data.get("cue_index"),
                        category=item_data.get("category"),
                        original_text=item_data.get("original_text"),
                        flagged_text=item_data.get("flagged_text"),
                        suggestion=item_data.get("suggestion"),
                        confidence=confidence,
                    )
                    result.append(item)
            except (ValueError, KeyError, TypeError) as e:
                self._logger.warning(
                    "cultural_adaptation_item_parse_error",
                    error=str(e),
                    item_data=item_data,
                )
                # Skip invalid items, don't fail
                continue

        return result

    def _chunk_segments(
        self, segments: list[TranslationSegment], size: int
    ) -> list[list[TranslationSegment]]:
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

        Claude Haiku 4.5: $0.80/MTok input, $4/MTok output.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD.
        """
        input_cost = (input_tokens / 1_000_000) * COST_PER_INPUT_MTOK
        output_cost = (output_tokens / 1_000_000) * COST_PER_OUTPUT_MTOK
        return round(input_cost + output_cost, 6)
