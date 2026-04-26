"""
Search endpoint for Burhan Islamic QA system.

Provides RAG-based search operations.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.schemas.search import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
    SearchRequest,
    SearchResponse,
    SimpleRAGRequest,
    SimpleRAGResponse,
    SearchResult,
)
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.generation.prompts.rag import get_rag_prompt

logger = get_logger()
search_router = APIRouter(prefix="/search", tags=["Search"])
GENERIC_SEARCH_ERROR = "Search service temporarily unavailable."


# ── Availability flag ────────────────────────────────────────────────────
try:
    import torch
    import transformers

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# ── Sentinel ─────────────────────────────────────────────────────────────
class _Unavailable:
    """Typed sentinel — replaces the 'fallback' string anti-pattern."""


UNAVAILABLE = _Unavailable()


# ── Compiled regexes ─────────────────────────────────────────────────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CARRIAGE_RE = re.compile(r"\r")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Pure helpers ────────────────────────────────────────────────────────
def _require_rag_available() -> None:
    """Check if RAG features are available."""
    if not RAG_AVAILABLE:
        raise HTTPException(503, detail="RAG features not available.")


def _agent_unavailable_response() -> RAGQueryResponse:
    """Return unavailable response."""
    return RAGQueryResponse(
        answer=("نموذج التضمين غير متاح حالياً. الرجاء تثبيت torch و transformers للبحث المتقدم."),
        citations=[],
        metadata={"rag_available": False},
        confidence=0.0,
        requires_human_review=True,
        trace_id="unavailable",
        processing_time_ms=0,
    )


def _clean_content(text: str) -> str:
    """Strip HTML tags and normalise carriage returns."""
    text = _HTML_TAG_RE.sub("", text)
    text = _CARRIAGE_RE.sub("\n", text)
    return text.strip()


def _strip_thinking(text: str) -> str:
    """Remove <think>… reasoning blocks emitted by models."""
    return _THINK_RE.sub("", text).strip()


def _deduplicate_results(results: list[dict]) -> list[dict]:
    """
    Remove exact duplicate chunks via content fingerprint.

    Uses first ~200 chars of cleaned content as a fingerprint.
    """
    seen: set[int] = set()
    unique: list[dict] = []
    for r in results:
        raw = r.get("content", "") or ""
        # نظف أولاً ثم خذ أوّل 200 حرف
        cleaned = _clean_content(raw)
        fp = hash(cleaned[:200])
        if fp not in seen:
            seen.add(fp)
            unique.append(r)
    return unique


def _build_context(results: list[dict]) -> tuple[str, list[dict]]:
    """
    Dedup → cap → strip HTML → number passages.

    Returns:
        context_str: النص الذي سيُمرّر للـ LLM (مع [1], [2], ...)
        context_results: نفس النتائج بعد dedup + cap (تُستخدم كمصادر).
    """
    deduped = _deduplicate_results(results)
    capped = deduped[:10]
    parts: list[str] = []
    for i, r in enumerate(capped, 1):
        clean = _clean_content(r.get("content", "") or "")
        if clean:
            parts.append(f"[{i}] {clean}")
    return "\n\n".join(parts), capped


def _format_sources(results: list[dict]) -> list[dict]:
    """
    Format search results as sources.

    Adds 'index' لربط [1] في الجواب بالمصدر.
    """
    sources: list[dict] = []
    for i, r in enumerate(results, 1):
        cleaned = _clean_content(r.get("content", "") or "")
        sources.append(
            {
                "index": i,
                "score": r.get("score", 0.0),
                "content": cleaned[:500],
                "content_truncated": len(cleaned) > 500,
                "metadata": r.get("metadata", {}) or {},
            }
        )
    return sources


# ── Dependencies ─────────────────────────────────────────────────────────
def _get_state(request: Request, attr: str, label: str):
    """Get state attribute from app state."""
    obj = getattr(request.app.state, attr, None)
    if obj is None:
        raise HTTPException(503, detail=f"{label} is not initialised.")
    return obj


def get_fiqh_agent(request: Request):
    return _get_state(request, "fiqh_agent", "FiqhAgent")


def get_general_agent(request: Request):
    return _get_state(request, "general_agent", "GeneralIslamicAgent")


def get_embedding_model(request: Request):
    return _get_state(request, "embedding_model", "EmbeddingModel")


def get_vector_store(request: Request):
    return _get_state(request, "vector_store", "VectorStore")


def get_llm_client(request: Request):
    return _get_state(request, "llm_client", "LLM client")


# ── GET /search/stats ────────────────────────────────────────────────────
@search_router.get(
    "/stats",
    response_model=RAGStatsResponse,
    summary="Get RAG statistics",
    responses={503: {"model": ErrorResponse, "description": "Service unavailable"}},
)
async def get_rag_stats(
    request: Request,
    vector_store=Depends(get_vector_store),
    embedding_model=Depends(get_embedding_model),
):
    """Get RAG system statistics."""
    trace_id = _build_trace_id()
    _require_rag_available()

    if not getattr(vector_store, "client", None):
        raise HTTPException(503, detail="Vector store connection is not available.")

    collections: dict[str, Any] = {}
    total_docs = 0
    for coll in vector_store.list_collections():
        try:
            stats = vector_store.get_collection_stats(coll)
            collections[coll] = stats
            total_docs += stats.get("vectors_count", 0)
        except Exception as e:
            logger.warning(
                "search.stats_failed",
                trace_id=trace_id,
                collection=coll,
                error=str(e),
            )
            collections[coll] = {"vectors_count": 0, "error": "unavailable"}

    return RAGStatsResponse(
        collections=collections,
        total_documents=total_docs,
        embedding_model=embedding_model.MODEL_NAME,
    )


# ── POST /search/simple ──────────────────────────────────────────────────
@search_router.post(
    "/simple",
    response_model=SimpleRAGResponse,
    summary="Simple RAG search (single-turn Islamic QA)",
)
async def simple_rag_query(
    request: Request,
    req: SimpleRAGRequest,
    embedding_model=Depends(get_embedding_model),
    vector_store=Depends(get_vector_store),
    llm_client=Depends(get_llm_client),
):
    trace_id = _build_trace_id()
    start_time = time.time()
    _require_rag_available()

    # 1. استخدم SearchService عشان يفسّر "all"
    search_service = request.app.state.search_service
    if req.collection == "all":
        retrieval_output = await search_service.search(
            query=req.query,
            collections=None,  # all = DEFAULT_COLLECTIONS
            top_k=req.top_k,
            filters=None,
        )
    else:
        retrieval_output = await search_service.search(
            query=req.query,
            collections=[req.collection],
            top_k=req.top_k,
            filters=None,
        )

    results: list[dict] = retrieval_output.results

    if not results:
        processing_time_ms = int((time.time() - start_time) * 1000)
        return SimpleRAGResponse(
            answer="لم يتم العثور على نتائج.",
            sources=[],
            metadata={
                "collection": req.collection,
                "retrieved_count": 0,
                "unique_count": 0,
                "context_passages": 0,
                "language": req.language,
                "embedding_model": embedding_model.MODEL_NAME,
                "llm_model": settings.llm_model,
            },
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    # 2. Build context (dedup + cap inside)
    context, context_results = _build_context(results)
    # deduped = context_results  # نفس النتائج بعد إزالة التكرار وتحديد الحد الأعلى

    # 3. Generate with LLM
    rag_prompt = get_rag_prompt(context, req.query, req.language)
    response = await llm_client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": rag_prompt["system"]},
            {"role": "user", "content": rag_prompt["user"]},
        ],
        temperature=settings.rag_temperature,
        max_tokens=settings.rag_max_tokens,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    # نستخدم context_results في sources حتى تطابق ما رآه الـ LLM
    formatted_sources_dicts = _format_sources(context_results)
    # تحويلها لنماذج SearchResult سيقوم به Pydantic تلقائيًا عند بناء SimpleRAGResponse

    return SimpleRAGResponse(
        answer=_strip_thinking(response.choices[0].message.content),
        sources=[SearchResult(**s) for s in formatted_sources_dicts],
        metadata={
            "collection": req.collection,
            "retrieved_count": len(results),
            "unique_count": len(context_results),
            "context_passages": len(context_results),
            "language": req.language,
            "embedding_model": embedding_model.MODEL_NAME,
            "llm_model": settings.llm_model,
        },
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


# ──
