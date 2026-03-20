"""Tests for subtitle editor API endpoints."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.project import Project
from app.models.subtitle import Subtitle


async def _create_project_and_job(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[Project, Job]:
    """Helper to create a project with a completed job."""
    project = Project(
        user_id=user_id,
        name="Test Project",
        source_language="en",
        target_languages=["fr"],
    )
    db.add(project)
    await db.flush()

    job = Job(
        project_id=project.id,
        job_type="full_pipeline",
        status="completed",
    )
    db.add(job)
    await db.flush()
    return project, job


async def _create_subtitles(
    db: AsyncSession, job_id: uuid.UUID, count: int = 3, language: str = "en"
) -> list[Subtitle]:
    """Helper to create test subtitle cues."""
    subs = []
    for i in range(1, count + 1):
        sub = Subtitle(
            job_id=job_id,
            index=i,
            start_ms=(i - 1) * 3000,
            end_ms=i * 3000,
            text=f"Subtitle line {i}",
            language=language,
            confidence=0.9 if i % 2 == 0 else -1.5,
            flags=["low_confidence"] if i == 1 else None,
        )
        db.add(sub)
        subs.append(sub)
    await db.commit()
    for s in subs:
        await db.refresh(s)
    return subs


class TestListSubtitles:
    """Tests for GET /jobs/{job_id}/subtitles/{language}."""

    async def test_list_subtitles_success(self, test_client, test_user, db_session):
        """Returns subtitles ordered by index."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.get(
            f"/api/v1/jobs/{job.id}/subtitles/en"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["language"] == "en"
        assert len(data["subtitles"]) == 3
        assert data["subtitles"][0]["index"] == 1
        assert data["subtitles"][2]["index"] == 3

    async def test_list_subtitles_filters_by_language(
        self, test_client, test_user, db_session
    ):
        """Only returns subtitles for the requested language."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        await _create_subtitles(db_session, job.id, count=3, language="en")
        await _create_subtitles(db_session, job.id, count=2, language="fr")

        response = await test_client.get(
            f"/api/v1/jobs/{job.id}/subtitles/fr"
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2

    async def test_list_subtitles_job_not_found(self, test_client):
        """Returns 404 for non-existent job."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.get(
            f"/api/v1/jobs/{fake_id}/subtitles/en"
        )
        assert response.status_code == 404


class TestUpdateSubtitle:
    """Tests for PUT /subtitles/{subtitle_id}."""

    async def test_update_text(self, test_client, test_user, db_session):
        """Can update subtitle text."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.put(
            f"/api/v1/subtitles/{subs[0].id}",
            json={"text": "Updated text"},
        )
        assert response.status_code == 200
        assert response.json()["text"] == "Updated text"

    async def test_update_timing(self, test_client, test_user, db_session):
        """Can update subtitle timing."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.put(
            f"/api/v1/subtitles/{subs[0].id}",
            json={"start_ms": 100, "end_ms": 2500},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_ms"] == 100
        assert data["end_ms"] == 2500

    async def test_update_invalid_timing(self, test_client, test_user, db_session):
        """Rejects start_ms >= end_ms."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.put(
            f"/api/v1/subtitles/{subs[0].id}",
            json={"start_ms": 5000, "end_ms": 3000},
        )
        assert response.status_code == 422

    async def test_update_not_found(self, test_client):
        """Returns 404 for non-existent subtitle."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.put(
            f"/api/v1/subtitles/{fake_id}",
            json={"text": "nope"},
        )
        assert response.status_code == 404


class TestBatchUpdate:
    """Tests for PUT /jobs/{job_id}/subtitles/batch."""

    async def test_batch_update_success(self, test_client, test_user, db_session):
        """Can batch-update multiple subtitles."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.put(
            f"/api/v1/jobs/{job.id}/subtitles/batch",
            json={
                "updates": [
                    {"id": str(subs[0].id), "text": "First updated"},
                    {"id": str(subs[1].id), "text": "Second updated"},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        texts = {s["text"] for s in data}
        assert texts == {"First updated", "Second updated"}


class TestSplitSubtitle:
    """Tests for POST /subtitles/{subtitle_id}/split."""

    async def test_split_success(self, test_client, test_user, db_session):
        """Splits a subtitle into two."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.post(
            f"/api/v1/subtitles/{subs[0].id}/split",
            json={
                "split_at_ms": 1500,
                "first_text": "First half",
                "second_text": "Second half",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2
        assert data[0]["text"] == "First half"
        assert data[0]["end_ms"] == 1500
        assert data[1]["text"] == "Second half"
        assert data[1]["start_ms"] == 1500

    async def test_split_invalid_timecode(self, test_client, test_user, db_session):
        """Rejects split_at_ms outside subtitle range."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.post(
            f"/api/v1/subtitles/{subs[0].id}/split",
            json={
                "split_at_ms": 5000,
                "first_text": "A",
                "second_text": "B",
            },
        )
        assert response.status_code == 422


class TestMergeSubtitle:
    """Tests for POST /subtitles/{subtitle_id}/merge."""

    async def test_merge_success(self, test_client, test_user, db_session):
        """Merges subtitle with the next one."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.post(
            f"/api/v1/subtitles/{subs[0].id}/merge",
        )
        assert response.status_code == 200
        data = response.json()
        assert "Subtitle line 1" in data["text"]
        assert "Subtitle line 2" in data["text"]
        assert data["end_ms"] == subs[1].end_ms

    async def test_merge_last_subtitle_fails(
        self, test_client, test_user, db_session
    ):
        """Cannot merge the last subtitle (no next)."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        subs = await _create_subtitles(db_session, job.id)

        response = await test_client.post(
            f"/api/v1/subtitles/{subs[2].id}/merge",
        )
        assert response.status_code == 422


class TestFlaggedSubtitles:
    """Tests for flagged segment support."""

    async def test_flags_in_response(self, test_client, test_user, db_session):
        """Flags are included in subtitle list response."""
        project, job = await _create_project_and_job(db_session, test_user.id)
        await _create_subtitles(db_session, job.id)

        response = await test_client.get(
            f"/api/v1/jobs/{job.id}/subtitles/en"
        )
        assert response.status_code == 200
        subs = response.json()["subtitles"]
        # First subtitle has low_confidence flag
        assert subs[0]["flags"] == ["low_confidence"]
        # Others have no flags
        assert subs[1]["flags"] is None
