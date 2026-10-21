"""Load Quran data into PostgreSQL.

Two sources are supported:

* :meth:`QuranLoader.load_from_json` reads the bundled sample layout used by
  ``data/seed/quran_sample.json``.
* :meth:`QuranLoader.load_from_api` reads the complete Quran from the
  Quran.com v4 API, 114 chapters and 6236 verses, with the Saheeh
  International translation.

Both paths upsert by natural keys, so running them again updates rows instead
of duplicating them.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah, Surah, Translation
from src.quran.quotation_validator import normalize_arabic

logger = get_logger()

API_BASE = "https://api.quran.com/api/v4"
TRANSLATION_ID = 20  # Saheeh International
TRANSLATOR = "Saheeh International"
USER_AGENT = "Burhan-Quran-Seeder/1.0"
PER_PAGE = 300
REQUEST_PAUSE_SECONDS = 0.2
MAX_ATTEMPTS = 3

_SUP_RE = re.compile(r"<sup[^>]*>.*?</sup>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

_REVELATION_TYPES = {
    "makkah": "meccan",
    "madinah": "medinan",
    "meccan": "meccan",
    "medinan": "medinan",
    "mecca": "meccan",
    "medina": "medinan",
}

# Canonical verse counts per surah (Kufan count, 114 entries, 6236 verses).
# Used to derive the global verse number when a JSON file is partial.
SURAH_VERSE_COUNTS: tuple[int, ...] = (
    7,
    286,
    200,
    176,
    120,
    165,
    206,
    75,
    129,
    109,
    123,
    111,
    43,
    52,
    99,
    128,
    111,
    110,
    98,
    135,
    112,
    78,
    118,
    64,
    77,
    227,
    93,
    88,
    69,
    60,
    34,
    30,
    73,
    54,
    45,
    83,
    182,
    88,
    75,
    85,
    54,
    53,
    89,
    59,
    37,
    35,
    38,
    29,
    18,
    45,
    60,
    49,
    62,
    55,
    78,
    96,
    29,
    22,
    24,
    13,
    14,
    11,
    11,
    18,
    12,
    12,
    30,
    52,
    52,
    44,
    28,
    28,
    20,
    56,
    40,
    31,
    50,
    40,
    46,
    42,
    29,
    19,
    36,
    25,
    22,
    17,
    19,
    26,
    30,
    20,
    15,
    21,
    11,
    8,
    8,
    19,
    5,
    8,
    8,
    11,
    11,
    8,
    3,
    9,
    5,
    4,
    7,
    3,
    6,
    3,
    5,
    4,
    5,
    6,
)


def global_ayah_number(surah_number: int, number_in_surah: int) -> int:
    """Return the 1-based global verse number for a surah-local verse number."""
    if not 1 <= surah_number <= len(SURAH_VERSE_COUNTS):
        raise ValueError(f"surah number out of range: {surah_number}")
    if not 1 <= number_in_surah <= SURAH_VERSE_COUNTS[surah_number - 1]:
        raise ValueError(f"verse {number_in_surah} out of range for surah {surah_number}")
    return sum(SURAH_VERSE_COUNTS[: surah_number - 1]) + number_in_surah


def clean_translation(text: str) -> str:
    """Strip footnote markers, HTML tags, and entity escapes from a translation."""
    text = _SUP_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    return _SPACE_RE.sub(" ", text).strip()


def revelation_type(place: str | None) -> str:
    """Map a Quran.com revelation place to the stored vocabulary."""
    return _REVELATION_TYPES.get((place or "").lower(), "meccan")


class QuranLoader:
    """Upsert Quran surahs, verses, and translations through a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_from_json(self, path: str) -> dict[str, int]:
        """Load a surahs/ayahs/translations document from a JSON file."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        stats = {"surahs": 0, "ayahs": 0, "translations": 0}

        for surah_data in payload.get("surahs", []):
            surah = self._upsert_surah(surah_data)
            stats["surahs"] += 1

            for ayah_data in surah_data.get("ayahs", []):
                ayah = self._upsert_ayah(surah, ayah_data)
                stats["ayahs"] += 1

                for translation_data in ayah_data.get("translations", []):
                    self._upsert_translation(ayah, translation_data)
                    stats["translations"] += 1

        self.session.commit()
        logger.info("quran.loaded_json", path=path, **stats)
        return stats

    async def load_from_api(self, language: str = "en") -> dict[str, int]:
        """Load the complete Quran from the Quran.com v4 API."""
        chapters = self._fetch_json(f"{API_BASE}/chapters?language={language}")["chapters"]
        stats = {"surahs": 0, "ayahs": 0, "translations": 0}

        for chapter in chapters:
            surah = self._upsert_surah(
                {
                    "number": chapter["id"],
                    "name_ar": chapter["name_arabic"],
                    "name_en": chapter["name_simple"],
                    "verse_count": chapter["verses_count"],
                    "revelation_type": revelation_type(chapter.get("revelation_place")),
                }
            )
            stats["surahs"] += 1

            page = 1
            while True:
                url = (
                    f"{API_BASE}/verses/by_chapter/{chapter['id']}"
                    f"?fields=text_uthmani,text_uthmani_simple,juz_number,page_number,"
                    f"hizb_number,rub_el_hizb_number,sajdah_number"
                    f"&translations={TRANSLATION_ID}&per_page={PER_PAGE}&page={page}"
                )
                payload = self._fetch_json(url)

                for verse in payload.get("verses", []):
                    ayah = self._upsert_ayah(
                        surah,
                        {
                            "number_in_surah": verse["verse_number"],
                            "text_uthmani": verse["text_uthmani"],
                            "text_simple": verse.get("text_uthmani_simple"),
                            "juz": verse.get("juz_number"),
                            "page": verse.get("page_number"),
                            "hizb": verse.get("hizb_number"),
                            "rub_el_hizb": verse.get("rub_el_hizb_number"),
                            "sajdah": verse.get("sajdah_number") is not None,
                        },
                    )
                    stats["ayahs"] += 1

                    for translation in verse.get("translations", []):
                        self._upsert_translation(
                            ayah,
                            {
                                "language": language,
                                "translator": TRANSLATOR,
                                "text": clean_translation(translation.get("text", "")),
                            },
                        )
                        stats["translations"] += 1

                pagination = payload.get("pagination") or {}
                if not pagination.get("next_page"):
                    break
                page = pagination["next_page"]

            # Commit per chapter so a network failure leaves a usable prefix.
            self.session.commit()
            logger.info("quran.chapter_loaded", chapter=chapter["id"], ayahs=stats["ayahs"])

        logger.info("quran.loaded_api", **stats)
        return stats

    # ------------------------------------------------------------------
    # Row upserts
    # ------------------------------------------------------------------

    def _upsert_surah(self, data: dict[str, Any]) -> Surah:
        number = int(data["number"])
        surah: Any = self.session.scalar(select(Surah).where(Surah.number == number))
        if surah is None:
            surah = Surah(number=number)
            self.session.add(surah)

        surah.name_ar = data.get("name_ar") or f"Surah {number}"
        surah.name_en = data.get("name_en") or f"Surah {number}"
        surah.verse_count = int(data.get("verse_count") or 0)
        surah.revelation_type = revelation_type(data.get("revelation_type"))
        if 1 <= number <= len(SURAH_VERSE_COUNTS) and surah.verse_count != SURAH_VERSE_COUNTS[number - 1]:
            logger.warning(
                "quran.verse_count_mismatch",
                surah=number,
                declared=surah.verse_count,
                expected=SURAH_VERSE_COUNTS[number - 1],
            )
        self.session.flush()
        return cast(Surah, surah)

    def _upsert_ayah(self, surah: Surah, data: dict[str, Any]) -> Ayah:
        number_in_surah = int(data["number_in_surah"])
        ayah: Any = self.session.scalar(
            select(Ayah).where(
                Ayah.surah_id == surah.id,
                Ayah.number_in_surah == number_in_surah,
            )
        )
        if ayah is None:
            ayah = Ayah(surah_id=surah.id, number_in_surah=number_in_surah)
            self.session.add(ayah)

        text_uthmani = (data.get("text_uthmani") or "").strip()
        ayah.number = global_ayah_number(int(surah.number), number_in_surah)
        ayah.text_uthmani = text_uthmani
        ayah.text_simple = data.get("text_simple") or normalize_arabic(text_uthmani)
        ayah.juz = int(data.get("juz") or 1)
        ayah.page = int(data.get("page") or 1)
        ayah.hizb = data.get("hizb")
        ayah.rub_el_hizb = data.get("rub_el_hizb")
        ayah.sajdah = bool(data.get("sajdah", False))
        ayah.surah_name = surah.name_en
        ayah.surah_name_ar = surah.name_ar

        self.session.flush()
        return cast(Ayah, ayah)

    def _upsert_translation(self, ayah: Ayah, data: dict[str, Any]) -> Translation:
        language = (data.get("language") or "en")[:5]
        translator = data.get("translator")
        translation: Any = self.session.scalar(
            select(Translation).where(
                Translation.ayah_id == ayah.id,
                Translation.language == language,
                Translation.translator == translator,
            )
        )
        if translation is None:
            translation = Translation(ayah_id=ayah.id, language=language, translator=translator)
            self.session.add(translation)

        translation.text = data.get("text") or ""
        self.session.flush()
        return cast(Translation, translation)

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _fetch_json(self, url: str) -> dict[str, Any]:
        """Fetch JSON with a user agent, bounded retries, and a polite pause."""
        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                )
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload: Any = json.loads(response.read().decode("utf-8"))
                time.sleep(REQUEST_PAUSE_SECONDS)
                return cast(dict[str, Any], payload)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning(
                    "quran.fetch_failed",
                    url=url,
                    attempt=attempt,
                    error=f"{type(exc).__name__}: {exc}",
                )
                time.sleep(2 * attempt)

        raise RuntimeError(f"Failed to fetch {url}: {last_error}")
