"""Invoice model — tracks per-job billing records."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Invoice(TimestampMixin, Base):
    """A billing record for a completed job."""

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount_usd: Mapped[float] = mapped_column(
        Numeric(10, 6), nullable=False
    )
    duration_minutes: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pending"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="invoices")
    job: Mapped["Job | None"] = relationship()
