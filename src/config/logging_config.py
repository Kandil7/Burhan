"""
Logging configuration for Athar Islamic QA system.

Provides a LoggerWrapper that handles both structlog-style calls (with keyword args)
and standard Python logging for maximum compatibility.
"""

import logging
import sys
from typing import Any, Optional


class LoggerWrapper:
    """
    A wrapper around Python's logging.Logger that handles structlog-style calls.

    This allows both of these calling styles to work:
        logger.info("message", key=value)  # structlog style
        logger.info("message")              # standard style
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


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: Optional[str] = None) -> LoggerWrapper:
    """
    Get a logger instance that handles structlog-style calls.

    Args:
        name: Logger name (defaults to "athar")

    Returns:
        LoggerWrapper instance
    """
    if name is None:
        name = "athar"
    logger = logging.getLogger(name)
    return LoggerWrapper(logger)
