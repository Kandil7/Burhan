"""
Application interfaces (Protocols) for Athar Islamic QA system.

Defines the contracts that classifiers and routers must implement:
- IntentClassifier: Classifies raw query strings into ClassificationResult
- Router: Resolves query to RoutingDecision (intent + route + metadata)
- Retriever: Document retrieval protocol
- Generator: Answer generation protocol

Phase 9: Enhanced with Retriever and Generator protocols.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import ClassificationResult
from src.application.models import RoutingDecision


# ==========================================
# Core Protocols
# ==========================================


@runtime_checkable
class IntentClassifier(Protocol):
    """
    Classifies a raw query string into a ClassificationResult.

    Implementations:
    - HybridIntentClassifier  (keyword + Jaccard fallback)  — Phase 1
    - LLMIntentClassifier     (OpenAI-compatible LLM)       — Phase 3
    - EmbeddingClassifier     (Qwen3-Embedding cosine sim)  — Phase 5
    """

    async def classify(self, query: str) -> ClassificationResult:
        """Classify a query into an intent."""
        ...

    async def close(self) -> None:
        """Clean up resources. Optional."""
        ...


@runtime_checkable
class Router(Protocol):
    """
    Resolves a query to a RoutingDecision (intent + route + metadata).

    Wraps an IntentClassifier and applies confidence gating,
    sub-intent resolution, and route construction.
    """

    async def route(self, query: str) -> RoutingDecision:
        """Route a query and return a routing decision."""
        ...

    async def close(self) -> None:
        """Clean up resources. Optional."""
        ...

    @property
    def classifier(self) -> IntentClassifier:
        """Get the underlying classifier."""
        ...


# ==========================================
# RAG Protocols
# ==========================================


class RetrievalResult:
    """Structured retrieval result with metadata."""

    def __init__(
        self,
        content: str,
        source: str,
        score: float,
        metadata: dict | None = None,
    ):
        self.content = content
        self.source = source
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "source": self.source,
            "score": self.score,
            "metadata": self.metadata,
        }


@runtime_checkable
class Retriever(Protocol):
    """
    Document retrieval protocol.

    Implementations:
    - VectorStoreRetriever: Qdrant-based semantic retrieval
    - BM25Retriever: Keyword-based retrieval
    - HybridRetriever: Combined semantic + keyword
    """

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve documents for query."""
        ...

    async def initialize(self) -> None:
        """Initialize the retriever."""
        ...

    async def close(self) -> None:
        """Clean up resources."""
        ...


@runtime_checkable
class Generator(Protocol):
    """
    Answer generation protocol.

    Implementations:
    - LLMGenerator: OpenAI/Groq-based generation
    - FallbackGenerator: Template-based fallback
    """

    async def generate(
        self,
        query: str,
        context: list[RetrievalResult],
        language: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate answer from context."""
        ...

    async def close(self) -> None:
        """Clean up resources."""
        ...


@runtime_checkable
class Reranker(Protocol):
    """
    Document reranking protocol.

    Implementations:
    - CrossEncoderReranker: Cross-encoder based reranking
    - LLMReranker: LLM-based reranking
    """

    async def rerank(
        self,
        query: str,
        passages: list[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Rerank retrieval results."""
        ...


# ==========================================
# Cache Protocols
# ==========================================


@runtime_checkable
class EmbeddingCache(Protocol):
    """Embedding cache protocol."""

    async def get(
        self,
        text: str,
        model: str,
    ) -> list[float] | None:
        """Get cached embedding."""
        ...

    async def set(
        self,
        text: str,
        model: str,
        embedding: list[float],
    ) -> None:
        """Cache embedding."""
        ...


@runtime_checkable
class QueryCache(Protocol):
    """Query result cache protocol."""

    async def get(self, key: str) -> dict | None:
        """Get cached query result."""
        ...

    async def set(self, key: str, value: dict) -> None:
        """Cache query result."""
        ...
