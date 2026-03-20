"""Tests for project API endpoints."""

import pytest


class TestCreateProject:
    """Tests for POST /api/v1/projects."""

    async def test_create_project_success(self, test_client):
        """Valid request creates a project and returns 201."""
        response = await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test Documentary",
                "source_language": "en",
                "target_languages": ["fr", "es", "de"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Documentary"
        assert data["source_language"] == "en"
        assert data["target_languages"] == ["fr", "es", "de"]
        assert data["status"] == "created"
        assert "id" in data

    async def test_create_project_missing_name(self, test_client):
        """Missing required field returns 422."""
        response = await test_client.post(
            "/api/v1/projects",
            json={
                "source_language": "en",
                "target_languages": ["fr"],
            },
        )

        assert response.status_code == 422

    async def test_create_project_empty_target_languages(self, test_client):
        """Empty target_languages list returns 422."""
        response = await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "source_language": "en",
                "target_languages": [],
            },
        )

        assert response.status_code == 422


class TestGetProject:
    """Tests for GET /api/v1/projects/{project_id}."""

    async def test_get_project_success(self, test_client):
        """Existing project returns 200 with jobs list."""
        # Create project first
        create_resp = await test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "source_language": "en",
                "target_languages": ["fr"],
            },
        )
        project_id = create_resp.json()["id"]

        response = await test_client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"
        assert data["jobs"] == []

    async def test_get_project_not_found(self, test_client):
        """Non-existent project returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.get(f"/api/v1/projects/{fake_id}")

        assert response.status_code == 404


class TestHealthCheck:
    """Tests for GET /health."""

    async def test_health_check(self, test_client):
        """Health endpoint returns 200 with status ok."""
        response = await test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
