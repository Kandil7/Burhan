"""
Verse Retrieval Engine for Burhan Islamic QA system.

This module provides a class for retrieving verses from the database based on a given query.

"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah, Surah

logger = get_logger()

NAMED_VERSES_PATH = Path(__file__).parent / "named_verses.json"

_RE_DIACRITICS    = re.compile(r"[\u064B-\u065F\u0670]")
_RE_ALEF          = re.compile(r"[أإآٱ]")
_RE_NUMBER_REF    = re.compile(r"^\d+\s*[:\-]\s*\d+$")
# include Arabic-Indic digits U+0660–U+0669
_RE_NAME_NUM      = re.compile(r"^(.+?)\s+([\d\u0660-\u0669]+)$")
_RE_ARABIC_INDIC  = re.compile(r"[\u0660-\u0669]")


def _to_arabic_ascii(text: str) -> str:
    """Convert Arabic-Indic digits to ASCII digits."""
    return _RE_ARABIC_INDIC.sub(lambda m: str(ord(m.group()) - 0x0660), text)


class VerseRetrievalError(Exception):
    """Base error for verse retrieval."""


class VerseNotFoundError(VerseRetrievalError):
    """Verse not found in database."""


class VerseRetrievalEngine:
    """
    Retrieves Quran verses from the database.

    Supported formats:
      "2:255"            → exact surah:ayah reference
      "Ayat al-Kursi"    → named verse lookup (English key or alias)
      "آية الكرسي"       → named verse lookup (Arabic name or alias)
      "البقرة 255"       → Arabic surah name + ayah number
      "Al-Baqarah 255"   → English surah name + ayah number
      "نور على نور"       → fuzzy text search (all 6236 ayahs)
    """

    def __init__(self, session: Session) -> None:
        self.session      = session
        self._raw_verses  = self._load_named_verses()        # full JSON including _meta
        self.named_verses = self._build_verse_index()        # only valid verse entries

    # ── Named verse loader ────────────────────────────────────────────────────

    def _load_named_verses(self) -> dict:
        try:
            if NAMED_VERSES_PATH.exists():
                with open(NAMED_VERSES_PATH, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error("verse.named_verses_load_error", error=str(e))
        return {}

    def _build_verse_index(self) -> dict[str, dict]:
        """
        strip _meta and any entry that is not a verse dict.
        A valid verse entry must have "surah" key.
        """
        return {
            k: v
            for k, v in self._raw_verses.items()
            if isinstance(v, dict) and "surah" in v
        }

    # ── Public API ─────────────────────────────────────────────────────────────

    async def lookup(
        self,
        reference: str,
        include_translation: bool = True,
    ) -> dict | list[dict]:
        try:
            if self._is_number_reference(reference):
                return await self.lookup_by_number(reference, include_translation)

            if self._is_named_verse(reference):
                return await self.lookup_by_name(reference, include_translation)

            if self._is_name_number_reference(reference):
                return await self.lookup_by_name_and_number(reference, include_translation)

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
        match = re.match(r"(\d+)\s*[:\-]\s*(\d+)", reference)
        if not match:
            raise VerseNotFoundError(f"Invalid reference format: {reference!r}")

        surah_num = int(match.group(1))
        ayah_num  = int(match.group(2))

        ayah = (
            self.session.query(Ayah)
            .options(joinedload(Ayah.surah))          # Fix #7
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
        priority: exact key → exact alias → partial key → partial alias.
        Always returns list[dict].
        """
        verse_data = self._resolve_named_verse(name)
        if verse_data is None:
            raise VerseNotFoundError(f"Named verse not found: {name!r}")

        surah_num = verse_data["surah"]

        if "ayah_range" in verse_data:
            start, end = verse_data["ayah_range"]
            return await self.lookup_surah_range(surah_num, start, end, include_translation)

        verse = await self.lookup_by_number(
            f"{surah_num}:{verse_data['ayah']}", include_translation
        )
        return [verse]

    def _resolve_named_verse(self, name: str) -> dict | None:
        """
        four-pass lookup with proper priority.

        Pass 1: exact key match (normalised)
        Pass 2: exact alias match (normalised)
        Pass 3: partial key match  (key in name_key or name_key in key)
        Pass 4: partial alias match
        """
        if len(name.strip()) < 2:              # guard against 1-char inputs
            return None

        name_key = self._normalise_key(name)

        # Pass 1: exact key
        if name_key in self.named_verses:
            return self.named_verses[name_key]

        # Pass 2: exact alias
        for verse_data in self.named_verses.values():
            for alias in verse_data.get("aliases", []):
                if name_key == self._normalise_key(alias):
                    return verse_data

        # Pass 3: partial key (only if name_key >= 3 chars — Fix #2)
        if len(name_key) >= 3:
            for key, verse_data in self.named_verses.items():
                if key == "_meta":
                    continue
                if key in name_key or name_key in key:
                    return verse_data

            # Pass 4: partial alias
            for verse_data in self.named_verses.values():
                for alias in verse_data.get("aliases", []):
                    alias_key = self._normalise_key(alias)
                    if alias_key in name_key or name_key in alias_key:
                        return verse_data

        return None

    async def lookup_by_name_and_number(
        self,
        reference: str,
        include_translation: bool = True,
    ) -> dict:
        match = _RE_NAME_NUM.match(reference.strip())   # Fix #5
        if not match:
            raise VerseNotFoundError(f"Invalid reference: {reference!r}")

        surah_name = match.group(1).strip()
        ayah_num   = int(_to_arabic_ascii(match.group(2)))  # Fix #5

        surah = self._find_surah_by_name(surah_name)
        if not surah:
            raise VerseNotFoundError(f"Surah not found: {surah_name!r}")

        ayah = (
            self.session.query(Ayah)
            .options(joinedload(Ayah.surah))            # Fix #7
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
        ayahs = (
            self.session.query(Ayah)
            .options(joinedload(Ayah.surah))            # Fix #7
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
        stage 2 uses text_simple (already diacritic-free) when available.
        """
        # Stage 1: DB-side LIKE on text_simple
        ayahs = (
            self.session.query(Ayah)
            .options(joinedload(Ayah.surah))            # Fix #7
            .filter(Ayah.text_simple.like(f"%{query}%"))
            .limit(limit)
            .all()
        )
        if ayahs:
            return [self._format_ayah(a, include_translation=False) for a in ayahs]

        # Stage 2: normalised Python scan — all 6236 ayahs
        normalized_query = self._normalize_arabic(query)
        matching: list[Ayah] = []
        batch_size, offset = 500, 0

        while len(matching) < limit:
            batch: list[Ayah] = (
                self.session.query(Ayah)
                .options(joinedload(Ayah.surah))        # Fix #7
                .order_by(Ayah.number)
                .limit(batch_size)
                .offset(offset)
                .all()
            )
            if not batch:
                break

            for ayah in batch:
                source = getattr(ayah, "text_simple", None) or ayah.text_uthmani or ""
                if normalized_query in self._normalize_arabic(source):
                    matching.append(ayah)
                    if len(matching) >= limit:
                        break

            offset += batch_size

        return [self._format_ayah(a, include_translation=False) for a in matching]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise_key(text: str) -> str:
        """Normalise a name to a lookup key (lowercase, spaces→underscores)."""
        return text.strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _normalize_arabic(text: str) -> str:
        """Strip diacritics and unify alef/ya/ta-marbuta."""
        text = _RE_DIACRITICS.sub("", text)
        text = _RE_ALEF.sub("ا", text)
        text = text.replace("ة", "ه").replace("ى", "ي")
        return text

    def _find_surah_by_name(self, name: str) -> Surah | None:
        surah = (
            self.session.query(Surah)
            .filter(or_(Surah.name_ar == name, Surah.name_en == name))
            .first()
        )
        if surah:
            return surah

        if name.isdigit():
            return (
                self.session.query(Surah)
                .filter(Surah.number == int(name))
                .first()
            )

        return (
            self.session.query(Surah)
            .filter(or_(Surah.name_ar.contains(name), Surah.name_en.contains(name)))
            .first()
        )

    def _format_ayah(self, ayah: Ayah, include_translation: bool = True) -> dict:
        result: dict[str, Any] = {
            "surah_number":  ayah.surah.number,
            "surah_name_ar": ayah.surah.name_ar,
            "surah_name_en": ayah.surah.name_en,
            "ayah_number":   ayah.number_in_surah,
            "text_uthmani":  ayah.text_uthmani,
            "text_simple":   getattr(ayah, "text_simple",  None),
            "juz":           getattr(ayah, "juz",          None),
            "page":          getattr(ayah, "page",         None),
            "hizb":          getattr(ayah, "hizb",         None),
            "rub_el_hizb":   getattr(ayah, "rub_el_hizb", None),
            "sajdah":        getattr(ayah, "sajdah",       None),
            "quran_url":     f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}",
        }

        if include_translation and getattr(ayah, "translations", None):
            result["translations"] = [
                {"language": t.language, "translator": t.translator, "text": t.text}
                for t in ayah.translations
            ]

        return result

    # ── Format detectors ──────────────────────────────────────────────────────

    def _is_number_reference(self, ref: str) -> bool:
        return bool(_RE_NUMBER_REF.match(ref.strip()))

    def _is_named_verse(self, ref: str) -> bool:
        return self._resolve_named_verse(ref) is not None

    def _is_name_number_reference(self, ref: str) -> bool:
        return bool(_RE_NAME_NUM.match(ref.strip()))