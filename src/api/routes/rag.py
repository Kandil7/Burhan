"""
RAG API endpoints for Athar Islamic QA system.

Provides direct access to RAG pipelines bypassing intent router.
Useful for specialized fiqh and general knowledge queries.

Phase 4: RAG-specific endpoints with citation traces.
Phase 7: Added simple RAG endpoint for direct query-to-answer flow.

Note: RAG features require torch and transformers (optional dependency).
Install with: poetry install --with rag
"""

from fastapi import APIRouter, HTTPException, Query
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
# Simple RAG Request/Response Models
# ==========================================


class SimpleRAGRequest(BaseModel):
    """Simple RAG query request."""

    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    collection: str = Field(
        default="general_islamic",
        description="Collection to search: general_islamic, fiqh_passages, hadith_passages, quran_tafsir, duas_adhkar, seerah_passages, aqeedah_passages, arabic_language_passages, spirituality_passages, usul_fiqh",
    )
    language: str = Field("ar", description="Response language: ar or en")
    top_k: int = Field(5, ge=1, le=20, description="Number of passages to retrieve")


class SimpleRAGResponse(BaseModel):
    """Simple RAG query response."""

    answer: str
    sources: list[dict]  # List of retrieved passages with scores
    metadata: dict


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

            # Disable cache to avoid async issues
            embedding_model = EmbeddingModel(cache_enabled=False)
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

            # Disable cache to avoid async issues
            embedding_model = EmbeddingModel(cache_enabled=False)
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
                requires_human_review=True,
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
            requires_human_review=True,
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
                requires_human_review=False,
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
            requires_human_review=True,
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

        # Check connection before iterating
        if not vector_store.client:
             raise HTTPException(status_code=503, detail="Vector store connection failed")

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
        # Re-raise to let global middleware handle connection errors with 503
        if "connection" in str(e).lower() or "refused" in str(e).lower():
             raise HTTPException(status_code=503, detail=f"Vector store unavailable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# Simple RAG Endpoint (Direct Query-to-Answer)
# ==========================================

# Global caches for Simple RAG
_embedding_model_cache = None
_vector_store_cache = None


async def get_embedding_model():
    """Get or create embedding model instance (no cache for reliability)."""
    global _embedding_model_cache
    if _embedding_model_cache is None:
        from src.knowledge.embedding_model import EmbeddingModel

        # Disable cache for simple RAG to avoid async issues
        _embedding_model_cache = EmbeddingModel(cache_enabled=False)
        await _embedding_model_cache.load_model()
    return _embedding_model_cache


async def get_vector_store():
    """Get or create vector store instance."""
    global _vector_store_cache
    if _vector_store_cache is None:
        _vector_store_cache = VectorStore()
        await _vector_store_cache.initialize()
    return _vector_store_cache


@router.post("/simple", response_model=SimpleRAGResponse)
async def simple_rag_query(request: SimpleRAGRequest):
    """
    Simple RAG endpoint - direct query to answer flow.

    This is a lightweight RAG endpoint that:
    1. Embeds the query using BGE-m3
    2. Searches the specified collection in Qdrant
    3. Generates answer using LLM with retrieved context

    No agent routing - just direct RAG flow.

    Args:
        query: User question
        collection: Qdrant collection to search (default: general_islamic)
        language: Response language (default: ar)
        top_k: Number of passages to retrieve (default: 5)

    Returns:
        answer: Generated answer with retrieved context
        sources: List of retrieved passages with scores
        metadata: Additional info (model, timing, etc.)
    """
    if not RAG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG features not available. Install torch and transformers: poetry install --with rag",
        )

    import time

    start_time = time.time()

    try:
        # Get embedding model and vector store
        try:
            embedding_model = await get_embedding_model()
        except Exception as e:
            logger.error("rag.simple_embedding_error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail=f"Embedding model not available: {str(e)}. Make sure torch and transformers are installed.",
            )

        try:
            vector_store = await get_vector_store()
        except Exception as e:
            logger.error("rag.simple_vectorstore_error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail=f"Vector store not available: {str(e)}",
            )

        # Generate query embedding
        try:
            query_embedding = await embedding_model.encode_query(request.query)
        except Exception as e:
            logger.error("rag.simple_encode_error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail=f"Failed to encode query: {str(e)}",
            )

        # Search Qdrant
        results = await vector_store.search(
            collection=request.collection, query_embedding=query_embedding, top_k=request.top_k, filters=None
        )

        if not results:
            return SimpleRAGResponse(
                answer=f"لم يتم العثور على نتائج لـ: {request.query}",
                sources=[],
                metadata={
                    "collection": request.collection,
                    "query": request.query,
                    "检索结果": 0,
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                },
            )

        # Build context from retrieved passages
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            if content:
                context_parts.append(f"[{i}] {content}")

        context = "\n\n".join(context_parts)

        # Build prompt for LLM
        if request.language == "en":
            system_prompt = """You are an Islamic scholar assistant. Answer the user's question based ONLY on the provided context from Islamic sources. If the context doesn't contain enough information to answer, say so clearly. Always cite sources using [1], [2], etc. format."""
            user_prompt = f"""Context from Islamic sources:
{context}

Question: {request.query}

Provide a clear answer based on the context above."""
        else:
            system_prompt = """أنت عالم إسلامي مساعد. أجب على سؤال المستخدم بناءً ONLY على السياق المقدم من المصادر الإسلامية. إذا كان السياق لا يحتوي على معلومات كافية للإجابة، قل ذلك بوضوح. استخدم تنسيق [1]، [2]، إلخ للاستشهاد بالمصادر."""
            user_prompt = f"""سياق من المصادر الإسلامية:
{context}

السؤال: {request.query}

أجب بوضوح بناءً على السياق أعلاه."""

        # Get LLM client and generate answer
        from src.infrastructure.llm_client import get_llm_client

        llm_client = await get_llm_client()

        from src.config.settings import settings

        response = await llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content

        # Format sources
        sources = []
        for result in results:
            sources.append(
                {
                    "score": result.get("score", 0),
                    "content": result.get("content", "")[:500],  # Truncate long content
                    "metadata": result.get("metadata", {}),
                }
            )

        processing_time = int((time.time() - start_time) * 1000)

        return SimpleRAGResponse(
            answer=answer,
            sources=sources,
            metadata={
                "collection": request.collection,
                "query": request.query,
                "retrieved_count": len(results),
                "language": request.language,
                "processing_time_ms": processing_time,
                "embedding_model": embedding_model.MODEL_NAME,
                "llm_model": settings.llm_model,
            },
        )

    except Exception as e:
        logger.error("rag.simple_error", error=str(e), collection=request.collection)
        raise HTTPException(status_code=500, detail=str(e)) from e
