"""
Collection Policy for Burhan retrieval system.

Defines retrieval policies for different Athar-Datasets
collections, including priority, weighting, and filtering rules.

Phase 9: Added collection policy for collection-aware retrieval.
"""

from __future__ import annotations

from typing import Any


class CollectionPolicy:
    """
    Retrieval policy for a specific collection.

    Defines how documents from this collection should be
    weighted, filtered, and prioritized during retrieval.

    Usage:
        policy = CollectionPolicy(
            collection="fiqh_passages",
            priority=1.0,
            weight=1.0,
            max_results=20,
        )
    """

    def __init__(
        self,
        collection: str,
        priority: float = 1.0,
        weight: float = 1.0,
        max_results: int = 20,
        min_score: float = 0.0,
        filters: dict[str, Any] | None = None,
        boost_authors: list[str] | None = None,
        exclude_authors: list[str] | None = None,
    ):
        """
        Initialize collection policy.

        Args:
            collection: Collection identifier
            priority: Priority weight (0.0-1.0) for this collection
            weight: Score multiplier for this collection's results
            max_results: Maximum results to return from this collection
            min_score: Minimum score threshold
            filters: Default filters to apply
            boost_authors: Authors to boost in rankings
            exclude_authors: Authors to exclude
        """
        self.collection = collection
        self.priority = priority
        self.weight = weight
        self.max_results = max_results
        self.min_score = min_score
        self.filters = filters or {}
        self.boost_authors = boost_authors or []
        self.exclude_authors = exclude_authors or []

    def apply_weight(self, score: float) -> float:
        """
        Apply collection weight to a score.

        Args:
            score: Original score

        Returns:
            Weighted score
        """
        return score * self.weight

    def apply_filters(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Apply collection-specific filters to documents.

        Args:
            documents: List of document dicts

        Returns:
            Filtered documents
        """
        filtered = []

        for doc in documents:
            # Check exclude authors
            author = doc.get("author", "")
            if author in self.exclude_authors:
                continue

            # Check minimum score
            score = doc.get("score", 0)
            if score < self.min_score:
                continue

            filtered.append(doc)

        return filtered

    def should_boost_author(self, author: str) -> bool:
        """
        Check if author should be boosted.

        Args:
            author: Author name

        Returns:
            True if author should be boosted
        """
        return author in self.boost_authors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "collection": self.collection,
            "priority": self.priority,
            "weight": self.weight,
            "max_results": self.max_results,
            "min_score": self.min_score,
            "filters": self.filters,
            "boost_authors": self.boost_authors,
            "exclude_authors": self.exclude_authors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CollectionPolicy:
        """Create from dictionary."""
        return cls(
            collection=data["collection"],
            priority=data.get("priority", 1.0),
            weight=data.get("weight", 1.0),
            max_results=data.get("max_results", 20),
            min_score=data.get("min_score", 0.0),
            filters=data.get("filters", {}),
            boost_authors=data.get("boost_authors", []),
            exclude_authors=data.get("exclude_authors", []),
        )


# ==========================================
# Default Collection Policies
# ==========================================

DEFAULT_POLICIES: dict[str, CollectionPolicy] = {
    # Hadith collections - highest priority
    "hadith_passages": CollectionPolicy(
        collection="hadith_passages",
        priority=1.0,
        weight=1.2,
        max_results=15,
        min_score=0.3,
    ),
    # Fiqh collections
    "fiqh_passages": CollectionPolicy(
        collection="fiqh_passages",
        priority=0.95,
        weight=1.1,
        max_results=20,
        min_score=0.25,
    ),
    # Quran/Tafsir
    "quran_passages": CollectionPolicy(
        collection="quran_passages",
        priority=0.9,
        weight=1.0,
        max_results=10,
        min_score=0.35,
    ),
    # General Islamic
    "general_passages": CollectionPolicy(
        collection="general_passages",
        priority=0.7,
        weight=0.8,
        max_results=10,
        min_score=0.2,
    ),
}


def get_collection_policy(collection: str) -> CollectionPolicy:
    """
    Get policy for a collection.

    Args:
        collection: Collection identifier

    Returns:
        Collection policy (or default policy)
    """
    return DEFAULT_POLICIES.get(
        collection,
        CollectionPolicy(collection=collection),
    )


def get_all_policies() -> dict[str, CollectionPolicy]:
    """Get all default policies."""
    return DEFAULT_POLICIES.copy()
