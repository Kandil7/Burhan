"""
Answer Query Use Case for Burhan Islamic QA system.

Orchestrates the full query answering flow:
1. Intent classification & routing
2. Agent selection from registry
3. RAG pipeline execution (retrieve -> verify -> generate)
4. Policy enforcement
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from src.agents.base import AgentInput, AgentOutput
from src.config.logging_config import get_logger

logger = get_logger()


@dataclass
class AnswerQueryInput:
    """Input for answer query use case."""

    query: str
    language: str = "ar"
    madhhab: str | None = None
    user_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerQueryOutput:
    """Output for answer query use case."""

    answer: str
    intent: str
    confidence: float
    citations: list[dict[str, Any]]
    citation_chunks: list[dict[str, Any]] = field(default_factory=list)  
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_human_review: bool = False


class AnswerQueryUseCase:
    """
    Main use case for answering user queries.

    Coordinates between the router, the agent registry, and the agents.
    """

    def __init__(self, agent_registry: Any = None, router: Any = None):
        """
        Initialize with injected dependencies.
        
        Args:
            agent_registry: AgentRegistry instance
            router: RouterAgent instance
        """
        self._registry = agent_registry
        self._router = router

    async def execute(self, input_data: AnswerQueryInput) -> AnswerQueryOutput:
        """
        Execute the answer query flow.

        Args:
            input_data: Request parameters

        Returns:
            AnswerQueryOutput with response and metadata
        """
        start_time = time.time()
        
        # 1. Resolve Dependencies
        # Use injected or global fallbacks
        router = self._router
        if not router:
            from src.application.router.router_agent import get_router_agent
            router = get_router_agent()
            
        registry = self._registry
        if not registry:
            from src.core.registry import get_registry
            registry = get_registry()
        
        # 2. Routing & Intent Classification
        decision = await router.route(input_data.query)
        intent = decision.result.intent
        
        logger.info(
            "use_case.answer_query.routed",
            intent=intent.value,
            confidence=decision.result.confidence,
        )

        # 2. Agent Selection from Registry
        registry = self._registry
        if not registry:
            from src.core.registry import get_registry
            registry = get_registry()
            
        # IMPORTANT: Use the intent from the router to find the specialized agent
        agent, is_agent = registry.get_for_intent(intent)
        
        if not agent:
            logger.warning("use_case.answer_query.no_agent_for_intent", intent=intent.value)
            # Fallback to general agent or chatbot
            agent = registry.get_agent("general_islamic_agent")
            if not agent:
                agent = registry.get_agent("chatbot_agent")
        else:
            logger.info("use_case.answer_query.selected_agent", agent_name=getattr(agent, 'name', 'unknown'))

        # 4. Agent Execution
        # V2 agents use .run() for the full pipeline; legacy agents use .execute()
        try:
            if hasattr(agent, "run"):
                # V2 Collection-aware RAG pipeline
                result: AgentOutput = await agent.run(
                    input_data.query,
                    meta={
                        "language": input_data.language,
                        "madhhab": input_data.madhhab,
                        "sub_intent": getattr(decision.result, "quran_subintent", None),
                    }
                )
            else:
                # Standard/Legacy adapter
                result: AgentOutput = await agent.execute(
                    AgentInput(
                        query=input_data.query,
                        language=input_data.language,
                        metadata={
                            "madhhab": input_data.madhhab,
                            "sub_intent": getattr(decision.result, "quran_subintent", None),
                        }
                    )
                )
        except Exception as e:
            logger.error("use_case.answer_query.agent_error", error=str(e), exc_info=True)
            return self._build_error_output(input_data, str(e))

        processing_time_ms = int((time.time() - start_time) * 1000)
        

        # 5. Build Output
        # Use router confidence for the top-level 'confidence' field (intent_confidence in API)
        return AnswerQueryOutput(
            answer=result.answer,
            intent=intent.value,
            confidence=decision.result.confidence, # Correct: intent classification confidence
            citations=[c.model_dump() for c in result.citations],
            metadata={
                **result.metadata,
                "verification_confidence": result.confidence, # Now separate
                "processing_time_ms": processing_time_ms,
                "router_method": decision.result.method,
            },
            citation_chunks=result.citation_chunks,
            requires_human_review=result.requires_human_review,
        )
    

    def _build_error_output(self, input_data: AnswerQueryInput, error: str) -> AnswerQueryOutput:
        """Build error response when agent fails."""
        return AnswerQueryOutput(
            answer="عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.",
            intent="unknown",
            confidence=0.0,
            citations=[],
            metadata={"error": error},
            requires_human_review=True,
        )


# Singleton instance
_instance: Optional[AnswerQueryUseCase] = None


def get_answer_query_use_case(agent_registry: Any = None, router: Any = None) -> AnswerQueryUseCase:
    """Get or create global use case instance."""
    global _instance
    if _instance is None:
        _instance = AnswerQueryUseCase(agent_registry=agent_registry, router=router)
    return _instance

#default use case 
answer_query_use_case =AnswerQueryUseCase()