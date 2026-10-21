"""
Quotation Validation Engine for Burhan Islamic QA system.

v3 — Complete file (no partial snippets):
  - candidates fetched once per validate() call
  - text_uthmani replaces text_simple (hamza-safe output)
  - text_simple used for DB filtering (diacritics-free LIKE)
  - suggestion uses normalized length comparison
  - _check_* sync helpers replace async _find_* triplets
"""

from __future__ import annotations

import asyncio
import re
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah

logger = get_logger()

_ARABIC_RE = re.compile(r"[\u064B-\u065F]")
_ALEF_RE = re.compile(r"[أإآٱ]")
_YA_RE = re.compile(r"ى")
_TA_MARBUTA_RE = re.compile(r"ة")
_TATWEEL_RE = re.compile("\u0640")
_SUPERSCRIPT_ALEF_RE = re.compile("\u0670")
_NON_ARABIC_RE = re.compile(r"[^\u0600-\u06FF\s]")
_SPACES_RE = re.compile(r"\s+")

_MIN_INPUT_LEN = 5


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for comparison:
      - Expand superscript alef (U+0670) to a full alef
      - Remove diacritics (tashkeel) and tatweel
      - Unify alef variants → ا
      - Unify ya variants  → ي
      - Unify ta marbuta   → ه
      - Remove non-Arabic  (preserve spaces)
      - Collapse whitespace
    """
    if not text:
        return ""
    text = _SUPERSCRIPT_ALEF_RE.sub("ا", text)
    text = _ARABIC_RE.sub("", text)
    text = _ALEF_RE.sub("ا", text)
    text = _YA_RE.sub("ي", text)
    text = _TA_MARBUTA_RE.sub("ه", text)
    text = _TATWEEL_RE.sub("", text)
    text = _NON_ARABIC_RE.sub("", text)
    text = _SPACES_RE.sub(" ", text)
    return text.strip()


def _skeleton(text: str) -> str:
    """
    Comparison form: normalized Arabic with long alefs removed.

    Uthmani script marks some long alefs with a superscript alef (U+0670),
    and modern spelling varies (الرحمن vs الرحمان, العالمين vs العلمين).
    Dropping long alefs on both sides makes matching insensitive to that.
    """
    return normalize_arabic(text).replace("ا", "")


def _match_text(ayah: Ayah) -> str:
    """Text used for comparison: the diacritics-free column when present."""
    return str(ayah.text_simple or ayah.text_uthmani or "")


def _skeleton_sql(column: Any) -> Any:
    """
    SQL mirror of :func:`_skeleton`, with whitespace removed.

    Both sides must apply the same replacements, otherwise a stored verse that
    uses tatweel, alef maksura, or a hamza carrier never matches the Python
    skeleton of user input. Whitespace is dropped on both sides so that
    removing tatweel cannot leave a double space that breaks containment.
    """
    expr = func.replace(column, "\u0670", "\u0627")  # superscript alef → alef
    for variant in ("\u0622", "\u0623", "\u0625", "\u0671"):  # آ أ إ ٱ → ا
        expr = func.replace(expr, variant, "\u0627")
    expr = func.replace(expr, "\u0649", "\u064a")  # ى → ي
    expr = func.replace(expr, "\u0629", "\u0647")  # ة → ه
    expr = func.replace(expr, "\u0640", "")  # tatweel
    for mark in range(0x064B, 0x0660):  # tashkeel
        expr = func.replace(expr, chr(mark), "")
    expr = func.replace(expr, "\u0627", "")  # skeleton: drop long alefs
    return func.replace(expr, " ", "")


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

    def __init__(
        self,
        session: Session,
        similarity_threshold: float = 0.85,
    ) -> None:
        self.session = session
        self.threshold = similarity_threshold

    # ── Public API ──────────────────────────────────────────────────────────

    async def validate(self, text: str) -> dict:
        if not text or not text.strip():
            return {
                "is_quran": False,
                "confidence": 0.0,
                "matched_ayah": None,
                "suggestion": "No text provided",
            }

        normalized = self.normalize_arabic(text)

        if len(normalized) < _MIN_INPUT_LEN:
            return {
                "is_quran": False,
                "confidence": 0.0,
                "matched_ayah": None,
                "suggestion": "النص قصير جداً للتحقق — أدخل على الأقل كلمتين.",
            }

        # Single DB round-trip — shared by all three matchers
        candidates = await asyncio.to_thread(self._get_candidates, normalized)

        # 1. Exact match
        exact = self._check_exact(normalized, candidates)
        if exact:
            return {
                "is_quran": True,
                "confidence": 1.0,
                "matched_ayah": exact,
                "suggestion": None,
            }

        # 2. Fragment / containment match
        fragment = self._check_fragment(normalized, candidates)
        if fragment:
            matched = fragment["ayah"]
            norm_ayah = self.normalize_arabic(matched.get("text_simple") or matched["text_uthmani"])
            is_partial = len(normalized) < len(norm_ayah) * 0.9
            return {
                "is_quran": True,
                "confidence": fragment["confidence"],
                "matched_ayah": fragment["ayah"],
                "suggestion": (f"النص جزء من: {fragment['ayah']['text_uthmani'][:60]}…" if is_partial else None),
            }

        # 3. Fuzzy match
        fuzzy = self._check_fuzzy(normalized, candidates)
        if fuzzy:
            return {
                "is_quran": True,
                "confidence": fuzzy["similarity"],
                "matched_ayah": fuzzy["ayah"],
                "suggestion": f"Did you mean: {fuzzy['ayah']['text_uthmani']}",
            }

        return {
            "is_quran": False,
            "confidence": 0.0,
            "matched_ayah": None,
            "suggestion": "This text does not match any Quranic verse.",
        }

    # ── Normalization ────────────────────────────────────────────────────────

    def normalize_arabic(self, text: str) -> str:
        """Delegate to the module-level normalizer so seeding and validation agree."""
        return normalize_arabic(text)

    # ── Database ─────────────────────────────────────────────────────────────

    def _get_candidates(
        self,
        normalized_text: str,
        limit: int = 50,
    ) -> list[Ayah]:
        """
        Fetch ayah candidates whose diacritics-free skeleton contains the input.

        The containment query runs first because it is precise: a verbatim or
        partial quote is found directly. Only when it finds nothing does the
        word filter run, which is what keeps the fuzzy matcher working when the
        user mistypes a word.
        """
        skeleton = _skeleton(normalized_text)
        if not skeleton:
            return []

        pattern = skeleton.replace(" ", "")
        skeleton_column = _skeleton_sql(func.coalesce(Ayah.text_simple, ""))
        base = self.session.query(Ayah).options(joinedload(Ayah.surah))

        contained = (
            base.filter(skeleton_column.contains(pattern, autoescape=True)).order_by(Ayah.number).limit(limit).all()
        )
        if contained:
            return contained

        words = sorted({w for w in skeleton.split() if len(w) >= 3}, key=len, reverse=True)[:3]
        if not words:
            words = [skeleton[:6]]

        query = base
        for word in words:
            query = query.filter(skeleton_column.contains(word, autoescape=True))
        return query.order_by(Ayah.number).limit(limit).all()

    # ── Matchers (sync — candidates pre-fetched) ─────────────────────────────

    def _check_exact(
        self,
        normalized_text: str,
        candidates: list[Ayah],
    ) -> dict | None:
        target = _skeleton(normalized_text)
        for ayah in candidates:
            if _skeleton(_match_text(ayah)) == target:
                return self._ayah_to_dict(ayah)
        return None

    def _check_fragment(
        self,
        normalized_text: str,
        candidates: list[Ayah],
    ) -> dict | None:
        """
        Detects partial ayah input (most common user pattern).
        Two tiers:
          confidence=1.0  — exact substring after normalization
          confidence=0.95 — substring after space-stripping
                            (waw-attachment edge case)
        """
        target = _skeleton(normalized_text)
        target_nospace = target.replace(" ", "")
        for ayah in candidates:
            ayah_norm = _skeleton(_match_text(ayah))
            if target in ayah_norm:
                return {
                    "confidence": 1.0,
                    "ayah": self._ayah_to_dict(ayah),
                }
            if target_nospace in ayah_norm.replace(" ", ""):
                return {
                    "confidence": 0.95,
                    "ayah": self._ayah_to_dict(ayah),
                }
        return None

    def _check_fuzzy(
        self,
        normalized_text: str,
        candidates: list[Ayah],
    ) -> dict | None:
        """
        Ratcliff/Obershelp similarity for typo-tolerant full-ayah matching.
        Threshold configurable via __init__ (default 0.85).
        """
        best_score: float = 0.0
        best_match: dict | None = None
        target = _skeleton(normalized_text)
        for ayah in candidates:
            ayah_norm = _skeleton(_match_text(ayah))
            similarity = SequenceMatcher(None, target, ayah_norm).ratio()
            if similarity > best_score and similarity >= self.threshold:
                best_score = similarity
                best_match = {
                    "similarity": similarity,
                    "ayah": self._ayah_to_dict(ayah),
                }
        return best_match

    # ── Helper ────────────────────────────────────────────────────────────────

    def _ayah_to_dict(self, ayah: Ayah) -> dict:
        """
        Convert Ayah ORM object to plain dict.

        Matches ``AyahResponse`` so the result can be returned directly by the
        API. Accesses ayah.surah once (must be eagerly loaded via joinedload).
        """
        surah = ayah.surah
        return {
            "surah_number": surah.number,
            "surah_name_en": surah.name_en,
            "surah_name_ar": getattr(surah, "name_ar", ""),
            "ayah_number": ayah.number_in_surah,
            "text_uthmani": ayah.text_uthmani,
            "text_simple": ayah.text_simple,
            "juz": ayah.juz,
            "page": ayah.page,
            "quran_url": (f"https://quran.com/{surah.number}/{ayah.number_in_surah}"),
            "translations": None,
        }


__all__ = ["QuotationValidator", "QuotationValidatorError", "normalize_arabic"]
