# Application Use Cases Module
"""
Use cases for business logic orchestration.

This module provides the core use cases:
- AnswerQueryUseCase: Full orchestration for answering queries
- ClassifyQueryUseCase: Query intent classification
- RunRetrievalUseCase: Retrieval execution
- RunToolUseCase: Deterministic tool execution
- BuildTraceUseCase: Execution trace building

Each use case follows clean architecture:
- Takes request models as input
- Returns response models as output
- Coordinates between domain, agents, retrieval, generation, and verification
"""

from src.application.use_cases.answer_query import (
    AnswerQueryUseCase,
    answer_query_use_case,
    AnswerQueryInput,
    AnswerQueryOutput,
)

from src.application.use_cases.classify_query import (
    ClassifyQueryUseCase,
    classify_query_use_case,
    ClassifyQueryInput,
    ClassifyQueryOutput,
)

from src.application.use_cases.classify_schemas import QueryIntent

from src.application.use_cases.run_retrieval import (
    RunRetrievalUseCase,
    run_retrieval_use_case,
    RunRetrievalInput,
    RunRetrievalOutput,
)

from src.application.use_cases.run_tool import (
    RunToolUseCase,
    run_tool_use_case,
    RunToolInput,
    RunToolOutput,
    ToolType,
)

from src.application.use_cases.build_trace import (
    BuildTraceUseCase,
    build_trace_use_case,
    BuildTraceInput,
    BuildTraceOutput,
    TraceEvent,
)

__all__ = [
    # Answer query
    "AnswerQueryUseCase",
    "answer_query_use_case",
    "AnswerQueryInput",
    "AnswerQueryOutput",
    # Classify query
    "ClassifyQueryUseCase",
    "classify_query_use_case",
    "ClassifyQueryInput",
    "ClassifyQueryOutput",
    "QueryIntent",
    # Run retrieval
    "RunRetrievalUseCase",
    "run_retrieval_use_case",
    "RunRetrievalInput",
    "RunRetrievalOutput",
    # Run tool
    "RunToolUseCase",
    "run_tool_use_case",
    "RunToolInput",
    "RunToolOutput",
    "ToolType",
    # Build trace
    "BuildTraceUseCase",
    "build_trace_use_case",
    "BuildTraceInput",
    "BuildTraceOutput",
    "TraceEvent",
]
