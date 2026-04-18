# Retrieval Module
# Multi-Agent Collection-Aware RAG System

# Import from canonical v2 location
from src.agents.collection.base import RetrievalStrategy
from src.retrieval.strategies import (
    retrieval_matrix,
    get_strategy_for_agent,
    get_collection_for_agent,
)
from src.retrieval.retrievers.hybrid_retriever import HybridRetriever
from src.retrieval.retrievers.bm25_retriever import BM25Retriever
from src.retrieval.retrievers.dense_retriever import DenseRetriever
from src.retrieval.schemas import RetrievalResult, RetrievalQuery

__all__ = [
    # Strategy
    "RetrievalStrategy",
    "retrieval_matrix",
    "get_strategy_for_agent",
    "get_collection_for_agent",
    # Retrievers
    "HybridRetriever",
    "BM25Retriever",
    "DenseRetriever",
    # Schemas
    "RetrievalResult",
    "RetrievalQuery",
]
