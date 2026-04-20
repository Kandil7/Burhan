# Retrieval Module
# Multi-Agent Collection-Aware RAG System

# Import from canonical v2 location
from src.agents.collection.base import RetrievalStrategy
from src.retrieval.strategies import (
    retrieval_matrix,
    get_strategy_for_agent,
    get_collection_for_agent,
)
from src.retrieval.retrievers.hybrid_searcher import HybridSearcher
from src.retrieval.retrievers.bm25_retriever import BM25Retriever
from src.retrieval.retrievers.dense_retriever import DenseRetriever
from src.retrieval.schemas import RetrievalResult
from src.retrieval.schemas import QueryType as RetrievalQuery

__all__ = [
    # Strategy
    "RetrievalStrategy",
    "retrieval_matrix",
    "get_strategy_for_agent",
    "get_collection_for_agent",
    # Retrievers
    "HybridSearcher",
    "BM25Retriever",
    "DenseRetriever",
    # Schemas
    "RetrievalResult",
    "RetrievalQuery",  # alias for QueryType
]
