"""
Schemas for /classify endpoint.

Request/response models for intent classification.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    """Request model for intent classification."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Query to classify",
        examples=["ما حكم ترك صلاة الجمعة عمداً؟", "What is the ruling on zakah?"],
    )


class ClassificationResult(BaseModel):
    """Classification result details."""

    intent: str = Field(
        ...,
        description="Detected intent",
        examples=["fiqh", "quran", "hadith", "seerah"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence (0.0-1.0)",
    )
    language: str = Field(
        ...,
        description="Detected query language",
        examples=["ar", "en"],
    )
    reasoning: str = Field(
        ...,
        description="Classification reasoning",
    )
    requires_retrieval: bool = Field(
        ...,
        description="Whether retrieval is needed for this query",
    )
    method: str = Field(
        ...,
        description="Classification method used",
        examples=["keyword", "hybrid", "jaccard", "llm"],
    )
    quran_subintent: str | None = Field(
        None,
        description="Quran-specific subintent (if applicable)",
        examples=["verse_lookup", "tafsir", "quranic_advice"],
    )
    subquestions: list[str] = Field(
        default_factory=list,
        description="Extracted sub-questions for complex queries",
    )


class RoutingDecision(BaseModel):
    """Full routing decision from classifier."""

    result: ClassificationResult = Field(
        ...,
        description="Classification result",
    )
    route: str = Field(
        ...,
        description="Recommended route",
        examples=["/api/v1/ask", "/api/v1/tools/zakat"],
    )
    agent_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent metadata",
    )


class ClassifyResponse(BaseModel):
    """Response model for classification endpoint."""

    result: ClassificationResult = Field(
        ...,
        description="Classification result",
    )
    route: str = Field(
        ...,
        description="Recommended route",
    )
    agent_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent metadata",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
