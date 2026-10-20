# Classify Service Module
"""Service for handling classification operations."""

from src.application.use_cases.classify_query import (
    ClassifyQueryOutput,
)


class ClassifyService:
    """Service for processing classification queries."""

    def __init__(self) -> None:
        pass

    async def classify(
        self,
        query: str,
        language: str = "en",
    ) -> ClassifyQueryOutput:
        """
        Classify a query.

        Args:
            query: Query to classify
            language: Query language

        Returns:
            ClassifyQueryOutput with classification
        """
        # Placeholder - full classification is not wired yet.
        from src.application.use_cases.classify_schemas import QueryIntent

        return ClassifyQueryOutput(
            intent=QueryIntent.GENERAL_ISLAMIC,
            confidence=0.0,
            suggested_agent="general_islamic_agent",
            suggested_collections=[],
            requires_clarification=False,
            clarification_options=None,
        )


# Default service instance
classify_service = ClassifyService()
