"""
Schemas for /search endpoint.

Request/response models for search and RAG operations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Search query",
        examples=["زكاة المال", "prayer times"],
    )
    collection: str | None = Field(
        None,
        description="Specific collection to search (default: all)",
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
    """Individual search result."""

    score: float = Field(..., description="Relevance score")
    content: str = Field(..., description="Content text")
    content_truncated: bool = Field(
        default=False,
        description="Whether content was truncated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source metadata",
    )


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    query_id: str = Field(
        ...,
        description="Unique query ID for tracking",
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
        description="Search metadata",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


# ============================================================================
# RAG-specific schemas (merged from rag.py)
# ============================================================================


class RAGQueryRequest(BaseModel):
    """Request model for RAG endpoints."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query",
    )
    language: str | None = Field("ar", pattern="^(ar|en)$")
    madhhab: str | None = Field(
        None,
        pattern="^(hanafi|maliki|shafii|hanbali|auto)$",
    )
    top_k: int = Field(10, ge=1, le=20)


class RAGQueryResponse(BaseModel):
    """Response model for RAG endpoints."""

    answer: str = Field(..., description="Generated answer")
    citations: list[dict] = Field(
        default_factory=list,
        description="Source citations",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata",
    )
    confidence: float = Field(..., description="Confidence score")
    requires_human_review: bool = Field(
        default=False,
        description="Whether human review is needed",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


class RAGStatsResponse(BaseModel):
    """Response model for RAG stats endpoint."""

    collections: dict[str, Any] = Field(
        ...,
        description="Collection statistics",
    )
    total_documents: int = Field(..., ge=0, description="Total documents")
    embedding_model: str = Field(..., description="Embedding model name")


class SimpleRAGRequest(BaseModel):
    """Request model for simple RAG endpoint."""

    query: str = Field(..., min_length=1, max_length=2000)
    collection: str = Field(default="all")
    language: str = Field("ar", pattern="^(ar|en)$")
    top_k: int = Field(5, ge=1, le=20)


class SimpleRAGResponse(BaseModel):
    """Response model for simple RAG endpoint."""

    answer: str = Field(..., description="Generated answer")
    sources: list[dict] = Field(
        default_factory=list,
        description="Source documents",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
