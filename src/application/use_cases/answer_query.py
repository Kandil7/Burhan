from dataclasses import dataclass
from typing import Any, List, Optional

from src.agents.base import AgentInput, AgentOutput
from src.application.router.router_agent import RouterAgent, get_router_agent
from src.core.registry import AgentRegistry, get_registry


@dataclass
class AnswerQueryInput:
    """Input for answer query use case."""

    query: str
    language: str = "ar"
    madhhab: Optional[str] = None


@dataclass
class AnswerQueryOutput:
    """Output for answer query use case."""

    answer: str
    citations: List[Any]
    metadata: dict
    confidence: float
    intent: str


class AnswerQueryUseCase:
    """
    Use case for answering user queries using v2 architecture.
    Orchestrates the flow: Router -> AgentRegistry -> CollectionAgent.
    """

    def __init__(self, agent_registry: Optional[AgentRegistry] = None, router: Optional[RouterAgent] = None):
        self._registry = agent_registry
        self._router = router

    async def execute(self, query: str, language: str = "ar", madhhab: Optional[str] = None) -> AnswerQueryOutput:
        """
        Execute the answer query use case.

        1. Route identifying intent.
        2. Get appropriate agent from registry.
        3. Run agent (retrieve -> verify -> generate).
        """
        router = self._router or get_router_agent()
        registry = self._registry or get_registry()

        # 1. Intent Classification & Routing
        decision = await router.route(query)
        intent = decision.result.intent

        # 2. Resolve V2 Agent
        # Try finding a V2 collection agent first, fallback to general
        agent, is_v2 = registry.get_for_intent(intent)
        if not agent:
            # Re-fetch general agent
            agent = registry.get_agent("general_islamic_agent")
            is_v2 = True  # Assuming v2 by default for this registry

        if not agent:
            raise RuntimeError("No suitable agent found in registry for intent: " + str(intent))

        # 3. Execution (Full RAG Pipeline)
        # V2 CollectionAgent.run() handles Retrieve -> Rerank -> Verify -> Generate
        if is_v2 and hasattr(agent, "run"):
            result: AgentOutput = await agent.run(query, meta={"language": language, "madhhab": madhhab})
        else:
            # Fallback for legacy or standard agents
            result = await agent.execute(AgentInput(query=query, language=language, metadata={"madhhab": madhhab}))

        return AnswerQueryOutput(
            answer=result.answer,
            citations=result.citations,
            metadata=result.metadata,
            confidence=result.confidence,
            intent=intent.value if hasattr(intent, "value") else str(intent),
        )


# Default use case instance for simple DI or migration
answer_query_use_case = AnswerQueryUseCase()
