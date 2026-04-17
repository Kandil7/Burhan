"""
Search endpoint for Athar Islamic QA system.

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
)
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
search_router = APIRouter(prefix="/search", tags=["Search"])

# ── Availability flag ────────────────────────────────────────────────────
try:
    import torch
    import transformers

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# ── Sentinel ────────────────────────────────────────────────────────────────
class _Unavailable:
    """Typed sentinel — replaces the 'fallback' string anti-pattern."""


UNAVAILABLE = _Unavailable()

# ── Compiled regexes ────────────────────────────────────────────────────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CARRIAGE_RE = re.compile(r"\r")
_THINK_RE = re.compile(r"<think>.*?", re.DOTALL)


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Pure helpers ───────────────────────────────────────────────────────────


def _require_rag_available() -> None:
    """Check if RAG features are available."""
    if not RAG_AVAILABLE:
        raise HTTPException(503, detail="RAG features not available.")


def _agent_unavailable_response() -> RAGQueryResponse:
    """Return unavailable response."""
    return RAGQueryResponse(
        answer="نموذج التضمين غير متاح حالياً. الرجاء تثبيت torch و transformers للبحث المتقدم.",
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
    """Remove exact duplicate chunks via content fingerprint."""
    seen: set[int] = set()
    unique: list[dict] = []
    for r in results:
        fp = hash(_clean_content(r.get("content", ""))[:200])
        if fp not in seen:
            seen.add(fp)
            unique.append(r)
    return unique


def _build_context(results: list[dict]) -> tuple[str, list[dict]]:
    """Dedup → cap → strip HTML → number passages."""
    deduped = _deduplicate_results(results)
    capped = deduped[:10]
    parts = []
    for i, r in enumerate(capped, 1):
        clean = _clean_content(r.get("content", ""))
        if clean:
            parts.append(f"[{i}] {clean}")
    return "\n\n".join(parts), capped


def _build_llm_prompt(context: str, query: str, language: str) -> tuple[str, str]:
    """Build LLM prompt for generation."""
    if language == "en":
        system = (
            "You are a knowledgeable Islamic scholar assistant. "
            "Answer questions based ONLY on the provided context.\n"
            "Structure your answer:\n"
            "1. Direct answer (1-2 sentences)\n"
            "2. Evidence with citations [1], [2], …\n"
            "3. If context is insufficient, say so clearly.\n"
            "Never fabricate information not in the context."
        )
        user = f"Islamic sources:\n{context}\n\nQuestion: {query}\n\nAnswer strictly from the sources."
    else:
        system = (
            "أنت عالم إسلامي متخصص. أجب بناءً فقط على السياق المقدم.\n"
            "نظّم إجابتك:\n"
            "١. الجواب المباشر (جملة أو جملتان)\n"
            "٢. الدليل من المصادر مع الاستشهاد [1]، [2]، …\n"
            "٣. إن كانت المصادر غير كافية، صرّح بذلك.\n"
            "لا تخترع معلومات غير موجودة في السياق."
        )
        user = f"المصادر الإسلامية:\n{context}\n\nالسؤال: {query}\n\nأجب بناءً على المصادر أعلاه فقط."
    return system, user


def _format_sources(results: list[dict]) -> list[dict]:
    """Format search results as sources."""
    sources = []
    for r in results:
        cleaned = _clean_content(r.get("content", ""))
        sources.append(
            {
                "score": r.get("score", 0.0),
                "content": cleaned[:500],
                "content_truncated": len(cleaned) > 500,
                "metadata": r.get("metadata", {}),
            }
        )
    return sources


# ── Dependencies ────────────────────────────────────────────────────────────


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


# ── POST /search/fiqh ──────────────────────────────────────────────────────


@search_router.post(
    "/fiqh",
    response_model=RAGQueryResponse,
    summary="Query Fiqh RAG",
    responses={503: {"model": ErrorResponse, "description": "Service unavailable"}},
)
async def query_fiqh(request: Request, req: RAGQueryRequest, agent=Depends(get_fiqh_agent)):
    """Query the Fiqh RAG agent."""
    trace_id = _build_trace_id()
    start_time = time.time()

    if isinstance(agent, _Unavailable):
        return _agent_unavailable_response()

    from src.agents.base import AgentInput

    try:
        result = await agent.execute(
            AgentInput(
                query=req.query,
                language=req.language,
                metadata={"madhhab": req.madhhab},
            )
        )
    except Exception as e:
        logger.error("search.fiqh_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail="Fiqh RAG service temporarily unavailable.") from e

    processing_time_ms = int((time.time() - start_time) * 1000)

    return RAGQueryResponse(
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        metadata=result.metadata,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


# ── POST /search/general ───────────────────────────────────────────────────


@search_router.post(
    "/general",
    response_model=RAGQueryResponse,
    summary="Query General RAG",
    responses={503: {"model": ErrorResponse, "description": "Service unavailable"}},
)
async def query_general(request: Request, req: RAGQueryRequest, agent=Depends(get_general_agent)):
    """Query the General Islamic RAG agent."""
    trace_id = _build_trace_id()
    start_time = time.time()

    if isinstance(agent, _Unavailable):
        return _agent_unavailable_response()

    from src.agents.base import AgentInput

    try:
        result = await agent.execute(
            AgentInput(
                query=req.query,
                language=req.language,
                metadata={"madhhab": req.madhhab},
            )
        )
    except Exception as e:
        logger.error("search.general_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail="General RAG service temporarily unavailable.") from e

    processing_time_ms = int((time.time() - start_time) * 1000)

    return RAGQueryResponse(
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        metadata=result.metadata,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


# ── GET /search/stats ───────────────────────────────────────────────────────


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
            logger.warning("search.stats_failed", trace_id=trace_id, collection=coll, error=str(e))
            collections[coll] = {"vectors_count": 0, "error": "unavailable"}

    return RAGStatsResponse(
        collections=collections,
        total_documents=total_docs,
        embedding_model=embedding_model.MODEL_NAME,
    )


# ── POST /search/simple ────────────────────────────────────────────────────


@search_router.post(
    "/simple",
    response_model=SimpleRAGResponse,
    summary="Simple RAG query",
    responses={503: {"model": ErrorResponse, "description": "Service unavailable"}},
)
async def simple_rag_query(
    request: Request,
    req: SimpleRAGRequest,
    embedding_model=Depends(get_embedding_model),
    vector_store=Depends(get_vector_store),
    llm_client=Depends(get_llm_client),
):
    """Simple RAG query with retrieval + generation."""
    trace_id = _build_trace_id()
    start_time = time.time()

    _require_rag_available()

    # 1. Embed
    try:
        query_embedding = await embedding_model.encode_query(req.query)
        logger.info(
            "search.simple_encode",
            trace_id=trace_id,
            query=req.query[:50],
            embedding_type=type(embedding_model).__name__,
        )
    except Exception as e:
        logger.error("search.simple_encode_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail=f"Failed to encode query: {str(e)}") from e

    # 2. Search
    try:
        results = await vector_store.search(
            collection=req.collection,
            query_embedding=query_embedding,
            top_k=req.top_k,
            filters=None,
        )
        logger.info("search.simple_search", trace_id=trace_id, results_count=len(results))
    except Exception as e:
        logger.error("search.simple_search_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail=f"Vector store search failed: {str(e)}") from e

    if not results:
        processing_time_ms = int((time.time() - start_time) * 1000)
        return SimpleRAGResponse(
            answer=f"لم يتم العثور على نتائج في مجموعة «{req.collection}».",
            sources=[],
            metadata={
                "collection": req.collection,
                "retrieved_count": 0,
                "unique_count": 0,
                "context_passages": 0,
            },
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    # 3. Build context
    context, context_results = _build_context(results)
    deduped = _deduplicate_results(results)

    # 4. Generate
    try:
        system_prompt, user_prompt = _build_llm_prompt(context, req.query, req.language)
        response = await llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.rag_temperature,
            max_tokens=settings.rag_max_tokens,
        )
    except Exception as e:
        logger.error("search.simple_llm_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail="LLM service temporarily unavailable.") from e

    processing_time_ms = int((time.time() - start_time) * 1000)

    return SimpleRAGResponse(
        answer=_strip_thinking(response.choices[0].message.content),
        sources=_format_sources(results),
        metadata={
            "collection": req.collection,
            "retrieved_count": len(results),
            "unique_count": len(deduped),
            "context_passages": len(context_results),
            "language": req.language,
            "embedding_model": embedding_model.MODEL_NAME,
            "llm_model": settings.llm_model,
        },
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


# ── Legacy: POST /search (new basic search) ────────────────────────────────


@search_router.post(
    "",
    response_model=SearchResponse,
    summary="Basic search",
)
async def basic_search(
    request: Request,
    req: SearchRequest,
    embedding_model=Depends(get_embedding_model),
    vector_store=Depends(get_vector_store),
):
    """Basic semantic search."""
    trace_id = _build_trace_id()
    start_time = time.time()

    _require_rag_available()

    # Embed and search
    try:
        query_embedding = await embedding_model.encode_query(req.query)
        results = await vector_store.search(
            collection=req.collection or "general_islamic",
            query_embedding=query_embedding,
            top_k=req.top_k,
            filters=req.filters,
        )
    except Exception as e:
        logger.error("search.basic_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(503, detail=f"Search failed: {str(e)}") from e

    processing_time_ms = int((time.time() - start_time) * 1000)

    return SearchResponse(
        query_id=trace_id,
        query=req.query,
        results=[
            {
                "score": r.get("score", 0.0),
                "content": _clean_content(r.get("content", "")),
                "content_truncated": len(r.get("content", "")) > 500,
                "metadata": r.get("metadata", {}),
            }
            for r in results
        ],
        total=len(results),
        collection=req.collection,
        metadata={"language": req.language},
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )
