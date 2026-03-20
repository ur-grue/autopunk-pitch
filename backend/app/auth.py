"""Clerk JWT authentication for FastAPI.

Verifies JWTs issued by Clerk. In development mode (no Clerk secret key),
falls back to a dev user for local testing.
"""

import uuid

import httpx
import jwt
import structlog
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.exceptions import AppError
from app.models.user import User

logger = structlog.get_logger(__name__)

# Cache JWKS keys in memory
_jwks_cache: dict | None = None


class AuthenticationError(AppError):
    """Authentication failure (401)."""

    def __init__(self, message: str = "Authentication required", **kwargs) -> None:
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(AppError):
    """Authorization failure (403)."""

    def __init__(self, message: str = "Forbidden", **kwargs) -> None:
        super().__init__(message, status_code=403, **kwargs)


async def _fetch_jwks(issuer: str) -> dict:
    """Fetch JWKS from Clerk's well-known endpoint."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    jwks_url = f"{issuer}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url, timeout=10.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _decode_clerk_token(token: str, settings) -> dict:
    """Decode and verify a Clerk JWT.

    Uses the Clerk secret key (HS256) for session tokens,
    which is the standard Clerk backend verification approach.
    """
    try:
        payload = jwt.decode(
            token,
            settings.clerk_secret_key,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")


async def _get_or_create_user(
    db: AsyncSession, clerk_id: str, email: str, name: str | None
) -> User:
    """Get existing user or create a new one from Clerk claims."""
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            clerk_id=clerk_id,
            email=email,
            display_name=name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("user_created", clerk_id=clerk_id, email=email)
    else:
        # Update email/name if changed
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if name and user.display_name != name:
            user.display_name = name
            changed = True
        if changed:
            await db.commit()
            await db.refresh(user)

    return user


async def _get_dev_user(db: AsyncSession) -> User:
    """Get or create a development user (when Clerk is not configured)."""
    result = await db.execute(select(User).where(User.clerk_id == "dev_user"))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            clerk_id="dev_user",
            email="dev@autopunk.local",
            display_name="Dev User",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts and verifies the authenticated user.

    In development (no clerk_secret_key), falls back to a dev user.
    In production, requires a valid Clerk JWT in the Authorization header.
    """
    settings = get_settings()

    # Dev mode: no Clerk configured
    if not settings.clerk_secret_key:
        return await _get_dev_user(db)

    # Extract Bearer token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing Authorization header")

    token = auth_header[7:]  # Strip "Bearer "

    # Decode and verify
    claims = _decode_clerk_token(token, settings)

    clerk_id = claims.get("sub", "")
    if not clerk_id:
        raise AuthenticationError("Token missing subject claim")

    # Extract user info from Clerk claims
    email = claims.get("email", claims.get("email_address", f"{clerk_id}@clerk.user"))
    name = claims.get("name", claims.get("first_name"))

    return await _get_or_create_user(db, clerk_id, email, name)
