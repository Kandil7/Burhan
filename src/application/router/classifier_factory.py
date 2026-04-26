"""
Intent Classification Module for Athar Islamic QA System.

This module provides the canonical intent classification system:
1. KeywordBasedClassifier - Fast keyword matching for clear signals
2. MasterHybridClassifier - Combines keyword + embedding tiers
3. ClassifierFactory - Factory for creating classifiers

All classification code should use these implementations.

Note: EmbeddingClassifier is in src/application/router/embedding_classifier.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.application.interfaces import IntentClassifier
from src.config.logging_config import get_logger
from src.domain.intents import (
    Intent,
    INTENT_DESCRIPTIONS,
    KEYWORD_PATTERNS as INTENT_KEYWORDS,
    normalize_arabic,
    detect_language,
)
from src.domain.models import ClassificationResult

logger = get_logger()


# ============================================================================
# Query Classifier Abstract Base Class
# ============================================================================


class QueryClassifier(ABC):
    """Abstract base class for query classifiers."""

    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        """Classify a query."""
        pass


# ============================================================================
# Keyword-Based Classifier
# ============================================================================


class KeywordBasedClassifier(QueryClassifier):
    """
    High-precision keyword-based query classifier.

    Uses robust Arabic normalization and match counting for classification.
    """

    def __init__(self, keywords: Optional[Dict[Intent, List[str]]] = None):
        """
        Initialize the classifier with keywords.

        Args:
            keywords: Optional custom keywords dict. Uses INTENT_KEYWORDS if not provided.
        """
        self.keywords = keywords or INTENT_KEYWORDS
        # Pre-normalize keywords for performance
        self._norm_keywords: Dict[Intent, List[str]] = {
            intent: [normalize_arabic(kw) for kw in kws] for intent, kws in self.keywords.items()
        }

    async def classify(self, query: str) -> ClassificationResult:
        """Classify based on keyword density and priority."""
        if not query or not query.strip():
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.0,
                language="ar",
                reasoning="Empty query.",
                requires_retrieval=True,
                method="keyword",
            )

        norm_query = normalize_arabic(query)

        # Count matches per intent
        matches: Dict[Intent, int] = {}
        for intent, patterns in self._norm_keywords.items():
            count = sum(1 for p in patterns if p in norm_query)
            if count > 0:
                matches[intent] = count

        if not matches:
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.0,
                language="ar",
                reasoning="No keywords matched.",
                requires_retrieval=True,
                method="keyword",
            )

        # Pick highest match count
        best_intent = max(matches, key=matches.get)
        count = matches[best_intent]

        # Confidence based on match count
        confidence = 0.7 if count == 1 else (0.85 if count == 2 else 0.95)

        return ClassificationResult(
            intent=best_intent,
            confidence=confidence,
            language=detect_language(query),
            reasoning=f"Matched {count} keywords for {best_intent.value}.",
            requires_retrieval=True,
            method="keyword",
        )


# ============================================================================
# Hybrid Classifier
# ============================================================================


class MasterHybridClassifier(IntentClassifier):
    """
    Consolidated Hybrid Classifier combining Keyword and Semantic tiers.

    Tier 1: Keyword fast-path (always runs first)
    Tier 2: Embedding fallback (when no keywords matched)
    """

    def __init__(self, embedding_model: Any = None, low_conf_threshold: float = 0.65) -> None:
        self._low_conf = low_conf_threshold
        self._keyword_classifier = KeywordBasedClassifier()
        self._embedding_classifier = None
        if embedding_model:
            from src.application.router.embedding_classifier import EmbeddingClassifier

            self._embedding_classifier = EmbeddingClassifier(embedding_model)

    async def classify(self, query: str) -> ClassificationResult:
        """Run classification tiers in order."""
        logger.info("hybrid_classifier.classify_start", query=query[:50])

        if not query or not query.strip():
            return await self._keyword_classifier.classify("")

        # Tier 1: Keyword Fast-Path
        kw_result = await self._keyword_classifier.classify(query)
        logger.debug("hybrid_classifier.keyword_result", intent=kw_result.intent.value, confidence=kw_result.confidence)

        # If keyword match exists, use it
        if kw_result.confidence > 0.0:
            logger.info("hybrid_classifier.keyword_win", intent=kw_result.intent.value)
            return kw_result

        # Tier 2: Embedding Fallback
        if self._embedding_classifier:
            try:
                emb_result = await self._embedding_classifier.classify(query)
                logger.info(
                    "hybrid_classifier.embedding_result",
                    intent=emb_result.intent.value,
                    confidence=emb_result.confidence,
                )
                return emb_result
            except Exception as e:
                logger.error("hybrid_classifier.embedding_failed", error=str(e))

        # Fallback
        logger.info("hybrid_classifier.fallback_to_default")
        return kw_result

    async def close(self) -> None:
        """Clean up resources."""
        if self._embedding_classifier:
            await self._embedding_classifier.close()


# ============================================================================
# Classifier Factory
# ============================================================================


class ClassifierFactory:
    """Factory for creating query classifiers."""

    @staticmethod
    def create_keyword() -> KeywordBasedClassifier:
        """Create a keyword-based classifier."""
        return KeywordBasedClassifier()

    @staticmethod
    def create_hybrid(embedding_model: Any = None) -> MasterHybridClassifier:
        """Create a hybrid classifier with optional embedding support."""
        return MasterHybridClassifier(embedding_model=embedding_model)

    @staticmethod
    def create_default() -> KeywordBasedClassifier:
        """Create the default classifier (keyword-based)."""
        return KeywordBasedClassifier()


# Default factory instance
classifier_factory = ClassifierFactory()

# Backward compatibility aliases
HybridIntentClassifier = MasterHybridClassifier


__all__ = [
    # Core classes
    "QueryClassifier",
    "KeywordBasedClassifier",
    "MasterHybridClassifier",
    "HybridIntentClassifier",
    "ClassifierFactory",
    # Utilities
    "normalize_arabic",
    "detect_language",
    "INTENT_KEYWORDS",
    # Backward compatibility
    "classifier_factory",
]
