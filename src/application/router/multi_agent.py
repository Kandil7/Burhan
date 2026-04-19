# Multi-Agent Router Module
"""
Multi-agent routing capabilities for handling complex queries.

This module provides:
- MultiAgentRouter: Wrapper for routing to multiple agents
- route_multi: Route to multiple agents for complex queries
- should_orchestrate: Determine if query needs orchestration
- Integration with existing RouterAgent
"""

from __future__ import annotations

import logging
from typing import Optional

from src.application.router.router_agent import (
    RouterAgent,
    SimpleRoutingDecision,
)
from src.application.router.orchestration import (
    OrchestrationPattern,
    create_orchestration_plan,
    MultiAgentOrchestrator,
    route_via_decision_tree,
    PRIMARY_THRESHOLD,
    SECONDARY_THRESHOLD,
)
from src.domain.intents import Intent, get_agent_for_intent

logger = logging.getLogger(__name__)


# ============================================================================
# Multi-Agent Router
# ============================================================================


class MultiAgentRouter:
    """
    Wrapper around RouterAgent with multi-agent routing capabilities.

    This class extends the basic RouterAgent with:
    - Detection of multiple domains in queries
    - Orchestration planning for complex queries
    - Fallback routing for low confidence scenarios
    """

    def __init__(self, router_agent: RouterAgent):
        """
        Initialize the MultiAgentRouter.

        Args:
            router_agent: Base RouterAgent instance
        """
        self._router_agent = router_agent
        logger.info("multi_agent_router_initialized")

    @property
    def router_agent(self) -> RouterAgent:
        """Get the underlying router agent."""
        return self._router_agent

    async def route(self, query: str) -> SimpleRoutingDecision:
        """
        Route a query using the base router agent.

        Args:
            query: Raw user query

        Returns:
            SimpleRoutingDecision with routing information
        """
        # Use the underlying router agent
        routing_decision = await self._router_agent.route(query)

        return SimpleRoutingDecision(
            agent_id=routing_decision.route,
            collections=[_get_collection_for_agent(routing_decision.route)],
            response_mode="answer",
            confidence=routing_decision.result.confidence,
            reasoning=f"Intent: {routing_decision.result.intent.value}",
        )

    def route_multi(self, query: str) -> SimpleRoutingDecision:
        """
        Route to multiple agents based on keyword patterns.

        This method uses keyword detection to identify multiple domains
        in the query and return appropriate routing information.

        Args:
            query: Raw user query

        Returns:
            SimpleRoutingDecision with list of agents, collections, and response mode
        """
        # Use decision tree for rule-based routing
        primary_agent = route_via_decision_tree(query)

        # Check for multiple domains
        agents = self._detect_multiple_domains(query)
        if len(agents) > 1:
            # Multiple agents needed - PARALLEL mode
            collections = [_get_collection_for_agent(a) for a in agents]
            return SimpleRoutingDecision(
                agent_id=agents[0],  # Primary agent
                agents=agents,  # All detected agents
                collections=collections,
                response_mode="answer",
                confidence=SECONDARY_THRESHOLD,
                reasoning=f"Multiple domains detected: {', '.join(agents)}",
            )

        # Single agent - SEQUENTIAL mode
        collection = _get_collection_for_agent(primary_agent)
        return SimpleRoutingDecision(
            agent_id=primary_agent,
            collections=[collection],
            response_mode="answer",
            confidence=PRIMARY_THRESHOLD,
            reasoning=f"Single domain: {primary_agent}",
        )

    def _detect_multiple_domains(self, query: str) -> list[str]:
        """
        Detect multiple domains in a query based on keywords.

        Args:
            query: Raw user query

        Returns:
            List of agent names for detected domains
        """
        query_lower = query.lower()
        agents = []

        # Domain keyword mapping
        domain_keywords = {
            "hadith_agent": ["حديث", "hadith", "سند", "إسناد"],
            "tafsir_agent": ["آية", "سورة", "قرآن", "تفسير", "tafsir", "surah", "ayah"],
            "fiqh_agent": ["حكم", "فتوى", "fiqh", "halal", "haram"],
            "aqeedah_agent": ["عقيدة", "توحيد", "aqeedah", "tawhid"],
            "seerah_agent": ["سيرة", "seerah", "sirah"],
            "language_agent": ["نحو", "صرف", "بلاغة", "arabic"],
        }

        for agent, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                if agent not in agents:
                    agents.append(agent)

        # If no agents detected, use general_islamic_agent
        if not agents:
            agents.append("general_islamic_agent")

        return agents

    def should_orchestrate(self, query: str) -> bool:
        """
        Determine if a query requires orchestration (multiple agents).

        Complex queries need orchestration if:
        - Contains multiple domain keywords
        - Cross-collection question
        - Ambiguous intent

        Args:
            query: Raw user query

        Returns:
            True if orchestration is needed, False otherwise
        """
        query_lower = query.lower()

        # Count domain keywords
        domain_count = 0

        # Quran-related keywords
        if any(kw in query_lower for kw in ["آية", "سورة", "قرآن", "quran", "surah"]):
            domain_count += 1

        # Hadith-related keywords
        if any(kw in query_lower for kw in ["حديث", "hadith", "سند"]):
            domain_count += 1

        # Tafsir-related keywords
        if any(kw in query_lower for kw in ["تفسير", "tafsir"]):
            domain_count += 1

        # Fiqh-related keywords
        if any(kw in query_lower for kw in ["حكم", "فتوى", "fiqh", "halal"]):
            domain_count += 1

        # Aqeedah-related keywords
        if any(kw in query_lower for kw in ["عقيدة", "توحيد", "aqeedah"]):
            domain_count += 1

        # Need orchestration if 2+ domains detected
        return domain_count >= 2

    def create_plan(self, query: str, intent: Intent) -> "OrchestrationPlan":
        """
        Create an orchestration plan for the query.

        Args:
            query: Raw user query
            intent: Detected primary intent

        Returns:
            OrchestrationPlan with tasks and pattern
        """
        return create_orchestration_plan(query, intent)


# ============================================================================
# Helper Functions
# ============================================================================


def _get_collection_for_agent(agent_name: str) -> str:
    """Get the collection name for an agent."""
    from src.retrieval.strategies import get_collection_for_agent

    return get_collection_for_agent(agent_name)


# ============================================================================
# Enhanced Router Agent Factory
# ============================================================================


def create_multi_agent_router(classifier: Any) -> MultiAgentRouter:
    """
    Create a MultiAgentRouter with the given classifier.

    Args:
        classifier: IntentClassifier implementation

    Returns:
        Configured MultiAgentRouter instance
    """
    from src.application.router.router_agent import create_router_agent

    router_agent = create_router_agent(classifier)
    return MultiAgentRouter(router_agent)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "MultiAgentRouter",
    "create_multi_agent_router",
    "route_multi",
    "should_orchestrate",
]
