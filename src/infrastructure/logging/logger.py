"""
Structured logging for Athar Islamic QA system.

Provides a configured logger with structured output for production use.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def get_logger(name: str = "athar", level: Optional[int] = None) -> logging.Logger:
    """
    Return a configured logger.

    In production, swap the StreamHandler for a JSON handler
    (e.g. python-json-logger) or a structlog processor.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured — avoid duplicate handlers

    logger.setLevel(level or logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
