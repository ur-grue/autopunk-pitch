"""Billing service — wraps Stripe API for customer management and payments."""

import math
import uuid
from typing import Any

import stripe
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.exceptions import BillingError, PaymentRequiredError
from app.models.invoice import Invoice
from app.models.job import Job
from app.models.user import User

logger = structlog.get_logger(__name__)


class BillingService:
    """Handles Stripe customer lifecycle, checkout sessions, webhooks, and usage.

    All public methods are async. Stripe SDK calls are synchronous but safe to
    invoke directly inside FastAPI's async handlers because they are short-lived
    HTTP requests that run in the default thread pool managed by the event loop.

    Args:
        settings: Application settings instance. Defaults to the cached singleton.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        stripe.api_key = self._settings.stripe_secret_key

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def get_or_create_customer(self, user: User, db: AsyncSession) -> str:
        """Return the Stripe customer ID for a user, creating one if needed.

        If the user already has a ``stripe_customer_id`` it is returned
        immediately.  Otherwise a new Stripe Customer is created and the ID is
        persisted back to the user row before returning.

        Args:
            user: The authenticated application user.
            db: An open async database session.

        Returns:
            The Stripe customer ID string (e.g. ``"cus_..."``).

        Raises:
            BillingError: If the Stripe API call fails.
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        log = logger.bind(user_id=str(user.id), email=user.email)
        log.info("stripe_customer_creating")

        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.display_name or user.email,
                metadata={"user_id": str(user.id), "clerk_id": user.clerk_id},
            )
        except stripe.StripeError as exc:
            log.error("stripe_customer_create_failed", error=str(exc))
            raise BillingError(f"Failed to create Stripe customer: {exc}") from exc

        user.stripe_customer_id = customer.id
        db.add(user)
        await db.flush()

        log.info("stripe_customer_created", stripe_customer_id=customer.id)
        return customer.id

    async def create_checkout_session(
        self, user: User, job: Job, db: AsyncSession
    ) -> dict[str, Any]:
        """Create a Stripe Checkout Session for a single job.

        Price is calculated as ``ceil(duration_seconds / 60) * price_per_minute_usd``.
        An ``Invoice`` record with status ``"pending"`` is inserted before the
        Stripe session is created so that we can correlate webhook events back
        to the job.

        Args:
            user: The authenticated user who owns the job.
            job: The job to bill for. Must have ``duration_seconds`` set.
            db: An open async database session.

        Returns:
            Dict with ``checkout_url`` and ``invoice_id``.

        Raises:
            PaymentRequiredError: If the job has no ``duration_seconds``.
            BillingError: If the Stripe API call fails.
        """
        if not job.duration_seconds:
            raise PaymentRequiredError(
                "Job has no duration; cannot calculate billing amount."
            )

        duration_minutes = math.ceil(job.duration_seconds / 60)
        amount_usd = duration_minutes * self._settings.price_per_minute_usd
        # Stripe amounts are in cents (integer)
        amount_cents = round(amount_usd * 100)

        log = logger.bind(
            user_id=str(user.id),
            job_id=str(job.id),
            duration_minutes=duration_minutes,
            amount_usd=amount_usd,
        )
        log.info("checkout_session_creating")

        customer_id = await self.get_or_create_customer(user, db)

        description = (
            f"Autopunk Localize — job {job.id} "
            f"({duration_minutes} min @ ${self._settings.price_per_minute_usd:.2f}/min)"
        )

        # Persist a pending invoice so we can look it up from webhook events.
        invoice = Invoice(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            amount_usd=amount_usd,
            duration_minutes=duration_minutes,
            status="pending",
            description=description,
        )
        db.add(invoice)
        await db.flush()  # obtain invoice.id before passing to Stripe metadata

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": amount_cents,
                            "product_data": {
                                "name": "Autopunk Localize — media processing",
                                "description": description,
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                metadata={
                    "invoice_id": str(invoice.id),
                    "job_id": str(job.id),
                    "user_id": str(user.id),
                },
                # Callers must supply success/cancel URLs via the request context;
                # these sensible defaults allow the session to be created without them.
                success_url="https://app.autopunk.io/dashboard?payment=success",
                cancel_url="https://app.autopunk.io/dashboard?payment=cancelled",
            )
        except stripe.StripeError as exc:
            log.error("checkout_session_create_failed", error=str(exc))
            raise BillingError(
                f"Failed to create Stripe checkout session: {exc}"
            ) from exc

        # Back-fill the session ID on the invoice.
        invoice.stripe_checkout_session_id = session.id
        db.add(invoice)
        await db.flush()

        log.info(
            "checkout_session_created",
            stripe_session_id=session.id,
            invoice_id=str(invoice.id),
        )
        return {
            "checkout_url": session.url,
            "invoice_id": invoice.id,
        }

    async def handle_webhook(
        self, payload: bytes, sig_header: str, db: AsyncSession
    ) -> None:
        """Verify and process an inbound Stripe webhook event.

        Handled event types:

        * ``checkout.session.completed`` — marks the associated invoice as
          ``"paid"`` and increments the user's ``monthly_minutes_used``.
        * ``payment_intent.payment_failed`` — marks the associated invoice as
          ``"failed"``.

        All other event types are acknowledged without action.

        Args:
            payload: The raw request body bytes from Stripe.
            sig_header: The value of the ``Stripe-Signature`` HTTP header.
            db: An open async database session.

        Raises:
            BillingError: If webhook signature verification fails or if the
                Stripe event cannot be parsed.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self._settings.stripe_webhook_secret
            )
        except stripe.SignatureVerificationError as exc:
            logger.warning("webhook_signature_invalid", error=str(exc))
            raise BillingError(f"Webhook signature verification failed: {exc}") from exc
        except Exception as exc:
            logger.error("webhook_parse_failed", error=str(exc))
            raise BillingError(f"Failed to parse webhook payload: {exc}") from exc

        event_type: str = event["type"]
        log = logger.bind(stripe_event_id=event["id"], event_type=event_type)
        log.info("webhook_received")

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(event["data"]["object"], db, log)
        elif event_type == "payment_intent.payment_failed":
            await self._handle_payment_failed(event["data"]["object"], db, log)
        else:
            log.debug("webhook_event_unhandled")

    async def get_usage_summary(self, user: User, db: AsyncSession) -> dict[str, Any]:
        """Return a billing and usage summary for the given user.

        Queries the ``invoices`` table to aggregate total spend and invoice
        count, then combines with quota fields from the user row.

        Args:
            user: The authenticated application user.
            db: An open async database session.

        Returns:
            A dictionary with the following keys:

            * ``total_minutes_used`` (int): Lifetime minutes consumed, derived
              from ``monthly_minutes_used`` on the user row.
            * ``monthly_minutes_limit`` (int): Current plan limit.
            * ``total_spent_usd`` (float): Sum of all paid invoice amounts.
            * ``plan`` (str): The user's current plan name.
            * ``invoice_count`` (int): Total number of invoices (any status).
        """
        log = logger.bind(user_id=str(user.id))
        log.debug("usage_summary_querying")

        paid_result = await db.execute(
            select(func.coalesce(func.sum(Invoice.amount_usd), 0))
            .where(Invoice.user_id == user.id)
            .where(Invoice.status == "paid")
        )
        total_spent_usd: float = float(paid_result.scalar_one())

        count_result = await db.execute(
            select(func.count(Invoice.id)).where(Invoice.user_id == user.id)
        )
        invoice_count: int = count_result.scalar_one()

        summary = {
            "monthly_minutes_used": user.monthly_minutes_used,
            "monthly_minutes_limit": user.monthly_minutes_limit,
            "total_spent_usd": round(total_spent_usd, 6),
            "plan": user.plan,
            "invoice_count": invoice_count,
        }

        log.info("usage_summary_returned", **summary)
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _handle_checkout_completed(
        self,
        session_obj: dict[str, Any],
        db: AsyncSession,
        log: Any,
    ) -> None:
        """Mark the invoice paid and update the user's monthly quota.

        Args:
            session_obj: The Stripe ``checkout.Session`` object from the event.
            db: An open async database session.
            log: A bound structlog logger carrying event context.
        """
        session_id: str = session_obj.get("id", "")
        invoice_id_str: str | None = (session_obj.get("metadata") or {}).get(
            "invoice_id"
        )
        payment_intent_id: str | None = session_obj.get("payment_intent")

        log = log.bind(
            stripe_session_id=session_id,
            invoice_id=invoice_id_str,
            payment_intent_id=payment_intent_id,
        )

        if not invoice_id_str:
            log.warning("checkout_completed_no_invoice_id")
            return

        try:
            invoice_uuid = uuid.UUID(invoice_id_str)
        except ValueError:
            log.error("checkout_completed_bad_invoice_uuid")
            return

        result = await db.execute(select(Invoice).where(Invoice.id == invoice_uuid))
        invoice: Invoice | None = result.scalar_one_or_none()

        if invoice is None:
            log.error("checkout_completed_invoice_not_found")
            return

        invoice.status = "paid"
        if payment_intent_id:
            invoice.stripe_payment_intent_id = payment_intent_id
        db.add(invoice)

        # Increment the user's monthly usage counter.
        user_result = await db.execute(select(User).where(User.id == invoice.user_id))
        user: User | None = user_result.scalar_one_or_none()
        if user is not None:
            minutes_billed = int(math.ceil(float(invoice.duration_minutes)))
            user.monthly_minutes_used = user.monthly_minutes_used + minutes_billed
            db.add(user)
            log.info(
                "user_quota_updated",
                minutes_added=minutes_billed,
                monthly_minutes_used=user.monthly_minutes_used,
            )

        await db.flush()
        log.info("invoice_marked_paid", invoice_id=invoice_id_str)

    async def _handle_payment_failed(
        self,
        payment_intent_obj: dict[str, Any],
        db: AsyncSession,
        log: Any,
    ) -> None:
        """Mark the invoice as failed when a PaymentIntent is declined.

        Args:
            payment_intent_obj: The Stripe ``PaymentIntent`` object from the event.
            db: An open async database session.
            log: A bound structlog logger carrying event context.
        """
        payment_intent_id: str = payment_intent_obj.get("id", "")
        log = log.bind(payment_intent_id=payment_intent_id)

        if not payment_intent_id:
            log.warning("payment_failed_no_intent_id")
            return

        result = await db.execute(
            select(Invoice).where(Invoice.stripe_payment_intent_id == payment_intent_id)
        )
        invoice: Invoice | None = result.scalar_one_or_none()

        if invoice is None:
            # The intent may not have been recorded yet (e.g. failed before
            # checkout.session.completed fired).  Log and move on.
            log.warning("payment_failed_invoice_not_found")
            return

        invoice.status = "failed"
        db.add(invoice)
        await db.flush()
        log.info("invoice_marked_failed", invoice_id=str(invoice.id))
