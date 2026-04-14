"""
Logging configuration for Athar Islamic QA system.

Uses structlog for structured JSON logging in production,
with human-readable output for development.
"""
import logging
import sys
from typing import Any

import structlog

from src.config.settings import settings


def setup_logging() -> None:
    """
    Configure logging for the application.

    Development: Human-readable colored output
    Production: Structured JSON for log aggregation
    """
    # Set standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Prepare event dict
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,

            # Format output
            structlog.processors.TimeStamper(fmt="iso"),

            # JSON in production, console in development
            structlog.processors.JSONRenderer() if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(*args: Any, **kwargs: Any) -> Any:
    """
    Get a logger instance.

    Usage:
        logger = get_logger()
        logger.info("query.received", query_id="123", query="...")
    """
    return structlog.get_logger(*args, **kwargs)
