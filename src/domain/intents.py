"""
Domain intents and classifications for Athar Islamic QA system.

This module defines:
- Intent enum: Supported query intents
- QuranSubIntent: Sub-intents for Quran queries
- INTENT_DESCRIPTIONS: Human-readable descriptions for LLM prompts
- INTENT_ROUTING: Intent → agent/tool routing table
- INTENT_PRIORITY: Priority scores for resolving keyword conflicts
- KEYWORD_PATTERNS: Fast-path keyword matching patterns
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class Intent(str, Enum):
    """
    Supported query intents for Athar Islamic QA system.
    """

    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    HADITH = "hadith"
    TAFSIR = "tafsir"
    AQEEDAH = "aqeedah"
    SEERAH = "seerah"
    USUL_FIQH = "usul_fiqh"
    ISLAMIC_HISTORY = "islamic_history"
    ARABIC_LANGUAGE = "arabic_language"
    ISLAMIC_TAZKIYAH = "islamic_tazkiyah"  # ⬅ جديد
    # Additional intents for specific tools and queries
    ZAKAT = "zakat"
    INHERITANCE = "inheritance"
    GREETING = "greeting"
    DUAS = "duas"
    PRAYER_TIMES = "prayer_times"
    HIJRI_CALENDAR = "hijri_calendar"


class QuranSubIntent(str, Enum):
    """
    Sub-intents for Quran queries.

    - verse_lookup: exact verse / surah text retrieval
    - interpretation: tafsir and meaning (RAG)
    - analytics: NL2SQL statistics (count, length, position)
    - quotation_validation: verify whether a text is a real Quran verse
    """

    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"


# ============================================================================
# Human-readable descriptions used in LLM classifier prompts
# ============================================================================


INTENT_DESCRIPTIONS: Dict[Intent, str] = {
    Intent.FIQH: ("Islamic jurisprudence (halal/haram, worship, transactions, rulings, fiqh questions)"),
    Intent.QURAN: ("Quranic verses, surahs, tafsir, Quran statistics, or verse lookup"),
    Intent.ISLAMIC_KNOWLEDGE: (
        "General Islamic knowledge (history, biography, theology, concepts) that does not fit a more specific intent"
    ),
    Intent.HADITH: ("Hadith retrieval, authentication, sanad, and matn (Prophetic traditions)"),
    Intent.TAFSIR: ("Quran interpretation and exegesis (Ibn Kathir, Al-Jalalayn, Al-Qurtubi, etc.)"),
    Intent.AQEEDAH: ("Islamic creed and theology (Tawhid, faith, beliefs, theological questions)"),
    Intent.SEERAH: ("Prophet Muhammad's biography and life events (Seerah, prophetic history)"),
    Intent.USUL_FIQH: ("Principles of Islamic jurisprudence (methodology, sources of Islamic law, ijtihad, qiyas)"),
    Intent.ISLAMIC_HISTORY: ("Islamic history and civilization (historical events, figures, dynasties, culture)"),
    Intent.ARABIC_LANGUAGE: (
        "Arabic language: grammar (nahw), morphology (sarf), rhetoric (balaghah), literature, poetry, dictionaries"
    ),
    Intent.ISLAMIC_TAZKIYAH: (  # ⬅ جديد
        "Tazkiyah and spiritual development (tasawwuf, suluk, hearts, manners, Ibn al-Qayyim, Madarij al-Salikin)"
    ),
    # Additional intents for specific tools
    Intent.ZAKAT: ("Zakat calculation and rulings (zakat al-fitr, niacin, wealth)"),
    Intent.INHERITANCE: ("Islamic inheritance distribution and rulings"),
    Intent.GREETING: ("Greetings and salam exchanges"),
    Intent.DUAS: ("Islamic supplications and duas"),
    Intent.PRAYER_TIMES: ("Prayer times calculation and schedules"),
    Intent.HIJRI_CALENDAR: ("Hijri calendar conversion and dates"),
}


# ============================================================================
# Intent → agent/tool routing table (Epic 6 - Collection-aware)
# ============================================================================


INTENT_ROUTING: Dict[Intent, str] = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "tafsir_agent",  # Tafsir handles Quran interpretation
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",
    Intent.TAFSIR: "tafsir_agent",  # Dedicated tafsir agent (Epic 6)
    Intent.AQEEDAH: "aqeedah_agent",  # Dedicated aqeedah agent (Epic 6)
    Intent.USUL_FIQH: "usul_fiqh_agent",  # Dedicated usul_fiqh agent (Epic 6)
    Intent.ISLAMIC_HISTORY: "history_agent",  # Dedicated history agent (Epic 6)
    Intent.ARABIC_LANGUAGE: "language_agent",  # Dedicated language agent (Epic 6)
    Intent.ISLAMIC_TAZKIYAH: "tazkiyah_agent",  # ⬅ جديد
    # Additional intents route to tools or appropriate agents
    Intent.ZAKAT: "tool_agent",  # Zakat calculator tool
    Intent.INHERITANCE: "tool_agent",  # Inheritance calculator tool
    Intent.GREETING: "chatbot_agent",  # Greeting responses
    Intent.DUAS: "general_islamic_agent",  # Duas retrieval
    Intent.PRAYER_TIMES: "tool_agent",  # Prayer times tool
    Intent.HIJRI_CALENDAR: "tool_agent",  # Hijri calendar tool
}


# ============================================================================
# Priority scores — higher = more specific.
# Used by HybridIntentClassifier to resolve keyword conflicts.
# Note: More specific intents should have HIGHER priority.
# ============================================================================


INTENT_PRIORITY: Dict[Intent, int] = {
    Intent.TAFSIR: 10,  # Most specific Quran intent (tafsir > general quran)
    Intent.QURAN: 9,  # General Quran intent
    Intent.HADITH: 9,
    Intent.SEERAH: 8,
    Intent.AQEEDAH: 8,
    Intent.USUL_FIQH: 8,
    Intent.ISLAMIC_TAZKIYAH: 8,  # ⬅ جديد
    Intent.ARABIC_LANGUAGE: 7,
    Intent.ISLAMIC_HISTORY: 6,
    Intent.FIQH: 5,
    Intent.ZAKAT: 5,
    Intent.INHERITANCE: 5,
    Intent.PRAYER_TIMES: 4,
    Intent.HIJRI_CALENDAR: 4,
    Intent.DUAS: 4,
    Intent.GREETING: 3,
    Intent.ISLAMIC_KNOWLEDGE: 1,  # most general — matched last
}


# ============================================================================
# Keyword patterns for fast-path classification.
#
# NOTE: Keywords are now imported from classifier_factory.py as the
# single source of truth. This avoids duplication.
# ============================================================================

# Import keywords from the canonical classifier factory
# This is the SINGLE SOURCE OF TRUTH for classification keywords
try:
    from src.application.router.classifier_factory import INTENT_KEYWORDS as KEYWORD_PATTERNS
except ImportError:
    # Fallback to empty dict if classifier not available (e.g., during early imports)
    KEYWORD_PATTERNS: Dict[Intent, List[str]] = {}


# ============================================================================
# Helper functions
# ============================================================================


def get_intent_description(intent: Intent) -> str:
    """Return human-readable description for a given intent."""
    return INTENT_DESCRIPTIONS.get(intent, "Unknown intent")


def get_agent_for_intent(intent: Intent) -> str | None:
    """Return the agent/tool name for a given intent, if defined."""
    return INTENT_ROUTING.get(intent)


def is_quran_intent(intent: Intent) -> bool:
    """Return True if the intent is specifically Quran-related."""
    return intent == Intent.QURAN


def all_intents() -> List[Intent]:
    """Convenience: return list of all supported intents."""
    return list(Intent)


def all_quran_sub_intents() -> List[QuranSubIntent]:
    """Convenience: return list of supported Quran sub-intents."""
    return list(QuranSubIntent)
