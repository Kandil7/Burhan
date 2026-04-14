"""
Verse Retrieval Engine for Athar Islamic QA system.

Supports multiple input formats:
- Exact reference: "2:255", "112:1"
- Arabic name: "البقرة 255", "الإخلاص 1"
- English name: "Al-Baqarah 255", "Al-Ikhlas 1"
- Named verses: "Ayat al-Kursi", "Al-Fatihah"
- Fuzzy search: partial verse text

Phase 3: Foundation for all Quran lookup features.
"""
import json
import re
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger
from src.data.models.quran import Ayah, Surah

logger = get_logger()

# Path to named verses database
NAMED_VERSES_PATH = Path(__file__).parent / "named_verses.json"


class VerseRetrievalError(Exception):
    """Error in verse retrieval."""
    pass


class VerseNotFoundError(VerseRetrievalError):
    """Verse not found in database."""
    pass


class VerseRetrievalEngine:
    """
    Engine for retrieving Quran verses from database.

    Supports multiple input formats and fuzzy matching.

    Usage:
        engine = VerseRetrievalEngine(session)
        verse = await engine.lookup("2:255")
        verse = await engine.lookup("البقرة 255")
        verse = await engine.lookup("Ayat al-Kursi")
    """

    def __init__(self, session: Session):
        """
        Initialize engine with database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.named_verses = self._load_named_verses()

    def _load_named_verses(self) -> dict:
        """Load named verses database."""
        try:
            if NAMED_VERSES_PATH.exists():
                with open(NAMED_VERSES_PATH, encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("verse.named_verses_load_error", error=str(e))
        return {}

    async def lookup(self, reference: str, include_translation: bool = True) -> dict:
        """
        Lookup verse by reference (auto-detect format).

        Args:
            reference: Verse reference in any supported format
            include_translation: Whether to include translation

        Returns:
            Verse data dict

        Raises:
            VerseNotFoundError: If verse not found
        """
        # Try different formats
        try:
            # Format 1: "2:255"
            if self._is_number_reference(reference):
                return await self.lookup_by_number(reference, include_translation)

            # Format 2: Named verse (Ayat al-Kursi)
            if self._is_named_verse(reference):
                return await self.lookup_by_name(reference, include_translation)

            # Format 3: "البقرة 255" or "Al-Baqarah 255"
            if self._is_name_number_reference(reference):
                return await self.lookup_by_name_and_number(reference, include_translation)

            # Format 4: Fuzzy search
            results = await self.search_verses(reference, limit=1)
            if results:
                return results[0]

            raise VerseNotFoundError(f"Verse not found: {reference}")

        except VerseNotFoundError:
            raise
        except Exception as e:
            logger.error("verse.lookup_error", reference=reference, error=str(e))
            raise VerseRetrievalError(
                f"Error looking up verse: {str(e)}"
            ) from e

    async def lookup_by_number(
        self,
        reference: str,
        include_translation: bool = True
    ) -> dict:
        """
        Lookup verse by surah:ayah number.

        Args:
            reference: "2:255" format
            include_translation: Include translation

        Returns:
            Verse data dict
        """
        # Parse reference
        match = re.match(r"(\d+)\s*[:\-]\s*(\d+)", reference)
        if not match:
            raise VerseNotFoundError(f"Invalid reference format: {reference}")

        surah_num = int(match.group(1))
        ayah_num = int(match.group(2))

        # Query database
        ayah = (
            self.session.query(Ayah)
            .join(Surah)
            .filter(
                Surah.number == surah_num,
                Ayah.number_in_surah == ayah_num
            )
            .first()
        )

        if not ayah:
            raise VerseNotFoundError(f"Verse {reference} not found")

        return self._format_ayah(ayah, include_translation)

    async def lookup_by_name(
        self,
        name: str,
        include_translation: bool = True
    ) -> list[dict]:
        """
        Lookup named verse(s).

        Args:
            name: "Ayat al-Kursi", "Al-Fatihah", etc.
            include_translation: Include translation

        Returns:
            List of verse data dicts
        """
        # Search in named verses
        name_lower = name.lower().replace(" ", "_").replace("-", "_")

        for key, verse_data in self.named_verses.items():
            if key in name_lower or name_lower in key:
                surah_num = verse_data["surah"]

                if "ayah_range" in verse_data:
                    # Range (entire surah)
                    start, end = verse_data["ayah_range"]
                    return await self.lookup_surah_range(
                        surah_num, start, end, include_translation
                    )
                else:
                    # Single ayah
                    ayah_num = verse_data["ayah"]
                    return [await self.lookup_by_number(
                        f"{surah_num}:{ayah_num}",
                        include_translation
                    )]

        raise VerseNotFoundError(f"Named verse not found: {name}")

    async def lookup_by_name_and_number(
        self,
        reference: str,
        include_translation: bool = True
    ) -> dict:
        """
        Lookup verse by surah name + number.

        Args:
            reference: "البقرة 255", "Al-Baqarah 255"
            include_translation: Include translation

        Returns:
            Verse data dict
        """
        # Parse reference
        match = re.match(r"(.+?)\s+(\d+)", reference)
        if not match:
            raise VerseNotFoundError(f"Invalid reference: {reference}")

        surah_name = match.group(1).strip()
        ayah_num = int(match.group(2))

        # Find surah by name (fuzzy match)
        surah = self._find_surah_by_name(surah_name)
        if not surah:
            raise VerseNotFoundError(f"Surah not found: {surah_name}")

        # Find ayah
        ayah = (
            self.session.query(Ayah)
            .filter(
                Ayah.surah_id == surah.id,
                Ayah.number_in_surah == ayah_num
            )
            .first()
        )

        if not ayah:
            raise VerseNotFoundError(f"Verse {surah.number}:{ayah_num} not found")

        return self._format_ayah(ayah, include_translation)

    async def lookup_surah_range(
        self,
        surah_number: int,
        start: int,
        end: int,
        include_translation: bool = True
    ) -> list[dict]:
        """
        Lookup range of ayahs in a surah.

        Args:
            surah_number: Surah number
            start: Starting ayah number
            end: Ending ayah number
            include_translation: Include translation

        Returns:
            List of verse data dicts
        """
        ayahs = (
            self.session.query(Ayah)
            .join(Surah)
            .filter(
                Surah.number == surah_number,
                Ayah.number_in_surah.between(start, end)
            )
            .order_by(Ayah.number_in_surah)
            .all()
        )

        return [self._format_ayah(ayah, include_translation) for ayah in ayahs]

    async def search_verses(
        self,
        query: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Search verses by text (fuzzy matching).

        Args:
            query: Search text (Arabic or English)
            limit: Maximum results

        Returns:
            List of matching verse dicts
        """

        # Try exact match first (for performance)
        ayahs = (
            self.session.query(Ayah)
            .filter(Ayah.text_uthmani.like(f"%{query}%"))
            .limit(limit)
            .all()
        )

        # If no results, try normalized matching (limited for performance)
        if not ayahs:
            # Get ayahs in batches and filter with normalization
            normalized_query = self._normalize_arabic_text(query)

            matching_ayahs = []
            batch_size = 1000
            offset = 0

            # Only search first 3000 ayahs for performance
            while len(matching_ayahs) < limit and offset < 3000:
                batch = (
                    self.session.query(Ayah)
                    .order_by(Ayah.number)
                    .limit(batch_size)
                    .offset(offset)
                    .all()
                )

                if not batch:
                    break

                for ayah in batch:
                    normalized_text = self._normalize_arabic_text(ayah.text_uthmani or "")
                    if normalized_query in normalized_text:
                        matching_ayahs.append(ayah)
                        if len(matching_ayahs) >= limit:
                            break

                offset += batch_size

            ayahs = matching_ayahs

        return [self._format_ayah(ayah, include_translation=False) for ayah in ayahs]

    def _normalize_arabic_text(self, text: str) -> str:
        """
        Normalize Arabic text by removing diacritical marks.

        Args:
            text: Arabic text with diacritics

        Returns:
            Normalized text without diacritics
        """
        import re
        # Remove Arabic diacritical marks (Unicode range 064B-065F)
        normalized = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        # Normalize alef variations
        normalized = normalized.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        # Normalize ha variations
        normalized = normalized.replace('ة', 'ه')
        # Normalize ya variations
        normalized = normalized.replace('ى', 'ي')
        return normalized

    def _find_surah_by_name(self, name: str) -> Surah | None:
        """
        Find surah by name (fuzzy match).

        Args:
            name: Surah name (Arabic or English)

        Returns:
            Surah object or None
        """
        # Try exact match first
        surah = (
            self.session.query(Surah)
            .filter(
                or_(
                    Surah.name_ar == name,
                    Surah.name_en == name
                )
            )
            .first()
        )

        if surah:
            return surah

        # Try number match
        if name.isdigit():
            return (
                self.session.query(Surah)
                .filter(Surah.number == int(name))
                .first()
            )

        # Try fuzzy match (simple contains)
        surah = (
            self.session.query(Surah)
            .filter(
                or_(
                    Surah.name_ar.contains(name),
                    Surah.name_en.contains(name)
                )
            )
            .first()
        )

        return surah

    def _format_ayah(
        self,
        ayah: Ayah,
        include_translation: bool = True
    ) -> dict:
        """
        Format ayah object into response dict.

        Args:
            ayah: Ayah ORM object
            include_translation: Include translation

        Returns:
            Formatted verse dict
        """
        result = {
            "surah_number": ayah.surah.number,
            "surah_name_ar": ayah.surah.name_ar,
            "surah_name_en": ayah.surah.name_en,
            "ayah_number": ayah.number_in_surah,
            "text_uthmani": ayah.text_uthmani,
            "text_simple": ayah.text_simple,
            "juz": ayah.juz,
            "page": ayah.page,
            "hizb": ayah.hizb,
            "rub_el_hizb": ayah.rub_el_hizb,
            "sajdah": ayah.sajdah,
            "quran_url": f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}",
        }

        # Add translation if requested
        if include_translation and ayah.translations:
            result["translations"] = [
                {
                    "language": t.language,
                    "translator": t.translator,
                    "text": t.text
                }
                for t in ayah.translations
            ]

        return result

    def _is_number_reference(self, reference: str) -> bool:
        """Check if reference is number format (2:255)."""
        return bool(re.match(r"^\d+\s*[:\-]\s*\d+$", reference))

    def _is_named_verse(self, reference: str) -> bool:
        """Check if reference is a named verse."""
        name_lower = reference.lower().replace(" ", "_").replace("-", "_")
        return any(key in name_lower for key in self.named_verses.keys())

    def _is_name_number_reference(self, reference: str) -> bool:
        """Check if reference is name + number format."""
        return bool(re.match(r".+\s+\d+", reference))
