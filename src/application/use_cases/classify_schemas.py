"""
Query Intent Enum for Burhan Islamic QA System.

This enum represents high-level domain intents for query classification.
It's kept for backward compatibility - the canonical classifier uses
src.domain.intents.Intent instead.
"""

from enum import Enum


class QueryIntent(str, Enum):
    """Query intent types for classify query use case."""

    ISLAMIC_FIQH = "islamic_fiqh"
    ISLAMIC_HADITH = "islamic_hadith"
    ISLAMIC_TAFSIR = "islamic_tafsir"
    ISLAMIC_AQEEDAH = "islamic_aqeedah"
    ISLAMIC_SEERAH = "islamic_seerah"
    ISLAMIC_HISTORY = "islamic_history"
    ISLAMIC_LANGUAGE = "islamic_language"
    ISLAMIC_TAZKIYAH = "islamic_tazkiyah"
    ISLAMIC_USUL_FIQH = "islamic_usul_fiqh"
    GENERAL_ISLAMIC = "general_islamic"
    TOOL = "tool"
    OUT_OF_SCOPE = "out_of_scope"


__all__ = ["QueryIntent"]
