"""
Retrieval Schemas for Athar Islamic QA system.

This module defines the canonical data schemas for the retrieval layer.
These are used across retrieval, verification, and generation components.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RetrievalMethod(str, Enum):
    """Retrieval method types."""

    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    BM25 = "bm25"


class QueryType(str, Enum):
    """Query classification types."""

    FIQH = "fiqh"
    HADITH = "hadith"
    TAFSIR = "tafsir"
    AQEEDAH = "aqeedah"
    SEERAH = "seerah"
    USUL_FIQH = "usul_fiqh"
    HISTORY = "history"
    LANGUAGE = "language"
    TAZKIYAH = "tazkiyah"
    GENERAL = "general"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class RetrievalPassage(BaseModel):
    """
    Standardized passage representation from retrieval.
    This is the canonical format for passing passages between retrieval and verification.
    """

    content: str = Field(description="Passage text content")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Retrieval score")
    score_vector: float | None = Field(default=None, description="Semantic score component")
    score_sparse: float | None = Field(default=None, description="Keyword score component")
    rank: int = Field(default=0, description="Rank after reranking")
    collection: str = Field(description="Source collection name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        frozen = False


class RetrievalResult(BaseModel):
    """Result from a retrieval operation."""

    query: str = Field(description="Original query")
    method: RetrievalMethod = Field(description="Retrieval method used")
    passages: list[RetrievalPassage] = Field(default_factory=list, description="Retrieved passages")
    total_found: int = Field(default=0, description="Total passages found before filtering")
    query_expansion: list[str] | None = Field(default=None, description="Expanded query terms")
    filters_applied: dict[str, Any] | None = Field(default=None, description="Metadata filters used")
    timing_ms: float | None = Field(default=None, description="Retrieval time in milliseconds")


class RerankedResult(BaseModel):
    """Result after reranking."""

    original_result: RetrievalResult = Field(description="Original retrieval result")
    reranked_passages: list[RetrievalPassage] = Field(default_factory=list, description="Reranked passages")
    reranking_method: str = Field(default="default", description="Reranking method used")
    timing_ms: float | None = Field(default=None, description="Reranking time in milliseconds")


class FusionConfig(BaseModel):
    """Configuration for score fusion."""

    method: str = Field(default="rrf", description="Fusion method: rrf, weighted, etc.")
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight for dense scores")
    sparse_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight for sparse scores")
    rrf_k: int = Field(default=60, description="RRF k parameter")


class FilterConfig(BaseModel):
    """Configuration for metadata filtering."""

    field: str = Field(description="Metadata field to filter on")
    operator: str = Field(description="Operator: eq, ne, gt, gte, lt, lte, in, nin")
    value: Any = Field(description="Filter value")


class QueryExpansionConfig(BaseModel):
    """Configuration for query expansion."""

    enabled: bool = Field(default=True, description="Enable query expansion")
    expanders: list[str] = Field(
        default_factory=lambda: ["islamic_synonyms"], description="List of expander names to apply"
    )
    max_terms: int = Field(default=10, description="Maximum number of expansion terms")


__all__ = [
    "RetrievalMethod",
    "QueryType",
    "RetrievalPassage",
    "RetrievalResult",
    "RerankedResult",
    "FusionConfig",
    "FilterConfig",
    "QueryExpansionConfig",
]
