"""
RAG API endpoints for Athar Islamic QA system.

Provides direct access to RAG pipelines bypassing intent router.
Useful for specialized fiqh and general knowledge queries.

Phase 4: RAG-specific endpoints with citation traces.

Note: RAG features require torch and transformers (optional dependency).
Install with: poetry install --with rag
"""


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# RAG dependencies are optional - allow app to run without them
try:
    import torch
    import transformers

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    torch = None
    transformers = None

from src.config.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/rag", tags=["RAG"])

# Only import RAG components if dependencies available
if RAG_AVAILABLE:
    from src.knowledge.embedding_model import EmbeddingModel
    from src.knowledge.vector_store import VectorStore


# ==========================================
# Request/Response Models
# ==========================================


class RAGQueryRequest(BaseModel):
    """RAG query request."""

    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    language: str | None = Field("ar", description="Response language")
    madhhab: str | None = Field(None, description="Preferred madhhab")
    top_k: int = Field(10, ge=1, le=20, description="Number of passages to retrieve")


class RAGQueryResponse(BaseModel):
    """RAG query response."""

    answer: str
    citations: list[dict]
    metadata: dict
    confidence: float
    requires_human_review: bool


class RAGStatsResponse(BaseModel):
    """RAG statistics."""

    collections: dict
    total_documents: int
    embedding_model: str


# ==========================================
# RAG Agent Instances (lazy init)
# ==========================================
fiqh_agent_cache = None
general_agent_cache = None
embedding_model_cache = None
vector_store_cache = None


async def get_fiqh_agent():
    """Get or create FiqhAgent instance with graceful fallback."""
    global fiqh_agent_cache

    if fiqh_agent_cache is None:
        try:
            from src.agents.fiqh_agent import FiqhAgent
            from src.knowledge.embedding_model import EmbeddingModel
            from src.knowledge.vector_store import VectorStore

            embedding_model = EmbeddingModel()
            await embedding_model.load_model()

            vector_store = VectorStore()
            await vector_store.initialize()

            fiqh_agent_cache = FiqhAgent(embedding_model=embedding_model, vector_store=vector_store)
        except Exception as e:
            logger.warning("rag.fiqh_agent_init_failed", error=str(e))
            # Return a placeholder agent
            fiqh_agent_cache = "fallback"

    if fiqh_agent_cache == "fallback":
        return "fallback"

    return fiqh_agent_cache


async def get_general_agent():
    """Get or create GeneralIslamicAgent instance with graceful fallback."""
    global general_agent_cache

    if general_agent_cache is None:
        try:
            from src.agents.general_islamic_agent import GeneralIslamicAgent
            from src.knowledge.embedding_model import EmbeddingModel
            from src.knowledge.vector_store import VectorStore

            embedding_model = EmbeddingModel()
            await embedding_model.load_model()

            vector_store = VectorStore()
            await vector_store.initialize()

            general_agent_cache = GeneralIslamicAgent(embedding_model=embedding_model, vector_store=vector_store)
        except Exception as e:
            logger.warning("rag.general_agent_init_failed", error=str(e))
            general_agent_cache = "fallback"

    if general_agent_cache == "fallback":
        return "fallback"

    return general_agent_cache


# ==========================================
# Fiqh RAG Endpoint
# ==========================================


@router.post("/fiqh", response_model=RAGQueryResponse)
async def query_fiqh(request: RAGQueryRequest):
    """
    Ask a fiqh question with RAG retrieval.

    Retrieves from fiqh corpus and generates grounded answer with citations.
    Falls back gracefully if embedding model not available.
    """
    try:
        agent = await get_fiqh_agent()

        # Check for fallback
        if agent == "fallback":
            return RAGQueryResponse(
                answer="نموذج التضمين غير متاح حالياً. الرجاء تثبيت torch و transformers للبحث المتقدم.\n\nالتثبيت: pip install torch transformers",
                citations=[],
                metadata={"error": "Embedding model not available", "fix": "pip install torch transformers"},
                confidence=0.0,
                requires_human_review=True
            )

        from src.agents.base import AgentInput

        result = await agent.execute(
            AgentInput(query=request.query, language=request.language, metadata={"madhhab": request.madhhab})
        )

        return RAGQueryResponse(
            answer=result.answer,
            citations=[c.model_dump() for c in result.citations],
            metadata=result.metadata,
            confidence=result.confidence,
            requires_human_review=result.requires_human_review,
        )

    except Exception as e:
        logger.error("rag.fiqh_error", error=str(e))
        # Return fallback instead of error
        return RAGQueryResponse(
            answer=f"عذراً، حدث خطأ: {str(e)}\n\nالرجاء تثبيت torch و transformers للبحث المتقدم.",
            citations=[],
            metadata={"error": str(e)},
            confidence=0.0,
            requires_human_review=True
        )


# ==========================================
# General Islamic Knowledge Endpoint
# ==========================================


@router.post("/general", response_model=RAGQueryResponse)
async def query_general(request: RAGQueryRequest):
    """
    Ask a general Islamic knowledge question.

    Retrieves from general Islamic corpus (history, biography, theology).
    Falls back gracefully if embedding model not available.
    """
    try:
        agent = await get_general_agent()

        # Check for fallback
        if agent == "fallback":
            return RAGQueryResponse(
                answer="نموذج التضمين غير متاح حالياً. الرجاء تثبيت torch و transformers للبحث المتقدم.\n\nالتثبيت: pip install torch transformers",
                citations=[],
                metadata={"error": "Embedding model not available"},
                confidence=0.0,
                requires_human_review=False
            )

        from src.agents.base import AgentInput

        result = await agent.execute(
            AgentInput(query=request.query, language=request.language, metadata={"madhhab": request.madhhab})
        )

        return RAGQueryResponse(
            answer=result.answer,
            citations=[c.model_dump() for c in result.citations],
            metadata=result.metadata,
            confidence=result.confidence,
            requires_human_review=result.requires_human_review,
        )

    except Exception as e:
        logger.error("rag.general_error", error=str(e))
        return RAGQueryResponse(
            answer=f"عذراً، حدث خطأ: {str(e)}",
            citations=[],
            metadata={"error": str(e)},
            confidence=0.0,
            requires_human_review=True
        )


# ==========================================
# RAG Statistics Endpoint
# ==========================================


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats():
    """
    Get RAG system statistics.

    Returns document counts, collection info, and model info.
    """
    if not RAG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG features not available. Install torch and transformers: poetry install --with rag",
        )

    try:
        vector_store = VectorStore()
        await vector_store.initialize()

        collections = {}
        total_docs = 0

        for coll in vector_store.list_collections():
            try:
                stats = vector_store.get_collection_stats(coll)
                collections[coll] = stats
                total_docs += stats.get("vectors_count", 0)
            except Exception as e:
                logger.warning("rag.stats_collection_failed", collection=coll, error=str(e))
                collections[coll] = {"vectors_count": 0}

        embedding_model = EmbeddingModel()

        return RAGStatsResponse(
            collections=collections, total_documents=total_docs, embedding_model=embedding_model.MODEL_NAME
        )

    except Exception as e:
        logger.error("rag.stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
