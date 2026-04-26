"""
Application Routing Module - Re-exports from router.

This module is kept for backward compatibility.
Use src.application.router for all routing needs.
"""

# Import directly from modules to avoid circular import with src.application.router
from src.application.routing.intent_router import (
    IntentRouter,
    get_intent_router,
    INTENT_TO_AGENT,
)
from src.application.routing.planner import QueryPlan, QueryPlanner
from src.application.routing.executor import ExecutionResult, AgentExecutor

__all__ = [
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
    "QueryPlan",
    "QueryPlanner",
    "ExecutionResult",
    "AgentExecutor",
]
