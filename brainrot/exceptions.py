"""Custom exceptions and retry utilities for the brainrot platform.

This module defines the exception hierarchy and provides a retry decorator
with exponential backoff for handling transient failures.

Exception Hierarchy:
    BrainrotError (base)
    ├── ConfigurationError
    ├── AuthenticationError
    ├── QuotaExceededError
    ├── TrendFetchError
    ├── VideoGenerationError
    └── UploadFailedError
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

__all__ = [
    "BrainrotError",
    "ConfigurationError",
    "AuthenticationError",
    "QuotaExceededError",
    "TrendFetchError",
    "VideoGenerationError",
    "UploadFailedError",
    "retry",
]


class BrainrotError(Exception):
    """Base exception for all brainrot-specific errors.

    All custom exceptions in the brainrot package should inherit from this
    class to allow for easy catching of application-specific errors.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ConfigurationError(BrainrotError):
    """Raised when there is a configuration error.

    This includes missing required settings, invalid configuration values,
    or issues with configuration files.

    Example:
        >>> raise ConfigurationError("Missing API key", {"env_var": "YOUTUBE_API_KEY"})
    """

    pass


class AuthenticationError(BrainrotError):
    """Raised when authentication fails.

    This includes invalid credentials, expired tokens, or permission issues.

    Example:
        >>> raise AuthenticationError("OAuth token expired", {"service": "YouTube"})
    """

    pass


class QuotaExceededError(BrainrotError):
    """Raised when an API quota limit is exceeded.

    This is used to signal that the application has hit its quota limit
    for a given API (YouTube, Reddit, etc.).

    Example:
        >>> raise QuotaExceededError(
        ...     "YouTube daily quota exceeded",
        ...     {"service": "YouTube", "limit": 10000, "used": 10000}
        ... )
    """

    pass


class TrendFetchError(BrainrotError):
    """Raised when fetching trending content fails.

    This includes errors from Reddit API, YouTube API, or other sources
    used to gather trending content.

    Example:
        >>> raise TrendFetchError(
        ...     "Failed to fetch Reddit trends",
        ...     {"subreddit": "AskReddit", "status_code": 503}
        ... )
    """

    pass


class VideoGenerationError(BrainrotError):
    """Raised when video generation fails.

    This includes errors during script generation, audio synthesis,
    video assembly, or FFmpeg processing.

    Example:
        >>> raise VideoGenerationError(
        ...     "FFmpeg processing failed",
        ...     {"input_file": "input.mp4", "exit_code": 1}
        ... )
    """

    pass


class UploadFailedError(BrainrotError):
    """Raised when uploading content fails.

    This includes errors during YouTube upload, file transfer,
    or other upload operations.

    Example:
        >>> raise UploadFailedError(
        ...     "YouTube upload failed",
        ...     {"video_id": None, "reason": "invalid_credentials"}
        ... )
    """

    pass


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int, float], None] | None = None,
) -> Callable[[F], F]:
    """Decorator that retries a function with exponential backoff.

    Retries the decorated function when it raises specified exceptions,
    with exponential backoff between attempts.

    Args:
        max_attempts: Maximum number of attempts (including the first call).
                      Defaults to 3.
        backoff_factor: Multiplier for backoff delay between attempts.
                        Delay = backoff_factor ** (attempt - 1).
                        Defaults to 2.0.
        exceptions: Tuple of exception types to catch and retry on.
                    Defaults to (Exception,).
        on_retry: Optional callback called on each retry with:
                  (exception, attempt_number, delay_seconds).

    Returns:
        Decorated function that will retry on specified exceptions.

    Example:
        >>> @retry(max_attempts=3, backoff_factor=2.0, exceptions=(ConnectionError,))
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data")
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt >= max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    delay = backoff_factor ** (attempt - 1)
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt}/{max_attempts}, "
                        f"retrying in {delay:.1f}s: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt, delay)

                    time.sleep(delay)

            if last_exception:
                raise last_exception

        return wrapper  # type: ignore[return-value]

    return decorator
