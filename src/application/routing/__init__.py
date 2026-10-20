"""
Application Routing Module - Re-exports from router.

This module is kept for backward compatibility.
Use src.application.router for all routing needs.
"""

# Import directly from modules to avoid circular import with src.application.router
from src.application.routing.executor import AgentExecutor, ExecutionResult
from src.application.routing.intent_router import (
    INTENT_TO_AGENT,
    IntentRouter,
    get_intent_router,
)
from src.application.routing.planner import QueryPlan, QueryPlanner

__all__ = [
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
    "QueryPlan",
    "QueryPlanner",
    "ExecutionResult",
    "AgentExecutor",
]
