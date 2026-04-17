"""
Retrieval Strategies Module

Defines collection-aware retrieval strategies for each agent in the Multi-Agent RAG system.
Each agent has optimized dense/sparse weights, top_k, reranking, and score thresholds.
"""

from src.agents.collection_agent import RetrievalStrategy

# Default strategy for unknown agents
DEFAULT_STRATEGY = RetrievalStrategy(
    dense_weight=0.5,
    sparse_weight=0.5,
    top_k=30,
    rerank=False,
    score_threshold=0.55,
)

# Retrieval matrix mapping agent names to their retrieval strategies
retrieval_matrix: dict[str, RetrievalStrategy] = {
    "fiqh_agent": RetrievalStrategy(
        dense_weight=0.6,
        sparse_weight=0.4,
        top_k=80,
        rerank=True,
        score_threshold=0.65,
    ),
    "hadith_agent": RetrievalStrategy(
        dense_weight=0.5,
        sparse_weight=0.5,
        top_k=60,
        rerank=True,
        score_threshold=0.70,
    ),
    "tafsir_agent": RetrievalStrategy(
        dense_weight=0.7,
        sparse_weight=0.3,
        top_k=40,
        rerank=True,
        score_threshold=0.75,
    ),
    "aqeedah_agent": RetrievalStrategy(
        dense_weight=0.6,
        sparse_weight=0.4,
        top_k=50,
        rerank=True,
        score_threshold=0.65,
    ),
    "seerah_agent": RetrievalStrategy(
        dense_weight=0.5,
        sparse_weight=0.5,
        top_k=50,
        rerank=True,
        score_threshold=0.60,
    ),
    "usul_fiqh_agent": RetrievalStrategy(
        dense_weight=0.7,
        sparse_weight=0.3,
        top_k=60,
        rerank=True,
        score_threshold=0.70,
    ),
    "history_agent": RetrievalStrategy(
        dense_weight=0.5,
        sparse_weight=0.5,
        top_k=50,
        rerank=True,
        score_threshold=0.60,
    ),
    "language_agent": RetrievalStrategy(
        dense_weight=0.4,
        sparse_weight=0.6,
        top_k=40,
        rerank=True,
        score_threshold=0.65,
    ),
    "general_islamic_agent": RetrievalStrategy(
        dense_weight=0.5,
        sparse_weight=0.5,
        top_k=30,
        rerank=False,
        score_threshold=0.55,
    ),
}

# Collection name mapping for each agent
COLLECTION_MAP: dict[str, str] = {
    "fiqh_agent": "fiqh",
    "hadith_agent": "hadith",
    "tafsir_agent": "quran",  # Maps to Quran collection (tafsir if exists)
    "aqeedah_agent": "aqeedah",
    "seerah_agent": "seerah",
    "usul_fiqh_agent": "usul_fiqh",
    "history_agent": "islamic_history",
    "language_agent": "arabic_language",
    "general_islamic_agent": "general_islamic",
}


def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy:
    """
    Get the retrieval strategy for a specific agent.

    Args:
        agent_name: The name of the agent (e.g., "fiqh_agent", "hadith_agent")

    Returns:
        RetrievalStrategy: The configured strategy for the agent,
                        or default strategy if agent not found
    """
    return retrieval_matrix.get(agent_name, DEFAULT_STRATEGY)


def get_collection_for_agent(agent_name: str) -> str:
    """
    Get the Qdrant collection name for a specific agent.

    Args:
        agent_name: The name of the agent (e.g., "fiqh_agent", "hadith_agent")

    Returns:
        str: The collection name, or "unknown" if agent not found
    """
    return COLLECTION_MAP.get(agent_name, "unknown")
