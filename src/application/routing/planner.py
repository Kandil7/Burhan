"""
Planner for Multi-Agent Queries.

Creates execution plans for complex queries requiring multiple agents.
"""

from __future__ import annotations

from typing import Any

from src.domain.intents import Intent


class QueryPlan:
    """Plan for executing a query."""

    def __init__(
        self,
        primary_intent: Intent,
        requires_multiple_agents: bool = False,
        sub_agents: list[str] | None = None,
        orchestration_pattern: str = "sequential",
    ):
        self.primary_intent = primary_intent
        self.requires_multiple_agents = requires_multiple_agents
        self.sub_agents = sub_agents or []
        self.orchestration_pattern = orchestration_pattern


class QueryPlanner:
    """
    Plans query execution strategies.

    Determines:
    - Single vs multi-agent execution
    - Which agents to involve
    - Orchestration pattern to use

    Usage:
        planner = QueryPlanner()
        plan = await planner.create_plan(query, intent)
    """

    # Multi-domain queries that require multiple agents
    MULTI_DOMAIN_INDICATORS = [
        "مقارنة",
        "COMPARE",  # Comparison queries
        "و",
        "and",  # Conjunction queries
        "ماذا عن",
        "what about",  # Follow-up queries
    ]

    def __init__(self):
        """Initialize the query planner."""
        pass

    async def create_plan(
        self,
        query: str,
        primary_intent: Intent,
    ) -> QueryPlan:
        """
        Create an execution plan for the query.

        Args:
            query: User query
            primary_intent: Primary intent from classification

        Returns:
            QueryPlan instance
        """
        # Check if multi-agent is needed
        requires_multi = self._check_multi_agent_needed(query)

        if requires_multi:
            return QueryPlan(
                primary_intent=primary_intent,
                requires_multiple_agents=True,
                sub_agents=self._suggest_sub_agents(query, primary_intent),
                orchestration_pattern="sequential",
            )

        # Single agent plan
        return QueryPlan(
            primary_intent=primary_intent,
            requires_multiple_agents=False,
            sub_agents=[],
            orchestration_pattern="single",
        )

    def _check_multi_agent_needed(self, query: str) -> bool:
        """Check if query requires multiple agents."""
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in self.MULTI_DOMAIN_INDICATORS)

    def _suggest_sub_agents(self, query: str, primary_intent: Intent) -> list[str]:
        """Suggest sub-agents for multi-agent queries."""
        # Simplified implementation
        # In production, this would analyze the query more deeply
        sub_agents = []

        query_lower = query.lower()

        # Add related domains
        if "fiqh" in query_lower or "حكم" in query_lower:
            sub_agents.append("fiqh")

        if "hadith" in query_lower or "حديث" in query_lower:
            sub_agents.append("hadith")

        if "quran" in query_lower or "قرآن" in query_lower:
            sub_agents.append("tafsir")

        return sub_agents


__all__ = ["QueryPlan", "QueryPlanner"]
