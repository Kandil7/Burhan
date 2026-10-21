"""Tafsir retrieval error mapping."""

from __future__ import annotations

from typing import Any

import pytest

from src.quran.tafsir_retrieval import TafsirNotFoundError, TafsirRetrievalEngine
from src.quran.verse_retrieval import VerseNotFoundError


class _MissingVerseEngine:
    """Verse engine stub that never finds a verse."""

    async def lookup(self, reference: str, include_translation: bool = True) -> Any:
        raise VerseNotFoundError(f"Verse not found: {reference!r}")


async def test_missing_verse_maps_to_tafsir_not_found() -> None:
    """A missing verse is a 404 case, not a retrieval failure."""
    engine = TafsirRetrievalEngine(session=None)
    engine.verse_engine = _MissingVerseEngine()

    with pytest.raises(TafsirNotFoundError):
        await engine.get_tafsir("2:255")


class _StubVerseEngine:
    """Verse engine stub that always resolves to one verse."""

    async def lookup(self, reference: str, include_translation: bool = True) -> dict[str, Any]:
        return {
            "surah_number": 2,
            "ayah_number": 255,
            "text_uthmani": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ",
        }


async def test_verse_without_tafsir_raises_not_found() -> None:
    """An existing verse with no tafsir rows is a 404, not an empty list."""
    from unittest.mock import MagicMock

    session = MagicMock()
    chain = session.query.return_value.join.return_value.join.return_value
    chain.filter.return_value.order_by.return_value.all.return_value = []

    engine = TafsirRetrievalEngine(session=session)
    engine.verse_engine = _StubVerseEngine()

    with pytest.raises(TafsirNotFoundError):
        await engine.get_tafsir("2:255")
