"""Billing endpoints — Stripe checkout, invoices, usage, and webhooks."""

import uuid

import structlog
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceResponse,
    UsageResponse,
)
from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.invoice import Invoice
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.services.billing_service import BillingService

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _get_completed_user_job(
    job_id: uuid.UUID, user: User, db: AsyncSession
) -> Job:
    """Get a completed job scoped to the authenticated user's projects.

    Args:
        job_id: UUID of the job to retrieve.
        user: The authenticated user.
        db: Async database session.

    Returns:
        The matching Job instance.

    Raises:
        NotFoundError: If the job does not exist or does not belong to the user.
        ValidationError: If the job is not in a completed state.
    """
    result = await db.execute(
        select(Job)
        .join(Project)
        .where(Job.id == job_id, Project.user_id == user.id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise NotFoundError(f"Job {job_id} not found")

    if job.status != "completed":
        raise ValidationError(
            f"Job {job_id} is not completed (current status: {job.status})"
        )

    return job


@router.post("/billing/checkout", response_model=CheckoutResponse, status_code=201)
async def create_checkout_session(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Start a Stripe checkout session for a completed job.

    Args:
        body: Request containing the job_id to bill.
        user: The authenticated user.
        db: Async database session.

    Returns:
        CheckoutResponse with the Stripe-hosted checkout URL and invoice ID.

    Raises:
        NotFoundError: If the job does not exist or belong to the user.
        ValidationError: If the job is not completed.
        BillingError: If the Stripe session cannot be created.
    """
    job = await _get_completed_user_job(body.job_id, user, db)

    settings = get_settings()
    billing = BillingService(settings)
    result = await billing.create_checkout_session(user=user, job=job, db=db)

    logger.info(
        "checkout_session_created",
        user_id=str(user.id),
        job_id=str(job.id),
        invoice_id=str(result["invoice_id"]),
    )

    return CheckoutResponse(
        checkout_url=result["checkout_url"],
        invoice_id=result["invoice_id"],
    )


@router.get("/billing/usage", response_model=UsageResponse)
async def get_usage_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    """Return usage and quota summary for the authenticated user.

    Args:
        user: The authenticated user.
        db: Async database session.

    Returns:
        UsageResponse with plan details, consumed minutes, and spend totals.
    """
    settings = get_settings()
    billing = BillingService(settings)
    summary = await billing.get_usage_summary(user=user, db=db)

    return UsageResponse(**summary)


@router.get("/billing/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Invoice]:
    """List all invoices for the authenticated user, newest first.

    Args:
        user: The authenticated user.
        db: Async database session.

    Returns:
        List of InvoiceResponse objects ordered by creation date descending.
    """
    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .order_by(Invoice.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/billing/webhooks/stripe", status_code=200)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(default="", alias="stripe-signature"),
) -> dict:
    """Handle incoming Stripe webhook events.

    This endpoint is unauthenticated — Stripe calls it directly. The payload
    is verified using the webhook secret via the stripe-signature header.

    Args:
        request: Raw FastAPI request (used to read the unmodified body bytes).
        db: Async database session.
        stripe_signature: Value of the Stripe-Signature header.

    Returns:
        A minimal acknowledgement dict on success.

    Raises:
        BillingError: If the webhook signature is invalid or processing fails.
    """
    payload = await request.body()

    settings = get_settings()
    billing = BillingService(settings)
    await billing.handle_webhook(payload=payload, sig_header=stripe_signature, db=db)

    logger.info("stripe_webhook_processed")
    return {"received": True}
