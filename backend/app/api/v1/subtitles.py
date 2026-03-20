"""Subtitle editor endpoints — CRUD for individual subtitle cues."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import (
    SubtitleBatchUpdate,
    SubtitleListResponse,
    SubtitleResponse,
    SubtitleSplitRequest,
    SubtitleUpdate,
)
from app.auth import get_current_user
from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.job import Job
from app.models.project import Project
from app.models.subtitle import Subtitle
from app.models.user import User

router = APIRouter()


async def _get_user_subtitle(
    subtitle_id: uuid.UUID, user: User, db: AsyncSession
) -> Subtitle:
    """Get a subtitle belonging to the authenticated user."""
    result = await db.execute(
        select(Subtitle)
        .join(Job)
        .join(Project)
        .where(Subtitle.id == subtitle_id, Project.user_id == user.id)
    )
    subtitle = result.scalar_one_or_none()
    if subtitle is None:
        raise NotFoundError(f"Subtitle {subtitle_id} not found")
    return subtitle


@router.get(
    "/jobs/{job_id}/subtitles/{language}",
    response_model=SubtitleListResponse,
)
async def list_subtitles(
    job_id: uuid.UUID,
    language: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all subtitle cues for a job and language.

    Returns subtitles ordered by index, for use in the subtitle editor.
    """
    # Verify job belongs to user
    result = await db.execute(
        select(Job)
        .join(Project)
        .where(Job.id == job_id, Project.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")

    # Fetch subtitles for the language
    subs_result = await db.execute(
        select(Subtitle)
        .where(Subtitle.job_id == job_id, Subtitle.language == language)
        .order_by(Subtitle.index)
    )
    subtitles = list(subs_result.scalars().all())

    return {
        "job_id": job_id,
        "language": language,
        "total": len(subtitles),
        "subtitles": subtitles,
    }


@router.get("/subtitles/{subtitle_id}", response_model=SubtitleResponse)
async def get_subtitle(
    subtitle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subtitle:
    """Get a single subtitle cue."""
    return await _get_user_subtitle(subtitle_id, user, db)


@router.put("/subtitles/{subtitle_id}", response_model=SubtitleResponse)
async def update_subtitle(
    subtitle_id: uuid.UUID,
    body: SubtitleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subtitle:
    """Update a subtitle cue's text, timing, or speaker."""
    subtitle = await _get_user_subtitle(subtitle_id, user, db)

    if body.text is not None:
        subtitle.text = body.text
    if body.start_ms is not None:
        subtitle.start_ms = body.start_ms
    if body.end_ms is not None:
        subtitle.end_ms = body.end_ms
    if body.speaker is not None:
        subtitle.speaker = body.speaker

    # Validate timing
    if subtitle.start_ms >= subtitle.end_ms:
        raise ValidationError("start_ms must be less than end_ms")

    await db.commit()
    await db.refresh(subtitle)
    return subtitle


@router.put(
    "/jobs/{job_id}/subtitles/batch",
    response_model=list[SubtitleResponse],
)
async def batch_update_subtitles(
    job_id: uuid.UUID,
    body: SubtitleBatchUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Subtitle]:
    """Batch-update multiple subtitle cues (auto-save from editor)."""
    # Verify job belongs to user
    result = await db.execute(
        select(Job)
        .join(Project)
        .where(Job.id == job_id, Project.user_id == user.id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError(f"Job {job_id} not found")

    # Fetch all subtitles to update
    sub_ids = [item.id for item in body.updates]
    subs_result = await db.execute(
        select(Subtitle).where(
            Subtitle.id.in_(sub_ids), Subtitle.job_id == job_id
        )
    )
    subs_by_id = {s.id: s for s in subs_result.scalars().all()}

    updated = []
    for item in body.updates:
        sub = subs_by_id.get(item.id)
        if sub is None:
            raise NotFoundError(f"Subtitle {item.id} not found in job {job_id}")

        if item.text is not None:
            sub.text = item.text
        if item.start_ms is not None:
            sub.start_ms = item.start_ms
        if item.end_ms is not None:
            sub.end_ms = item.end_ms

        if sub.start_ms >= sub.end_ms:
            raise ValidationError(
                f"Subtitle {sub.index}: start_ms must be less than end_ms"
            )
        updated.append(sub)

    await db.commit()
    for sub in updated:
        await db.refresh(sub)

    return sorted(updated, key=lambda s: s.index)


@router.post(
    "/subtitles/{subtitle_id}/split",
    response_model=list[SubtitleResponse],
    status_code=201,
)
async def split_subtitle(
    subtitle_id: uuid.UUID,
    body: SubtitleSplitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Subtitle]:
    """Split a subtitle cue into two at the given timecode.

    Shifts all subsequent subtitle indices up by 1.
    """
    subtitle = await _get_user_subtitle(subtitle_id, user, db)

    if body.split_at_ms <= subtitle.start_ms or body.split_at_ms >= subtitle.end_ms:
        raise ValidationError(
            "split_at_ms must be between start_ms and end_ms"
        )

    # Shift indices of all subsequent subtitles
    later_subs_result = await db.execute(
        select(Subtitle).where(
            Subtitle.job_id == subtitle.job_id,
            Subtitle.language == subtitle.language,
            Subtitle.index > subtitle.index,
        )
    )
    for later_sub in later_subs_result.scalars().all():
        later_sub.index += 1

    # Create the second half
    new_sub = Subtitle(
        job_id=subtitle.job_id,
        index=subtitle.index + 1,
        start_ms=body.split_at_ms,
        end_ms=subtitle.end_ms,
        text=body.second_text,
        language=subtitle.language,
        speaker=subtitle.speaker,
    )
    db.add(new_sub)

    # Modify the original to be the first half
    subtitle.end_ms = body.split_at_ms
    subtitle.text = body.first_text

    await db.commit()
    await db.refresh(subtitle)
    await db.refresh(new_sub)

    return [subtitle, new_sub]


@router.post(
    "/subtitles/{subtitle_id}/merge",
    response_model=SubtitleResponse,
)
async def merge_subtitle_with_next(
    subtitle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subtitle:
    """Merge a subtitle cue with the next one.

    Combines text, extends timing to cover both, and shifts
    all subsequent indices down by 1.
    """
    subtitle = await _get_user_subtitle(subtitle_id, user, db)

    # Find the next subtitle
    next_result = await db.execute(
        select(Subtitle).where(
            Subtitle.job_id == subtitle.job_id,
            Subtitle.language == subtitle.language,
            Subtitle.index == subtitle.index + 1,
        )
    )
    next_sub = next_result.scalar_one_or_none()
    if next_sub is None:
        raise ValidationError("No next subtitle to merge with")

    # Merge: extend timing, combine text
    subtitle.end_ms = next_sub.end_ms
    subtitle.text = f"{subtitle.text}\n{next_sub.text}"

    # Shift indices of subtitles after the merged one
    later_result = await db.execute(
        select(Subtitle).where(
            Subtitle.job_id == subtitle.job_id,
            Subtitle.language == subtitle.language,
            Subtitle.index > next_sub.index,
        )
    )
    for later_sub in later_result.scalars().all():
        later_sub.index -= 1

    # Delete the merged subtitle
    await db.delete(next_sub)

    await db.commit()
    await db.refresh(subtitle)

    return subtitle
