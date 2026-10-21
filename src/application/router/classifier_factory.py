"""
Intent Classification Module for Burhan Islamic QA System.

This module provides the canonical intent classification system:
1. KeywordBasedClassifier - Fast keyword matching for clear signals
2. MasterHybridClassifier - Combines keyword + embedding tiers
3. ClassifierFactory - Factory for creating classifiers

All classification code should use these implementations.

Note: EmbeddingClassifier is in src/application/router/embedding_classifier.py
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from src.application.interfaces import IntentClassifier
from src.config.logging_config import get_logger
from src.domain.intents import (
    INTENT_PRIORITY,
    Intent,
    detect_language,
    normalize_arabic,
)
from src.domain.intents import (
    KEYWORD_PATTERNS as INTENT_KEYWORDS,
)
from src.domain.models import ClassificationResult

logger = get_logger()


# A deterministic calculator needs an actual case to compute. Questions that
# only ask for a ruling are knowledge questions, even when they name the topic.
_CALCULATOR_INTENTS = frozenset({Intent.ZAKAT, Intent.INHERITANCE})
_DIGIT_RE = re.compile(r"\d")
_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_RULING_CUES = (
    "حكم",
    "احكام",
    "فضل",
    "فضيل",
    "معني",
    "يجوز",
    "مشروع",
    "دليل",
    "تعريف",
    "شروط",
    "اركان",
    "نصيب",
    "سهم",
    "حصه",
)
_HEIR_TOKENS = frozenset(
    {
        "زوج",
        "زوجه",
        "زوجات",
        "زوجتان",
        "ام",
        "اب",
        "ابن",
        "ابنه",
        "ابنن",
        "بنت",
        "بنتان",
        "بنتين",
        "اولاد",
        "ابناء",
        "اخ",
        "اخت",
        "اخوات",
        "عم",
        "عمة",
        "خال",
        "خاله",
        "جد",
        "جده",
        "حفيد",
        "حفيده",
    }
)


# ============================================================================
# Query Classifier Abstract Base Class
# ============================================================================


_HERITAGE_PREFIXES = ("وال", "بال", "فال", "كال", "لل", "ال")


def _strip_arabic_prefix(token: str) -> str:
    """Drop a leading conjunction and article so "والأم" matches "ام"."""
    for prefix in _HERITAGE_PREFIXES:
        if token.startswith(prefix) and len(token) > len(prefix) + 1:
            return token[len(prefix) :]
    if token.startswith("و") and len(token) > 3:
        return token[1:]
    return token


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

    def __init__(self, keywords: dict[Intent, list[str]] | None = None):
        """
        Initialize the classifier with keywords.

        Args:
            keywords: Optional custom keywords dict. Uses INTENT_KEYWORDS if not provided.
        """
        self.keywords = keywords or INTENT_KEYWORDS
        # Pre-normalize and compile keywords for performance.
        # Word-boundary matching stops short keywords such as "علي" from
        # matching inside "عليكم", while still allowing Arabic proclitics.
        # Variants that normalize to the same string (e.g. "صلاة" and "صلاه")
        # are collapsed so they cannot double-count for one intent.
        self._norm_keywords: dict[Intent, list[re.Pattern[str]]] = {}
        for intent, kws in self.keywords.items():
            seen: set[str] = set()
            compiled: list[re.Pattern[str]] = []
            for kw in kws:
                normalized = normalize_arabic(kw)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                compiled.append(self._compile_keyword(kw))
            self._norm_keywords[intent] = compiled

    @staticmethod
    def _compile_keyword(keyword: str) -> re.Pattern[str]:
        normalized = normalize_arabic(keyword)
        if not normalized:
            return re.compile(r"(?!x)x")  # never matches
        body = re.escape(normalized)
        # Boundary class is letters and digits only. The wider Arabic block
        # \u0600-\u06FF also contains punctuation such as "؟" (U+061F), which
        # made keywords at the end of a sentence fail to match.
        letters = r"A-Za-z\u0621-\u064A\u0660-\u0669\u06F0-\u06F9"
        return re.compile(
            r"(?<![" + letters + r"])"
            r"(?:ال|و|ف|ب|ل|ك)?" + body + r"(?![" + letters + r"])"
        )

    def match_counts(self, query: str) -> dict[Intent, int]:
        """Return how many keywords matched for each intent."""
        norm_query = normalize_arabic(query or "")
        counts: dict[Intent, int] = {}
        for intent, patterns in self._norm_keywords.items():
            count = sum(1 for p in patterns if p.search(norm_query))
            if count > 0:
                counts[intent] = count
        return counts

    @staticmethod
    def best_intent(counts: dict[Intent, int]) -> Intent | None:
        """Pick the winning intent.

        Match count decides first, so a query that mentions several fiqh terms
        beats a single incidental tool keyword. Priority only breaks ties,
        which is where specific tool intents outrank the general FIQH bucket.
        """
        if not counts:
            return None
        return max(counts, key=lambda intent: (counts[intent], INTENT_PRIORITY.get(intent, 0)))

    @staticmethod
    def _requests_calculation(intent: Intent, query: str) -> bool:
        """Return True when the query supplies a case for a deterministic tool.

        "ما هي أحكام زكاة عروض التجارة؟" matched ZAKAT and FIQH once each, so
        the tool intent won on priority and the calculator replied with a
        usage notice instead of an answer. Amounts are what the zakat
        calculator consumes, so a zakat question without a number is a
        knowledge question. An inheritance case can be described in words
        ("توفي وترك زوجة وأم"), so named heirs also count, unless the question
        asks for a ruling rather than a distribution.
        """
        normalized = normalize_arabic(query)
        if _DIGIT_RE.search(normalized):
            return True
        if any(cue in normalized for cue in _RULING_CUES):
            return False
        if intent is Intent.ZAKAT:
            return False
        tokens = {_strip_arabic_prefix(token) for token in _TOKEN_RE.findall(normalized)}
        return bool(tokens & _HEIR_TOKENS)

    def classify_sync(self, query: str) -> ClassificationResult:
        """Synchronous keyword classification.

        Kept separate from :meth:`classify` so synchronous callers, such as
        the legacy ``core.router`` wrapper, can reuse the same logic.
        """
        if not query or not query.strip():
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.50,
                language="ar",
                reasoning="Empty query.",
                requires_retrieval=True,
                method="keyword",
            )

        matches = self.match_counts(query)
        if not matches:
            # A zero confidence here used to disable the embedding tier in
            # MasterHybridClassifier, so nothing ever fell back.
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.30,
                language=detect_language(query),
                reasoning="No keywords matched; defaulted to general Islamic knowledge.",
                requires_retrieval=True,
                method="keyword",
            )

        intent = self.best_intent(matches)
        assert intent is not None  # matches is non-empty
        count = matches[intent]

        if intent in _CALCULATOR_INTENTS and not self._requests_calculation(intent, query):
            intent = Intent.FIQH
            count = matches.get(Intent.FIQH, 1)

        # Confidence based on match count
        confidence = 0.7 if count == 1 else (0.85 if count == 2 else 0.95)

        from src.domain.intents import (
            classify_quran_subintent,
            infer_requires_retrieval,
        )

        quran_subintent = None
        if intent is Intent.QURAN:
            quran_subintent, _ = classify_quran_subintent(query)

        return ClassificationResult(
            intent=intent,
            confidence=confidence,
            language=detect_language(query),
            reasoning=f"Matched {count} keywords for {intent.value}.",
            requires_retrieval=infer_requires_retrieval(intent, quran_subintent),
            quran_subintent=quran_subintent,
            method="keyword",
        )

    async def classify(self, query: str) -> ClassificationResult:
        """Classify based on keyword density and priority."""
        return self.classify_sync(query)


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

        # Confident keyword match wins without a semantic pass.
        # A weak or absent match falls through to the embedding tier.
        if kw_result.confidence >= self._low_conf:
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
                if emb_result.confidence >= kw_result.confidence:
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
