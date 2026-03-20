"""Custom exception hierarchy for the application."""


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: dict | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", **kwargs) -> None:
        super().__init__(message, status_code=404, **kwargs)


class ValidationError(AppError):
    """Invalid input (422)."""

    def __init__(self, message: str = "Validation error", **kwargs) -> None:
        super().__init__(message, status_code=422, **kwargs)


class StorageError(AppError):
    """S3/MinIO storage failure (502)."""

    def __init__(self, message: str = "Storage error", **kwargs) -> None:
        super().__init__(message, status_code=502, **kwargs)


class TranscriptionError(AppError):
    """OpenAI transcription API failure (502)."""

    def __init__(self, message: str = "Transcription error", **kwargs) -> None:
        super().__init__(message, status_code=502, **kwargs)


class AudioExtractionError(AppError):
    """FFmpeg audio extraction failure (422)."""

    def __init__(self, message: str = "Audio extraction error", **kwargs) -> None:
        super().__init__(message, status_code=422, **kwargs)


class JobAlreadyProcessingError(AppError):
    """Job is already being processed (409)."""

    def __init__(
        self, message: str = "Job is already processing", **kwargs
    ) -> None:
        super().__init__(message, status_code=409, **kwargs)


class QuotaExceededError(AppError):
    """Usage quota exceeded (429)."""

    def __init__(self, message: str = "Quota exceeded", **kwargs) -> None:
        super().__init__(message, status_code=429, **kwargs)


class TranslationError(AppError):
    """Claude translation API failure (502)."""

    def __init__(self, message: str = "Translation error", **kwargs) -> None:
        super().__init__(message, status_code=502, **kwargs)


class BillingError(AppError):
    """Stripe billing or payment failure (502)."""

    def __init__(self, message: str = "Billing error", **kwargs) -> None:
        super().__init__(message, status_code=502, **kwargs)


class PaymentRequiredError(AppError):
    """Payment required to proceed (402)."""

    def __init__(self, message: str = "Payment required", **kwargs) -> None:
        super().__init__(message, status_code=402, **kwargs)
