"""
Ports: the narrow interfaces through which the application touches the
outside world.

Every effect on a database, a model, or a tool call goes through one of these
four protocols. The protocols describe the surface the concrete adapters
already have, so today's infrastructure satisfies them structurally with no
wrapper. When Phase 5 lands the RAG pipeline, its calls narrow onto these
ports and the concrete clients move behind adapters.

The layer rules (docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md):

- this module imports nothing from the project
- application code depends on these protocols, never on the adapters
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy.typing as npt

NDArray = npt.NDArray[Any]


class ToolResult(Protocol):
    """Structural match for the tools' output model."""

    result: dict[str, Any]
    success: bool
    error: str
    metadata: dict[str, Any]


@runtime_checkable
class VectorSearchPort(Protocol):
    """Read side of the vector store."""

    async def search(
        self,
        collection: str,
        query_embedding: NDArray,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Return scored payload dicts for one collection."""
        ...

    async def search_with_score_threshold(
        self,
        collection: str,
        query_embedding: NDArray,
        top_k: int = 10,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """Return scored payload dicts above a similarity floor."""
        ...

    def list_collections(self) -> list[str]:
        """Names of the collections the store holds."""
        ...

    def get_collection_stats(self, collection: str) -> dict:
        """Row counts and status for one collection."""
        ...


@runtime_checkable
class EmbeddingPort(Protocol):
    """Text embedding."""

    MODEL_NAME: str

    async def encode_query(self, query: str) -> NDArray:
        """Encode one query into a single vector."""
        ...

    async def encode(self, texts: list[str], batch_size: int | None = None) -> NDArray:
        """Encode raw texts into a matrix of vectors."""
        ...

    async def encode_documents(
        self,
        documents: list[dict],
        text_field: str = "content",
    ) -> NDArray:
        """Encode payload dicts by extracting one text field."""
        ...


@runtime_checkable
class LLMPort(Protocol):
    """Text generation."""

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a plain-text completion."""
        ...

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """Generate and parse a JSON completion."""
        ...


@runtime_checkable
class ToolPort(Protocol):
    """One deterministic tool."""

    name: str

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Run the tool and return its structured result."""
        ...
