# Classify Service Module
"""Service for handling classification operations.

Thin wrapper over :class:`src.application.use_cases.classify_query.ClassifyQueryUseCase`
so the service layer and the ``/classify`` route share one classifier.
"""

from src.application.use_cases.classify_query import (
    ClassifyQueryInput,
    ClassifyQueryOutput,
    ClassifyQueryUseCase,
)


class ClassifyService:
    """Service for processing classification queries."""

    def __init__(self) -> None:
        self.use_case = ClassifyQueryUseCase()

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
        return await self.use_case.execute(ClassifyQueryInput(query=query, language=language))


# Default service instance
classify_service = ClassifyService()
