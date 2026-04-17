"""
Hybrid Intent Classifier for Athar Islamic QA system.

Implements a two-tier classification approach:
1. Keyword fast-path — scans KEYWORD_PATTERNS, picks highest-priority match
2. Jaccard fallback — lexical token overlap (morphology-unaware; Phase 5 upgrade)

This replaces the previous LLM-only classifier with a fast, accurate hybrid approach.
Phase 5 upgrade: Replace _jaccard_fallback() with EmbeddingClassifier.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from src.domain.intents import (
    INTENT_PRIORITY,
    INTENT_ROUTING,
    KEYWORD_PATTERNS,
    Intent,
    QuranSubIntent,
)
from src.domain.models import ClassificationResult
from src.application.interfaces import IntentClassifier


# ============================================================================
# Pre-compiled regex helpers
# ============================================================================

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_LATIN_RE = re.compile(r"[A-Za-z]")

# Quran sub-intent patterns (applied on un-normalised text for digit matching)
_VERSE_SPECIFIC = [
    re.compile(r"سور[ةه]\s+\S+\s+آي[ةه]\s+\d+"),
    re.compile(r"آي[ةه]\s+\d+"),
    re.compile(r"surah\s+[a-z0-9\-]+\s+verse\s+\d+", re.I),
    re.compile(r"ayah\s+\d+", re.I),
    re.compile(r"\b\d+\s*[:/]\s*\d+\b"),  # 2:255 or 2/255
]

_SURAH_FULL = [
    re.compile(r"سور[ةه]\s+\S+\s+كامل[ةه]?"),
    re.compile(r"اكتب\s+سور[ةه]"),
    re.compile(r"entire\s+surah", re.I),
    re.compile(r"full\s+surah", re.I),
]

_QURAN_STATS = [
    re.compile(r"كم\s+عدد\s+آي[ةه]?ات?"),
    re.compile(r"عدد\s+آي[ةه]?ات?"),
    re.compile(r"how many verses", re.I),
    re.compile(r"which surah has the most", re.I),
    re.compile(r"\b(makki|madani)\b", re.I),
]

_QURAN_INTERPRET = [
    re.compile(r"ما\s+معنى"),
    re.compile(r"فسّر|فسر|تفسير"),
    re.compile(r"what is the meaning", re.I),
    re.compile(r"interpretation|explain", re.I),
]

_QUOTE_VALIDATE = [
    re.compile(r"هل هذه آية"),
    re.compile(r"هل هذا من القرآن"),
    re.compile(r"is this (a|in the) quran", re.I),
    re.compile(r"verify.*quran", re.I),
]


# ============================================================================
# Text utilities
# ============================================================================


def _normalize(text: str) -> str:
    """
    Normalise Arabic text for keyword matching:
    - Strip diacritics (tashkeel)
    - Unify alef variants → ا
    - Collapse repeated spaces
    NOTE: We intentionally do NOT convert ة→ه or ى→ي here,
    because KEYWORD_PATTERNS uses the standard orthography.
    """
    text = text.strip().lower()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # tashkeel
    text = re.sub(r"[\u0622\u0623\u0625\u0671]", "\u0627", text)  # alef variants → ا
    text = re.sub(r"[^\w\s:،؟!/.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _detect_language(text: str) -> str:
    ar = len(_ARABIC_RE.findall(text))
    en = len(_LATIN_RE.findall(text))
    if ar == 0 and en == 0:
        return "ar"  # default for empty / numeric queries
    if ar > en:
        return "ar"
    if en > ar:
        return "en"
    return "mixed"


def _tokenize(text: str) -> List[str]:
    return [t for t in _normalize(text).split() if t]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ============================================================================
# Quran sub-intent classifier
# ============================================================================


def _classify_quran_subintent(text: str) -> Tuple[QuranSubIntent, float]:
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


# ============================================================================
# Business rules: requires_retrieval
# ============================================================================

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
    sub: Optional[QuranSubIntent],
) -> bool:
    if intent in _ALWAYS_RETRIEVAL:
        return True
    if intent is Intent.QURAN:
        # Analytics queries are answered by NL2SQL — no RAG needed
        return sub is not QuranSubIntent.ANALYTICS
    return False


# ============================================================================
# HybridIntentClassifier
# ============================================================================


class HybridIntentClassifier(IntentClassifier):
    """
    Phase-1 hybrid classifier (keyword fast-path + Jaccard fallback).

    Classification pipeline:
    1. keyword fast-path  → scans KEYWORD_PATTERNS, picks highest-priority match
    2. Jaccard fallback   → lexical token overlap (morphology-unaware; Phase 5 upgrade)

    The LLM and Embedding classifiers are separate classes conforming to
    the IntentClassifier protocol and are injected by RouterAgent in later phases.

    Phase 5 upgrade path:
        Replace _jaccard_fallback() with an EmbeddingClassifier injected via DI.
    """

    def __init__(self, low_conf_threshold: float = 0.55) -> None:
        """
        Initialize the hybrid classifier.

        Args:
            low_conf_threshold: Minimum confidence for classification (default: 0.55)
        """
        self._low_conf = low_conf_threshold
        # Pre-normalise all keyword patterns for fast matching
        self._norm_patterns: Dict[Intent, List[Tuple[str, str]]] = {
            intent: [(kw, _normalize(kw)) for kw in patterns] for intent, patterns in KEYWORD_PATTERNS.items()
        }

    async def classify(self, query: str) -> ClassificationResult:
        """
        Classify a query string into a ClassificationResult.

        Classification pipeline:
        1. Keyword fast-path → scans KEYWORD_PATTERNS, picks highest-priority match
        2. Jaccard fallback → lexical token overlap
        """
        if not query or not query.strip():
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.50,
                language="ar",
                reasoning="Empty query — defaulted to general Islamic knowledge.",
                requires_retrieval=False,
                method="fallback",
            )

        norm = _normalize(query)
        lang = _detect_language(query)

        # ── Step 1: keyword fast-path ────────────────────────────────────
        kw_result = self._fast_path(norm)

        if kw_result is not None:
            intent, confidence, matched_kw = kw_result
            q_sub: Optional[QuranSubIntent] = None
            reasoning = f"Keyword fast-path matched: '{matched_kw}'"

            if intent is Intent.QURAN:
                q_sub, q_conf = _classify_quran_subintent(query)
                confidence = max(confidence, q_conf)
                reasoning += f" | Quran sub-intent: {q_sub.value}"

            return ClassificationResult(
                intent=intent,
                confidence=round(confidence, 4),
                language=lang,
                reasoning=reasoning,
                requires_retrieval=_infer_requires_retrieval(intent, q_sub),
                method="keyword",
                quran_subintent=q_sub,
                subquestions=[],
            )

        # ── Step 2: Jaccard fallback ─────────────────────────────────────
        intent, confidence, reasoning = self._jaccard_fallback(norm)

        q_sub = None
        if intent is Intent.QURAN:
            q_sub, q_conf = _classify_quran_subintent(query)
            confidence = max(confidence, q_conf)
            reasoning += f" | Quran sub-intent: {q_sub.value}"

        return ClassificationResult(
            intent=intent,
            confidence=round(confidence, 4),
            language=lang,
            reasoning=reasoning,
            requires_retrieval=_infer_requires_retrieval(intent, q_sub),
            method="embedding",  # labelled "embedding" as placeholder for Phase 5
            quran_subintent=q_sub,
            subquestions=[],
        )

    async def close(self) -> None:
        """Clean up resources (no-op for this classifier)."""
        pass

    # ============================================================================
    # Private helpers
    # ============================================================================

    def _fast_path(self, norm: str) -> Optional[Tuple[Intent, float, str]]:
        """
        Scan normalised keyword patterns.

        Returns the highest-priority (intent, confidence, matched_keyword) tuple,
        or None if no keyword matched.
        """
        matches: List[Tuple[int, Intent, str]] = []

        for intent, kw_pairs in self._norm_patterns.items():
            for raw_kw, norm_kw in kw_pairs:
                if norm_kw in norm:
                    priority = INTENT_PRIORITY.get(intent, 0)
                    matches.append((priority, intent, raw_kw))

        if not matches:
            return None

        matches.sort(key=lambda x: x[0], reverse=True)
        _, best_intent, matched_kw = matches[0]
        return best_intent, 0.90, matched_kw

    def _jaccard_fallback(self, norm: str) -> Tuple[Intent, float, str]:
        """
        Lexical similarity fallback using Jaccard on token sets.

        ⚠ Phase 1 limitation: does not handle Arabic morphology.
          e.g. "صلاته" vs "صلاة" will NOT match.
          Will be replaced by Qwen3-Embedding cosine similarity in Phase 5.
        """
        tokens = _tokenize(norm)
        best_intent: Optional[Intent] = None
        best_score = 0.0
        best_kw = ""

        for intent, kw_pairs in self._norm_patterns.items():
            for _, norm_kw in kw_pairs:
                score = _jaccard(tokens, _tokenize(norm_kw))
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    best_kw = norm_kw

        if best_intent is None or best_score < 0.05:
            return (
                Intent.ISLAMIC_KNOWLEDGE,
                0.50,
                "No keyword or similarity match — defaulted to general Islamic knowledge.",
            )

        # Map raw Jaccard [0,1] to confidence [0.4, 0.85]
        confidence = round(max(0.40, min(0.85, best_score + 0.40)), 4)
        return (
            best_intent,
            confidence,
            f"Jaccard similarity match on '{best_kw}' (score={best_score:.3f})",
        )
