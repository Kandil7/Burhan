"""
Ask Service for Burhan Islamic QA system.

Orchestration service for the ask/query endpoint.
Bridges the API transport layer and the AnswerQueryUseCase.
"""

from __future__ import annotations

from typing import Any, Optional

from src.application.use_cases.answer_query import (
    AnswerQueryInput,
    AnswerQueryOutput,
    get_answer_query_use_case,
)
from src.config.logging_config import get_logger

logger = get_logger()


class AskService:
    """
    Service for processing ask queries.

    Coordinates the execution of the answer query use case and handles
    API-level metadata/context.
    """

    def __init__(self, answer_query_use_case: Optional[Any] = None):
        """
        Initialize the ask service.
        
        Args:
            answer_query_use_case: Injected use case instance
        """
        self._use_case = answer_query_use_case

    @property
    def use_case(self):
        """Get or initialize use case instance."""
        if self._use_case is None:
            self._use_case = get_answer_query_use_case()
        return self._use_case

    async def process_query(
        self,
        query: str,
        language: str = "ar",
        madhhab: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> AnswerQueryOutput:
        """
        Process an ask query.

        Args:
            query: User query text
            language: Desired response language
            madhhab: Optional school of jurisprudence
            user_id: Optional user identifier for personalization/logging
            context: Additional context parameters

        Returns:
            AnswerQueryOutput with answer and metadata
        """
        logger.info(
            "service.ask.process",
            query=query[:100],
            language=language,
            madhhab=madhhab,
        )

        input_data = AnswerQueryInput(
            query=query,
            language=language,
            madhhab=madhhab,
            user_id=user_id,
            context=context or {},
        )

        # Execute the core use case
        return await self.use_case.execute(input_data)


# Global service instance
_ask_service: AskService | None = None


def get_ask_service(answer_query_use_case: Any = None) -> AskService:
    """Get the global ask service instance."""
    global _ask_service
    if _ask_service is None:
        _ask_service = AskService(answer_query_use_case=answer_query_use_case)
    return _ask_service



# For backward compatibility with lifespan.py
ask_service = get_ask_service()
