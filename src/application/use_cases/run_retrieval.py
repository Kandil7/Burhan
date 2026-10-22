import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from src.application.ports import EmbeddingPort, VectorSearchPort

logger = logging.getLogger(__name__)


@dataclass
class RunRetrievalInput:
    query: str
    collections: list[str]
    top_k: int = 10
    enable_expansion: bool = True
    filters: dict[str, Any] | None = None


@dataclass
class RunRetrievalOutput:
    results: list[dict[str, Any]]
    query_expansions: list[str] | None = None
    retrieval_strategy: str = ""
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] | None = None


class RunRetrievalUseCase:
    """Use case for executing retrieval operations.

    One retrieval path: dense vector search through VectorSearchPort. The
    keyword re-rank left the live tree after the measured gate of 2026-10-21
    (REFACTOR_PLAN_HARDENING.md, Phase 4): it scored worse than dense on every
    measure of the golden set, so both the ask path and the search path now
    share the dense path.
    """

    def __init__(self, embedding_model: EmbeddingPort, vector_store: VectorSearchPort) -> None:
        self._embedding_model = embedding_model
        self._vector_store = vector_store

    async def execute(self, input: RunRetrievalInput) -> RunRetrievalOutput:
        start = time.time()

        # 1) Embed query once
        query_embedding = await self._embedding_model.encode_query(input.query)

        # 2) (optional) expansions: today the expansion list is the query itself
        query_expansions = [input.query] if input.enable_expansion else None

        all_results: list[dict[str, Any]] = []

        # 3) Dense search per collection, in parallel
        tasks = []
        collections_order: list[str] = []

        for coll in input.collections:
            tasks.append(
                self._vector_store.search(
                    coll,
                    query_embedding,
                    top_k=input.top_k,
                    filters=input.filters,
                )
            )
            collections_order.append(coll)

        if tasks:
            results_per_collection = await asyncio.gather(*tasks, return_exceptions=True)
            for coll, res in zip(collections_order, results_per_collection, strict=False):
                if isinstance(res, BaseException):
                    logger.warning(f"Retrieval failed for collection={coll}: {res}")
                    continue
                for r in res:
                    meta = r.get("metadata", {}) or {}
                    meta.setdefault("collection", coll)
                    r["metadata"] = meta
                all_results.extend(res)

        if not all_results:
            return RunRetrievalOutput(
                results=[],
                query_expansions=query_expansions,
                retrieval_strategy="dense_multi_collection",
                execution_time_ms=(time.time() - start) * 1000,
                metadata={
                    "collections": input.collections,
                    "retrieved_initial": 0,
                    "retrieved_final": 0,
                },
            )

        # 4) Global sort by the dense score
        all_results.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)
        final_results = all_results[: input.top_k]

        exec_ms = (time.time() - start) * 1000

        return RunRetrievalOutput(
            results=final_results,
            query_expansions=query_expansions,
            retrieval_strategy="dense_multi_collection",
            execution_time_ms=exec_ms,
            metadata={
                "collections": input.collections,
                "retrieved_initial": len(all_results),
                "retrieved_final": len(final_results),
            },
        )


# Default service instance - will be initialized properly in the application container
# DO NOT use this directly - get it from the container after proper initialization
run_retrieval_use_case: RunRetrievalUseCase | None = None


def get_run_retrieval_use_case(
    embedding_model: EmbeddingPort,
    vector_store: VectorSearchPort,
) -> RunRetrievalUseCase:
    """Factory function to create a properly initialized use case instance."""
    return RunRetrievalUseCase(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )
