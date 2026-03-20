"""Job model — a single pipeline execution within a project."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.platform_profile import PlatformProfile
    from app.models.project import Project
    from app.models.subtitle import Subtitle


class Job(TimestampMixin, Base):
    """A processing job (transcription, translation, full pipeline, etc.)."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pending"
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    input_file_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    output_file_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 6), nullable=False, server_default="0"
    )
    api_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    platform_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("platform_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="jobs")
    subtitles: Mapped[list["Subtitle"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    platform_profile: Mapped["PlatformProfile | None"] = relationship()
