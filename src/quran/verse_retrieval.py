"""
Verse Retrieval Engine for Athar Islamic QA system.

Fixes:
  - lookup_by_name return type unified to list[dict]; lookup() handles both
  - search_verses fuzzy fallback covers all 6236 ayahs (removed offset < 3000 cap)
  - _format_ayah: optional columns guarded with getattr(..., None)
  - redundant `import re` inside method removed
  - search_verses: uses text_simple (diacritic-free) for LIKE, not text_uthmani
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah, Surah

logger = get_logger()

NAMED_VERSES_PATH = Path(__file__).parent / "named_verses.json"

# Compiled normalisation patterns (module-level)
_RE_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
_RE_ALEF       = re.compile(r"[أإآٱ]")


class VerseRetrievalError(Exception):
    """Base error for verse retrieval."""


class VerseNotFoundError(VerseRetrievalError):
    """Verse not found in database."""


class VerseRetrievalEngine:
    """
    Retrieves Quran verses from the database.

    Supported formats:
      "2:255"           → exact surah:ayah reference
      "Ayat al-Kursi"   → named verse lookup
      "البقرة 255"      → Arabic surah name + ayah number
      "Al-Baqarah 255"  → English surah name + ayah number
      "نور على نور"      → fuzzy text search (all 6236 ayahs)
    """

    def __init__(self, session: Session) -> None:
        self.session      = session
        self.named_verses = self._load_named_verses()

    # ── Named verse loader ────────────────────────────────────────────────────

    def _load_named_verses(self) -> dict:
        try:
            if NAMED_VERSES_PATH.exists():
                with open(NAMED_VERSES_PATH, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error("verse.named_verses_load_error", error=str(e))
        return {}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def lookup(
        self,
        reference: str,
        include_translation: bool = True,
    ) -> dict | list[dict]:
        """
        Auto-detect format and return verse(s).

        Returns:
          - dict       for single-verse lookups (number ref, name+number, fuzzy)
          - list[dict] for named verses that span a range (e.g. Al-Fatihah)

        Raises:
          VerseNotFoundError if nothing is found.
          VerseRetrievalError for unexpected errors.
        """
        try:
            # 1. "2:255"
            if self._is_number_reference(reference):
                return await self.lookup_by_number(reference, include_translation)

            # 2. Named verse → always returns list[dict]
            if self._is_named_verse(reference):
                return await self.lookup_by_name(reference, include_translation)

            # 3. "البقرة 255" / "Al-Baqarah 255"
            if self._is_name_number_reference(reference):
                return await self.lookup_by_name_and_number(reference, include_translation)

            # 4. Fuzzy text search
            results = await self.search_verses(reference, limit=1)
            if results:
                return results[0]

            raise VerseNotFoundError(f"Verse not found: {reference!r}")

        except VerseNotFoundError:
            raise
        except Exception as e:
            logger.error("verse.lookup_error", reference=reference, error=str(e), exc_info=True)
            raise VerseRetrievalError(f"Error looking up verse: {e}") from e

    async def lookup_by_number(
        self,
        reference: str,
        include_translation: bool = True,
    ) -> dict:
        """Look up a single ayah by "surah:ayah" reference."""
        match = re.match(r"(\d+)\s*[:\-]\s*(\d+)", reference)
        if not match:
            raise VerseNotFoundError(f"Invalid reference format: {reference!r}")

        surah_num = int(match.group(1))
        ayah_num  = int(match.group(2))

        ayah = (
            self.session.query(Ayah)
            .join(Surah)
            .filter(Surah.number == surah_num, Ayah.number_in_surah == ayah_num)
            .first()
        )

        if not ayah:
            raise VerseNotFoundError(f"Verse {reference!r} not found.")

        return self._format_ayah(ayah, include_translation)

    async def lookup_by_name(
        self,
        name: str,
        include_translation: bool = True,
    ) -> list[dict]:
        """
        Look up verse(s) by well-known name.

        Always returns list[dict] — may be 1 ayah (Ayat al-Kursi)
        or a full surah (Al-Fatihah).
        """
        name_key = name.lower().replace(" ", "_").replace("-", "_")

        for key, verse_data in self.named_verses.items():
            if key in name_key or name_key in key:
                surah_num = verse_data["surah"]

                if "ayah_range" in verse_data:
                    start, end = verse_data["ayah_range"]
                    return await self.lookup_surah_range(
                        surah_num, start, end, include_translation
                    )

                ayah_num = verse_data["ayah"]
                verse = await self.lookup_by_number(
                    f"{surah_num}:{ayah_num}", include_translation
                )
                return [verse]

        raise VerseNotFoundError(f"Named verse not found: {name!r}")

    async def lookup_by_name_and_number(
        self,
        reference: str,
        include_translation: bool = True,
    ) -> dict:
        """Look up ayah by surah name + ayah number ("البقرة 255")."""
        match = re.match(r"(.+?)\s+(\d+)$", reference.strip())
        if not match:
            raise VerseNotFoundError(f"Invalid reference: {reference!r}")

        surah_name = match.group(1).strip()
        ayah_num   = int(match.group(2))

        surah = self._find_surah_by_name(surah_name)
        if not surah:
            raise VerseNotFoundError(f"Surah not found: {surah_name!r}")

        ayah = (
            self.session.query(Ayah)
            .filter(Ayah.surah_id == surah.id, Ayah.number_in_surah == ayah_num)
            .first()
        )

        if not ayah:
            raise VerseNotFoundError(f"Verse {surah.number}:{ayah_num} not found.")

        return self._format_ayah(ayah, include_translation)

    async def lookup_surah_range(
        self,
        surah_number: int,
        start: int,
        end: int,
        include_translation: bool = True,
    ) -> list[dict]:
        """Return all ayahs in surah_number between start and end (inclusive)."""
        ayahs = (
            self.session.query(Ayah)
            .join(Surah)
            .filter(
                Surah.number == surah_number,
                Ayah.number_in_surah.between(start, end),
            )
            .order_by(Ayah.number_in_surah)
            .all()
        )
        return [self._format_ayah(a, include_translation) for a in ayahs]

    async def search_verses(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search all 6236 ayahs by text.

        Strategy:
          1. LIKE on text_simple (diacritic-free column) — fast index scan.
          2. If no results, normalise query + Python-side scan (full corpus).
             No artificial offset cap — searches all ayahs.
        """
        # Stage 1: DB-side LIKE on diacritic-free column
        ayahs = (
            self.session.query(Ayah)
            .filter(Ayah.text_simple.like(f"%{query}%"))
            .limit(limit)
            .all()
        )

        if ayahs:
            return [self._format_ayah(a, include_translation=False) for a in ayahs]

        # Stage 2: full normalised scan — covers all 6236 ayahs
        normalized_query = self._normalize_arabic(query)
        matching: list[Ayah] = []
        batch_size = 500
        offset     = 0

        while len(matching) < limit:
            batch: list[Ayah] = (
                self.session.query(Ayah)
                .order_by(Ayah.number)
                .limit(batch_size)
                .offset(offset)
                .all()
            )

            if not batch:
                break   # exhausted the full corpus

            for ayah in batch:
                if normalized_query in self._normalize_arabic(ayah.text_uthmani or ""):
                    matching.append(ayah)
                    if len(matching) >= limit:
                        break

            offset += batch_size

        return [self._format_ayah(a, include_translation=False) for a in matching]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_arabic(text: str) -> str:
        """Strip diacritics and unify alef/ya/ta-marbuta."""
        text = _RE_DIACRITICS.sub("", text)
        text = _RE_ALEF.sub("ا", text)
        text = text.replace("ة", "ه").replace("ى", "ي")
        return text

    def _find_surah_by_name(self, name: str) -> Surah | None:
        """Find surah by exact name, digit, or fuzzy contains."""
        # Exact match
        surah = (
            self.session.query(Surah)
            .filter(or_(Surah.name_ar == name, Surah.name_en == name))
            .first()
        )
        if surah:
            return surah

        # Digit → surah number
        if name.isdigit():
            return (
                self.session.query(Surah)
                .filter(Surah.number == int(name))
                .first()
            )

        # Fuzzy contains
        return (
            self.session.query(Surah)
            .filter(or_(Surah.name_ar.contains(name), Surah.name_en.contains(name)))
            .first()
        )

    def _format_ayah(self, ayah: Ayah, include_translation: bool = True) -> dict:
        """Serialize Ayah ORM object → plain dict."""
        result: dict[str, Any] = {
            "surah_number":  ayah.surah.number,
            "surah_name_ar": ayah.surah.name_ar,
            "surah_name_en": ayah.surah.name_en,
            "ayah_number":   ayah.number_in_surah,
            "text_uthmani":  ayah.text_uthmani,
            "text_simple":   getattr(ayah, "text_simple",   None),  # optional
            "juz":           getattr(ayah, "juz",           None),  # optional
            "page":          getattr(ayah, "page",          None),  # optional
            "hizb":          getattr(ayah, "hizb",          None),  # optional
            "rub_el_hizb":   getattr(ayah, "rub_el_hizb",  None),  # optional
            "sajdah":        getattr(ayah, "sajdah",        None),  # optional
            "quran_url": (
                f"https://quran.com/"
                f"{ayah.surah.number}/{ayah.number_in_surah}"
            ),
        }

        if include_translation and getattr(ayah, "translations", None):
            result["translations"] = [
                {
                    "language":   t.language,
                    "translator": t.translator,
                    "text":       t.text,
                }
                for t in ayah.translations
            ]

        return result

    # ── Format detectors ──────────────────────────────────────────────────────

    def _is_number_reference(self, ref: str) -> bool:
        return bool(re.match(r"^\d+\s*[:\-]\s*\d+$", ref.strip()))

    def _is_named_verse(self, ref: str) -> bool:
        key = ref.lower().replace(" ", "_").replace("-", "_")
        return any(k in key or key in k for k in self.named_verses)

    def _is_name_number_reference(self, ref: str) -> bool:
        # Must end with a number to avoid matching pure text queries
        return bool(re.match(r".+\s+\d+$", ref.strip()))