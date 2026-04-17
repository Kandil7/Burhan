"""
Agent Registry for Athar Islamic QA System.

Centralized agent management with lazy initialization.
Supports dynamic agent loading, intent-based routing, and collection-aware retrieval.

Phase 9: Added centralized agent registry with lazy initialization.
Epic 6: Added collection-aware agent registration with explicit mappings.
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


# ==========================================
# Collection Policy Mappings
# ==========================================

# Maps agent names to the collections they handle
AGENT_COLLECTION_MAPPING: dict[str, list[str]] = {
    "fiqh": ["fiqh_passages", "usul_fiqh"],
    "hadith": ["hadith_passages"],
    "seerah": ["seerah_passages"],
    "tafsir": ["tafsir_passages", "quran_tafsir"],
    "aqeedah": ["aqeedah_passages"],
    "history": ["history_passages", "islamic_history_passages"],
    "language": ["language_passages", "arabic_language_passages"],
    "tazkiyah": ["tazkiyah_passages", "spirituality_passages"],
    "usul_fiqh": ["usul_fiqh_passages", "usul_fiqh"],
    "general_islamic": ["general_islamic"],
    "chatbot": [],  # No collection - fallback only
}

# Intent to agent mapping (updated for Epic 6)
INTENT_TO_AGENT: dict[Intent, str] = {
    Intent.FIQH: "fiqh",
    Intent.QURAN: "tafsir",  # Tafsir handles Quran interpretation
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic",
    Intent.HADITH: "hadith",
    Intent.SEERAH: "seerah",
    Intent.TAFSIR: "tafsir",  # Dedicated tafsir agent
    Intent.AQEEDAH: "aqeedah",  # Dedicated aqeedah agent
    Intent.USUL_FIQH: "usul_fiqh",  # Dedicated usul_fiqh agent
    Intent.ISLAMIC_HISTORY: "history",  # Dedicated history agent
    Intent.ARABIC_LANGUAGE: "language",  # Dedicated language agent
    Intent.GREETING: "chatbot",
}

# Collection-specific retrieval policies
COLLECTION_POLICIES: dict[str, dict[str, Any]] = {
    "fiqh_passages": {
        "score_threshold": 0.65,
        "top_k": 15,
        "verification_enabled": True,
        "verification_policy": "fiqh",
        "requires_school_context": True,
    },
    "hadith_passages": {
        "score_threshold": 0.50,
        "top_k": 10,
        "verification_enabled": True,
        "verification_policy": "hadith",
        "requires_grade": True,
    },
    "tafsir_passages": {
        "score_threshold": 0.15,
        "top_k": 12,
        "verification_enabled": True,
        "verification_policy": "tafsir",
        "requires_verse_reference": True,
    },
    "quran_tafsir": {
        "score_threshold": 0.15,
        "top_k": 12,
        "verification_enabled": True,
        "verification_policy": "tafsir",
        "requires_verse_reference": True,
    },
    "aqeedah_passages": {
        "score_threshold": 0.15,
        "top_k": 10,
        "verification_enabled": True,
        "verification_policy": "aqeedah",
        "requires_dalil": True,
    },
    "seerah_passages": {
        "score_threshold": 0.50,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "general",
    },
    "history_passages": {
        "score_threshold": 0.50,
        "top_k": 12,
        "verification_enabled": False,
        "verification_policy": "general",
    },
    "islamic_history_passages": {
        "score_threshold": 0.50,
        "top_k": 12,
        "verification_enabled": False,
        "verification_policy": "general",
    },
    "language_passages": {
        "score_threshold": 0.45,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "general",
    },
    "arabic_language_passages": {
        "score_threshold": 0.45,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "general",
    },
    "tazkiyah_passages": {
        "score_threshold": 0.45,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "tazkiyah",
    },
    "spirituality_passages": {
        "score_threshold": 0.45,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "tazkiyah",
    },
    "usul_fiqh_passages": {
        "score_threshold": 0.55,
        "top_k": 10,
        "verification_enabled": True,
        "verification_policy": "usul_fiqh",
        "requires_dalil": True,
    },
    "usul_fiqh": {
        "score_threshold": 0.65,
        "top_k": 15,
        "verification_enabled": True,
        "verification_policy": "usul_fiqh",
        "requires_dalil": True,
    },
    "general_islamic": {
        "score_threshold": 0.35,
        "top_k": 10,
        "verification_enabled": False,
        "verification_policy": "general",
    },
}


def get_collection_policy(collection: str) -> dict[str, Any]:
    """Get retrieval policy for a specific collection."""
    return COLLECTION_POLICIES.get(
        collection,
        {
            "score_threshold": 0.50,
            "top_k": 10,
            "verification_enabled": False,
            "verification_policy": "general",
        },
    )


def get_agent_collections(agent_name: str) -> list[str]:
    """Get list of collections handled by an agent."""
    return AGENT_COLLECTION_MAPPING.get(agent_name, [])


def resolve_collection_for_intent(intent: Intent) -> str | None:
    """Resolve the primary collection for a given intent."""
    agent_name = INTENT_TO_AGENT.get(intent)
    if agent_name:
        collections = get_agent_collections(agent_name)
        return collections[0] if collections else None
    return None


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

        # Get policy for collection
        policy = registry.get_collection_policy("fiqh_passages")
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
        from src.agents.tafsir_agent import TafsirAgent
        from src.agents.aqeedah_agent import AqeedahAgent
        from src.agents.history_agent import HistoryAgent
        from src.agents.language_agent import LanguageAgent
        from src.agents.tazkiyah_agent import TazkiyahAgent
        from src.agents.usul_fiqh_agent import UsulFiqhAgent

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
            self._agents["tafsir"] = TafsirAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["aqeedah"] = AqeedahAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["history"] = HistoryAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["language"] = LanguageAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["tazkiyah"] = TazkiyahAgent(
                embedding_model=self._embedding_model,
                vector_store=self._vector_store,
                llm_client=self._llm_client,
            )
            self._agents["usul_fiqh"] = UsulFiqhAgent(
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
        """Get agent for intent using updated mapping."""
        agent_name = INTENT_TO_AGENT.get(intent)
        return self._agents.get(agent_name) if agent_name else None

    def get_for_collection(self, collection: str) -> "BaseAgent | None":
        """Get agent for a specific collection."""
        for agent_name, collections in AGENT_COLLECTION_MAPPING.items():
            if collection in collections:
                return self._agents.get(agent_name)
        return None

    def get_collection_policy(self, collection: str) -> dict[str, Any]:
        """Get retrieval policy for a specific collection."""
        return get_collection_policy(collection)

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

    def create_tafsir_agent(self) -> "TafsirAgent":
        """Create Tafsir agent."""
        from src.agents.tafsir_agent import TafsirAgent

        return TafsirAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_aqeedah_agent(self) -> "AqeedahAgent":
        """Create Aqeedah agent."""
        from src.agents.aqeedah_agent import AqeedahAgent

        return AqeedahAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_history_agent(self) -> "HistoryAgent":
        """Create History agent."""
        from src.agents.history_agent import HistoryAgent

        return HistoryAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_language_agent(self) -> "LanguageAgent":
        """Create Language agent."""
        from src.agents.language_agent import LanguageAgent

        return LanguageAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_tazkiyah_agent(self) -> "TazkiyahAgent":
        """Create Tazkiyah agent."""
        from src.agents.tazkiyah_agent import TazkiyahAgent

        return TazkiyahAgent(
            embedding_model=self._embedding_model,
            vector_store=self._vector_store,
            llm_client=self._llm_client,
        )

    def create_usul_fiqh_agent(self) -> "UsulFiqhAgent":
        """Create UsulFiqh agent."""
        from src.agents.usul_fiqh_agent import UsulFiqhAgent

        return UsulFiqhAgent(
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
