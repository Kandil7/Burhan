"""
Domain value objects for Burhan Islamic QA system.

This module contains:
- ClassificationResult: Pure domain value object produced by the intent classifier
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.domain.intents import Intent, QuranSubIntent


@dataclass(frozen=True)
class ClassificationResult:
    """
    Pure domain value object produced by the intent classifier.

    Does NOT contain routing information — that is an application concern
    decided by RouterAgent based on this result.

    Attributes:
        intent: The classified primary intent
        confidence: Confidence score (0.0 - 1.0)
        language: Detected language ("ar" | "en" | "mixed")
        reasoning: Human-readable explanation of classification
        requires_retrieval: Whether this query needs document retrieval (RAG)
        method: Classification method used ("keyword" | "llm" | "embedding" | "fallback")
        quran_subintent: Optional sub-intent for Quran queries
        scores: Optional dictionary of intent scores for debugging
        subquestions: List of sub-questions if query is compound
    """

    intent: Intent
    confidence: float  # 0.0 – 1.0
    language: str  # "ar" | "en" | "mixed"
    reasoning: str
    requires_retrieval: bool
    method: str  # "keyword" | "llm" | "embedding" | "fallback"
    quran_subintent: Optional[QuranSubIntent] = None
    scores: Optional[Dict[str, float]] = field(default=None)
    subquestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate classification result after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.language not in ("ar", "en", "mixed"):
            raise ValueError(f"Language must be 'ar', 'en', or 'mixed', got {self.language}")
        if self.method not in ("keyword", "llm", "embedding", "fallback"):
            raise ValueError(f"Invalid method: {self.method}")
