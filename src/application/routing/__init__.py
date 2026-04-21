"""Application routing module.

This module provides routing components:
- IntentRouter: Routes queries to agents based on intent classification
- QueryPlanner: Plans query execution strategies
- AgentExecutor: Executes queries against agents
"""

from src.application.routing.intent_router import IntentRouter, get_intent_router, INTENT_TO_AGENT
from src.application.routing.planner import QueryPlan, QueryPlanner
from src.application.routing.executor import ExecutionResult, AgentExecutor

__all__ = [
    # Intent routing
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
    # Query planning
    "QueryPlan",
    "QueryPlanner",
    # Execution
    "ExecutionResult",
    "AgentExecutor",
]
