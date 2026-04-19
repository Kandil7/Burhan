"""
Pytest configuration and fixtures for regression tests.

Provides common fixtures for loading and processing golden test cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


# Base path for regression test data
REGRESSION_DATA_DIR = Path(__file__).parent


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load test cases from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of test case dictionaries
    """
    cases = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


@pytest.fixture(scope="session")
def fiqh_cases() -> List[Dict[str, Any]]:
    """Load FiQH golden test cases."""
    return load_jsonl(REGRESSION_DATA_DIR / "fiqh_cases.jsonl")


@pytest.fixture(scope="session")
def hadith_cases() -> List[Dict[str, Any]]:
    """Load Hadith golden test cases."""
    return load_jsonl(REGRESSION_DATA_DIR / "hadith_cases.jsonl")


@pytest.fixture(scope="session")
def quran_cases() -> List[Dict[str, Any]]:
    """Load Quran golden test cases."""
    return load_jsonl(REGRESSION_DATA_DIR / "quran_cases.jsonl")


@pytest.fixture(scope="session")
def all_regression_cases() -> List[Dict[str, Any]]:
    """Load all regression test cases from all categories."""
    all_cases = []
    all_cases.extend(load_jsonl(REGRESSION_DATA_DIR / "fiqh_cases.jsonl"))
    all_cases.extend(load_jsonl(REGRESSION_DATA_DIR / "hadith_cases.jsonl"))
    all_cases.extend(load_jsonl(REGRESSION_DATA_DIR / "quran_cases.jsonl"))
    return all_cases


@pytest.fixture
def classifier():
    """
    Create a HybridIntentClassifier instance for regression tests.

    Uses the same configuration as production for accurate testing.
    """
    from src.application.router.hybrid_classifier import HybridIntentClassifier

    return HybridIntentClassifier(low_conf_threshold=0.55)


@pytest.fixture
def router_agent(classifier):
    """
    Create a RouterAgent instance for regression tests.

    Uses the configured classifier for intent routing.
    """
    from src.application.router.router_agent import RouterAgent

    return RouterAgent(classifier=classifier)
