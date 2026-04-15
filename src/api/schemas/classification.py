"""
Pydantic schemas for classification API.

Provides request/response models for the /classify endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    """Request model for intent classification."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["ما حكم ترك صلاة الجمعة عمداً؟"],
    )


class ClassificationResultSchema(BaseModel):
    """Schema for classification result."""

    intent: str
    confidence: float
    language: str
    reasoning: str
    requires_retrieval: bool
    method: str
    quran_subintent: Optional[str] = None
    subquestions: List[str] = []


class RoutingDecisionSchema(BaseModel):
    """Full response returned by POST /classify."""

    result: ClassificationResultSchema
    route: str
    agent_metadata: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
