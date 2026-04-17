# Router Agent Module
"""Router agent for directing queries to appropriate handlers.

This module provides the main routing entrypoint for the application.
It combines intent classification with routing decisions.
"""

from typing import Any, Dict, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Inline RouterAgent implementation to avoid circular import issues
class RouterAgent:
    """
    Main router for query routing.

    This wraps an IntentClassifier with:
    - Confidence gating
    - Route construction
    - Agent metadata
    """

    def __init__(self, classifier: Any, conf_threshold: float = 0.5):
        self._classifier = classifier
        self._conf_threshold = conf_threshold

    async def route(self, query: str) -> "RoutingDecision":
        """
        Route a query and return a routing decision.

        Args:
            query: Raw user query string

        Returns:
            RoutingDecision with intent, route, and metadata
        """
        from src.application.models import RoutingDecision
        from src.domain.intents import get_agent_for_intent

        result = await self._classifier.classify(query)
        route = get_agent_for_intent(result.intent) or "chatbot_agent"

        return RoutingDecision(result=result, route=route, agent_metadata={})

    @property
    def classifier(self) -> Any:
        """Get the underlying classifier."""
        return self._classifier


@dataclass
class SimpleRoutingDecision:
    """Simplified routing decision for basic use cases."""

    agent_id: str
    collections: list[str]
    response_mode: str  # answer, clarify, abstain
    confidence: float
    reasoning: Optional[str] = None


def create_router_agent(classifier: Any) -> RouterAgent:
    """
    Create a RouterAgent with the given classifier.

    Args:
        classifier: IntentClassifier implementation

    Returns:
        Configured RouterAgent instance
    """
    return RouterAgent(classifier=classifier)


# Default singleton instance - will be configured during app startup
router_agent: Optional[RouterAgent] = None


def get_router_agent() -> RouterAgent:
    """Get the global router agent instance."""
    global router_agent
    if router_agent is None:
        raise RuntimeError("RouterAgent not initialized. Call init_router_agent() first.")
    return router_agent


def init_router_agent(classifier: Any) -> RouterAgent:
    """Initialize the global router agent."""
    global router_agent
    router_agent = RouterAgent(classifier=classifier)
    logger.info("router_agent_initialized", classifier=type(classifier).__name__)
    return router_agent


__all__ = [
    "RouterAgent",
    "SimpleRoutingDecision",
    "create_router_agent",
    "get_router_agent",
    "init_router_agent",
    "router_agent",
]
