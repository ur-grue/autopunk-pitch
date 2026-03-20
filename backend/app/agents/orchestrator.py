"""Pipeline orchestrator — chains transcription → translation.

Coordinates the full localization flow. Translations for multiple
target languages run in parallel via asyncio.gather().
"""

import asyncio

import structlog

from app.agents.schemas import (
    PipelineInput,
    PipelineOutput,
    TranscriptionInput,
    TranscriptionOutput,
    TranslationInput,
    TranslationOutput,
)
from app.agents.transcription import TranscriptionAgent
from app.agents.translation import TranslationAgent

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the localization pipeline: transcription → translation.

    Pure function — takes input, returns output, never touches the database.
    The Celery task handles persistence and error recovery.
    """

    def __init__(
        self,
        openai_api_key: str,
        anthropic_api_key: str,
    ) -> None:
        self._transcription_agent = TranscriptionAgent(openai_api_key)
        self._translation_agent = TranslationAgent(anthropic_api_key)
        self._logger = logger.bind(component="orchestrator")

    async def process(self, input: PipelineInput) -> PipelineOutput:
        """Run the full pipeline: transcribe then translate to all targets.

        Translations run in parallel across target languages.

        Args:
            input: Pipeline input with audio path and language config.

        Returns:
            Complete pipeline output with transcription and all translations.
        """
        self._logger.info(
            "pipeline_started",
            job_id=str(input.job_id),
            source=input.source_language,
            targets=input.target_languages,
        )

        # Step 1: Transcription
        transcription = await self._transcription_agent.process(
            TranscriptionInput(
                job_id=input.job_id,
                audio_file_path=input.audio_file_path,
                source_language=input.source_language,
            )
        )

        self._logger.info(
            "transcription_phase_done",
            job_id=str(input.job_id),
            segment_count=len(transcription.segments),
        )

        # Step 2: Translation (parallel across languages)
        translations = await self._translate_all(
            job_id=input.job_id,
            transcription=transcription,
            target_languages=input.target_languages,
        )

        # Aggregate costs
        total_cost = transcription.api_cost_usd + sum(
            t.api_cost_usd for t in translations.values()
        )
        total_usage = {
            "transcription": transcription.api_usage,
            "translations": {
                lang: t.api_usage for lang, t in translations.items()
            },
        }

        self._logger.info(
            "pipeline_completed",
            job_id=str(input.job_id),
            languages_translated=list(translations.keys()),
            total_cost_usd=total_cost,
        )

        return PipelineOutput(
            job_id=input.job_id,
            transcription=transcription,
            translations=translations,
            total_cost_usd=total_cost,
            total_api_usage=total_usage,
        )

    async def _translate_all(
        self,
        job_id,
        transcription: TranscriptionOutput,
        target_languages: list[str],
    ) -> dict[str, TranslationOutput]:
        """Translate to all target languages in parallel.

        Args:
            job_id: Job UUID.
            transcription: Source transcription output.
            target_languages: List of target language codes.

        Returns:
            Dict mapping language code to TranslationOutput.
        """
        async def translate_one(target_lang: str) -> tuple[str, TranslationOutput]:
            result = await self._translation_agent.process(
                TranslationInput(
                    job_id=job_id,
                    segments=transcription.segments,
                    source_language=transcription.language,
                    target_language=target_lang,
                )
            )
            return target_lang, result

        tasks = [translate_one(lang) for lang in target_languages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        translations: dict[str, TranslationOutput] = {}
        for result in results:
            if isinstance(result, Exception):
                self._logger.error(
                    "translation_language_failed",
                    error=str(result),
                )
                # Don't silently swallow — re-raise if all fail
                continue
            lang, output = result
            translations[lang] = output

        if not translations and target_languages:
            raise Exception(
                f"All translations failed for languages: {target_languages}"
            )

        return translations
