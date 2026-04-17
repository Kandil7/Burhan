# Orchestration Module
"""
Multi-agent orchestration for handling complex queries.

This module provides:
- OrchestrationPattern: SEQUENTIAL, PARALLEL, HIERARCHICAL
- AgentTask: Task definition for agent execution
- OrchestrationPlan: Complete plan for multi-agent execution
- create_orchestration_plan: Factory for creating plans based on intent
- MultiAgentOrchestrator: Orchestrates execution across multiple agents
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from src.domain.intents import Intent, get_agent_for_intent, INTENT_ROUTING
from src.retrieval.strategies import get_strategy_for_agent, get_collection_for_agent
from src.agents.base import AgentOutput, AgentInput

logger = logging.getLogger(__name__)


# ============================================================================
# Orchestration Patterns
# ============================================================================


class OrchestrationPattern(str, Enum):
    """Patterns for multi-agent orchestration."""

    SEQUENTIAL = "sequential"  # Execute tasks one after another
    PARALLEL = "parallel"  # Execute tasks concurrently
    HIERARCHICAL = "hierarchical"  # Primary with sub-agents


# ============================================================================
# Task and Plan Data Classes
# ============================================================================


@dataclass
class AgentTask:
    """Represents a single task to be executed by an agent."""

    agent_name: str
    query: str
    priority: int = 0
    requires_verification: bool = False


@dataclass
class OrchestrationPlan:
    """Complete orchestration plan for query execution."""

    pattern: OrchestrationPattern
    tasks: list[AgentTask]
    primary_agent: str
    fallback_agent: str = "general_islamic_agent"


# ============================================================================
# Configuration Thresholds
# ============================================================================

PRIMARY_THRESHOLD = 0.7  # High confidence → single primary agent
SECONDARY_THRESHOLD = 0.4  # Medium confidence → consider multiple agents
LOW_CONFIDENCE_THRESHOLD = 0.2  # Low confidence → use fallback


# ============================================================================
# Orchestration Plan Factory
# ============================================================================


def create_orchestration_plan(query: str, intent: Intent) -> OrchestrationPlan:
    """
    Create an orchestration plan based on query and detected intent.

    Args:
        query: Raw user query
        intent: Detected primary intent from classification

    Returns:
        OrchestrationPlan with appropriate pattern and tasks

    Logic:
        - Simple queries (single intent): SEQUENTIAL with single task
        - Complex queries (multiple intents): PARALLEL with multiple tasks
    """
    # Get agent for the primary intent
    primary_agent = get_agent_for_intent(intent) or "general_islamic_agent"

    # Create primary task
    primary_task = AgentTask(
        agent_name=primary_agent,
        query=query,
        priority=1,
        requires_verification=False,
    )

    # Determine if we need multiple agents (complex query detection)
    # by checking for multiple domain keywords in query
    complex_query = _detect_complex_query(query)

    if complex_query:
        # PARALLEL pattern for complex queries requiring multiple agents
        secondary_agents = _get_secondary_agents(intent, query)
        tasks = [primary_task] + secondary_agents
        pattern = OrchestrationPattern.PARALLEL

        logger.info(
            "complex_query_orchestration",
            extra={"intent": intent.value, "num_agents": len(tasks), "query_preview": query[:50]},
        )
    else:
        # SEQUENTIAL pattern for simple queries
        tasks = [primary_task]
        pattern = OrchestrationPattern.SEQUENTIAL

        logger.info(
            "simple_query_orchestration",
            extra={
                "intent": intent.value,
                "agent": primary_agent,
                "query_preview": query[:50],
            },
        )

    return OrchestrationPlan(
        pattern=pattern,
        tasks=tasks,
        primary_agent=primary_agent,
        fallback_agent="general_islamic_agent",
    )


def _detect_complex_query(query: str) -> bool:
    """
    Detect if a query is complex and may require multiple agents.

    Complexity indicators:
    - Contains keywords from multiple domains (Quran + Hadith, etc.)
    - Cross-collection questions
    - Ambiguous or compound queries
    """
    query_lower = query.lower()

    # Count how many domain keywords are present
    domain_keywords = {
        "quran": ["آية", "سورة", "قرآن", "quran", "surah", "ayah"],
        "hadith": ["حديث", "hadith", "سند", "إسناد"],
        "tafsir": ["تفسير", "tafsir"],
        "fiqh": ["حكم", "فتوى", "fiqh", "halal", "haram"],
        "aqeedah": ["عقيدة", "توحيد", "aqeedah", "tawhid"],
    }

    matched_domains = 0
    for domain, keywords in domain_keywords.items():
        if any(kw in query_lower for kw in keywords):
            matched_domains += 1

    # Consider complex if 2+ domains detected
    return matched_domains >= 2


def _get_secondary_agents(intent: Intent, query: str) -> list[AgentTask]:
    """
    Get secondary agents that might be needed based on query content.

    Args:
        intent: Primary detected intent
        query: User query

    Returns:
        List of secondary AgentTask objects
    """
    secondary_tasks = []

    # Rule-based detection for additional domains
    query_lower = query.lower()

    # If query mentions hadith concepts, add hadith_agent
    if any(kw in query_lower for kw in ["حديث", "hadith", "سند", "إسناد"]):
        if intent != Intent.HADITH:
            secondary_tasks.append(
                AgentTask(
                    agent_name="hadith_agent",
                    query=query,
                    priority=2,
                    requires_verification=True,
                )
            )

    # If query mentions tafsir concepts, add tafsir_agent
    if any(kw in query_lower for kw in ["تفسير", "tafsir"]):
        if intent != Intent.TAFSIR:
            secondary_tasks.append(
                AgentTask(
                    agent_name="tafsir_agent",
                    query=query,
                    priority=2,
                    requires_verification=True,
                )
            )

    # If query mentions fiqh concepts, add fiqh_agent
    if any(kw in query_lower for kw in ["حكم", "فتوى", "fiqh", "halal"]):
        if intent != Intent.FIQH:
            secondary_tasks.append(
                AgentTask(
                    agent_name="fiqh_agent",
                    query=query,
                    priority=2,
                    requires_verification=True,
                )
            )

    return secondary_tasks


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================


class MultiAgentOrchestrator:
    """
    Orchestrates execution of tasks across multiple agents.

    This class manages:
    - Agent registry for looking up agents by name
    - Plan execution based on orchestration pattern
    - Result aggregation from multiple agents
    - Fallback handling for low confidence scenarios
    """

    def __init__(self, agent_registry: dict[str, Callable] | None = None):
        """
        Initialize the orchestrator.

        Args:
            agent_registry: Dictionary mapping agent names to agent instances
        """
        self._agent_registry = agent_registry or {}
        logger.info("multi_agent_orchestrator_initialized", extra={"num_agents": len(self._agent_registry)})

    def register_agent(self, name: str, agent: Callable) -> None:
        """Register an agent for orchestration."""
        self._agent_registry[name] = agent
        logger.debug("agent_registered", extra={"agent_name": name})

    async def execute_plan(
        self,
        plan: OrchestrationPlan,
        query: str,
    ) -> AgentOutput:
        """
        Execute an orchestration plan.

        Args:
            plan: The orchestration plan to execute
            query: Raw user query

        Returns:
            AgentOutput: Aggregated result from agent(s)
        """
        logger.info(
            "executing_orchestration_plan",
            extra={
                "pattern": plan.pattern.value,
                "num_tasks": len(plan.tasks),
                "primary_agent": plan.primary_agent,
            },
        )

        if plan.pattern == OrchestrationPattern.SEQUENTIAL:
            return await self._execute_sequential(plan.tasks, query)
        elif plan.pattern == OrchestrationPattern.PARALLEL:
            return await self._execute_parallel(plan.tasks, query)
        else:
            # Default to sequential for hierarchical (simplified)
            return await self._execute_sequential(plan.tasks, query)

    async def _execute_sequential(
        self,
        tasks: list[AgentTask],
        query: str,
    ) -> AgentOutput:
        """Execute tasks sequentially (one after another)."""
        if not tasks:
            return self._create_empty_output()

        # Execute primary task
        primary_task = tasks[0]
        result = await self._execute_agent_task(primary_task, query)

        # Check confidence - fallback if too low
        if result.confidence < LOW_CONFIDENCE_THRESHOLD:
            logger.warning(
                "low_confidence_sequential",
                extra={
                    "confidence": result.confidence,
                    "agent": primary_task.agent_name,
                },
            )
            return await self.route_to_fallback(query)

        return result

    async def _execute_parallel(
        self,
        tasks: list[AgentTask],
        query: str,
    ) -> AgentExecuteParallelResult:
        """Execute multiple agents in parallel and aggregate results."""
        import asyncio

        if not tasks:
            return AgentOutput(answer="", citations=[], metadata={})

        # Execute all tasks concurrently
        task_coros = [self._execute_agent_task(task, query) for task in tasks]
        results = await asyncio.gather(*task_coros, return_exceptions=True)

        # Filter out exceptions and aggregate
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "agent_task_failed",
                    extra={
                        "agent": tasks[i].agent_name,
                        "error": str(result),
                    },
                )
            else:
                valid_results.append(result)

        if not valid_results:
            return await self.route_to_fallback(query)

        # Aggregate results - use highest confidence result as primary
        valid_results.sort(key=lambda r: r.confidence, reverse=True)
        primary_result = valid_results[0]

        # Merge citations and metadata
        all_citations = []
        for result in valid_results:
            all_citations.extend(result.citations)

        # Merge answer with context from other results if needed
        final_answer = primary_result.answer
        if len(valid_results) > 1:
            # Add supplemental context from other results
            supplemental = "\n\n".join(
                f"[{r.metadata.get('agent_name', 'agent')}]: {r.answer}"
                for r in valid_results[1:]
                if r.answer and r.confidence > 0.3
            )
            if supplemental:
                final_answer = f"{final_answer}\n\n---\n{supplemental}"

        return AgentOutput(
            answer=final_answer,
            citations=all_citations[:20],  # Limit citations
            metadata={
                "orchestration": "parallel",
                "num_agents": len(valid_results),
                "agents_executed": [t.agent_name for t in tasks],
                "primary_agent": primary_result.metadata.get("agent_name", tasks[0].agent_name),
            },
            confidence=primary_result.confidence,
        )

    async def _execute_agent_task(
        self,
        task: AgentTask,
        query: str,
    ) -> AgentOutput:
        """Execute a single agent task."""
        agent = self._agent_registry.get(task.agent_name)

        if agent is None:
            logger.warning(
                "agent_not_found_in_registry",
                extra={"agent_name": task.agent_name},
            )
            return self._create_fallback_output(
                f"Agent {task.agent_name} not available",
                confidence=0.0,
            )

        try:
            # Create agent input
            input_data = AgentInput(
                query=query,
                language="ar",
                metadata={
                    "agent_name": task.agent_name,
                    "priority": task.priority,
                    "requires_verification": task.requires_verification,
                    "retrieval_strategy": get_strategy_for_agent(task.agent_name),
                },
            )

            # Execute agent
            result = await agent.execute(input_data)

            # Add agent name to metadata
            result.metadata["agent_name"] = task.agent_name

            return result

        except Exception as e:
            logger.error(
                "agent_execution_failed",
                extra={
                    "agent_name": task.agent_name,
                    "error": str(e),
                },
            )
            return self._create_fallback_output(
                f"Agent {task.agent_name} execution failed: {str(e)}",
                confidence=0.0,
            )

    async def route_to_fallback(self, query: str) -> AgentOutput:
        """
        Route to fallback agent when primary agents fail or have low confidence.

        Fallback chain:
        1. GeneralIslamicAgent (general Islamic knowledge)
        2. ChatbotAgent (generic conversation)
        """
        logger.info("routing_to_fallback", extra={"query_preview": query[:50]})

        # Try general_islamic_agent first
        fallback_agent = self._agent_registry.get("general_islamic_agent")

        if fallback_agent is None:
            # Fall back to chatbot
            fallback_agent = self._agent_registry.get("chatbot_agent")

        if fallback_agent is None:
            return self._create_empty_output()

        try:
            input_data = AgentInput(
                query=query,
                language="ar",
                metadata={"fallback": True},
            )
            result = await fallback_agent.execute(input_data)
            result.metadata["fallback_used"] = True
            return result

        except Exception as e:
            logger.error("fallback_agent_failed", extra={"error": str(e)})
            return self._create_empty_output()

    def _create_empty_output(self) -> AgentOutput:
        """Create an empty agent output."""
        return AgentOutput(
            answer="",
            citations=[],
            metadata={"error": "No agents available"},
            confidence=0.0,
        )

    def _create_fallback_output(self, message: str, confidence: float) -> AgentOutput:
        """Create a fallback output with message."""
        return AgentOutput(
            answer=message,
            citations=[],
            metadata={"fallback": True},
            confidence=confidence,
        )


# Type alias for parallel execution results
AgentExecuteParallelResult = AgentOutput


# ============================================================================
# Decision Tree Logic for Rule-Based Routing
# ============================================================================


def route_via_decision_tree(query: str) -> str:
    """
    Rule-based routing using keyword patterns.

    This provides a fast-path for common Islamic domain keywords:
    - "حديث" → hadith_agent
    - "آية" / "سورة" → tafsir_agent
    - "عقيدة" → aqeedah_agent
    - etc.

    Args:
        query: Raw user query

    Returns:
        Agent name to route to
    """
    query_lower = query.lower()

    # Priority-ordered keyword matching
    if any(kw in query_lower for kw in ["حديث", "hadith", "سند", "إسناد", "الحديث"]):
        return "hadith_agent"

    if any(kw in query_lower for kw in ["آية", "ايه", "سورة", "سوره", "قرآن"]):
        return "tafsir_agent"

    if any(kw in query_lower for kw in ["تفسير", "tafsir"]):
        return "tafsir_agent"

    if any(kw in query_lower for kw in ["عقيدة", "عقيده", "توحيد", "aqeedah", "tawhid"]):
        return "aqeedah_agent"

    if any(kw in query_lower for kw in ["سيرة", "سيره", "seerah", "sirah", "غزوة", "غزوه"]):
        return "seerah_agent"

    if any(kw in query_lower for kw in ["أصول الفقه", "اصول الفقه", "usul"]):
        return "usul_fiqh_agent"

    if any(kw in query_lower for kw in ["تاريخ إسلامي", "islamic history"]):
        return "history_agent"

    if any(kw in query_lower for kw in ["نحو", "صرف", "بلاغة", "arabic"]):
        return "language_agent"

    if any(kw in query_lower for kw in ["ما حكم", "هل يجوز", "حكم", "فتوى", "fiqh"]):
        return "fiqh_agent"

    # Default fallback
    return "general_islamic_agent"


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "OrchestrationPattern",
    "AgentTask",
    "OrchestrationPlan",
    "create_orchestration_plan",
    "MultiAgentOrchestrator",
    "route_via_decision_tree",
    # Thresholds
    "PRIMARY_THRESHOLD",
    "SECONDARY_THRESHOLD",
    "LOW_CONFIDENCE_THRESHOLD",
]
