"""Tests for platform profile API endpoints and models."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.formats.validators import SubtitleCue, validate_subtitles
from app.models.platform_profile import PlatformProfile


# Example profile data for seeding tests
NETFLIX_PROFILE = {
    "name": "netflix",
    "display_name": "Netflix",
    "description": "Netflix Timed Text Style Guide",
    "max_chars_per_line": 42,
    "max_lines_per_cue": 2,
    "max_cps": 20.0,
    "min_duration_ms": 833,
    "min_gap_ms": 2,
    "settings": {
        "forced_narrative": True,
        "italic_for_foreign": True,
        "max_duration_ms": 7000,
    },
}

BBC_PROFILE = {
    "name": "bbc",
    "display_name": "BBC",
    "description": "BBC Subtitle Guidelines",
    "max_chars_per_line": 37,
    "max_lines_per_cue": 2,
    "max_cps": 18.0,
    "min_duration_ms": 1000,
    "min_gap_ms": 0,
    "settings": {
        "phonetic_allowed": False,
        "max_duration_ms": 7000,
    },
}

YOUTUBE_PROFILE = {
    "name": "youtube",
    "display_name": "YouTube",
    "description": "YouTube Subtitles Guidelines",
    "max_chars_per_line": 42,
    "max_lines_per_cue": 3,
    "max_cps": 25.0,
    "min_duration_ms": 500,
    "min_gap_ms": 0,
    "settings": {"supports_html": True},
}


class TestListPlatformProfiles:
    """Tests for GET /api/v1/platform-profiles."""

    async def test_list_profiles_empty(self, test_client):
        """Empty database returns empty list."""
        response = await test_client.get("/api/v1/platform-profiles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_profiles_with_data(self, test_client, async_engine):
        """Seeded profiles are returned in sorted order by name."""
        # Insert profiles into the test database
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profiles = [
                PlatformProfile(**NETFLIX_PROFILE),
                PlatformProfile(**BBC_PROFILE),
                PlatformProfile(**YOUTUBE_PROFILE),
            ]
            for profile in profiles:
                session.add(profile)
            await session.commit()

        # Now test the endpoint
        response = await test_client.get("/api/v1/platform-profiles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify sorted by name
        names = [p["name"] for p in data]
        assert names == ["bbc", "netflix", "youtube"]

    async def test_list_profiles_fields_present(self, test_client, async_engine):
        """Each profile contains all expected fields."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(**NETFLIX_PROFILE)
            session.add(profile)
            await session.commit()

        response = await test_client.get("/api/v1/platform-profiles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        profile_data = data[0]

        # Check all required fields are present
        assert "id" in profile_data
        assert "name" in profile_data
        assert "display_name" in profile_data
        assert "description" in profile_data
        assert "max_chars_per_line" in profile_data
        assert "max_lines_per_cue" in profile_data
        assert "max_cps" in profile_data
        assert "min_duration_ms" in profile_data
        assert "min_gap_ms" in profile_data
        assert "settings" in profile_data

        # Check values match inserted data
        assert profile_data["name"] == "netflix"
        assert profile_data["display_name"] == "Netflix"
        assert profile_data["max_chars_per_line"] == 42
        assert profile_data["max_cps"] == 20.0


class TestGetPlatformProfile:
    """Tests for GET /api/v1/platform-profiles/{profile_id}."""

    async def test_get_profile_success(self, test_client, async_engine):
        """Valid UUID returns the profile."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(**NETFLIX_PROFILE)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            profile_id = profile.id

        response = await test_client.get(f"/api/v1/platform-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(profile_id)
        assert data["name"] == "netflix"
        assert data["display_name"] == "Netflix"
        assert data["max_chars_per_line"] == 42
        assert data["max_cps"] == 20.0
        assert data["min_duration_ms"] == 833

    async def test_get_profile_not_found(self, test_client):
        """Non-existent UUID returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await test_client.get(f"/api/v1/platform-profiles/{fake_id}")

        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

    async def test_get_profile_invalid_uuid(self, test_client):
        """Invalid UUID format returns 422."""
        response = await test_client.get("/api/v1/platform-profiles/not-a-uuid")

        assert response.status_code == 422


class TestPlatformProfileCreation:
    """Tests for PlatformProfile model creation and validation."""

    async def test_platform_profile_creation_all_fields(self, db_session):
        """Create a PlatformProfile with all fields specified."""
        profile = PlatformProfile(**NETFLIX_PROFILE)
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert isinstance(profile.id, uuid.UUID)
        assert profile.name == "netflix"
        assert profile.display_name == "Netflix"
        assert profile.description == "Netflix Timed Text Style Guide"
        assert profile.max_chars_per_line == 42
        assert profile.max_lines_per_cue == 2
        assert profile.max_cps == 20.0
        assert profile.min_duration_ms == 833
        assert profile.min_gap_ms == 2
        assert profile.settings == {
            "forced_narrative": True,
            "italic_for_foreign": True,
            "max_duration_ms": 7000,
        }
        assert profile.created_at is not None
        assert profile.updated_at is not None

    async def test_platform_profile_defaults(self, db_session):
        """Verify server defaults for PlatformProfile."""
        # Create profile with only required fields (name, display_name)
        profile = PlatformProfile(
            name="default_profile",
            display_name="Default Profile",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Verify defaults
        assert profile.max_chars_per_line == 42
        assert profile.max_lines_per_cue == 2
        assert profile.max_cps == 25.0
        assert profile.min_duration_ms == 1000
        assert profile.min_gap_ms == 0
        assert profile.description is None
        assert profile.settings is None

    async def test_platform_profile_unique_name_constraint(
        self, db_session
    ):
        """Duplicate profile name raises IntegrityError."""
        profile1 = PlatformProfile(**NETFLIX_PROFILE)
        db_session.add(profile1)
        await db_session.commit()

        # Try to insert another profile with the same name
        profile2 = PlatformProfile(
            name="netflix",  # Same name as profile1
            display_name="Netflix Copy",
        )
        db_session.add(profile2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_platform_profile_optional_fields(self, db_session):
        """Create profile with optional fields as None."""
        profile = PlatformProfile(
            name="minimal",
            display_name="Minimal Profile",
            description=None,
            settings=None,
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.description is None
        assert profile.settings is None
        assert profile.max_chars_per_line == 42  # Default


class TestValidateSubtitlesWithProfiles:
    """Tests for validating subtitles using platform profiles."""

    def test_validate_subtitles_with_netflix_profile(self):
        """Validate subtitles against Netflix profile rules."""
        # Netflix: max_chars=42, max_cps=20, min_duration=833ms
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="Hello, this is a subtitle.\nIt has two lines.",
            ),
            SubtitleCue(
                index=2,
                start_ms=2500,
                end_ms=4000,
                text="Another cue with valid content.",
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=NETFLIX_PROFILE["max_chars_per_line"],
            max_lines=NETFLIX_PROFILE["max_lines_per_cue"],
            max_cps=NETFLIX_PROFILE["max_cps"],
            min_duration_ms=NETFLIX_PROFILE["min_duration_ms"],
        )

        assert result.passed
        assert result.error_count == 0

    def test_validate_subtitles_exceeds_netflix_line_length(self):
        """Subtitle exceeding Netflix 42-char limit is flagged."""
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="A" * 50,  # 50 chars, exceeds Netflix's 42
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=NETFLIX_PROFILE["max_chars_per_line"],
            max_lines=NETFLIX_PROFILE["max_lines_per_cue"],
            max_cps=NETFLIX_PROFILE["max_cps"],
            min_duration_ms=NETFLIX_PROFILE["min_duration_ms"],
        )

        assert not result.passed
        assert result.error_count >= 1
        line_issues = [i for i in result.issues if i.rule == "line_length"]
        assert len(line_issues) == 1

    def test_validate_subtitles_exceeds_netflix_reading_speed(self):
        """High reading speed exceeds Netflix 20 CPS limit."""
        # 100 chars in 2 seconds = 50 CPS (exceeds Netflix's 20)
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="A" * 100,
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=NETFLIX_PROFILE["max_chars_per_line"],
            max_lines=NETFLIX_PROFILE["max_lines_per_cue"],
            max_cps=NETFLIX_PROFILE["max_cps"],
            min_duration_ms=NETFLIX_PROFILE["min_duration_ms"],
        )

        # Should have line_length error and reading_speed warning
        assert not result.passed
        assert result.error_count >= 1
        speed_issues = [i for i in result.issues if i.rule == "reading_speed"]
        assert len(speed_issues) >= 1

    def test_validate_subtitles_with_bbc_profile(self):
        """Validate subtitles against BBC profile rules."""
        # BBC: max_chars=37, max_cps=18, min_duration=1000ms
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="Hello, BBC subtitle.\nSecond line here.",
            ),
            SubtitleCue(
                index=2,
                start_ms=2500,
                end_ms=4000,
                text="Another valid BBC cue.",
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=BBC_PROFILE["max_chars_per_line"],
            max_lines=BBC_PROFILE["max_lines_per_cue"],
            max_cps=BBC_PROFILE["max_cps"],
            min_duration_ms=BBC_PROFILE["min_duration_ms"],
        )

        # First cue may have warning (second line is 21 chars, within 37 limit)
        # But "Hello, BBC subtitle." is 20 chars, and "Second line here." is 17 chars
        # So both lines are valid for BBC
        assert result.error_count == 0

    def test_validate_subtitles_exceeds_bbc_line_length(self):
        """Subtitle exceeding BBC 37-char limit is flagged."""
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="A" * 40,  # 40 chars, exceeds BBC's 37
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=BBC_PROFILE["max_chars_per_line"],
            max_lines=BBC_PROFILE["max_lines_per_cue"],
            max_cps=BBC_PROFILE["max_cps"],
            min_duration_ms=BBC_PROFILE["min_duration_ms"],
        )

        assert not result.passed
        assert result.error_count >= 1
        line_issues = [i for i in result.issues if i.rule == "line_length"]
        assert len(line_issues) == 1

    def test_validate_subtitles_bbc_reading_speed_strict(self):
        """BBC's stricter 18 CPS limit catches faster content."""
        # 60 chars in 2 seconds = 30 CPS (exceeds BBC's 18)
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="This is a test of BBC reading speed limits",  # 43 chars
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=BBC_PROFILE["max_chars_per_line"],
            max_lines=BBC_PROFILE["max_lines_per_cue"],
            max_cps=BBC_PROFILE["max_cps"],
            min_duration_ms=BBC_PROFILE["min_duration_ms"],
        )

        # Line length error (43 > 37) and speed warning (21.5 CPS > 18)
        assert result.error_count >= 1
        speed_issues = [i for i in result.issues if i.rule == "reading_speed"]
        assert len(speed_issues) >= 1

    def test_validate_subtitles_bbc_min_duration(self):
        """BBC requires minimum 1000ms duration."""
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=800,  # 800ms, below BBC's 1000ms minimum
                text="Short duration.",
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=BBC_PROFILE["max_chars_per_line"],
            max_lines=BBC_PROFILE["max_lines_per_cue"],
            max_cps=BBC_PROFILE["max_cps"],
            min_duration_ms=BBC_PROFILE["min_duration_ms"],
        )

        # BBC minimum duration is 1000ms
        duration_issues = [i for i in result.issues if i.rule == "min_duration"]
        assert len(duration_issues) == 1

    def test_validate_subtitles_youtube_more_permissive(self):
        """YouTube profile allows more lines (3) and lower minimum duration."""
        # YouTube: max_lines=3, min_duration=500ms
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=1000,
                text="Line 1\nLine 2\nLine 3",
            ),
        ]

        result = validate_subtitles(
            cues,
            max_chars_per_line=YOUTUBE_PROFILE["max_chars_per_line"],
            max_lines=YOUTUBE_PROFILE["max_lines_per_cue"],
            max_cps=YOUTUBE_PROFILE["max_cps"],
            min_duration_ms=YOUTUBE_PROFILE["min_duration_ms"],
        )

        # 3 lines should pass (YouTube allows 3)
        max_line_issues = [i for i in result.issues if i.rule == "max_lines"]
        assert len(max_line_issues) == 0

    def test_validate_subtitles_youtube_vs_netflix_line_count(self):
        """YouTube allows 3 lines, Netflix only 2."""
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="Line 1\nLine 2\nLine 3",
            ),
        ]

        # Netflix validation (max 2 lines)
        netflix_result = validate_subtitles(
            cues,
            max_chars_per_line=NETFLIX_PROFILE["max_chars_per_line"],
            max_lines=NETFLIX_PROFILE["max_lines_per_cue"],
            max_cps=NETFLIX_PROFILE["max_cps"],
            min_duration_ms=NETFLIX_PROFILE["min_duration_ms"],
        )
        netflix_line_issues = [
            i for i in netflix_result.issues if i.rule == "max_lines"
        ]
        assert len(netflix_line_issues) == 1  # Netflix rejects 3 lines

        # YouTube validation (max 3 lines)
        youtube_result = validate_subtitles(
            cues,
            max_chars_per_line=YOUTUBE_PROFILE["max_chars_per_line"],
            max_lines=YOUTUBE_PROFILE["max_lines_per_cue"],
            max_cps=YOUTUBE_PROFILE["max_cps"],
            min_duration_ms=YOUTUBE_PROFILE["min_duration_ms"],
        )
        youtube_line_issues = [
            i for i in youtube_result.issues if i.rule == "max_lines"
        ]
        assert len(youtube_line_issues) == 0  # YouTube accepts 3 lines

    def test_validate_subtitles_profile_cps_differences(self):
        """Different profiles enforce different CPS limits."""
        # 50 characters in 2 seconds = 25 CPS
        cues = [
            SubtitleCue(
                index=1,
                start_ms=0,
                end_ms=2000,
                text="Exactly fifty character test content here.",  # 43 chars
            ),
        ]

        # Netflix: max_cps=20
        netflix_result = validate_subtitles(
            cues,
            max_chars_per_line=NETFLIX_PROFILE["max_chars_per_line"],
            max_lines=NETFLIX_PROFILE["max_lines_per_cue"],
            max_cps=NETFLIX_PROFILE["max_cps"],
            min_duration_ms=NETFLIX_PROFILE["min_duration_ms"],
        )
        netflix_speed = [
            i for i in netflix_result.issues if i.rule == "reading_speed"
        ]
        assert len(netflix_speed) >= 1  # Netflix catches this

        # YouTube: max_cps=25
        youtube_result = validate_subtitles(
            cues,
            max_chars_per_line=YOUTUBE_PROFILE["max_chars_per_line"],
            max_lines=YOUTUBE_PROFILE["max_lines_per_cue"],
            max_cps=YOUTUBE_PROFILE["max_cps"],
            min_duration_ms=YOUTUBE_PROFILE["min_duration_ms"],
        )
        youtube_speed = [
            i for i in youtube_result.issues if i.rule == "reading_speed"
        ]
        # This may still have line_length issue (43 > 42), but not speed
        assert len(youtube_speed) == 0


class TestPlatformProfilesIntegration:
    """Integration tests for platform profiles."""

    async def test_multiple_profiles_isolation(self, db_session):
        """Each profile maintains independent QC rules."""
        netflix = PlatformProfile(**NETFLIX_PROFILE)
        bbc = PlatformProfile(**BBC_PROFILE)
        youtube = PlatformProfile(**YOUTUBE_PROFILE)

        db_session.add(netflix)
        db_session.add(bbc)
        db_session.add(youtube)
        await db_session.commit()

        # Query each profile
        result = await db_session.execute(
            select(PlatformProfile).where(PlatformProfile.name == "netflix")
        )
        netflix_retrieved = result.scalar_one()
        assert netflix_retrieved.max_cps == 20.0

        result = await db_session.execute(
            select(PlatformProfile).where(PlatformProfile.name == "bbc")
        )
        bbc_retrieved = result.scalar_one()
        assert bbc_retrieved.max_cps == 18.0

        result = await db_session.execute(
            select(PlatformProfile).where(PlatformProfile.name == "youtube")
        )
        youtube_retrieved = result.scalar_one()
        assert youtube_retrieved.max_cps == 25.0

    async def test_profile_with_complex_settings(self, db_session):
        """JSONB settings can store complex nested data."""
        profile = PlatformProfile(
            name="complex_profile",
            display_name="Complex",
            settings={
                "rules": {
                    "forced_narrative": True,
                    "italic_for_foreign": True,
                    "max_duration_ms": 7000,
                },
                "metadata": {
                    "version": "2.0",
                    "updated_date": "2026-01-15",
                },
                "features": ["html", "colors", "styling"],
            },
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Verify nested structure is preserved
        assert profile.settings["rules"]["forced_narrative"] is True
        assert profile.settings["metadata"]["version"] == "2.0"
        assert "colors" in profile.settings["features"]

    async def test_profile_timestamps_updated(self, db_session):
        """Profile timestamps are correctly set on creation."""
        profile = PlatformProfile(**NETFLIX_PROFILE)
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Both timestamps should be set
        assert profile.created_at is not None
        assert profile.updated_at is not None
        # Initially, they should be equal (or very close)
        assert profile.created_at <= profile.updated_at


class TestPlatformProfileEndpointEdgeCases:
    """Edge case tests for platform profile endpoints."""

    async def test_get_profile_returns_correct_schema(self, test_client, async_engine):
        """Response matches PlatformProfileResponse schema."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(**NETFLIX_PROFILE)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            profile_id = profile.id

        response = await test_client.get(f"/api/v1/platform-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify UUID serialization
        assert isinstance(data["id"], str)
        try:
            uuid.UUID(data["id"])  # Should not raise
        except ValueError:
            pytest.fail("Profile ID is not a valid UUID string")

        # Verify numeric fields are correct types
        assert isinstance(data["max_chars_per_line"], int)
        assert isinstance(data["max_lines_per_cue"], int)
        assert isinstance(data["max_cps"], float)
        assert isinstance(data["min_duration_ms"], int)
        assert isinstance(data["min_gap_ms"], int)

    async def test_list_profiles_maintains_order(self, test_client, async_engine):
        """Profile list is consistently ordered by name."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            # Add profiles in non-alphabetical order
            for profile_data in [YOUTUBE_PROFILE, NETFLIX_PROFILE, BBC_PROFILE]:
                session.add(PlatformProfile(**profile_data))
            await session.commit()

        # Request list multiple times
        response1 = await test_client.get("/api/v1/platform-profiles")
        response2 = await test_client.get("/api/v1/platform-profiles")

        data1 = response1.json()
        data2 = response2.json()

        # Should be identical
        assert len(data1) == len(data2) == 3
        for p1, p2 in zip(data1, data2):
            assert p1["id"] == p2["id"]
            assert p1["name"] == p2["name"]

    async def test_get_profile_with_null_description(
        self, test_client, async_engine
    ):
        """Profile without description returns null in response."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(
                name="no_description",
                display_name="No Description",
                description=None,
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            profile_id = profile.id

        response = await test_client.get(f"/api/v1/platform-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["description"] is None

    async def test_get_profile_with_null_settings(self, test_client, async_engine):
        """Profile without settings returns null in response."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(
                name="no_settings",
                display_name="No Settings",
                settings=None,
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            profile_id = profile.id

        response = await test_client.get(f"/api/v1/platform-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["settings"] is None

    async def test_list_profiles_public_endpoint(self, unauthenticated_client, async_engine):
        """Platform profiles endpoint works without authentication."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(**NETFLIX_PROFILE)
            session.add(profile)
            await session.commit()

        # Use unauthenticated client
        response = await unauthenticated_client.get("/api/v1/platform-profiles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "netflix"

    async def test_get_profile_public_endpoint(self, unauthenticated_client, async_engine):
        """Getting single profile works without authentication."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            profile = PlatformProfile(**NETFLIX_PROFILE)
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            profile_id = profile.id

        # Use unauthenticated client
        response = await unauthenticated_client.get(
            f"/api/v1/platform-profiles/{profile_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "netflix"
