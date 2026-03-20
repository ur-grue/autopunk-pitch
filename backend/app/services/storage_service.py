"""S3-compatible storage service using aioboto3."""

import aioboto3
import structlog
from fastapi import UploadFile

from app.config import Settings, get_settings
from app.exceptions import StorageError

logger = structlog.get_logger(__name__)


class StorageService:
    """Async S3 operations for file upload, download, and management."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._session = aioboto3.Session()

    def _client_kwargs(self) -> dict:
        """Return kwargs for the S3 client."""
        return {
            "endpoint_url": self._settings.s3_endpoint_url,
            "aws_access_key_id": self._settings.s3_access_key,
            "aws_secret_access_key": self._settings.s3_secret_key,
        }

    async def ensure_bucket(self) -> None:
        """Create the storage bucket if it doesn't exist."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                try:
                    await s3.head_bucket(Bucket=self._settings.s3_bucket_name)
                except s3.exceptions.ClientError:
                    await s3.create_bucket(
                        Bucket=self._settings.s3_bucket_name
                    )
                    logger.info(
                        "bucket_created",
                        bucket=self._settings.s3_bucket_name,
                    )
        except Exception as e:
            raise StorageError(f"Failed to ensure bucket exists: {e}") from e

    async def upload_file(self, file: UploadFile, key: str) -> str:
        """Upload a file to S3 and return the object key."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                content = await file.read()
                await s3.put_object(
                    Bucket=self._settings.s3_bucket_name,
                    Key=key,
                    Body=content,
                )
                logger.info("file_uploaded", key=key, size=len(content))
                return key
        except Exception as e:
            raise StorageError(f"Failed to upload file: {e}") from e

    async def upload_bytes(self, data: bytes, key: str) -> str:
        """Upload raw bytes to S3 and return the object key."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.put_object(
                    Bucket=self._settings.s3_bucket_name,
                    Key=key,
                    Body=data,
                )
                logger.info("bytes_uploaded", key=key, size=len(data))
                return key
        except Exception as e:
            raise StorageError(f"Failed to upload bytes: {e}") from e

    async def download_file(self, key: str) -> bytes:
        """Download file content from S3."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                response = await s3.get_object(
                    Bucket=self._settings.s3_bucket_name,
                    Key=key,
                )
                content = await response["Body"].read()
                logger.info("file_downloaded", key=key, size=len(content))
                return content
        except Exception as e:
            raise StorageError(f"Failed to download file: {e}") from e

    async def generate_presigned_url(
        self, key: str, expires_in: int = 3600
    ) -> str:
        """Generate a presigned download URL."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self._settings.s3_bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expires_in,
                )
                return url
        except Exception as e:
            raise StorageError(f"Failed to generate presigned URL: {e}") from e

    async def delete_file(self, key: str) -> None:
        """Delete a file from S3."""
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.delete_object(
                    Bucket=self._settings.s3_bucket_name,
                    Key=key,
                )
                logger.info("file_deleted", key=key)
        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}") from e
