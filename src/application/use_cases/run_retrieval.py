from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time
import asyncio

from src.retrieval.retrievers.hybrid_searcher import HybridSearcher
from src.indexing.vectorstores.qdrant_store import VectorStore
from src.indexing.embeddings.embedding_model import EmbeddingModel  # أو المسار الفعلي


@dataclass
class RunRetrievalInput:
    query: str
    collections: List[str]
    top_k: int = 10
    enable_reranking: bool = True
    enable_expansion: bool = True
    filters: Optional[Dict[str, Any]] = None


@dataclass
class RunRetrievalOutput:
    results: List[Dict[str, Any]]
    query_expansions: Optional[List[str]] = None
    retrieval_strategy: str = ""
    execution_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class RunRetrievalUseCase:
    """Use case for executing retrieval operations."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: VectorStore) -> None:
        self._embedding_model = embedding_model
        self._vector_store = vector_store
        self._hybrid_searcher = HybridSearcher(vector_store)

    async def execute(self, input: RunRetrievalInput) -> RunRetrievalOutput:
        start = time.time()

        # 1) Embed query once
        query_embedding = await self._embedding_model.encode_query(input.query)

        # 2) (optional) expansions – حالياً بس نرجّع الـ query نفسه
        query_expansions = [input.query] if input.enable_expansion else None

        all_results: List[Dict[str, Any]] = []        

        # 3) Run hybrid search على كل collection مطلوبة (بالتوازي)
        tasks = []
        collections_order: list[str] = []

        for coll in input.collections:
            tasks.append(
                self._hybrid_searcher.search(
                    query=input.query,
                    query_embedding=query_embedding,
                    collection=coll,
                    top_k=input.top_k,
                )
            )
            collections_order.append(coll)

        all_results: List[Dict[str, Any]] = []

        if tasks:
            results_per_collection = await asyncio.gather(*tasks, return_exceptions=True)
            for coll, res in zip(collections_order, results_per_collection):
                if isinstance(res, Exception):
                    # TODO: log warning with coll and error
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
                retrieval_strategy="hybrid_multi_collection",
                execution_time_ms=(time.time() - start) * 1000,
                metadata={
                    "collections": input.collections,
                    "retrieved_initial": 0,
                    "retrieved_final": 0,
                },
            )

        # 4) Global sort by hybrid_score (أو score fallback)
        def score_of(r: dict) -> float:
            if "hybrid_score" in r:
                return float(r["hybrid_score"])
            return float(r.get("score", 0.0))

        all_results.sort(key=score_of, reverse=True)
        final_results = all_results[: input.top_k]

        exec_ms = (time.time() - start) * 1000

        return RunRetrievalOutput(
            results=final_results,
            query_expansions=query_expansions,
            retrieval_strategy="hybrid_multi_collection",
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
    embedding_model: "EmbeddingModel",
    vector_store: "VectorStore",
) -> RunRetrievalUseCase:
    """Factory function to create a properly initialized use case instance."""
    return RunRetrievalUseCase(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )
