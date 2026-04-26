#!/usr/bin/env python3
"""
Common utilities for Burhan scripts.

Provides shared functionality used across all scripts:
- Path helpers (project root, data dirs, etc.)
- Logging setup with consistent format
- Progress bar helpers
- Error handling decorators
- Configuration loading

Usage:
    from scripts.utils import (
        get_project_root,
        get_data_dir,
        setup_script_logger,
        ProgressBar,
        safe_run,
    )

Author: Burhan Engineering Team
"""

import functools
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

from tqdm import tqdm

# -- Path Helpers --

_PROJECT_ROOT: Optional[Path] = None


def get_project_root() -> Path:
    """
    Return the project root directory (parent of scripts/).

    Cached after first call for performance.

    Returns:
        Absolute path to project root.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    return _PROJECT_ROOT


def get_data_dir(subdir: str = "") -> Path:
    """Return path to a data directory under project root."""
    path = get_project_root() / "data"
    if subdir:
        path = path / subdir
    return path


def get_datasets_dir(subdir: str = "") -> Path:
    """Return path to a datasets directory under project root."""
    path = get_project_root() / "datasets"
    if subdir:
        path = path / subdir
    return path


def get_scripts_dir(subdir: str = "") -> Path:
    """Return path to the scripts directory."""
    path = get_project_root() / "scripts"
    if subdir:
        path = path / subdir
    return path


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


# -- Logging Setup --

_SCRIPT_LOGGER: Optional[logging.Logger] = None


def setup_script_logger(
    name: str = "Burhan-script",
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up a consistent logger for scripts."""
    global _SCRIPT_LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_to_file:
        if log_file is None:
            log_dir = get_scripts_dir()
            log_file = str(log_dir / f"{name}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _SCRIPT_LOGGER = logger
    return logger


def get_script_logger(name: str = "Burhan-script") -> logging.Logger:
    """Get an existing script logger or create one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_script_logger(name)
    return logger


# -- Progress Bar Helpers --


class ProgressBar:
    """Unified progress bar wrapper around tqdm."""

    def __init__(
        self,
        total: int,
        desc: str = "Processing",
        unit: str = "items",
        disable: bool = False,
    ):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.disable = disable
        self._bar: Optional[tqdm] = None

    def __enter__(self) -> "ProgressBar":
        self._bar = tqdm(
            total=self.total,
            desc=self.desc,
            unit=self.unit,
            disable=self.disable,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )
        return self

    def __exit__(self, *args: Any) -> None:
        if self._bar:
            self._bar.close()

    def update(self, n: int = 1) -> None:
        """Advance progress bar by n items."""
        if self._bar:
            self._bar.update(n)

    def set_postfix(self, **kwargs: Any) -> None:
        """Set postfix info on the progress bar."""
        if self._bar:
            self._bar.set_postfix(**kwargs)


def progress_iter(
    iterable,
    total: Optional[int] = None,
    desc: str = "Processing",
    unit: str = "items",
) -> Any:
    """Wrap an iterable with a progress bar."""
    return tqdm(iterable, total=total, desc=desc, unit=unit)


# -- Error Handling --


def safe_run(
    func: Callable,
    *args: Any,
    on_error: Optional[Callable] = None,
    retry_count: int = 0,
    retry_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Run a function with error handling and optional retry."""
    last_error = None
    attempts = retry_count + 1

    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if on_error:
                on_error(e, attempt)

            if attempt < retry_count:
                delay = retry_delay * (2 ** attempt)
                time.sleep(delay)

    if last_error:
        logger = get_script_logger()
        logger.error("safe_run.failed", error=str(last_error), attempts=attempts)
    return None


def retry_async(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying async functions with exponential backoff."""
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        delay = backoff_base * (2 ** attempt)
                        logger = get_script_logger()
                        logger.warning(
                            "retry.async",
                            func=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e),
                        )
                        await asyncio.sleep(delay)
            raise last_error

        return wrapper

    return decorator


# -- Configuration Loading --


def load_script_config() -> dict:
    """Load script configuration from environment and defaults."""
    root = get_project_root()

    return {
        "project_root": str(root),
        "data_dir": str(root / "data"),
        "datasets_dir": str(root / "datasets"),
        "processed_dir": str(root / "data" / "processed"),
        "seed_dir": str(root / "data" / "seed"),
        "embeddings_dir": str(root / "data" / "embeddings"),
        "api_url": os.environ.get("Burhan_API_URL", "http://localhost:8000"),
        "api_port": int(os.environ.get("Burhan_API_PORT", "8000")),
    }


# -- Utility Functions --


def format_size(size_bytes: int) -> str:
    """Format byte size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system usage."""
    import re

    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = sanitized.strip('. ')
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:195] + ext
    return sanitized or "unnamed"


def add_project_root_to_path() -> None:
    """Add project root to sys.path for importing src modules."""
    root = str(get_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)
