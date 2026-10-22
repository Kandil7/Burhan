# Retrieval Module
# Multi-Agent Collection-Aware RAG System
#
# The designed retrieval layer (retrievers, ranking, fusion, expanders,
# filters, mapping, planning, policies, aggregation) was deleted in hardening
# Phase 7; see docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md.
# What remains is what the live tree uses: the strategy table and the hybrid
# searcher, which the evaluation harness keeps as the record of the dense
# versus keyword-rerank measurement.

# Import from canonical v2 location
from src.agents.collection.base import RetrievalStrategy
from src.retrieval.retrievers.hybrid_searcher import HybridSearcher
from src.retrieval.strategies import (
    get_collection_for_agent,
    get_strategy_for_agent,
    retrieval_matrix,
)

__all__ = [
    # Strategy
    "RetrievalStrategy",
    "retrieval_matrix",
    "get_strategy_for_agent",
    "get_collection_for_agent",
    # Retrievers
    "HybridSearcher",
]
