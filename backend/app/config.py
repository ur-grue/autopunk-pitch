"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/autopunk"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3-compatible storage
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "autopunk-media"

    # OpenAI
    openai_api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Clerk auth
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Pricing (USD per minute of media)
    price_per_minute_usd: float = 5.0

    # App settings
    log_level: str = "INFO"
    max_upload_size_mb: int = 10240
    video_retention_hours: int = 72

    # Celery (defaults to redis_url if not set)
    celery_broker_url: str = ""

    @property
    def effective_celery_broker(self) -> str:
        """Return Celery broker URL, defaulting to Redis URL."""
        return self.celery_broker_url or self.redis_url


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
