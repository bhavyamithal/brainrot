"""Structured logging configuration with JSON formatter and correlation ID support.

This module provides logging utilities for the brainrot platform, including:
- JSON-formatted logs for structured logging
- Correlation ID tracking for request tracing
- Configurable log levels and output formats
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

__all__ = [
    "setup_logging",
    "get_correlation_id",
    "set_correlation_id",
    "JSONFormatter",
]


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Outputs log records as JSON objects with the following fields:
    - timestamp: ISO 8601 formatted timestamp with timezone
    - level: Log level name
    - name: Logger name
    - message: Log message
    - correlation_id: Request correlation ID (if present)
    - Any extra fields passed to the log call
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "message", "asctime",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context.

    Returns:
        The current correlation ID, or None if not set.
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation ID in the current context.

    Args:
        correlation_id: The correlation ID to set, or None to clear.
    """
    _correlation_id.set(correlation_id)


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_format: str | None = None,
) -> None:
    """Configure logging for the brainrot application.

    Sets up the root logger with appropriate handlers and formatters.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to "INFO".
        json_output: If True, use JSON formatter for structured logs.
                     Defaults to False (human-readable format).
        log_format: Custom log format string. If provided and json_output
                    is False, this format will be used instead of the default.

    Example:
        >>> setup_logging(level="DEBUG", json_output=True)
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> set_correlation_id("req-12345")
        >>> logger.info("Processing request", extra={"user_id": "abc"})
        {"timestamp": "2026-03-15T...", "level": "INFO", ...}
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_output:
        formatter: logging.Formatter = JSONFormatter()
    else:
        if log_format is None:
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(correlation_id)s] - %(message)s"
            )
        formatter = CorrelationFormatter(log_format)

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


class CorrelationFormatter(logging.Formatter):
    """Log formatter that includes correlation ID in the output.

    Extends the standard formatter to support a %(correlation_id)s
    placeholder in the format string.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record, adding correlation ID if available.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string.
        """
        record.correlation_id = get_correlation_id() or "-"  # type: ignore[attr-defined]
        return super().format(record)
