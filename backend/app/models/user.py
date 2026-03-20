"""User model — maps to Clerk external auth."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.project import Project


class User(TimestampMixin, Base):
    """Application user, linked to Clerk via clerk_id."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    clerk_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="free"
    )
    monthly_minutes_used: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    monthly_minutes_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="10"
    )

    # Stripe fields
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
