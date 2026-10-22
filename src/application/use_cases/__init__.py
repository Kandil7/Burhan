# Application Use Cases Module
"""
Use cases for the live tree:
- AnswerQueryUseCase: the /ask flow
- RunRetrievalUseCase: the retrieval flow behind the search endpoint

The designed classify, tool, and trace use cases were deleted in hardening
Phase 7; see docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md.
"""

from src.application.use_cases.answer_query import (
    AnswerQueryInput,
    AnswerQueryOutput,
    AnswerQueryUseCase,
    answer_query_use_case,
)
from src.application.use_cases.run_retrieval import (
    RunRetrievalInput,
    RunRetrievalOutput,
    RunRetrievalUseCase,
    run_retrieval_use_case,
)

__all__ = [
    # Answer query
    "AnswerQueryUseCase",
    "AnswerQueryInput",
    "AnswerQueryOutput",
    "answer_query_use_case",
    # Retrieval
    "RunRetrievalUseCase",
    "RunRetrievalInput",
    "RunRetrievalOutput",
    "run_retrieval_use_case",
]
