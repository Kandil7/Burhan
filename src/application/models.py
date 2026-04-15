"""
Application-level models for Athar Islamic QA system.

This module contains:
- RoutingDecision: Application-level result wrapping ClassificationResult with routing info
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from src.domain.models import ClassificationResult


@dataclass(frozen=True)
class RoutingDecision:
    """
    Application-level result: wraps ClassificationResult with a resolved
    route string and optional metadata for downstream agents.

    Route examples:
      "fiqh_agent"
      "hadith_agent"
      "quran:verse_lookup"
      "quran:nl2sql"
      "quran:interpretation_rag"
      "quran:quote_validation"

    Attributes:
        result: The underlying ClassificationResult
        route: Resolved route string for agent/tool dispatch
        agent_metadata: Optional metadata for downstream agents
    """

    result: ClassificationResult
    route: str
    agent_metadata: Dict[str, Any] = field(default_factory=dict)
