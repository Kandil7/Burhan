"""
Query route for Athar Islamic QA system.

Routes queries to appropriate agents based on intent:
- greeting/chatbot → ChatbotAgent
- fiqh → FiqhAgent (RAG with faceted search)
- quran → Quran endpoints
- zakat/inheritance/dua/prayer/hijri → Tool endpoints
- general knowledge → GeneralIslamicAgent

Enhanced with:
- Faceted search filters (author, era, book, category)
- Hierarchical retrieval for coherent results
- Rich citation metadata in response
"""

import uuid
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import QueryResponse, CitationResponse
from src.core.router import HybridQueryClassifier
from src.infrastructure.llm_client import get_llm_client
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.fiqh_agent import FiqhAgent
from src.agents.general_islamic_agent import GeneralIslamicAgent
from src.agents.base import AgentInput
from src.config.intents import Intent
from src.config.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/query", tags=["Query"])

# Thread-safe singleton instances with locks
import threading

_chatbot = None
_chatbot_lock = threading.Lock()

_classifier = None
_classifier_lock = threading.Lock()

_fiqh_agent = None
_fiqh_lock = threading.Lock()

_general_agent = None
_general_lock = threading.Lock()

_agents_loaded = False

def get_chatbot() -> ChatbotAgent:
    """Get or create chatbot agent (thread-safe)."""
    global _chatbot
    with _chatbot_lock:
        if _chatbot is None:
            _chatbot = ChatbotAgent()
        return _chatbot

async def get_classifier() -> HybridQueryClassifier:
    """Get or create query classifier (thread-safe)."""
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            llm_client = await get_llm_client()
            _classifier = HybridQueryClassifier(llm_client=llm_client)
        return _classifier

async def get_fiqh_agent():
    """Get or create FiqhAgent with lazy initialization (thread-safe)."""
    global _fiqh_agent, _agents_loaded
    with _fiqh_lock:
        if _fiqh_agent is None and not _agents_loaded:
            try:
                _fiqh_agent = FiqhAgent()
                await _fiqh_agent._initialize()
                _agents_loaded = True
                logger.info("query.fiqh_agent_initialized")
            except Exception as e:
                logger.warning("query.fiqh_agent_init_failed", error=str(e))
                _agents_loaded = True  # Don't retry
        return _fiqh_agent


async def get_general_agent():
    """Get or create GeneralIslamicAgent with lazy initialization (thread-safe)."""
    global _general_agent, _agents_loaded
    with _general_lock:
        if _general_agent is None and not _agents_loaded:
            try:
                _general_agent = GeneralIslamicAgent()
                await _general_agent._initialize()
                _agents_loaded = True
                logger.info("query.general_agent_initialized")
            except Exception as e:
                logger.warning("query.general_agent_init_failed", error=str(e))
                _agents_loaded = True
        return _general_agent


@router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
)
async def handle_query(
    request: QueryRequest,
    # Faceted search filters
    author: Optional[str] = Query(None, description="Filter by author name"),
    era: Optional[str] = Query(None, description="Filter by scholarly era (prophetic, tabiun, classical, medieval, ottoman, modern)"),
    book_id: Optional[int] = Query(None, description="Filter by specific book ID"),
    category: Optional[str] = Query(None, description="Filter by category/madhhab"),
    death_year_min: Optional[int] = Query(None, description="Minimum author death year (Hijri)"),
    death_year_max: Optional[int] = Query(None, description="Maximum author death year (Hijri)"),
    # Retrieval options
    hierarchical: bool = Query(False, description="Use hierarchical retrieval for coherent results"),
):
    """
    Handle user query with intent-based routing and optional faceted search.

    Flow:
    1. Classify intent
    2. Build filters from query parameters
    3. Route to appropriate agent with filters
    4. Return structured response with rich citations

    Faceted Search Examples:
    - /api/v1/query?query=ما+حكم+الصلاة&author=Imam+Bukhari
    - /api/v1/query?query=التوحيد&era=classical
    - /api/v1/query?query=المواريث&death_year_min=200&death_year_max=500
    - /api/v1/query?query=الفقه&hierarchical=true
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())

    try:
        logger.info("query.received", query_id=query_id, query=request.query[:50])

        # Get components
        chatbot = get_chatbot()
        classifier = await get_classifier()
        
        # Classify intent
        router_result = await classifier.classify(request.query)
        intent = router_result.intent
        language = request.language or router_result.language
        
        logger.info(
            "query.classified",
            query_id=query_id,
            intent=intent.value,
            confidence=router_result.confidence,
        )

        # Route based on intent
        # Build filters from query parameters
        filters = None
        if any([author, era, book_id, category, death_year_min, death_year_max]):
            filters = {}
            if author:
                filters["author"] = author
            if era:
                filters["era"] = era
            if book_id:
                filters["book_id"] = book_id
            if category:
                filters["category"] = category
            if death_year_min:
                filters["author_death_min"] = death_year_min
            if death_year_max:
                filters["author_death_max"] = death_year_max
            
            logger.info(
                "query.filters_applied",
                query_id=query_id,
                filters=list(filters.keys()),
            )

        if intent == Intent.GREETING:
            # Greeting → ChatbotAgent
            agent_result = await chatbot.execute(AgentInput(
                query=request.query,
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "chatbot_agent"

        elif intent == Intent.FIQH:
            # Fiqh → FiqhAgent (RAG with vector store, faceted search)
            fiqh_agent = await get_fiqh_agent()
            if fiqh_agent and hasattr(fiqh_agent, 'embedding_model') and fiqh_agent.embedding_model:
                # Pass filters and hierarchical via metadata
                agent_input = AgentInput(
                    query=request.query,
                    language=language,
                    metadata={
                        "madhhab": request.madhhab,
                        "filters": filters,
                        "hierarchical": hierarchical,
                    }
                )
                agent_result = await fiqh_agent.execute(agent_input)
                agent_name = "fiqh_agent"
            else:
                # FiqhAgent not available, use chatbot with helpful message
                agent_result = await chatbot.execute(AgentInput(
                    query=f"أعتذر، لا تتوفر حالياً نصوص فقهية كافية للإجابة. يرجى السؤال عن موضوع آخر.\n\n{request.query}",
                    language=language,
                    metadata={"madhhab": request.madhhab}
                ))
                agent_name = "chatbot_fallback"

        elif intent == Intent.ISLAMIC_KNOWLEDGE:
            # General Islamic → GeneralIslamicAgent with faceted search
            general_agent = await get_general_agent()
            if general_agent and hasattr(general_agent, 'embedding_model') and general_agent.embedding_model:
                agent_input = AgentInput(
                    query=request.query,
                    language=language,
                    metadata={
                        "madhhab": request.madhhab,
                        "filters": filters,
                        "hierarchical": hierarchical,
                    }
                )
                agent_result = await general_agent.execute(agent_input)
                agent_name = "general_islamic_agent"
            else:
                agent_result = await chatbot.execute(AgentInput(
                    query=request.query,
                    language=language,
                    metadata={"madhhab": request.madhhab}
                ))
                agent_name = "chatbot_fallback"

        else:
            # Default → ChatbotAgent
            agent_result = await chatbot.execute(AgentInput(
                query=request.query,
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "chatbot_agent"

        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "query.completed",
            query_id=query_id,
            intent=intent.value,
            agent=agent_name,
            processing_time_ms=processing_time,
        )

        return QueryResponse(
            query_id=query_id,
            intent=intent.value,
            intent_confidence=router_result.confidence,
            answer=agent_result.answer,
            citations=[
                CitationResponse(
                    id=c.id, type=c.type, source=c.source, reference=c.reference, url=c.url, text_excerpt=c.text_excerpt
                )
                for c in agent_result.citations
            ],
            metadata={
                "agent": agent_name,
                "processing_time_ms": processing_time,
                "classification_method": router_result.method,
                **agent_result.metadata,
            },
            follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
        )

    except ValueError as e:
        logger.warning("query.validation_error", query_id=query_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("query.error", query_id=query_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/test")
async def test_query():
    """Test endpoint to verify query router is working."""
    chatbot = get_chatbot()
    result = await chatbot.execute(AgentInput(query="السلام عليكم", language="ar", metadata={}))
    return {"status": "ok", "chatbot": chatbot.name, "answer": result.answer, "agent_meta": result.metadata}
