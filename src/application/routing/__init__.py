"""
Application Routing Module - Re-exports from router.

This module is kept for backward compatibility.
Use src.application.router for all routing needs.
"""

from src.application.router import (
    IntentRouter,
    get_intent_router,
    INTENT_TO_AGENT,
    QueryPlan,
    QueryPlanner,
    ExecutionResult,
    AgentExecutor,
)

__all__ = [
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
    "QueryPlan",
    "QueryPlanner",
    "ExecutionResult",
    "AgentExecutor",
]
