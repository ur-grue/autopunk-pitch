"""Platform profile endpoints — public read-only access to QC profiles."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import PlatformProfileResponse
from app.database import get_db
from app.exceptions import NotFoundError
from app.models.platform_profile import PlatformProfile

router = APIRouter()


@router.get("/platform-profiles", response_model=list[PlatformProfileResponse])
async def list_platform_profiles(
    db: AsyncSession = Depends(get_db),
) -> list[PlatformProfile]:
    """Return all platform QC profiles ordered by name.

    This is a public endpoint — no authentication required.

    Args:
        db: Async database session.

    Returns:
        List of PlatformProfileResponse objects sorted alphabetically by name.
    """
    result = await db.execute(
        select(PlatformProfile).order_by(PlatformProfile.name)
    )
    return list(result.scalars().all())


@router.get(
    "/platform-profiles/{profile_id}",
    response_model=PlatformProfileResponse,
)
async def get_platform_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PlatformProfile:
    """Return a single platform QC profile by ID.

    This is a public endpoint — no authentication required.

    Args:
        profile_id: UUID of the platform profile to retrieve.
        db: Async database session.

    Returns:
        PlatformProfileResponse for the requested profile.

    Raises:
        NotFoundError: If no profile with the given ID exists.
    """
    result = await db.execute(
        select(PlatformProfile).where(PlatformProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise NotFoundError(f"Platform profile {profile_id} not found")

    return profile
