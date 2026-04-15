"""
Application interfaces (Protocols) for Athar Islamic QA system.

Defines the contracts that classifiers and routers must implement:
- IntentClassifier: Classifies raw query strings into ClassificationResult
- Router: Resolves query to RoutingDecision (intent + route + metadata)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import ClassificationResult
from src.application.models import RoutingDecision


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
