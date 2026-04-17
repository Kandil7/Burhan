"""
Quotation Validation Engine for Athar Islamic QA system.

v3 — Complete file (no partial snippets):
  - candidates fetched once per validate() call
  - text_uthmani replaces text_simple (hamza-safe)
  - suggestion uses normalized length comparison
  - _check_* sync helpers replace async _find_* triplets
"""
from __future__ import annotations

import asyncio
import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session, joinedload

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah

logger = get_logger()

_ARABIC_RE     = re.compile(r"[\u064B-\u065F\u0670]")
_ALEF_RE       = re.compile(r"[أإآٱ]")
_YA_RE         = re.compile(r"ى")
_TA_MARBUTA_RE = re.compile(r"ة")
_NON_ARABIC_RE = re.compile(r"[^\u0600-\u06FF\s]")
_SPACES_RE     = re.compile(r"\s+")

_MIN_INPUT_LEN = 5


class QuotationValidatorError(Exception):
    """Error in quotation validation."""


class QuotationValidator:
    """
    Validates whether user-provided text is from the Quran.

    Pipeline per request (single DB round-trip):
      normalize → _get_candidates → _check_exact
                                  → _check_fragment
                                  → _check_fuzzy
    """

    def __init__(self, session: Session, similarity_threshold: float = 0.85) -> None:
        self.session   = session
        self.threshold = similarity_threshold

    # ── Public API ──────────────────────────────────────────────────────────

    async def validate(self, text: str) -> dict:
        if not text or not text.strip():
            return {
                "is_quran": False, "confidence": 0.0,
                "matched_ayah": None, "suggestion": "No text provided",
            }

        normalized = self.normalize_arabic(text)

        if len(normalized) < _MIN_INPUT_LEN:
            return {
                "is_quran": False, "confidence": 0.0,
                "matched_ayah": None,
                "suggestion": "النص قصير جداً للتحقق — أدخل على الأقل كلمتين.",
            }

        # Single DB round-trip — shared by all three matchers
        candidates = await asyncio.to_thread(self._get_candidates, normalized)

        # 1. Exact match
        exact = self._check_exact(normalized, candidates)
        if exact:
            return {
                "is_quran": True, "confidence": 1.0,
                "matched_ayah": exact, "suggestion": None,
            }

        # 2. Fragment / containment match
        fragment = self._check_fragment(normalized, candidates)
        if fragment:
            norm_ayah = self.normalize_arabic(fragment["ayah"]["text_uthmani"])
            is_partial = len(normalized) < len(norm_ayah) * 0.9
            return {
                "is_quran":     True,
                "confidence":   fragment["confidence"],
                "matched_ayah": fragment["ayah"],
                "suggestion": (
                    f"النص جزء من: {fragment['ayah']['text_uthmani'][:60]}…"
                    if is_partial else None
                ),
            }

        # 3. Fuzzy match
        fuzzy = self._check_fuzzy(normalized, candidates)
        if fuzzy:
            return {
                "is_quran":     True,
                "confidence":   fuzzy["similarity"],
                "matched_ayah": fuzzy["ayah"],
                "suggestion":   f"Did you mean: {fuzzy['ayah']['text_uthmani']}",
            }

        return {
            "is_quran": False, "confidence": 0.0,
            "matched_ayah": None,
            "suggestion": "This text does not match any Quranic verse.",
        }

    # ── Normalization ────────────────────────────────────────────────────────

    def normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for comparison:
          - Remove diacritics (tashkeel)
          - Unify alef variants → ا
          - Unify ya variants  → ي
          - Unify ta marbuta   → ه
          - Remove non-Arabic  (preserve spaces)
          - Collapse whitespace
        """
        if not text:
            return ""
        text = _ARABIC_RE.sub("", text)
        text = _ALEF_RE.sub("ا", text)
        text = _YA_RE.sub("ي", text)
        text = _TA_MARBUTA_RE.sub("ه", text)
        text = _NON_ARABIC_RE.sub("", text)
        text = _SPACES_RE.sub(" ", text)
        return text.strip()

    # ── Database ─────────────────────────────────────────────────────────────

    def _get_candidates(self, normalized_text: str, limit: int = 50) -> list[Ayah]:
        """
        Fetch ayah candidates using text_uthmani (not text_simple).
        text_uthmani retains original hamza letters under diacritics,
        so LIKE '%ابراهيم%' correctly finds 'إِبْرَاهِيم'.

        Uses longest words (≥4 chars) as AND-filter for precision.
        """
        words = [w for w in normalized_text.split() if len(w) >= 4][:2]
        if not words:
            words = [normalized_text[:6]]

        q = self.session.query(Ayah).options(joinedload(Ayah.surah))
        for word in words:
            q = q.filter(Ayah.text_uthmani.contains(word))
        return q.limit(limit).all()

    # ── Matchers (sync — candidates pre-fetched) ─────────────────────────────

    def _check_exact(
        self, normalized_text: str, candidates: list[Ayah]
    ) -> dict | None:
        for ayah in candidates:
            if self.normalize_arabic(ayah.text_uthmani) == normalized_text:
                return self._ayah_to_dict(ayah)
        return None

    def _check_fragment(
        self, normalized_text: str, candidates: list[Ayah]
    ) -> dict | None:
        """
        Detects partial ayah input (most common user pattern).
        Two tiers:
          confidence=1.0 — exact substring after normalization
          confidence=0.95 — substring after space-stripping (waw-attachment edge case)
        """
        for ayah in candidates:
            ayah_norm = self.normalize_arabic(ayah.text_uthmani)
            if normalized_text in ayah_norm:
                return {"confidence": 1.0, "ayah": self._ayah_to_dict(ayah)}
            if normalized_text.replace(" ", "") in ayah_norm.replace(" ", ""):
                return {"confidence": 0.95, "ayah": self._ayah_to_dict(ayah)}
        return None

    def _check_fuzzy(
        self, normalized_text: str, candidates: list[Ayah]
    ) -> dict | None:
        """
        Ratcliff/Obershelp similarity for typo-tolerant full-ayah matching.
        Threshold configurable via __init__ (default 0.85).
        """
        best_score: float = 0.0
        best_match: dict | None = None
        for ayah in candidates:
            ayah_norm  = self.normalize_arabic(ayah.text_uthmani)
            similarity = SequenceMatcher(None, normalized_text, ayah_norm).ratio()
            if similarity > best_score and similarity >= self.threshold:
                best_score = similarity
                best_match = {
                    "similarity": similarity,
                    "ayah":       self._ayah_to_dict(ayah),
                }
        return best_match

    # ── Helper ────────────────────────────────────────────────────────────────

    def _ayah_to_dict(self, ayah: Ayah) -> dict:
        return {
            "surah_number":  ayah.surah.number,
            "surah_name_en": ayah.surah.name_en,
            "ayah_number":   ayah.number_in_surah,
            "text_uthmani":  ayah.text_uthmani,
            "quran_url":     f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}",
        }


__all__ = ["QuotationValidator", "QuotationValidatorError"]