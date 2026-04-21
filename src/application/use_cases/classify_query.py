"""
Use case for classifying user queries in Athar Islamic QA system.

This module provides:
- ClassifyQueryInput / ClassifyQueryOutput dataclasses
- ClassifyQueryUseCase: lightweight keyword-based classifier

NOTE:
This is a fast, deterministic classifier that can be used:
- as a first-pass router
- or as a fallback when LLM-based classification is unavailable.

It is designed to be consistent with src.domain.intents.Intent and routing.
For production, use src.application.router.KeywordBasedClassifier instead.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.application.use_cases.classify_schemas import QueryIntent
from src.application.use_cases.classify_rules import classify_by_keywords


@dataclass
class ClassifyQueryInput:
    """Input for classify query use case."""

    query: str
    language: str = "en"
    metadata: Optional[Dict] = None


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
    """
    Use case for classifying user queries.

    Uses keyword-based rules for fast, deterministic classification.
    For production, prefer src.application.router.KeywordBasedClassifier.
    """

    def __init__(self) -> None:
        pass

    async def execute(self, input_data: ClassifyQueryInput) -> ClassifyQueryOutput:
        """
        Execute classification.

        Args:
            input_data: Classification input

        Returns:
            Classification result with intent, confidence, and routing info
        """
        # Use keyword-based classification
        intent_str, confidence, agent, collections = classify_by_keywords(input_data.query)

        # Convert to QueryIntent enum
        try:
            intent = QueryIntent(intent_str)
        except ValueError:
            intent = QueryIntent.GENERAL_ISLAMIC

        return ClassifyQueryOutput(
            intent=intent,
            confidence=confidence,
            suggested_agent=agent,
            suggested_collections=collections,
            requires_clarification=False,
            clarification_options=None,
        )


# Default use case instance
classify_query_use_case = ClassifyQueryUseCase()


__all__ = [
    "ClassifyQueryInput",
    "ClassifyQueryOutput",
    "ClassifyQueryUseCase",
    "classify_query_use_case",
]
