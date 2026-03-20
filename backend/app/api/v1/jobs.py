"""Job endpoints — submit transcription, check status, get results."""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import (
    JobResponse,
    PipelineLanguagesResponse,
    TranscriptResponse,
    TranslatedSubtitlesResponse,
)
from app.agents.schemas import TranscriptionSegment, TranslationSegment
from app.auth import get_current_user
from app.database import get_db
from app.exceptions import NotFoundError, QuotaExceededError, ValidationError
from app.models.job import Job
from app.models.project import Project
from app.models.subtitle import Subtitle
from app.models.user import User
from app.services.storage_service import StorageService
from app.tasks.pipeline_task import run_pipeline
from app.tasks.transcription_task import run_transcription

router = APIRouter()

ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}
ALLOWED_EXTENSIONS = {".mp4", ".mov"}


def _check_quota(user: User) -> None:
    """Check if user has remaining minutes in their quota."""
    if user.monthly_minutes_used >= user.monthly_minutes_limit:
        raise QuotaExceededError(
            f"Monthly quota exceeded: {user.monthly_minutes_used}/{user.monthly_minutes_limit} minutes used. "
            f"Upgrade your plan for more minutes."
        )


def _validate_file(filename: str) -> str:
    """Validate file extension and return it."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


async def _get_user_project(
    project_id: uuid.UUID, user: User, db: AsyncSession
) -> Project:
    """Get a project belonging to the authenticated user."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError(f"Project {project_id} not found")
    return project


async def _get_user_job(
    job_id: uuid.UUID, user: User, db: AsyncSession
) -> Job:
    """Get a job belonging to the authenticated user."""
    result = await db.execute(
        select(Job)
        .join(Project)
        .where(Job.id == job_id, Project.user_id == user.id)
        .options(selectinload(Job.subtitles))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return job


@router.post(
    "/projects/{project_id}/jobs/transcribe",
    response_model=JobResponse,
    status_code=202,
)
async def submit_transcription(
    project_id: uuid.UUID,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Upload a video and start transcription."""
    _check_quota(user)
    project = await _get_user_project(project_id, user, db)

    filename = file.filename or ""
    _validate_file(filename)

    # Upload to S3
    storage = StorageService()
    file_key = f"{project_id}/input/{filename}"
    await storage.upload_file(file, file_key)

    # Create job record
    job = Job(
        project_id=project_id,
        job_type="transcription",
        status="queued",
        input_file_key=file_key,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    task = run_transcription.delay(str(job.id))
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)

    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Get job status and details."""
    return await _get_user_job(job_id, user, db)


@router.post(
    "/projects/{project_id}/jobs/localize",
    response_model=JobResponse,
    status_code=202,
)
async def submit_pipeline(
    project_id: uuid.UUID,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Upload a video and start the full localization pipeline."""
    _check_quota(user)
    project = await _get_user_project(project_id, user, db)

    if not project.target_languages:
        raise ValidationError("Project has no target languages configured")

    filename = file.filename or ""
    _validate_file(filename)

    # Upload to S3
    storage = StorageService()
    file_key = f"{project_id}/input/{filename}"
    await storage.upload_file(file, file_key)

    # Create job record
    job = Job(
        project_id=project_id,
        job_type="full_pipeline",
        status="queued",
        input_file_key=file_key,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    task = run_pipeline.delay(str(job.id))
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)

    return job


@router.get("/jobs/{job_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the source transcription for a completed job."""
    job = await _get_user_job(job_id, user, db)

    if job.status != "completed":
        raise ValidationError(
            f"Transcript not available. Job status: {job.status}"
        )

    proj_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = proj_result.scalar_one()

    subtitles = sorted(
        [s for s in job.subtitles if s.language == project.source_language],
        key=lambda s: s.index,
    )
    segments = [
        TranscriptionSegment(
            index=sub.index,
            start_ms=sub.start_ms,
            end_ms=sub.end_ms,
            text=sub.text,
            confidence=sub.confidence,
        )
        for sub in subtitles
    ]

    duration_ms = max((s.end_ms for s in segments), default=0)

    return {
        "job_id": job_id,
        "language": project.source_language,
        "duration_ms": duration_ms,
        "segments": segments,
    }


@router.get("/jobs/{job_id}/languages", response_model=PipelineLanguagesResponse)
async def get_job_languages(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List available languages for a completed pipeline job."""
    job = await _get_user_job(job_id, user, db)

    if job.status != "completed":
        raise ValidationError(f"Not available. Job status: {job.status}")

    proj_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = proj_result.scalar_one()

    languages = sorted(
        {s.language for s in job.subtitles if s.language != project.source_language}
    )

    return {
        "job_id": job_id,
        "source_language": project.source_language,
        "target_languages": languages,
    }


@router.get(
    "/jobs/{job_id}/translations/{language}",
    response_model=TranslatedSubtitlesResponse,
)
async def get_translated_subtitles(
    job_id: uuid.UUID,
    language: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get translated subtitles for a specific language."""
    job = await _get_user_job(job_id, user, db)

    if job.status != "completed":
        raise ValidationError(f"Not available. Job status: {job.status}")

    proj_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = proj_result.scalar_one()

    translated_subs = sorted(
        [s for s in job.subtitles if s.language == language],
        key=lambda s: s.index,
    )

    if not translated_subs:
        raise NotFoundError(
            f"No translations found for language: {language}"
        )

    source_subs = {
        s.index: s
        for s in job.subtitles
        if s.language == project.source_language
    }

    segments = [
        TranslationSegment(
            index=sub.index,
            start_ms=sub.start_ms,
            end_ms=sub.end_ms,
            original_text=(
                source_subs[sub.index].text
                if sub.index in source_subs
                else (sub.metadata_ or {}).get("original_text", "")
            ),
            translated_text=sub.text,
            flags=sub.flags or [],
        )
        for sub in translated_subs
    ]

    duration_ms = max((s.end_ms for s in segments), default=0)

    return {
        "job_id": job_id,
        "source_language": project.source_language,
        "target_language": language,
        "duration_ms": duration_ms,
        "segments": segments,
    }
