"""Shared test fixtures for the Autopunk Localize backend."""

import json
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.user import User

# Use in-memory SQLite for tests (no Postgres dependency)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
async def async_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_user(db_session) -> User:
    """Create a test user in the database."""
    user = User(
        clerk_id="test_clerk_123",
        email="test@autopunk.local",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_client(async_engine, test_user) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx AsyncClient wired to the FastAPI app with test DB and auth."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def unauthenticated_client(
    async_engine,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx AsyncClient with NO auth override (tests 401 paths)."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    # Only override DB, not auth — so real auth logic runs
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_transcription_response() -> dict:
    """Load the sample OpenAI transcription response fixture."""
    fixture_path = FIXTURES_DIR / "sample_transcription_response.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def mock_openai_response(sample_transcription_response) -> MagicMock:
    """Create a mock OpenAI transcription API response object."""
    response = MagicMock()
    response.duration = sample_transcription_response["duration"]
    response.text = sample_transcription_response["text"]
    response.language = sample_transcription_response["language"]
    response.segments = sample_transcription_response["segments"]
    response.words = sample_transcription_response["words"]
    return response


@pytest.fixture
def mock_openai_client(mock_openai_response) -> MagicMock:
    """Create a mock OpenAI AsyncClient."""
    client = MagicMock()
    client.audio = MagicMock()
    client.audio.transcriptions = MagicMock()
    client.audio.transcriptions.create = AsyncMock(
        return_value=mock_openai_response
    )
    return client


@pytest.fixture
def sample_project_id() -> uuid.UUID:
    """Return a consistent project UUID for tests."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_job_id() -> uuid.UUID:
    """Return a consistent job UUID for tests."""
    return uuid.UUID("87654321-4321-8765-4321-876543218765")
