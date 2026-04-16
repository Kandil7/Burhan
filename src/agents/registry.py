"""
Agent Registry for Athar Islamic QA System.

Centralized agent management with lazy initialization.
Supports dynamic agent loading and intent-based routing.

Phase 9: Added centralized agent registry with lazy initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.logging_config import get_logger
from src.domain.intents import Intent

if TYPE_CHECKING:
    from src.agents.base import BaseAgent
    from src.knowledge.vector_store import VectorStore
    from src.knowledge.embedding_model import EmbeddingModel
    from src.infrastructure.llm_client import LLMClient

logger = get_logger()


class AgentRegistry:
    """
    Central agent registry with lazy initialization.

    Manages all agents in the system and provides lookup by intent.

    Usage:
        registry = AgentRegistry(llm_client, vector_store, embedding_model)
        await registry.initialize()

        # Get by name
        agent = registry.get("fiqh")

        # Get by intent
        agent = registry.get_for_intent(Intent.FIQH)
    """

    def __init__(
        self,
        llm_client: "LLMClient | None" = None,
        vector_store: "VectorStore | None" = None,
        embedding_model: "EmbeddingModel | None" = None,
    ):
        self._agents: dict[str, "BaseAgent"] = {}
        self._llm_client = llm_client
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all agents lazily."""
        if self._initialized:
            return

        logger.info("agent_registry.initializing")

        # Import agents lazily to avoid circular imports
        from src.agents.chatbot_agent import ChatbotAgent
        from src.agents.fiqh_agent import FiqhAgent
        from src.agents.hadith_agent import HadithAgent
        from src.agents.seerah_agent import SeerahAgent
        from src.agents.general_islamic_agent import GeneralIslamicAgent
        from src.agents.fiqh_agent import FiqhAgent

        # Initialize chatbot (no dependencies)
        self._agents["chatbot"] = ChatbotAgent()

        # Initialize RAG agents (require dependencies)
        if self._embedding_model and self._vector_store and self._llm_client:
            self._agents["fiqh"] = FiqhAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["hadith"] = HadithAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["seerah"] = SeerahAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["general_islamic"] = GeneralIslamicAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )

            logger.info(
                "agent_registry.initialized",
                agent_count=len(self._agents),
            )
        else:
            logger.warning(
                "agent_registry.partial_init",
                llm_client=bool(self._llm_client),
                vector_store=bool(self._vector_store),
                embedding_model=bool(self._embedding_model),
            )

        self._initialized = True

    def get(self, name: str) -> "BaseAgent | None":
        """Get agent by name."""
        return self._agents.get(name)

    def get_for_intent(self, intent: Intent) -> "BaseAgent | None":
        """Get agent for intent."""
        intent_to_agent = {
            Intent.FIQH: "fiqh",
            Intent.HADITH: "hadith",
            Intent.QURAN: "quran",
            Intent.SEERAH: "seerah",
            Intent.ISLAMIC_KNOWLEDGE: "general_islamic",
            Intent.GREETING: "chatbot",
            Intent.TAFSIR: "quran",
            Intent.AQEEDAH: "fiqh",
            Intent.USUL_FIQH: "fiqh",
            Intent.ISLAMIC_HISTORY: "seerah",
            Intent.ARABIC_LANGUAGE: "general_islamic",
        }
        agent_name = intent_to_agent.get(intent)
        return self._agents.get(agent_name) if agent_name else None

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    async def close(self) -> None:
        """Close all agents."""
        for name, agent in self._agents.items():
            if hasattr(agent, "close"):
                try:
                    await agent.close()
                except Exception as e:
                    logger.warning(
                        "agent_registry.close_error",
                        agent=name,
                        error=str(e),
                    )

        self._agents.clear()
        self._initialized = False
        logger.info("agent_registry.closed")

    @property
    def is_initialized(self) -> bool:
        """Check if registry is initialized."""
        return self._initialized


# ==========================================
# Agent Factory
# ==========================================


class AgentFactory:
    """Factory for creating agents with dependencies."""

    def __init__(
        self,
        llm_client: "LLMClient",
        vector_store: "VectorStore",
        embedding_model: "EmbeddingModel",
    ):
        self._llm_client = llm_client
        self._vector_store = vector_store
        self._embedding_model = embedding_model

    def create_fiqh_agent(self) -> "FiqhAgent":
        """Create Fiqh agent."""
        from src.agents.fiqh_agent import FiqhAgent

        return FiqhAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_hadith_agent(self) -> "HadithAgent":
        """Create Hadith agent."""
        from src.agents.hadith_agent import HadithAgent

        return HadithAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_seerah_agent(self) -> "SeerahAgent":
        """Create Seerah agent."""
        from src.agents.seerah_agent import SeerahAgent

        return SeerahAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_general_agent(self) -> "GeneralIslamicAgent":
        """Create General Islamic agent."""
        from src.agents.general_islamic_agent import GeneralIslamicAgent

        return GeneralIslamicAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_chatbot_agent(self) -> "ChatbotAgent":
        """Create Chatbot agent."""
        from src.agents.chatbot_agent import ChatbotAgent

        return ChatbotAgent()
