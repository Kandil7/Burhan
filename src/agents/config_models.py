"""
Configuration models for collection agents.

Kept as a separate module when the ten agent classes collapsed into the
spec-driven RAGPipeline (hardening Phase 5): the retrieval layer and the
config manager still describe strategies and fallbacks with these models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.verification import (
    VerificationSuite,
)


class RetrievalStrategy(BaseModel):
    """Configuration for retrieval pipeline."""

    dense_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for dense (semantic) retrieval",
    )
    sparse_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for sparse (keyword) retrieval",
    )
    top_k: int = Field(
        default=12,
        ge=1,
        le=100,
        description="Number of candidates to retrieve",
    )
    rerank: bool = Field(default=True, description="Whether to apply reranking")
    score_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold for inclusion",
    )


class FallbackPolicy(BaseModel):
    """Fallback strategy when primary retrieval fails or is insufficient."""

    strategy: str = Field(
        default="chatbot",
        description="Strategy: chatbot/human_review/clarify",
    )
    message: str | None = Field(default=None, description="Custom fallback message")


class CollectionAgentConfig(BaseModel):
    """Complete configuration for a CollectionAgent."""

    collection_name: str = Field(description="Qdrant collection name")
    strategy: RetrievalStrategy = Field(
        default_factory=RetrievalStrategy,
        description="Retrieval strategy configuration",
    )
    verification_suite: VerificationSuite = Field(
        default_factory=VerificationSuite,
        description="Verification suite configuration",
    )
    fallback_policy: FallbackPolicy = Field(
        default_factory=FallbackPolicy,
        description="Fallback policy configuration",
    )
    system_prompt: str = Field(
        default="",
        description="Optional system prompt loaded from the prompt file",
    )
