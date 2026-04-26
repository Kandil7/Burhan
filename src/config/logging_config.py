"""
Logging configuration for Burhan Islamic QA system.

Provides a LoggerWrapper that handles both structlog-style calls (with keyword args)
and standard Python logging for maximum compatibility.

Phase 9 Enhancement:
- Added structured logging with context
- Added metrics tracking
- Added better exception handling
"""

import logging
import sys
import time
from typing import Any, Optional
from functools import wraps

from src.config.settings import settings


class LoggerWrapper:
    """
    A wrapper around Python's logging.Logger that handles structlog-style calls.

    This allows both of these calling styles to work:
        logger.info("message", key=value)  # structlog style
        logger.info("message")              # standard style

    Phase 9: Added structured logging and metrics tracking.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger
        # Map standard levels
        self._level_map = {
            "trace": logging.DEBUG,
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
            "fatal": logging.CRITICAL,
        }

    def _format_message(self, msg: str, **kwargs: Any) -> str:
        """Format message with extra kwargs appended."""
        if kwargs:
            # Format extra info as key=value pairs
            extras = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{msg} [{extras}]"
        return msg

    def _log(self, level: str, msg: str, **kwargs: Any) -> None:
        """Internal log method that handles both styles."""
        formatted_msg = self._format_message(msg, **kwargs)
        log_level = self._level_map.get(level, logging.INFO)

        # Handle exc_info if present in kwargs
        exc_info = kwargs.get("exc_info", False)
        if exc_info:
            self._logger.log(log_level, formatted_msg, exc_info=True)
        else:
            self._logger.log(log_level, formatted_msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log("error", msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log("critical", msg, **kwargs)

    def fatal(self, msg: str, **kwargs: Any) -> None:
        self._log("fatal", msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log an exception with the message."""
        kwargs["exc_info"] = True
        self._log("error", msg, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Pass through any other attributes to the underlying logger."""
        return getattr(self._logger, name)


# ==========================================
# Metrics Tracking
# ==========================================


class MetricsCollector:
    """Simple metrics collector for observability."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._timings: list[dict[str, float]] = []

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + value

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        self._gauges[name] = value

    def timing(self, name: str, duration_ms: float) -> None:
        """Record a timing."""
        self._timings.append({"name": name, "duration_ms": duration_ms, "timestamp": time.time()})

    def get_metrics(self) -> dict:
        """Get all metrics."""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "timings": self._timings[-100:],  # Last 100
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._timings.clear()


# Global metrics collector
metrics = MetricsCollector()


def track_time(name: str):
    """Decorator to track execution time."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.timing(name, duration_ms)
                metrics.increment(f"{name}.calls")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.timing(name, duration_ms)
                metrics.increment(f"{name}.calls")

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure format based on settings
    if settings.log_format == "json":
        # JSON logging - for production with log aggregation
        logging.basicConfig(
            format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            stream=sys.stdout,
            level=log_level,
        )
    else:
        # Standard logging - for development
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
            level=log_level,
        )


def get_logger(name: Optional[str] = None) -> LoggerWrapper:
    """
    Get a logger instance that handles structlog-style calls.

    Args:
        name: Logger name (defaults to "Burhan")

    Returns:
        LoggerWrapper instance
    """
    if name is None:
        name = "Burhan"
    logger = logging.getLogger(name)
    return LoggerWrapper(logger)
