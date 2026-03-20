"""PlatformProfile model — platform-specific QC rules (Netflix, YouTube, BBC)."""

import uuid

from sqlalchemy import JSON, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class PlatformProfile(TimestampMixin, Base):
    """A platform-specific subtitle quality profile.

    Stores QC rules (line length, reading speed, etc.) that vary by
    delivery platform. Settings are stored as JSONB for flexibility.
    """

    __tablename__ = "platform_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Core QC rule overrides (flat columns for fast queries)
    max_chars_per_line: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="42"
    )
    max_lines_per_cue: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="2"
    )
    max_cps: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="25"
    )
    min_duration_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1000"
    )
    min_gap_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # Extended settings (JSONB for platform-specific extras)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
