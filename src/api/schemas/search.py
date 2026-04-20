"""
Schemas for /search endpoint.

Request/response models for search and RAG operations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Basic search schemas
# ============================================================================


class SearchRequest(BaseModel):
    """Request model for basic search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Search query",
        examples=["زكاة المال", "prayer times"],
    )
    collection: str | None = Field(
        None,
        description="Specific collection to search (default: general_islamic)",
        examples=["fiqh", "quran", "hadith"],
    )
    language: str = Field(
        default="ar",
        pattern="^(ar|en)$",
        description="Query language",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of results to return",
    )
    filters: dict[str, Any] | None = Field(
        None,
        description="Additional search filters",
    )


class SearchResult(BaseModel):
    """Individual search result or source passage."""

    index: int | None = Field(
        default=None,
        description="Optional index used in generated answer citations ([1], [2], ...).",
    )
    score: float = Field(..., description="Relevance score")
    content: str = Field(..., description="Content text")
    content_truncated: bool = Field(
        default=False,
        description="Whether content was truncated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source metadata (book, page, collection, etc.)",
    )


class SearchResponse(BaseModel):
    """Response model for basic search endpoint."""

    query_id: str = Field(
        ...,
        description="Unique query ID for tracking (trace ID).",
    )
    query: str = Field(..., description="Original query")
    results: list[SearchResult] = Field(
        default_factory=list,
        description="Search results",
    )
    total: int = Field(..., ge=0, description="Total results found")
    collection: str | None = Field(
        None,
        description="Collection searched",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Search metadata (language, embedding model, etc.)",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
    )


# ============================================================================
# RAG-specific schemas
# ============================================================================


class RAGQueryRequest(BaseModel):
    """Request model for advanced RAG endpoints."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query",
    )
    language: str | None = Field(
        "ar",
        pattern="^(ar|en)$",
        description="Answer language (ar or en).",
    )
    madhhab: str | None = Field(
        None,
        pattern="^(hanafi|maliki|shafii|hanbali|auto)$",
        description="Target madhhab for fiqh questions (if applicable).",
    )
    top_k: int = Field(
        10,
        ge=1,
        le=20,
        description="Number of passages to retrieve for RAG context.",
    )


class RAGQueryResponse(BaseModel):
    """Response model for advanced RAG endpoints."""

    answer: str = Field(..., description="Generated answer")
    citations: list[dict] = Field(
        default_factory=list,
        description="Source citations (with mapping to passages).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata (retrieval stats, models, etc.).",
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0.0–1.0).",
    )
    requires_human_review: bool = Field(
        default=False,
        description="Whether human review is recommended.",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
    )


class RAGStatsResponse(BaseModel):
    """Response model for RAG stats endpoint."""

    collections: dict[str, Any] = Field(
        ...,
        description="Collection statistics (vectors_count, dimensions, etc.).",
    )
    total_documents: int = Field(
        ...,
        ge=0,
        description="Total documents across all collections.",
    )
    embedding_model: str = Field(
        ...,
        description="Embedding model name (e.g. BAAI/bge-m3).",
    )


class SimpleRAGRequest(BaseModel):
    """Request model for simple RAG endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query.",
    )
    collection: str = Field(
        default="all",
        description="Collection name or 'all' for default collections.",
    )
    language: str = Field(
        "ar",
        pattern="^(ar|en)$",
        description="Answer language.",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of passages to retrieve.",
    )


class SimpleRAGResponse(BaseModel):
    """Response model for simple RAG endpoint."""

    answer: str = Field(
        ...,
        description="Generated answer based on retrieved sources.",
    )
    sources: list[SearchResult] = Field(
        default_factory=list,
        description="Source documents actually used in generation.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Response metadata, including retrieval stats and model names. "
            "Expected keys: collection, retrieved_count, unique_count, "
            "context_passages, language, embedding_model, llm_model."
        ),
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
    )