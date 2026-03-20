"""Add billing tables and platform profiles.

Revision ID: 002
Revises: 001
Create Date: 2026-03-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Stripe fields to users
    op.add_column(
        "users",
        sa.Column(
            "stripe_customer_id",
            sa.String(255),
            unique=True,
            nullable=True,
        ),
    )

    # Platform profiles table
    op.create_table(
        "platform_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "max_chars_per_line",
            sa.Integer,
            nullable=False,
            server_default="42",
        ),
        sa.Column(
            "max_lines_per_cue",
            sa.Integer,
            nullable=False,
            server_default="2",
        ),
        sa.Column(
            "max_cps", sa.Float, nullable=False, server_default="25"
        ),
        sa.Column(
            "min_duration_ms",
            sa.Integer,
            nullable=False,
            server_default="1000",
        ),
        sa.Column(
            "min_gap_ms", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Add platform_profile_id FK to jobs
    op.add_column(
        "jobs",
        sa.Column(
            "platform_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Invoices table
    op.create_table(
        "invoices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("duration_minutes", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "stripe_payment_intent_id",
            sa.String(255),
            unique=True,
            nullable=True,
        ),
        sa.Column(
            "stripe_checkout_session_id",
            sa.String(255),
            unique=True,
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Seed default platform profiles
    op.execute("""
        INSERT INTO platform_profiles (id, name, display_name, description, max_chars_per_line, max_lines_per_cue, max_cps, min_duration_ms, min_gap_ms, settings)
        VALUES
        (gen_random_uuid(), 'netflix', 'Netflix', 'Netflix Timed Text Style Guide', 42, 2, 20, 833, 2, '{"forced_narrative": true, "italic_for_foreign": true, "max_duration_ms": 7000}'),
        (gen_random_uuid(), 'youtube', 'YouTube', 'YouTube subtitle best practices', 42, 2, 25, 1000, 0, '{"auto_punctuation": true}'),
        (gen_random_uuid(), 'bbc', 'BBC', 'BBC Subtitle Guidelines', 37, 2, 18, 1000, 2, '{"color_speaker_id": true, "max_duration_ms": 7000}'),
        (gen_random_uuid(), 'broadcast', 'Broadcast (Default)', 'Standard broadcast subtitle rules', 42, 2, 25, 1000, 0, '{}')
    """)


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_column("jobs", "platform_profile_id")
    op.drop_table("platform_profiles")
    op.drop_column("users", "stripe_customer_id")
