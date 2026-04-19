# Classify Query Use Case
"""Use case for classifying user queries."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    """Query intent types."""

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


@dataclass
class ClassifyQueryInput:
    """Input for classify query use case."""

    query: str
    language: str = "en"


@dataclass
class ClassifyQueryOutput:
    """Output for classify query use case."""

    intent: QueryIntent
    confidence: float
    suggested_agent: str
    suggested_collections: List[str]
    requires_clarification: bool
    clarification_options: Optional[List[str]] = None


class ClassifyQueryUseCase:
    """Use case for classifying user queries."""

    def __init__(self):
        pass

    async def execute(self, input: ClassifyQueryInput) -> ClassifyQueryOutput:
        """
        Execute the classify query use case.

        Steps:
        1. Analyze query for Islamic domain keywords
        2. Determine intent based on content analysis
        3. Map intent to appropriate agent
        4. Determine required collections
        5. Check if clarification is needed
        """
        # Placeholder - implement actual classification
        return ClassifyQueryOutput(
            intent=QueryIntent.GENERAL_ISLAMIC,
            confidence=0.8,
            suggested_agent="general_islamic_agent",
            suggested_collections=["quran", "sahih_bukhari", "fiqh_islami"],
            requires_clarification=False,
            clarification_options=None,
        )


# Default use case instance
classify_query_use_case = ClassifyQueryUseCase()
