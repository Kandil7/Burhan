"""
Master Hybrid Intent Classifier for Athar Islamic QA system.

Orchestrates multiple classification tiers:
1. Keyword Fast-Path (High priority matches like "حكم", "ميراث")
2. Embedding Classifier (Phase 5 - Semantic similarity via BGE-M3)
3. Fallback
"""

from __future__ import annotations

import re
from typing import Any

from src.application.interfaces import IntentClassifier
from src.application.router.classifier_factory import KeywordBasedClassifier
from src.application.router.embedding_classifier import EmbeddingClassifier
from src.config.logging_config import get_logger
from src.domain.intents import (
    Intent,
    QuranSubIntent,
)
from src.domain.models import ClassificationResult

logger = get_logger()


# ============================================================================
# Utility functions (ported from deprecated hybrid_classifier.py)
# ============================================================================

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_LATIN_RE = re.compile(r"[a-zA-Z]")

_QUOTE_VALIDATE = [
    re.compile(r"صحيح|weak|sth|ضعيف", re.I),
    re.compile(r"آية \d+| ayat \d+", re.I),
]
_VERSE_SPECIFIC = [
    re.compile(r"آية|اية|ayat", re.I),
    re.compile(r"سورة|surah", re.I),
]
_SURAH_FULL = [
    re.compile(r"اقرأ لي| اقرأني|read.*to.?me", re.I),
    re.compile(r"الآية$|الايات$", re.I),
]
_QURAN_STATS = [
    re.compile(r"عدد|كم|how many", re.I),
    re.compile(r"آية|ايات|verses?|ayat", re.I),
]
_QURAN_INTERPRET = [
    re.compile(r"معنى|meaning|interpret|tafsir|تفسير", re.I),
    re.compile(r"شرح|explain", re.I),
]


def _detect_language(text: str) -> str:
    """Detect whether text is primarily Arabic, English, or mixed."""
    ar = len(_ARABIC_RE.findall(text))
    en = len(_LATIN_RE.findall(text))
    if ar == 0 and en == 0:
        return "ar"  # default for empty / numeric queries
    if ar > en:
        return "ar"
    if en > ar:
        return "en"
    return "mixed"


def _classify_quran_subintent(text: str) -> tuple[QuranSubIntent, float]:
    """Determine Quran sub-intent from raw (un-normalised) query text."""
    if any(p.search(text) for p in _QUOTE_VALIDATE):
        return QuranSubIntent.QUOTATION_VALIDATION, 0.95

    if any(p.search(text) for p in _VERSE_SPECIFIC):
        return QuranSubIntent.VERSE_LOOKUP, 0.95

    if any(p.search(text) for p in _SURAH_FULL):
        return QuranSubIntent.VERSE_LOOKUP, 0.90  # full surah → same pipeline

    if any(p.search(text) for p in _QURAN_STATS):
        return QuranSubIntent.ANALYTICS, 0.92

    if any(p.search(text) for p in _QURAN_INTERPRET):
        return QuranSubIntent.INTERPRETATION, 0.90

    return QuranSubIntent.INTERPRETATION, 0.60  # safe default


_ALWAYS_RETRIEVAL = {
    Intent.FIQH,
    Intent.ISLAMIC_KNOWLEDGE,
    Intent.HADITH,
    Intent.TAFSIR,
    Intent.AQEEDAH,
    Intent.SEERAH,
    Intent.USUL_FIQH,
    Intent.ISLAMIC_HISTORY,
    Intent.ARABIC_LANGUAGE,
}


def _infer_requires_retrieval(
    intent: Intent,
    sub: QuranSubIntent | None,
) -> bool:
    """Determine whether an intent requires document retrieval."""
    if intent in _ALWAYS_RETRIEVAL:
        return True
    if intent is Intent.QURAN:
        # Analytics queries are answered by NL2SQL — no RAG needed
        return sub is not QuranSubIntent.ANALYTICS
    return False


# ============================================================================
# Hybrid Classifiers
# ============================================================================


class MasterHybridClassifier(IntentClassifier):
    """
    Consolidated Hybrid Classifier combining Keyword and Semantic tiers.
    """

    def __init__(self, embedding_model: Any = None, low_conf_threshold: float = 0.65) -> None:
        """
        Initialize the multi-tier classifier.
        """
        self._low_conf = low_conf_threshold
        self._keyword_classifier = KeywordBasedClassifier()
        self._embedding_classifier = None
        if embedding_model:
            self._embedding_classifier = EmbeddingClassifier(embedding_model)

    async def classify(self, query: str) -> ClassificationResult:
        """
        Run classification tiers in order.
        """
        logger.info("hybrid_classifier.classify_start", query=query[:50])
        if not query or not query.strip():
            return await self._keyword_classifier.classify("")

        # ── Tier 1: Keyword Fast-Path ────────────────────────────────────
        kw_result = await self._keyword_classifier.classify(query)
        logger.debug("hybrid_classifier.keyword_result", intent=kw_result.intent.value, confidence=kw_result.confidence)

        # If keyword match exists (even with low confidence), use it - NEVER override with embedding
        # This ensures seerah/hijra keywords like "هجرة" work correctly
        if kw_result.confidence > 0.0:
            logger.info("hybrid_classifier.keyword_win", intent=kw_result.intent.value, confidence=kw_result.confidence)
            return kw_result

        # ── Tier 2: Semantic (Embedding) ─────────────────────────────────
        # Only reach here if NO keywords matched at all
        logger.debug("hybrid_classifier.trying_embedding", present=self._embedding_classifier is not None)
        if self._embedding_classifier:
            try:
                emb_result = await self._embedding_classifier.classify(query)
                logger.info(
                    "hybrid_classifier.embedding_result",
                    intent=emb_result.intent.value,
                    confidence=emb_result.confidence,
                )

                # No keywords found - use embedding result
                logger.info("hybrid_classifier.embedding_only_win", intent=emb_result.intent.value)
                return emb_result

                # If embedding result is strong, it can override weak keyword
                if emb_result.confidence >= 0.65:
                    logger.info("hybrid_classifier.embedding_override_win", intent=emb_result.intent.value)
                    return emb_result

                # If both are weak, pick the highest confidence
                if emb_result.confidence > kw_result.confidence:
                    logger.info("hybrid_classifier.embedding_higher_win", intent=emb_result.intent.value)
                    return emb_result
            except Exception as e:
                logger.error("hybrid_classifier.embedding_failed", error=str(e), exc_info=True)

        # ── Tier 3: Return Keyword Result (even if weak/default) ──────────
        logger.info("hybrid_classifier.fallback_to_keyword", intent=kw_result.intent.value)
        return kw_result

    async def close(self) -> None:
        """Clean up resources."""
        if self._embedding_classifier:
            await self._embedding_classifier.close()


# Alias for backward compatibility
HybridIntentClassifier = MasterHybridClassifier


__all__ = [
    "MasterHybridClassifier",
    "HybridIntentClassifier",
    "_detect_language",
    "_classify_quran_subintent",
    "_infer_requires_retrieval",
]
