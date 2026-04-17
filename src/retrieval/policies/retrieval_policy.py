# Retrieval Policy Module
"""Policies for controlling retrieval behavior."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class RetrievalStrategy(str, Enum):
    """Available retrieval strategies."""

    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    HIERARCHICAL = "hierarchical"
    MULTI_COLLECTION = "multi_collection"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval operations."""

    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    top_k: int = 10
    min_relevance_score: float = 0.5
    enable_reranking: bool = True
    rerank_top_n: int = 5
    enable_expansion: bool = True
    expansion_terms: Optional[List[str]] = None


class RetrievalPolicy:
    """Policy for controlling retrieval behavior."""

    def __init__(self):
        self.default_config = RetrievalConfig()

    def get_config_for_intent(self, intent: Optional[str] = None) -> RetrievalConfig:
        """Get retrieval config based on query intent."""
        # Placeholder - return default config for now
        return self.default_config

    def should_use_reranking(self, query: str) -> bool:
        """Determine if reranking should be used."""
        # Placeholder - always enable for now
        return True

    def should_expand_query(self, query: str) -> bool:
        """Determine if query expansion should be used."""
        # Placeholder - always enable for now
        return True


# Default policy instance
retrieval_policy = RetrievalPolicy()
