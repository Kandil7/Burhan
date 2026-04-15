from __future__ import annotations

import re
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
router = APIRouter(prefix="/rag", tags=["RAG"])

# ── Availability flag ────────────────────────────────────────────────
try:
    import torch; import transformers
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# ── Sentinel ─────────────────────────────────────────────────────────
class _Unavailable:
    """Typed sentinel — replaces the "fallback" string anti-pattern."""

UNAVAILABLE = _Unavailable()

# ── Compiled regexes ─────────────────────────────────────────────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CARRIAGE_RE = re.compile(r"\r")

# ── Schemas ───────────────────────────────────────────────────────────
class RAGQueryRequest(BaseModel):
    query:    str        = Field(..., min_length=1, max_length=2000)
    language: str | None = Field("ar")
    madhhab:  str | None = Field(None)
    top_k:    int        = Field(10, ge=1, le=20)

class RAGQueryResponse(BaseModel):
    answer:                str
    citations:             list[dict]
    metadata:              dict
    confidence:            float
    requires_human_review: bool

class RAGStatsResponse(BaseModel):
    collections:     dict
    total_documents: int
    embedding_model: str

class SimpleRAGRequest(BaseModel):
    query:      str = Field(..., min_length=1, max_length=2000)
    collection: str = Field(default="general_islamic")
    language:   str = Field("ar")
    top_k:      int = Field(5, ge=1, le=20)

class SimpleRAGResponse(BaseModel):
    answer:   str
    sources:  list[dict]
    metadata: dict

# ── Dependencies ──────────────────────────────────────────────────────
def _get_state(request: Request, attr: str, label: str):
    obj = getattr(request.app.state, attr, None)
    if obj is None:
        raise HTTPException(503, detail=f"{label} is not initialised.")
    return obj

def get_fiqh_agent(request: Request):     return _get_state(request, "fiqh_agent",    "FiqhAgent")
def get_general_agent(request: Request):  return _get_state(request, "general_agent",  "GeneralIslamicAgent")
def get_embedding_model(request: Request):return _get_state(request, "embedding_model","EmbeddingModel")
def get_vector_store(request: Request):   return _get_state(request, "vector_store",   "VectorStore")
def get_llm_client(request: Request):     return _get_state(request, "llm_client",     "LLM client")

# ── Constants ─────────────────────────────────────────────────────────
_MAX_LLM_CONTEXT_PASSAGES = 10
_UNAVAILABLE_AR = (
    "نموذج التضمين غير متاح حالياً. "
    "الرجاء تثبيت torch و transformers للبحث المتقدم.\n\n"
    "التثبيت: poetry install --with rag"
)

# ── Pure helpers ──────────────────────────────────────────────────────
def _require_rag_available() -> None:
    if not RAG_AVAILABLE:
        raise HTTPException(503, detail="RAG features not available.")

def _agent_unavailable_response(*, requires_human_review: bool = True) -> RAGQueryResponse:
    return RAGQueryResponse(
        answer=_UNAVAILABLE_AR,
        citations=[],
        metadata={"rag_available": False},
        confidence=0.0,
        requires_human_review=requires_human_review,
    )

def _clean_content(text: str) -> str:
    """Strip HTML tags and normalise carriage returns."""
    text = _HTML_TAG_RE.sub("", text)
    text = _CARRIAGE_RE.sub("\n", text)
    return text.strip()
def _strip_thinking(text: str) -> str:
    """
    Remove <think>…</think> reasoning blocks emitted by Qwen3.

    Qwen3 (and similar chain-of-thought models) prepend an internal
    reasoning block to their output. These blocks are useful for
    debugging but must never reach the end user.
    """
    return _THINK_RE.sub("", text).strip()
def _deduplicate_results(results: list[dict]) -> list[dict]:
    """Remove exact duplicate chunks via content fingerprint."""
    seen:   set[int]   = set()
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
    capped  = deduped[:_MAX_LLM_CONTEXT_PASSAGES]
    parts   = []
    for i, r in enumerate(capped, 1):
        clean = _clean_content(r.get("content", ""))
        if clean:
            parts.append(f"[{i}] {clean}")
    return "\n\n".join(parts), capped

def _build_llm_prompt(context: str, query: str, language: str) -> tuple[str, str]:
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
    sources = []
    for r in results:
        cleaned = _clean_content(r.get("content", ""))
        sources.append({
            "score":             r.get("score", 0.0),
            "content":           cleaned[:500],
            "content_truncated": len(cleaned) > 500,
            "metadata":          r.get("metadata", {}),
        })
    return sources

# ── POST /rag/fiqh ────────────────────────────────────────────────────
@router.post("/fiqh", response_model=RAGQueryResponse)
async def query_fiqh(request: RAGQueryRequest, agent=Depends(get_fiqh_agent)):
    if isinstance(agent, _Unavailable):
        return _agent_unavailable_response(requires_human_review=True)
    from src.agents.base import AgentInput
    try:
        result = await agent.execute(AgentInput(
            query=request.query,
            language=request.language,
            metadata={"madhhab": request.madhhab},
        ))
    except Exception as e:
        logger.error("rag.fiqh_error", error=str(e), exc_info=True)
        raise HTTPException(503, detail="Fiqh RAG service temporarily unavailable.") from e
    return RAGQueryResponse(
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        metadata=result.metadata,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
    )

# ── POST /rag/general ─────────────────────────────────────────────────
@router.post("/general", response_model=RAGQueryResponse)
async def query_general(request: RAGQueryRequest, agent=Depends(get_general_agent)):
    if isinstance(agent, _Unavailable):
        return _agent_unavailable_response(requires_human_review=False)
    from src.agents.base import AgentInput
    try:
        result = await agent.execute(AgentInput(
            query=request.query,
            language=request.language,
            metadata={"madhhab": request.madhhab},
        ))
    except Exception as e:
        logger.error("rag.general_error", error=str(e), exc_info=True)
        raise HTTPException(503, detail="General RAG service temporarily unavailable.") from e
    return RAGQueryResponse(
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        metadata=result.metadata,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
    )

# ── GET /rag/stats ────────────────────────────────────────────────────
@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    vector_store=Depends(get_vector_store),
    embedding_model=Depends(get_embedding_model),
):
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
            logger.warning("rag.stats_failed", collection=coll, error=str(e))
            collections[coll] = {"vectors_count": 0, "error": "unavailable"}
    return RAGStatsResponse(
        collections=collections,
        total_documents=total_docs,
        embedding_model=embedding_model.MODEL_NAME,
    )

# ── POST /rag/simple ──────────────────────────────────────────────────
@router.post("/simple", response_model=SimpleRAGResponse)
async def simple_rag_query(
    request: SimpleRAGRequest,
    embedding_model=Depends(get_embedding_model),
    vector_store=Depends(get_vector_store),
    llm_client=Depends(get_llm_client),
):
    _require_rag_available()
    start = time.time()

    # 1. Embed
    try:
        query_embedding = await embedding_model.encode_query(request.query)
    except Exception as e:
        logger.error("rag.simple_encode_error", error=str(e), exc_info=True)
        raise HTTPException(503, detail="Failed to encode query.") from e

    # 2. Search
    try:
        results = await vector_store.search(
            collection=request.collection,
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=None,
        )
    except Exception as e:
        logger.error("rag.simple_search_error", collection=request.collection,
                     error=str(e), exc_info=True)
        raise HTTPException(503, detail="Vector store search failed.") from e

    if not results:
        return SimpleRAGResponse(
            answer=f"لم يتم العثور على نتائج في مجموعة «{request.collection}».",
            sources=[],
            metadata={
                "collection": request.collection,
                "retrieved_count": 0, "unique_count": 0,
                "context_passages": 0,
                "processing_time_ms": int((time.time() - start) * 1000),
            },
        )

    # 3. Dedup + build context
    context, context_results = _build_context(results)
    deduped = _deduplicate_results(results)

    logger.info("rag.simple_context_built",
                retrieved=len(results),
                after_dedup=len(deduped),
                context_passages=len(context_results))

    # 4. Build prompt
    system_prompt, user_prompt = _build_llm_prompt(context, request.query, request.language)

    # 5. Generate
    try:
        response = await llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=settings.rag_temperature,
            max_tokens=settings.rag_max_tokens,
        )
    except Exception as e:
        logger.error("rag.simple_llm_error", error=str(e), exc_info=True)
        raise HTTPException(503, detail="LLM service temporarily unavailable.") from e

    return SimpleRAGResponse(
        answer = _strip_thinking(response.choices[0].message.content),
        sources=_format_sources(results),
        metadata={
            "collection":         request.collection,
            "retrieved_count":    len(results),
            "unique_count":       len(deduped),
            "context_passages":   len(context_results),
            "language":           request.language,
            "processing_time_ms": int((time.time() - start) * 1000),
            "embedding_model":    embedding_model.MODEL_NAME,
            "llm_model":          settings.llm_model,
        },
    )