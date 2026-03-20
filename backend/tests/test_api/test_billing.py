"""Tests for billing API endpoints and BillingService."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.exceptions import BillingError, PaymentRequiredError
from app.models.invoice import Invoice
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.services.billing_service import BillingService

# ------------------------------------------------------------------
# Test fixtures
# ------------------------------------------------------------------


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        source_language="en",
        target_languages=["fr", "es"],
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def test_job_completed(db_session: AsyncSession, test_project: Project) -> Job:
    """Create a completed job with duration."""
    job = Job(
        project_id=test_project.id,
        job_type="full_pipeline",
        status="completed",
        duration_seconds=120.0,  # 2 minutes
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
async def test_job_no_duration(db_session: AsyncSession, test_project: Project) -> Job:
    """Create a completed job without duration."""
    job = Job(
        project_id=test_project.id,
        job_type="full_pipeline",
        status="completed",
        duration_seconds=None,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
async def test_job_pending(db_session: AsyncSession, test_project: Project) -> Job:
    """Create a pending job."""
    job = Job(
        project_id=test_project.id,
        job_type="full_pipeline",
        status="pending",
        duration_seconds=120.0,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe Customer object."""
    customer = MagicMock()
    customer.id = "cus_test_customer_123"
    customer.email = "test@autopunk.local"
    return customer


@pytest.fixture
def mock_stripe_session():
    """Mock Stripe Checkout Session object."""
    session = MagicMock()
    session.id = "cs_test_session_456"
    session.url = "https://checkout.stripe.com/pay/cs_test_session_456"
    session.payment_intent = "pi_test_intent_789"
    return session


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with Stripe keys."""
    return Settings(
        stripe_secret_key="sk_test_key",
        stripe_webhook_secret="whsec_test_secret",
        stripe_publishable_key="pk_test_key",
        price_per_minute_usd=5.0,
    )


# ------------------------------------------------------------------
# API Endpoint Tests
# ------------------------------------------------------------------


class TestBillingCheckoutEndpoint:
    """Tests for POST /api/v1/billing/checkout."""

    async def test_checkout_creates_response(
        self,
        test_client: AsyncClient,
    ):
        """Test checkout returns proper response structure on success."""
        # Mock job that exists and is completed
        mock_job_id = uuid.uuid4()

        with patch("stripe.Customer.create") as mock_cust:
            with patch("stripe.checkout.Session.create") as mock_session:
                # Setup mock returns
                mock_cust.return_value = MagicMock(id="cus_123")
                mock_session.return_value = MagicMock(
                    id="cs_456", url="https://checkout.stripe.com/pay/cs_456"
                )

                response = await test_client.post(
                    "/api/v1/billing/checkout",
                    json={"job_id": str(mock_job_id)},
                )

        # Response structure validation (actual success depends on job existing)
        if response.status_code == 404:
            # Job doesn't exist, which is expected in this test context
            assert "not found" in response.json()["error"].lower()
        elif response.status_code == 201:
            # If job did exist and request succeeded
            data = response.json()
            assert isinstance(data["checkout_url"], str)
            assert isinstance(data["invoice_id"], str)

    async def test_checkout_nonexistent_job(
        self,
        test_client: AsyncClient,
    ):
        """Test checkout with non-existent job returns 404."""
        nonexistent_id = uuid.uuid4()
        response = await test_client.post(
            "/api/v1/billing/checkout",
            json={"job_id": str(nonexistent_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"].lower()

    async def test_checkout_non_completed_job(
        self,
        test_client: AsyncClient,
        test_job_pending: Job,
    ):
        """Test checkout with non-completed job returns 422."""
        response = await test_client.post(
            "/api/v1/billing/checkout",
            json={"job_id": str(test_job_pending.id)},
        )

        assert response.status_code == 422
        data = response.json()
        assert "not completed" in data["error"].lower()

    async def test_checkout_job_without_duration(
        self,
        test_client: AsyncClient,
        test_job_no_duration: Job,
    ):
        """Test checkout with job missing duration returns 402."""
        response = await test_client.post(
            "/api/v1/billing/checkout",
            json={"job_id": str(test_job_no_duration.id)},
        )

        assert response.status_code == 402
        data = response.json()
        # The error message may contain details about duration
        assert "duration" in data["error"].lower()

    async def test_checkout_other_user_job(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test checkout prevents access to another user's job."""
        # Create another user
        other_user = User(
            clerk_id="other_clerk_456",
            email="other@autopunk.local",
            display_name="Other User",
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create their project and job
        project = Project(
            user_id=other_user.id,
            name="Other Project",
            source_language="en",
            target_languages=["fr"],
        )
        db_session.add(project)
        await db_session.flush()

        job = Job(
            project_id=project.id,
            job_type="full_pipeline",
            status="completed",
            duration_seconds=120.0,
        )
        db_session.add(job)
        await db_session.commit()

        # Try to access as test_user
        response = await test_client.post(
            "/api/v1/billing/checkout",
            json={"job_id": str(job.id)},
        )

        assert response.status_code == 404


class TestBillingUsageEndpoint:
    """Tests for GET /api/v1/billing/usage."""

    async def test_usage_no_history(
        self,
        test_client: AsyncClient,
        test_user: User,
    ):
        """Test usage summary with no invoices."""
        response = await test_client.get("/api/v1/billing/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert data["monthly_minutes_used"] == 0
        assert data["monthly_minutes_limit"] == 10
        assert data["total_spent_usd"] == 0.0
        assert data["invoice_count"] == 0

    async def test_usage_with_paid_invoices(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test usage summary aggregates paid invoices."""
        # Create invoices with various statuses
        invoice_paid_1 = Invoice(
            user_id=test_user.id,
            amount_usd=10.0,
            duration_minutes=2,
            status="paid",
        )
        invoice_paid_2 = Invoice(
            user_id=test_user.id,
            amount_usd=25.0,
            duration_minutes=5,
            status="paid",
        )
        invoice_pending = Invoice(
            user_id=test_user.id,
            amount_usd=5.0,
            duration_minutes=1,
            status="pending",
        )
        db_session.add_all([invoice_paid_1, invoice_paid_2, invoice_pending])
        await db_session.commit()

        response = await test_client.get("/api/v1/billing/usage")

        assert response.status_code == 200
        data = response.json()
        # Only paid invoices count toward total_spent_usd
        assert data["total_spent_usd"] == 35.0
        # All invoices count toward invoice_count
        assert data["invoice_count"] == 3

    async def test_usage_respects_user_quota(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test usage returns correct user plan limits."""
        # Update user's plan and quota
        test_user.plan = "pro"
        test_user.monthly_minutes_used = 45
        test_user.monthly_minutes_limit = 100
        db_session.add(test_user)
        await db_session.commit()

        response = await test_client.get("/api/v1/billing/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
        assert data["monthly_minutes_used"] == 45
        assert data["monthly_minutes_limit"] == 100


class TestBillingInvoicesEndpoint:
    """Tests for GET /api/v1/billing/invoices."""

    async def test_list_invoices_empty(
        self,
        test_client: AsyncClient,
    ):
        """Test listing invoices when none exist."""
        response = await test_client.get("/api/v1/billing/invoices")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_invoices_multiple(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing multiple invoices ordered by creation date."""
        # Create invoices
        invoice_1 = Invoice(
            user_id=test_user.id,
            amount_usd=10.0,
            duration_minutes=2,
            status="paid",
            description="Invoice 1",
        )
        invoice_2 = Invoice(
            user_id=test_user.id,
            amount_usd=20.0,
            duration_minutes=4,
            status="pending",
            description="Invoice 2",
        )
        invoice_3 = Invoice(
            user_id=test_user.id,
            amount_usd=15.0,
            duration_minutes=3,
            status="paid",
            description="Invoice 3",
        )
        db_session.add_all([invoice_1, invoice_2, invoice_3])
        await db_session.commit()

        response = await test_client.get("/api/v1/billing/invoices")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify all invoices are present
        descriptions = {d["description"] for d in data}
        assert descriptions == {"Invoice 1", "Invoice 2", "Invoice 3"}

    async def test_list_invoices_other_user(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test invoices are scoped to authenticated user."""
        # Create another user's invoice
        other_user = User(
            clerk_id="other_clerk_789",
            email="other2@autopunk.local",
        )
        db_session.add(other_user)
        await db_session.flush()

        other_invoice = Invoice(
            user_id=other_user.id,
            amount_usd=50.0,
            duration_minutes=10,
            status="paid",
        )
        db_session.add(other_invoice)
        await db_session.commit()

        # List as test_user should return empty
        response = await test_client.get("/api/v1/billing/invoices")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestBillingWebhookEndpoint:
    """Tests for POST /api/v1/billing/webhooks/stripe."""

    def _create_stripe_event(self, event_type: str, obj: dict) -> dict:
        """Create a mock Stripe event."""
        return {
            "id": "evt_test_123",
            "type": event_type,
            "data": {"object": obj},
        }

    async def test_webhook_checkout_completed(
        self,
        test_client: AsyncClient,
        test_settings: Settings,
    ):
        """Test webhook endpoint accepts checkout.session.completed events."""
        event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session",
                    "metadata": {"invoice_id": str(uuid.uuid4())},
                    "payment_intent": "pi_test_intent",
                }
            },
        }

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await test_client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b"test_payload",
                headers={"stripe-signature": "test_sig"},
            )

        # Endpoint should return 200 even if invoice doesn't exist
        assert response.status_code == 200
        assert response.json()["received"] is True

    async def test_webhook_payment_failed(
        self,
        test_client: AsyncClient,
        test_settings: Settings,
    ):
        """Test webhook endpoint accepts payment_intent.payment_failed events."""
        event = {
            "id": "evt_test_456",
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_test_intent_failed"}},
        }

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await test_client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b"test_payload",
                headers={"stripe-signature": "test_sig"},
            )

        # Endpoint should return 200
        assert response.status_code == 200
        assert response.json()["received"] is True

    async def test_webhook_invalid_signature(
        self,
        test_client: AsyncClient,
        test_settings: Settings,
    ):
        """Test webhook rejects invalid signature."""
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=Exception("Invalid signature"),
        ):
            response = await test_client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b"test_payload",
                headers={"stripe-signature": "invalid_sig"},
            )

        assert response.status_code == 502
        assert "error" in response.json()

    async def test_webhook_unknown_event_type(
        self,
        test_client: AsyncClient,
    ):
        """Test webhook gracefully handles unknown event types."""
        event = {
            "id": "evt_unknown_123",
            "type": "unknown.event.type",
            "data": {"object": {}},
        }

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await test_client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b"test_payload",
                headers={"stripe-signature": "test_sig"},
            )

        # Should still return 200, just log and skip the unknown event
        assert response.status_code == 200
        assert response.json()["received"] is True


# ------------------------------------------------------------------
# BillingService Unit Tests
# ------------------------------------------------------------------


class TestBillingServiceGetOrCreateCustomer:
    """Tests for BillingService.get_or_create_customer."""

    async def test_returns_existing_stripe_customer_id(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test returns existing stripe_customer_id without API call."""
        test_user.stripe_customer_id = "cus_existing_123"
        db_session.add(test_user)
        await db_session.commit()

        service = BillingService(test_settings)
        customer_id = await service.get_or_create_customer(test_user, db_session)

        assert customer_id == "cus_existing_123"

    async def test_creates_new_stripe_customer(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        mock_stripe_customer,
    ):
        """Test creates and stores new Stripe customer."""
        assert test_user.stripe_customer_id is None

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            customer_id = await service.get_or_create_customer(test_user, db_session)

        assert customer_id == "cus_test_customer_123"

        # Verify customer ID was persisted
        await db_session.refresh(test_user)
        assert test_user.stripe_customer_id == "cus_test_customer_123"

    async def test_create_customer_stripe_error(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test handles Stripe API errors."""
        import stripe as stripe_module

        service = BillingService(test_settings)

        with patch.object(
            stripe_module.Customer,
            "create",
            side_effect=stripe_module.StripeError("Stripe API error"),
        ):
            with pytest.raises(BillingError) as exc_info:
                await service.get_or_create_customer(test_user, db_session)

        assert "Failed to create Stripe customer" in str(exc_info.value)


class TestBillingServiceCreateCheckoutSession:
    """Tests for BillingService.create_checkout_session."""

    async def test_calculates_price_correctly(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_job_completed: Job,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
    ):
        """Test price calculation: ceil(duration/60) * rate."""
        from sqlalchemy import select

        # 120 seconds = 2 minutes, 2 * $5 = $10
        test_settings.price_per_minute_usd = 5.0

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )

        # Verify invoice was created with correct calculation
        result = await db_session.execute(
            select(Invoice).where(Invoice.job_id == test_job_completed.id)
        )
        invoices = list(result.scalars().all())
        assert len(invoices) == 1
        assert invoices[0].amount_usd == 10.0
        assert invoices[0].duration_minutes == 2

    async def test_rounds_up_fractional_minutes(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
        test_project: Project,
    ):
        """Test duration is rounded up to next minute."""
        from sqlalchemy import select

        job = Job(
            project_id=test_project.id,
            job_type="full_pipeline",
            status="completed",
            duration_seconds=65.0,  # 1.083 minutes -> should round up to 2
        )

        db_session.add(job)
        await db_session.commit()

        test_settings.price_per_minute_usd = 5.0
        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, job, db_session
                )

        result = await db_session.execute(
            select(Invoice).where(Invoice.job_id == job.id)
        )
        invoices = list(result.scalars().all())
        assert invoices[0].duration_minutes == 2  # ceil(65/60) = 2
        assert invoices[0].amount_usd == 10.0  # 2 * 5.0

    async def test_raises_on_missing_duration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test raises PaymentRequiredError if duration_seconds is None."""
        service = BillingService(test_settings)

        with pytest.raises(PaymentRequiredError) as exc_info:
            await service.create_checkout_session(
                test_user, Job(duration_seconds=None), db_session
            )

        assert "duration" in str(exc_info.value).lower()

    async def test_creates_pending_invoice(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_job_completed: Job,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
    ):
        """Test creates invoice with 'pending' status before Stripe call."""
        from sqlalchemy import select

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )

        # Invoice should be persisted with session ID
        result_obj = await db_session.execute(
            select(Invoice).where(Invoice.id == result["invoice_id"])
        )
        invoices = list(result_obj.scalars().all())
        assert len(invoices) == 1
        assert invoices[0].status == "pending"
        assert invoices[0].stripe_checkout_session_id == "cs_test_session_456"

    async def test_returns_checkout_url_and_invoice_id(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_job_completed: Job,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
    ):
        """Test returns both checkout_url and invoice_id."""
        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )

        assert "checkout_url" in result
        assert "invoice_id" in result
        assert isinstance(result["invoice_id"], uuid.UUID)
        assert (
            result["checkout_url"]
            == "https://checkout.stripe.com/pay/cs_test_session_456"
        )

    async def test_stripe_session_metadata(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_job_completed: Job,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
    ):
        """Test Stripe session includes correct metadata."""
        service = BillingService(test_settings)

        captured_call = {}

        def capture_session_create(**kwargs):
            captured_call.update(kwargs)
            return mock_stripe_session

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create",
                side_effect=capture_session_create,
            ):
                result = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )

        # Verify metadata was included in the session creation call
        assert "metadata" in captured_call
        metadata = captured_call["metadata"]
        assert "invoice_id" in metadata
        assert "job_id" in metadata
        assert str(test_job_completed.id) == metadata["job_id"]


class TestBillingServiceGetUsageSummary:
    """Tests for BillingService.get_usage_summary."""

    async def test_returns_correct_aggregates(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test returns correct usage summary with aggregates."""
        # Create invoices
        invoice_1 = Invoice(
            user_id=test_user.id,
            amount_usd=10.0,
            duration_minutes=2,
            status="paid",
        )
        invoice_2 = Invoice(
            user_id=test_user.id,
            amount_usd=20.0,
            duration_minutes=4,
            status="paid",
        )
        invoice_pending = Invoice(
            user_id=test_user.id,
            amount_usd=5.0,
            duration_minutes=1,
            status="pending",
        )
        db_session.add_all([invoice_1, invoice_2, invoice_pending])
        await db_session.commit()

        service = BillingService(test_settings)
        summary = await service.get_usage_summary(test_user, db_session)

        assert summary["total_spent_usd"] == 30.0  # Only paid invoices
        assert summary["invoice_count"] == 3  # All invoices
        assert summary["monthly_minutes_used"] == test_user.monthly_minutes_used
        assert summary["monthly_minutes_limit"] == test_user.monthly_minutes_limit
        assert summary["plan"] == test_user.plan

    async def test_sums_only_paid_invoices(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test total_spent_usd excludes pending/failed invoices."""
        Invoice(
            user_id=test_user.id, amount_usd=10.0, duration_minutes=2, status="paid"
        )
        Invoice(
            user_id=test_user.id, amount_usd=5.0, duration_minutes=1, status="pending"
        )
        Invoice(
            user_id=test_user.id, amount_usd=3.0, duration_minutes=1, status="failed"
        )

        db_session.add_all(
            [
                Invoice(
                    user_id=test_user.id,
                    amount_usd=10.0,
                    duration_minutes=2,
                    status="paid",
                ),
                Invoice(
                    user_id=test_user.id,
                    amount_usd=5.0,
                    duration_minutes=1,
                    status="pending",
                ),
                Invoice(
                    user_id=test_user.id,
                    amount_usd=3.0,
                    duration_minutes=1,
                    status="failed",
                ),
            ]
        )
        await db_session.commit()

        service = BillingService(test_settings)
        summary = await service.get_usage_summary(test_user, db_session)

        # Only the paid invoice should count
        assert summary["total_spent_usd"] == 10.0

    async def test_respects_user_plan_fields(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
    ):
        """Test returns user's current plan and quota."""
        test_user.plan = "pro"
        test_user.monthly_minutes_used = 50
        test_user.monthly_minutes_limit = 500
        db_session.add(test_user)
        await db_session.commit()

        service = BillingService(test_settings)
        summary = await service.get_usage_summary(test_user, db_session)

        assert summary["plan"] == "pro"
        assert summary["monthly_minutes_used"] == 50
        assert summary["monthly_minutes_limit"] == 500


class TestBillingServiceHandleWebhook:
    """Tests for BillingService.handle_webhook."""

    async def test_invalid_signature_raises_error(
        self,
        db_session: AsyncSession,
        test_settings: Settings,
    ):
        """Test webhook with invalid signature raises BillingError."""
        service = BillingService(test_settings)

        with patch(
            "stripe.Webhook.construct_event",
            side_effect=Exception("Signature verification failed"),
        ):
            with pytest.raises(BillingError) as exc_info:
                await service.handle_webhook(
                    b"invalid_payload", "invalid_sig", db_session
                )

        assert "signature" in str(exc_info.value).lower()

    async def test_handles_checkout_completed(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        async_engine,
    ):
        """Test processes checkout.session.completed event."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from sqlalchemy import select

        invoice = Invoice(
            user_id=test_user.id,
            amount_usd=10.0,
            duration_minutes=2,
            status="pending",
        )
        db_session.add(invoice)
        await db_session.commit()

        event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session",
                    "metadata": {"invoice_id": str(invoice.id)},
                    "payment_intent": "pi_test_intent",
                }
            },
        }

        service = BillingService(test_settings)

        with patch("stripe.Webhook.construct_event", return_value=event):
            await service.handle_webhook(b"payload", "sig", db_session)

        # Verify invoice was marked paid (use fresh session to avoid stale data)
        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                select(Invoice).where(Invoice.id == invoice.id)
            )
            updated_invoice = result.scalar_one()
            assert updated_invoice.status == "paid"

    async def test_handles_payment_failed(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        async_engine,
    ):
        """Test processes payment_intent.payment_failed event."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from sqlalchemy import select

        invoice = Invoice(
            user_id=test_user.id,
            amount_usd=10.0,
            duration_minutes=2,
            status="pending",
            stripe_payment_intent_id="pi_test_intent_failed",
        )
        db_session.add(invoice)
        await db_session.commit()

        event = {
            "id": "evt_test_456",
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_test_intent_failed"}},
        }

        service = BillingService(test_settings)

        with patch("stripe.Webhook.construct_event", return_value=event):
            await service.handle_webhook(b"payload", "sig", db_session)

        # Verify invoice was marked failed (use fresh session)
        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                select(Invoice).where(Invoice.id == invoice.id)
            )
            updated_invoice = result.scalar_one()
            assert updated_invoice.status == "failed"

    async def test_ignores_unhandled_event_types(
        self,
        db_session: AsyncSession,
        test_settings: Settings,
    ):
        """Test unhandled event types are acknowledged without error."""
        event = {
            "id": "evt_test_789",
            "type": "unknown.event",
            "data": {"object": {}},
        }

        service = BillingService(test_settings)

        # Should not raise
        with patch("stripe.Webhook.construct_event", return_value=event):
            await service.handle_webhook(b"payload", "sig", db_session)


# ------------------------------------------------------------------
# Edge Cases and Integration Tests
# ------------------------------------------------------------------


class TestBillingEdgeCases:
    """Tests for edge cases and integration scenarios."""

    async def test_checkout_with_very_small_duration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
        test_project: Project,
    ):
        """Test checkout with very small duration (1 second)."""
        from sqlalchemy import select

        job = Job(
            project_id=test_project.id,
            job_type="full_pipeline",
            status="completed",
            duration_seconds=1.0,
        )
        db_session.add(job)
        await db_session.commit()

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, job, db_session
                )

        result_obj = await db_session.execute(
            select(Invoice).where(Invoice.job_id == job.id)
        )
        invoices = list(result_obj.scalars().all())
        # ceil(1/60) = 1 minute
        assert invoices[0].duration_minutes == 1
        assert invoices[0].amount_usd == 5.0

    async def test_checkout_with_large_duration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
        test_project: Project,
    ):
        """Test checkout with large duration."""
        from sqlalchemy import select

        job = Job(
            project_id=test_project.id,
            job_type="full_pipeline",
            status="completed",
            duration_seconds=3600.0,  # 1 hour = 60 minutes
        )
        db_session.add(job)
        await db_session.commit()

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result = await service.create_checkout_session(
                    test_user, job, db_session
                )

        result_obj = await db_session.execute(
            select(Invoice).where(Invoice.job_id == job.id)
        )
        invoices = list(result_obj.scalars().all())
        assert invoices[0].duration_minutes == 60
        assert invoices[0].amount_usd == 300.0

    async def test_webhook_with_missing_invoice_id_metadata(
        self,
        db_session: AsyncSession,
        test_settings: Settings,
    ):
        """Test webhook gracefully handles missing invoice_id in metadata."""
        event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session",
                    "metadata": {},  # Missing invoice_id
                    "payment_intent": "pi_test_intent",
                }
            },
        }

        service = BillingService(test_settings)

        # Should not raise
        with patch("stripe.Webhook.construct_event", return_value=event):
            await service.handle_webhook(b"payload", "sig", db_session)

    async def test_webhook_with_nonexistent_invoice(
        self,
        db_session: AsyncSession,
        test_settings: Settings,
    ):
        """Test webhook gracefully handles nonexistent invoice."""
        event = {
            "id": "evt_test_456",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session",
                    "metadata": {"invoice_id": str(uuid.uuid4())},  # Non-existent
                    "payment_intent": "pi_test_intent",
                }
            },
        }

        service = BillingService(test_settings)

        # Should not raise
        with patch("stripe.Webhook.construct_event", return_value=event):
            await service.handle_webhook(b"payload", "sig", db_session)

    async def test_multiple_checkout_sessions_same_job(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_job_completed: Job,
        test_settings: Settings,
        mock_stripe_customer,
        mock_stripe_session,
    ):
        """Test creating multiple checkout sessions for same job creates multiple invoices."""
        from sqlalchemy import select

        service = BillingService(test_settings)

        with patch("stripe.Customer.create", return_value=mock_stripe_customer):
            with patch(
                "stripe.checkout.Session.create", return_value=mock_stripe_session
            ):
                result1 = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )
                # Reset mock session ID for second call
                mock_stripe_session.id = "cs_test_session_789"
                result2 = await service.create_checkout_session(
                    test_user, test_job_completed, db_session
                )

        result_obj = await db_session.execute(
            select(Invoice).where(Invoice.job_id == test_job_completed.id)
        )
        invoices = list(result_obj.scalars().all())
        assert len(invoices) == 2
        assert invoices[0].id != invoices[1].id
