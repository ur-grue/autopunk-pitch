"""Celery task for running the TranscriptionAgent."""

import asyncio
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.schemas import TranscriptionInput
from app.agents.transcription import TranscriptionAgent
from app.celery_app import celery_app
from app.config import get_settings
from app.models.job import Job
from app.models.subtitle import Subtitle
from app.services.audio_service import AudioService
from app.services.storage_service import StorageService

logger = structlog.get_logger(__name__)


async def _run_transcription(job_id: str) -> None:
    """Async implementation of the transcription pipeline.

    Flow:
    1. Load Job from DB, set status=processing
    2. Download video from S3 to temp dir
    3. Extract audio via AudioService
    4. Run TranscriptionAgent.process()
    5. Persist TranscriptionSegments as Subtitle rows
    6. Update Job: status=completed, cost, usage, timestamps
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    log = logger.bind(job_id=job_id)

    async with session_factory() as session:
        # 1. Load and update job status
        result = await session.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if job is None:
            log.error("job_not_found")
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                # 2. Download video from S3
                storage = StorageService(settings)
                video_data = await storage.download_file(job.input_file_key)
                video_path = tmp_path / "input_video"
                video_path.write_bytes(video_data)
                log.info("video_downloaded", size=len(video_data))

                # 3. Extract audio
                audio_service = AudioService()
                audio_path = str(tmp_path / "audio.mp3")
                duration = await audio_service.extract_audio(
                    str(video_path), audio_path
                )
                job.duration_seconds = duration
                log.info("audio_extracted", duration_seconds=duration)

                # 4. Load project to get source language
                from app.models.project import Project

                proj_result = await session.execute(
                    select(Project).where(Project.id == job.project_id)
                )
                project = proj_result.scalar_one()

                # 5. Run TranscriptionAgent
                agent = TranscriptionAgent(settings.openai_api_key)
                output = await agent.process(
                    TranscriptionInput(
                        job_id=uuid.UUID(job_id),
                        audio_file_path=audio_path,
                        source_language=project.source_language,
                    )
                )

                # 6. Persist segments as Subtitle rows
                for seg in output.segments:
                    subtitle = Subtitle(
                        job_id=uuid.UUID(job_id),
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        text=seg.text,
                        language=output.language,
                        confidence=seg.confidence,
                        metadata_={
                            "words": [w.model_dump() for w in seg.words]
                        }
                        if seg.words
                        else None,
                    )
                    session.add(subtitle)

                # 7. Update job
                job.status = "completed"
                job.cost_usd = output.api_cost_usd
                job.api_usage = output.api_usage
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()

                log.info(
                    "transcription_task_completed",
                    segment_count=len(output.segments),
                    cost_usd=output.api_cost_usd,
                )

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            log.error("transcription_task_failed", error=str(e))
            raise

    await engine.dispose()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_transcription(self, job_id: str) -> None:
    """Celery task wrapping the async transcription pipeline.

    Uses asyncio.run() to bridge Celery's sync execution model
    into the async agent code.
    """
    try:
        asyncio.run(_run_transcription(job_id))
    except Exception as exc:
        logger.error(
            "transcription_task_error",
            job_id=job_id,
            error=str(exc),
            retry=self.request.retries,
        )
        raise self.retry(exc=exc)
