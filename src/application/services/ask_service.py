from typing import Optional

from src.application.use_cases.answer_query import AnswerQueryOutput, AnswerQueryUseCase


class AskService:
    """Service for processing ask queries bridging API and Use Case."""

    def __init__(self) -> None:
        self.use_case = AnswerQueryUseCase()

    async def process_query(
        self, query: str, language: str = "ar", madhhab: Optional[str] = None
    ) -> AnswerQueryOutput:
        """
        Process an ask query using the AnswerQueryUseCase.
        """
        return await self.use_case.execute(query, language=language, madhhab=madhhab)


# Default service instance
ask_service = AskService()
