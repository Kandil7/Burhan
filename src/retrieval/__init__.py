# Retrieval Module
# Multi-Agent Collection-Aware RAG System

# Import from canonical v2 location
from src.agents.collection.base import RetrievalStrategy
from src.retrieval.strategies import (
    retrieval_matrix,
    get_strategy_for_agent,
    get_collection_for_agent,
)

__all__ = [
    "RetrievalStrategy",
    "retrieval_matrix",
    "get_strategy_for_agent",
    "get_collection_for_agent",
]
