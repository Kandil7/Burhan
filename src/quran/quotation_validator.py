"""
Quotation Validation Engine for Athar Islamic QA system.

Fixes:
  - _calculate_similarity: SequenceMatcher (Ratcliff/Obershelp) replaces broken char-in-text
  - _find_exact_match: searches on normalized column or applies normalization in Python
  - normalize_arabic: preserves spaces (removed only duplicate spaces)
  - aliases: corrected typos
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah

logger = get_logger()

# Arabic character ranges
_ARABIC_RE     = re.compile(r"[\u064B-\u065F\u0670]")   # diacritics
_ALEF_RE       = re.compile(r"[أإآٱ]")
_YA_RE         = re.compile(r"ى")
_TA_MARBUTA_RE = re.compile(r"ة")
_NON_ARABIC_RE = re.compile(r"[^\u0600-\u06FF\s]")      # keeps spaces
_SPACES_RE     = re.compile(r"\s+")


class QuotationValidatorError(Exception):
    """Error in quotation validation."""


class QuotationValidator:
    """
    Validates whether user-provided text is from the Quran.

    Uses SequenceMatcher (difflib) for similarity — avoids the false-positive
    trap of character-membership checks on Arabic text.

    Similarity threshold 0.85 is conservative; lower to 0.75 for more lenient matching.
    """

    def __init__(self, session: Session, similarity_threshold: float = 0.85) -> None:
        self.session   = session
        self.threshold = similarity_threshold

    # ── Public API ────────────────────────────────────────────────────────────

    async def validate(self, text: str) -> dict:
        """
        Returns:
            {
                "is_quran": bool,
                "confidence": float,
                "matched_ayah": dict | None,
                "suggestion": str | None,
            }
        """
        if not text or not text.strip():
            return {
                "is_quran": False, "confidence": 0.0,
                "matched_ayah": None, "suggestion": "No text provided",
            }

        normalized = self.normalize_arabic(text)

        # 1. Exact match (after normalization)
        exact = await self._find_exact_match(normalized)
        if exact:
            return {
                "is_quran": True, "confidence": 1.0,
                "matched_ayah": exact, "suggestion": None,
            }

        # 2. Fuzzy match
        fuzzy = await self._find_fuzzy_match(normalized, self.threshold)
        if fuzzy:
            return {
                "is_quran":    True,
                "confidence":  fuzzy["similarity"],
                "matched_ayah": fuzzy["ayah"],
                "suggestion":  f"Did you mean: {fuzzy['ayah']['text_uthmani']}",
            }

        return {
            "is_quran": False, "confidence": 0.0,
            "matched_ayah": None,
            "suggestion": "This text does not match any Quranic verse.",
        }

    # ── Normalization ─────────────────────────────────────────────────────────

    def normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for comparison:
        - Remove diacritics (tashkeel)
        - Unify alef variants → ا
        - Unify ya variants → ي
        - Unify ta marbuta → ه  (applied to BOTH sides when comparing)
        - Remove non-Arabic characters (keeps spaces)
        - Collapse multiple spaces
        """
        if not text:
            return ""
        text = _ARABIC_RE.sub("", text)        # remove diacritics
        text = _ALEF_RE.sub("ا", text)         # alef variants → ا
        text = _YA_RE.sub("ي", text)           # ى → ي
        text = _TA_MARBUTA_RE.sub("ه", text)   # ة → ه
        text = _NON_ARABIC_RE.sub("", text)    # keep Arabic + spaces
        text = _SPACES_RE.sub(" ", text)       # collapse spaces
        return text.strip()

    # ── Database search ───────────────────────────────────────────────────────

    async def _find_exact_match(self, normalized_text: str) -> dict | None:
        """
        Fetch candidate ayahs by token-based search, then normalize in Python
        and check for exact match.

        Note: text_uthmani in the DB has full tashkeel — we cannot do a direct
        contains() on normalized_text. Instead we fetch candidates by word tokens
        and re-normalize before comparing.
        """
        # Use the first non-trivial word (≥3 chars) as a DB filter
        words       = [w for w in normalized_text.split() if len(w) >= 3]
        search_word = words[0] if words else normalized_text[:6]

        candidates = (
            self.session.query(Ayah)
            .filter(Ayah.text_simple.contains(search_word))  # text_simple = diacritic-free
            .limit(20)
            .all()
        )

        for ayah in candidates:
            if self.normalize_arabic(ayah.text_uthmani) == normalized_text:
                return self._ayah_to_dict(ayah)

        return None

    async def _find_fuzzy_match(
        self, normalized_text: str, threshold: float
    ) -> dict | None:
        """
        Fetch candidates via LIKE on text_simple, then rank by SequenceMatcher similarity.
        Returns the best match above threshold, or None.
        """
        words      = [w for w in normalized_text.split() if len(w) >= 3]
        search_tok = words[0] if words else normalized_text[:6]

        candidates = (
            self.session.query(Ayah)
            .filter(Ayah.text_simple.like(f"%{search_tok}%"))
            .limit(30)
            .all()
        )

        best_score: float = 0.0
        best_match: dict | None = None

        for ayah in candidates:
            ayah_norm  = self.normalize_arabic(ayah.text_uthmani)
            similarity = self._calculate_similarity(normalized_text, ayah_norm)

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = {
                    "similarity": similarity,
                    "ayah":       self._ayah_to_dict(ayah),
                }

        return best_match

    # ── Similarity ────────────────────────────────────────────────────────────

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Similarity using difflib.SequenceMatcher (Ratcliff/Obershelp algorithm).

        Replaces the broken character-membership approach that produced false
        positives on any two Arabic texts sharing common letters.

        Returns 0.0–1.0. Two identical strings → 1.0.
        """
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()  # [web:8]

    # ── Helper ────────────────────────────────────────────────────────────────

    def _ayah_to_dict(self, ayah: Ayah) -> dict:
        return {
            "surah_number":  ayah.surah.number,
            "surah_name_en": ayah.surah.name_en,
            "ayah_number":   ayah.number_in_surah,
            "text_uthmani":  ayah.text_uthmani,
            "quran_url":     f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}",
        }


# Backwards-compatibility aliases (corrected typos)
QuotationValidatorError = QuotationValidatorError  # noqa: F811 (re-export)