"""Export endpoints — download subtitle files in various formats."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.formatting import FormattingAgent
from app.agents.schemas import FormattingInput, TranslationSegment
from app.auth import get_current_user
from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.job import Job
from app.models.project import Project
from app.models.user import User

router = APIRouter()

FORMAT_CONTENT_TYPES = {
    "srt": "application/x-subrip",
    "webvtt": "text/vtt",
    "ebu_stl": "application/octet-stream",
}
FORMAT_EXTENSIONS = {
    "srt": ".srt",
    "webvtt": ".vtt",
    "ebu_stl": ".stl",
}


@router.get("/jobs/{job_id}/export/{language}")
async def export_subtitles(
    job_id: uuid.UUID,
    language: str,
    format: str = "srt",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export subtitles for a language in the requested format."""
    if format not in FORMAT_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported format: {format}. Supported: {list(FORMAT_CONTENT_TYPES)}"
        )

    # Load job scoped to user
    result = await db.execute(
        select(Job)
        .join(Project)
        .where(Job.id == job_id, Project.user_id == user.id)
        .options(selectinload(Job.subtitles))
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise NotFoundError(f"Job {job_id} not found")

    if job.status != "completed":
        raise ValidationError(f"Export not available. Job status: {job.status}")

    # Get project for source language
    proj_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = proj_result.scalar_one()

    # Filter subtitles for requested language
    subs = sorted(
        [s for s in job.subtitles if s.language == language],
        key=lambda s: s.index,
    )

    if not subs:
        raise NotFoundError(f"No subtitles found for language: {language}")

    # Get source subtitles for original_text reference
    source_subs = {
        s.index: s
        for s in job.subtitles
        if s.language == project.source_language
    }

    # Build segments for the formatter
    segments = [
        TranslationSegment(
            index=sub.index,
            start_ms=sub.start_ms,
            end_ms=sub.end_ms,
            original_text=(
                source_subs[sub.index].text
                if sub.index in source_subs
                else (sub.metadata_ or {}).get("original_text", sub.text)
            ),
            translated_text=sub.text,
        )
        for sub in subs
    ]

    # Generate formatted content
    formatter = FormattingAgent()
    output = await formatter.process(
        FormattingInput(
            job_id=job_id,
            segments=segments,
            language=language,
            format=format,
        )
    )

    # Return as file download.
    # EBU-STL is a binary format: FormattingAgent stores the payload as a
    # latin-1 string (a lossless 1:1 byte mapping). Encode it back to bytes
    # before writing the HTTP response body.
    ext = FORMAT_EXTENSIONS[format]
    filename = f"{project.name}_{language}{ext}"

    if format == "ebu_stl":
        response_content: str | bytes = output.content.encode("latin-1")
    else:
        response_content = output.content

    return Response(
        content=response_content,
        media_type=FORMAT_CONTENT_TYPES[format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
