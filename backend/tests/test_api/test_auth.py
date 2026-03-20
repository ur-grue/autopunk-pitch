"""Tests for authentication and authorization."""

from unittest.mock import patch

import pytest

from app.config import Settings


class TestAuthRequired:
    """Test that endpoints require authentication."""

    async def test_projects_requires_auth(self, unauthenticated_client):
        """POST /projects returns 401 without auth when Clerk is configured."""
        mock_settings = Settings(clerk_secret_key="sk_test_fake_key_12345")
        with patch("app.auth.get_settings", return_value=mock_settings):
            response = await unauthenticated_client.post(
                "/api/v1/projects",
                json={
                    "name": "Test",
                    "source_language": "en",
                    "target_languages": ["fr"],
                },
            )
        assert response.status_code == 401

    async def test_get_projects_requires_auth(self, unauthenticated_client):
        """GET /projects returns 401 without auth when Clerk is configured."""
        mock_settings = Settings(clerk_secret_key="sk_test_fake_key_12345")
        with patch("app.auth.get_settings", return_value=mock_settings):
            response = await unauthenticated_client.get("/api/v1/projects")
        assert response.status_code == 401

    async def test_health_no_auth(self, unauthenticated_client):
        """GET /health does not require auth."""
        response = await unauthenticated_client.get("/health")
        assert response.status_code == 200


class TestDevMode:
    """Test dev mode fallback when Clerk is not configured."""

    async def test_dev_mode_creates_user(self, unauthenticated_client):
        """Without Clerk key, endpoints create a dev user automatically."""
        mock_settings = Settings(clerk_secret_key="")
        with patch("app.auth.get_settings", return_value=mock_settings):
            response = await unauthenticated_client.post(
                "/api/v1/projects",
                json={
                    "name": "Dev Project",
                    "source_language": "en",
                    "target_languages": ["fr"],
                },
            )
        assert response.status_code == 201
        assert response.json()["name"] == "Dev Project"


class TestListProjects:
    """Test GET /projects list endpoint."""

    async def test_list_projects_empty(self, test_client):
        """New user has no projects."""
        response = await test_client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_projects_returns_created(self, test_client):
        """Created projects appear in the list."""
        await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Project A",
                "source_language": "en",
                "target_languages": ["fr"],
            },
        )
        await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Project B",
                "source_language": "en",
                "target_languages": ["de"],
            },
        )

        response = await test_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {p["name"] for p in data}
        assert names == {"Project A", "Project B"}


class TestQuotaEnforcement:
    """Test quota checking on job submission endpoints."""

    async def test_quota_exceeded_returns_429(self, test_client, test_user, db_session):
        """User at quota limit cannot submit new jobs."""
        # Set user to quota limit
        test_user.monthly_minutes_used = 10
        test_user.monthly_minutes_limit = 10
        await db_session.commit()

        # Create a project first
        create_resp = await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Quota Test",
                "source_language": "en",
                "target_languages": ["fr"],
            },
        )
        project_id = create_resp.json()["id"]

        # Try to submit a job — should be rejected
        response = await test_client.post(
            f"/api/v1/projects/{project_id}/jobs/transcribe",
            files={"file": ("test.mp4", b"fake video content", "video/mp4")},
        )
        assert response.status_code == 429
        assert "quota" in response.json()["error"].lower()
