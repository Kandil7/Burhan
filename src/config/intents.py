"""
Backward compatibility layer for intent definitions.

This module re-exports Intent and related definitions from src.domain.intents
for backward compatibility with existing code.
"""

from src.domain.intents import (
    Intent,
    QuranSubIntent,
    INTENT_DESCRIPTIONS,
    INTENT_ROUTING,
    INTENT_PRIORITY,
    KEYWORD_PATTERNS,
    get_intent_description,
    get_agent_for_intent,
    is_quran_intent,
    all_intents,
    all_quran_sub_intents,
)

__all__ = [
    "Intent",
    "QuranSubIntent",
    "INTENT_DESCRIPTIONS",
    "INTENT_ROUTING",
    "INTENT_PRIORITY",
    "KEYWORD_PATTERNS",
    "get_intent_description",
    "get_agent_for_intent",
    "is_quran_intent",
    "all_intents",
    "all_quran_sub_intents",
]
