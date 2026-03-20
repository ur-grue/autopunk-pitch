"""Project CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import ProjectCreate, ProjectDetailResponse, ProjectResponse
from app.auth import get_current_user
from app.database import get_db
from app.exceptions import NotFoundError
from app.models.project import Project
from app.models.user import User

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Create a new localization project."""
    project = Project(
        user_id=user.id,
        name=body.name,
        source_language=body.source_language,
        target_languages=body.target_languages,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    """List all projects for the authenticated user."""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Get a project by ID with its jobs."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == user.id)
        .options(selectinload(Project.jobs))
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise NotFoundError(f"Project {project_id} not found")

    return project
