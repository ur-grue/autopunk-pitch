"""QCAgent — validates translated subtitles using Claude Haiku 4.5.

Combines rule-based validation (line length, reading speed, timing)
with AI-powered linguistic QC (grammar, consistency, mistranslations).
"""

import asyncio
import json

import anthropic
import structlog

from app.agents.schemas import (
    QCInput,
    QCIssueSchema,
    QCOutput,
    TranslationSegment,
)
from app.exceptions import AppError
from app.formats.validators import (
    SubtitleCue,
    ValidationResult,
    validate_subtitles,
)

logger = structlog.get_logger(__name__)

MODEL_NAME = "claude-haiku-4-5-20251001"
# Claude Haiku 4.5: $1/MTok input, $5/MTok output
COST_PER_INPUT_MTOK = 1.0
COST_PER_OUTPUT_MTOK = 5.0
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
API_TIMEOUT = 60
BATCH_SIZE = 50

SYSTEM_PROMPT = """You are a professional subtitle QC reviewer. Analyze translated subtitles from {source_language} to {target_language} for quality issues.

Check for:
1. Grammar and spelling errors in the target language
2. Obvious mistranslations or meaning shifts
3. Inconsistent terminology (same source term translated differently)
4. Untranslated text that should have been translated
5. Cultural references that may not work in the target culture

For each issue found, return a JSON array of objects:
- "cue_index": the subtitle index
- "severity": "error", "warning", or "info"
- "rule": short rule ID (e.g., "grammar", "mistranslation", "consistency", "cultural_ref")
- "message": description of the issue
- "suggestion": suggested fix (or null)

Return ONLY the JSON array. Return an empty array [] if no issues found."""

USER_PROMPT_TEMPLATE = """Review these {target_language} subtitles (translated from {source_language}):

{segments_json}"""


class QCAgent:
    """Validates translated subtitles with rule-based + AI-powered QC.

    Pure function agent: takes QCInput, returns QCOutput.
    Does not access the database.
    """

    def __init__(self, anthropic_api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self._logger = logger.bind(agent="qc")

    async def process(self, input: QCInput) -> QCOutput:
        """Run quality control on translated segments.

        Combines rule-based validation (format compliance) with
        AI-powered linguistic QC (Claude Haiku).

        Args:
            input: QC input with translated segments.

        Returns:
            QC output with issues and quality score.
        """
        self._logger.info(
            "qc_started",
            job_id=str(input.job_id),
            target=input.target_language,
            segment_count=len(input.segments),
        )

        # Step 1: Rule-based validation
        rule_issues = self._run_rule_validation(input.segments)

        # Step 2: AI-powered linguistic QC
        ai_issues, usage = await self._run_ai_validation(
            segments=input.segments,
            source_language=input.source_language,
            target_language=input.target_language,
        )

        # Merge issues
        all_issues = rule_issues + ai_issues

        # Calculate score
        error_count = sum(1 for i in all_issues if i.severity == "error")
        warning_count = sum(1 for i in all_issues if i.severity == "warning")
        score = max(0, 100 - (error_count * 5) - (warning_count * 2))

        cost = self._calculate_cost(
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )

        self._logger.info(
            "qc_completed",
            job_id=str(input.job_id),
            target=input.target_language,
            issue_count=len(all_issues),
            score=score,
            cost_usd=cost,
        )

        return QCOutput(
            job_id=input.job_id,
            target_language=input.target_language,
            issues=all_issues,
            score=score,
            api_cost_usd=cost,
            api_usage={
                "model": MODEL_NAME,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "rule_issues": len(rule_issues),
                "ai_issues": len(ai_issues),
            },
        )

    def _run_rule_validation(
        self, segments: list[TranslationSegment]
    ) -> list[QCIssueSchema]:
        """Run format-based validation rules.

        Args:
            segments: Translated segments.

        Returns:
            List of QC issues from rule validation.
        """
        cues = [
            SubtitleCue(
                index=s.index,
                start_ms=s.start_ms,
                end_ms=s.end_ms,
                text=s.translated_text,
            )
            for s in segments
        ]

        result: ValidationResult = validate_subtitles(cues)

        return [
            QCIssueSchema(
                cue_index=issue.cue_index,
                severity=issue.severity.value,
                rule=issue.rule,
                message=issue.message,
                suggestion=None,
            )
            for issue in result.issues
        ]

    async def _run_ai_validation(
        self,
        segments: list[TranslationSegment],
        source_language: str,
        target_language: str,
    ) -> tuple[list[QCIssueSchema], dict]:
        """Run AI-powered linguistic validation via Claude Haiku.

        Args:
            segments: Translated segments.
            source_language: Source language code.
            target_language: Target language code.

        Returns:
            Tuple of (issues list, token usage dict).
        """
        segments_json = json.dumps(
            [
                {
                    "index": s.index,
                    "original": s.original_text,
                    "translated": s.translated_text,
                }
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

        try:
            response = await self._call_api(system=system, user_message=user_msg)
        except AppError:
            # If AI QC fails, return empty — rule-based QC still applies
            self._logger.warning("ai_qc_failed_falling_back_to_rules_only")
            return [], {"input_tokens": 0, "output_tokens": 0}

        issues = self._parse_response(response)
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return issues, usage

    async def _call_api(
        self, system: str, user_message: str
    ) -> anthropic.types.Message:
        """Call Claude Haiku API with retry logic.

        Args:
            system: System prompt.
            user_message: User message with segments.

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
                        temperature=0.0,
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
                        "qc_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
            except asyncio.TimeoutError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(delay)
            except Exception as e:
                raise AppError(f"Unexpected QC error: {e}") from e

        raise AppError(
            f"QC validation failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def _parse_response(
        self, response: anthropic.types.Message
    ) -> list[QCIssueSchema]:
        """Parse Claude's JSON response into QCIssueSchema objects.

        Args:
            response: Claude API response.

        Returns:
            List of QC issues.
        """
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        text_content = text_content.strip()
        if text_content.startswith("```"):
            lines = text_content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text_content = "\n".join(lines)

        try:
            issues_list = json.loads(text_content)
        except json.JSONDecodeError:
            self._logger.warning("qc_json_parse_error", raw=text_content[:500])
            return []

        result: list[QCIssueSchema] = []
        for item in issues_list:
            try:
                result.append(
                    QCIssueSchema(
                        cue_index=item["cue_index"],
                        severity=item.get("severity", "warning"),
                        rule=item.get("rule", "ai_review"),
                        message=item.get("message", ""),
                        suggestion=item.get("suggestion"),
                    )
                )
            except (KeyError, ValueError) as e:
                self._logger.warning("qc_issue_parse_error", error=str(e))
                continue

        return result

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost.

        Claude Haiku 4.5: $1/MTok input, $5/MTok output.
        """
        input_cost = (input_tokens / 1_000_000) * COST_PER_INPUT_MTOK
        output_cost = (output_tokens / 1_000_000) * COST_PER_OUTPUT_MTOK
        return round(input_cost + output_cost, 6)
