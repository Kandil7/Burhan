"""
Tafsir Retrieval Engine for Athar Islamic QA system.

Fixes:
  - get_tafsir: handles list[dict] return from verse_engine.lookup()
  - search_tafsir: truncation only when text exceeds limit
  - source validation: clear error before DB query
  - available_sources: deterministic order via dict.fromkeys()
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah, Surah, Tafsir
from src.quran.verse_retrieval import VerseRetrievalEngine

logger = get_logger()

_TRUNCATE_AYAH   = 100
_TRUNCATE_TAFSIR = 300


class TafsirRetrievalError(Exception):
    """Base error for tafsir retrieval."""


class TafsirNotFoundError(TafsirRetrievalError):
    """Tafsir not found for the requested verse / source."""


class TafsirRetrievalEngine:
    """
    Retrieves scholarly Quran commentaries from the database.

    Supported sources: ibn-kathir, al-jalalayn, al-qurtubi.
    """

    AVAILABLE_SOURCES: dict[str, dict] = {
        "ibn-kathir": {
            "name_ar": "تفسير ابن كثير",
            "name_en": "Ibn Kathir",
            "author":  "Ismail ibn Kathir",
            "language": "ar",
        },
        "al-jalalayn": {
            "name_ar": "تفسير الجلالين",
            "name_en": "Al-Jalalayn",
            "author":  "Jalal ad-Din al-Mahalli and Jalal ad-Din as-Suyuti",
            "language": "ar",
        },
        "al-qurtubi": {
            "name_ar": "تفسير القرطبي",
            "name_en": "Al-Qurtubi",
            "author":  "Abu 'Abdullah Al-Qurtubi",
            "language": "ar",
        },
    }

    def __init__(self, session: Session) -> None:
        self.session      = session
        self.verse_engine = VerseRetrievalEngine(session)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def get_tafsir(
        self,
        ayah_reference: str,
        source: str | None = None,
    ) -> dict:
        """
        Get tafsir for a specific verse.

        Args:
            ayah_reference: "2:255", "البقرة 255", "Ayat al-Kursi", etc.
            source: One of AVAILABLE_SOURCES keys, or None for all.

        Returns:
            {"ayah": dict, "tafsirs": [...], "available_sources": [...]}

        Raises:
            TafsirNotFoundError: verse exists but no tafsir found.
            TafsirRetrievalError: unexpected DB / parsing error.
        """
        # Validate source before hitting the DB
        if source is not None:
            self._validate_source(source)

        try:
            # verse_engine.lookup() may return dict OR list[dict]
            lookup_result = await self.verse_engine.lookup(
                ayah_reference, include_translation=True
            )

            # Normalise to a single ayah dict
            if isinstance(lookup_result, list):
                if not lookup_result:
                    raise TafsirNotFoundError(
                        f"No verses returned for reference: {ayah_reference!r}"
                    )
                # For ranges (e.g. Al-Fatihah), use the first ayah as anchor
                ayah_dict = lookup_result[0]
            else:
                ayah_dict = lookup_result

            surah_num = ayah_dict["surah_number"]
            ayah_num  = ayah_dict["ayah_number"]

            # Build DB query
            q = (
                self.session.query(Tafsir)
                .join(Ayah)
                .join(Surah)
                .filter(
                    Surah.number == surah_num,
                    Ayah.number_in_surah == ayah_num,
                )
            )

            if source:
                q = q.filter(Tafsir.source_name == source)

            tafsirs = q.all()

            if source and not tafsirs:
                raise TafsirNotFoundError(
                    f"No tafsir from '{source}' found for {ayah_reference!r}."
                )

            # Deterministic source order (dict.fromkeys preserves insertion order)
            seen_sources = list(dict.fromkeys(t.source_name for t in tafsirs))

            result = {
                "ayah":              ayah_dict,
                "tafsirs":           [self._format_tafsir(t) for t in tafsirs],
                "available_sources": seen_sources,
            }

            logger.info("tafsir.retrieved",
                        reference=ayah_reference, sources=seen_sources)
            return result

        except TafsirNotFoundError:
            raise
        except Exception as e:
            logger.error("tafsir.retrieval_error", error=str(e), exc_info=True)
            raise TafsirRetrievalError(f"Error retrieving tafsir: {e}") from e

    async def search_tafsir(
        self,
        query: str,
        source: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Full-text search across tafsir entries.

        Args:
            query: Arabic or English search term.
            source: Optional source filter.
            limit: Maximum number of results (default 5).

        Returns:
            List of matching tafsir passage dicts.
        """
        if source is not None:
            self._validate_source(source)

        try:
            q = (
                self.session.query(Tafsir)
                .join(Ayah)
                .join(Surah)
                .filter(Tafsir.text.contains(query))
            )

            if source:
                q = q.filter(Tafsir.source_name == source)

            tafsirs = q.limit(limit).all()

            results = [self._format_search_result(t) for t in tafsirs]

            logger.info("tafsir.searched", query=query, results=len(results))
            return results

        except Exception as e:
            logger.error("tafsir.search_error", error=str(e), exc_info=True)
            raise TafsirRetrievalError(f"Error searching tafsir: {e}") from e

    def list_sources(self) -> list[dict]:
        """Return metadata for all available tafsir sources."""
        return [{"id": sid, **meta} for sid, meta in self.AVAILABLE_SOURCES.items()]

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_source(self, source: str) -> None:
        """
        Raise TafsirRetrievalError early if source is unknown.
        Prevents confusing TafsirNotFoundError ("tafsir not found")
        when the real problem is a bad source name.
        """
        if source not in self.AVAILABLE_SOURCES:
            valid = ", ".join(self.AVAILABLE_SOURCES)
            raise TafsirRetrievalError(
                f"Unknown source {source!r}. Available: {valid}"
            )

    # ── Formatters ────────────────────────────────────────────────────────────

    def _format_tafsir(self, t: Tafsir) -> dict:
        """Full tafsir entry (used in get_tafsir)."""
        return {
            "source":   t.source_name,
            "author":   self.AVAILABLE_SOURCES.get(t.source_name, {}).get(
                            "author", getattr(t, "author", "Unknown")),
            "text":     t.text,
            "language": getattr(t, "language", "ar"),
        }

    def _format_search_result(self, t: Tafsir) -> dict:
        """Compact tafsir entry for search results with safe truncation."""
        ayah_text   = t.ayah.text_uthmani or ""
        tafsir_text = t.text or ""

        return {
            "surah_number":  t.ayah.surah.number,
            "surah_name_en": t.ayah.surah.name_en,
            "ayah_number":   t.ayah.number_in_surah,
            # Only append "…" when the text is actually truncated
            "ayah_text":    (
                ayah_text[:_TRUNCATE_AYAH] + "…"
                if len(ayah_text) > _TRUNCATE_AYAH
                else ayah_text
            ),
            "source":       t.source_name,
            "author":       self.AVAILABLE_SOURCES.get(t.source_name, {}).get(
                                "author", getattr(t, "author", "Unknown")),
            "tafsir_text":  (
                tafsir_text[:_TRUNCATE_TAFSIR] + "…"
                if len(tafsir_text) > _TRUNCATE_TAFSIR
                else tafsir_text
            ),
            "quran_url":    (
                f"https://quran.com/"
                f"{t.ayah.surah.number}/{t.ayah.number_in_surah}"
            ),
        }