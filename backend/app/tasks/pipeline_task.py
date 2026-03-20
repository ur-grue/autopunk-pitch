"""Celery task for running the full localization pipeline."""

import asyncio
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.orchestrator import PipelineOrchestrator
from app.agents.schemas import PipelineInput
from app.celery_app import celery_app
from app.config import get_settings
from app.models.job import Job
from app.models.project import Project
from app.models.subtitle import Subtitle
from app.services.audio_service import AudioService
from app.services.storage_service import StorageService

logger = structlog.get_logger(__name__)


async def _run_pipeline(job_id: str) -> None:
    """Async implementation of the full localization pipeline.

    Flow:
    1. Load Job + Project from DB, set status=processing
    2. Download video from S3, extract audio
    3. Run PipelineOrchestrator (transcription → parallel translations)
    4. Persist source subtitles + translated subtitles as Subtitle rows
    5. Update Job: status=completed, cost, usage, timestamps
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    log = logger.bind(job_id=job_id)

    async with session_factory() as session:
        # 1. Load job and project
        result = await session.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if job is None:
            log.error("job_not_found")
            return

        proj_result = await session.execute(
            select(Project).where(Project.id == job.project_id)
        )
        project = proj_result.scalar_one()

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                # 2. Download video and extract audio
                storage = StorageService(settings)
                video_data = await storage.download_file(job.input_file_key)
                video_path = tmp_path / "input_video"
                video_path.write_bytes(video_data)
                log.info("video_downloaded", size=len(video_data))

                audio_service = AudioService()
                audio_path = str(tmp_path / "audio.mp3")
                duration = await audio_service.extract_audio(
                    str(video_path), audio_path
                )
                job.duration_seconds = duration

                # 3. Run pipeline
                orchestrator = PipelineOrchestrator(
                    openai_api_key=settings.openai_api_key,
                    anthropic_api_key=settings.anthropic_api_key,
                )
                output = await orchestrator.process(
                    PipelineInput(
                        job_id=uuid.UUID(job_id),
                        audio_file_path=audio_path,
                        source_language=project.source_language,
                        target_languages=project.target_languages,
                    )
                )

                # 4. Persist source transcription as Subtitle rows
                for seg in output.transcription.segments:
                    subtitle = Subtitle(
                        job_id=uuid.UUID(job_id),
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        text=seg.text,
                        language=output.transcription.language,
                        confidence=seg.confidence,
                        metadata_={
                            "words": [w.model_dump() for w in seg.words]
                        }
                        if seg.words
                        else None,
                    )
                    session.add(subtitle)

                # Persist translated subtitles
                for lang, translation in output.translations.items():
                    for seg in translation.segments:
                        subtitle = Subtitle(
                            job_id=uuid.UUID(job_id),
                            index=seg.index,
                            start_ms=seg.start_ms,
                            end_ms=seg.end_ms,
                            text=seg.translated_text,
                            language=lang,
                            flags=seg.flags if seg.flags else None,
                            metadata_={
                                "original_text": seg.original_text,
                            },
                        )
                        session.add(subtitle)

                # 5. Update job
                job.status = "completed"
                job.cost_usd = output.total_cost_usd
                job.api_usage = output.total_api_usage
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()

                log.info(
                    "pipeline_task_completed",
                    languages=list(output.translations.keys()),
                    total_cost_usd=output.total_cost_usd,
                )

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            log.error("pipeline_task_failed", error=str(e))
            raise

    await engine.dispose()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_pipeline(self, job_id: str) -> None:
    """Celery task wrapping the async localization pipeline.

    Uses asyncio.run() to bridge Celery's sync execution model
    into the async orchestrator code.
    """
    try:
        asyncio.run(_run_pipeline(job_id))
    except Exception as exc:
        logger.error(
            "pipeline_task_error",
            job_id=job_id,
            error=str(exc),
            retry=self.request.retries,
        )
        raise self.retry(exc=exc)
