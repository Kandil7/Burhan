"""
Query route for Athar Islamic QA system.

Routes queries to appropriate agents based on intent using AgentRegistry.
Supports faceted search, hierarchical retrieval, and multi-language responses.

Phase 6 Refactoring:
- Replaced duplicate global+lock patterns with LazySingleton
- Connected to AgentRegistry for dynamic routing (all 17 intents now work)
- Eliminated _agents_loaded bug that prevented GeneralIslamicAgent from loading
"""

import time
import traceback
import uuid

from fastapi import APIRouter, HTTPException, Query

from src.agents.base import AgentInput
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import CitationResponse, QueryResponse
from src.config.intents import Intent
from src.config.logging_config import get_logger
from src.core.registry import get_registry
from src.utils.lazy_singleton import LazySingleton

logger = get_logger()
router = APIRouter(prefix="/query", tags=["Query"])

# ==========================================
# Phase 6 Refactoring: LazySingleton pattern
# Replaces 40+ lines of duplicate global+lock+getter code
# ==========================================

_chatbot = LazySingleton(lambda: __import__('src.agents.chatbot_agent', fromlist=['ChatbotAgent']).ChatbotAgent())


async def get_classifier():
    """Get or create query classifier (async lazy initialization)."""
    from src.core.router import HybridQueryClassifier
    from src.infrastructure.llm_client import get_llm_client

    if not hasattr(get_classifier, '_instance'):
        llm_client = await get_llm_client()
        get_classifier._instance = HybridQueryClassifier(llm_client=llm_client)
    return get_classifier._instance


@router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
)
async def handle_query(
    request: QueryRequest,
    # Faceted search filters
    author: str | None = Query(None, description="Filter by author name"),
    era: str | None = Query(
        None,
        description="Filter by scholarly era (prophetic, tabiun, classical, medieval, ottoman, modern)",
    ),
    book_id: int | None = Query(None, description="Filter by specific book ID"),
    category: str | None = Query(None, description="Filter by category/madhhab"),
    death_year_min: int | None = Query(None, description="Minimum author death year (Hijri)"),
    death_year_max: int | None = Query(None, description="Maximum author death year (Hijri)"),
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
        chatbot = _chatbot.get()
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

        # ==========================================
        # Phase 6 Refactoring: Use AgentRegistry for dynamic routing
        # This replaces the hardcoded if/elif/else block
        # Now ALL 17 intents work automatically!
        # ==========================================

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

        # Use AgentRegistry to get the right agent/tool for this intent
        registry = get_registry()
        agent, is_agent = registry.get_for_intent(intent)
        
        logger.info(
            "query.registry_lookup",
            query_id=query_id,
            intent=intent.value,
            agent=str(agent),
            is_agent=is_agent,
            registry_status=registry.get_status(),
        )

        # Build common agent input
        agent_input = AgentInput(
            query=request.query,
            language=language,
            metadata={
                "madhhab": request.madhhab,
                "filters": filters,
                "hierarchical": hierarchical,
            }
        )

        if agent:
            # Route to registered agent or tool
            agent_result = await agent.execute(agent_input)
            agent_name = getattr(agent, 'name', 'unknown_agent')
            logger.info(
                "query.routed_to_agent",
                query_id=query_id,
                agent=agent_name,
                is_agent=is_agent,
            )
        elif intent == Intent.GREETING:
            # Fallback for greeting
            agent_result = await chatbot.execute(agent_input)
            agent_name = "chatbot_agent"
        else:
            # Default fallback for unhandled intents
            agent_result = await chatbot.execute(AgentInput(
                query=f"أعتذر، لا يمكنني الإجابة على هذا السؤال حالياً. يرجى السؤال عن موضوع آخر.\n\n{request.query}",
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "chatbot_fallback"
            logger.warning(
                "query.no_agent_for_intent",
                query_id=query_id,
                intent=intent.value,
            )

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
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            "query.error",
            query_id=query_id,
            error=str(e),
            error_type=type(e).__name__,
            traceback=tb,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e


@router.get("/test")
async def test_query():
    """Test endpoint to verify query router is working."""
    chatbot = _chatbot.get()
    result = await chatbot.execute(
        AgentInput(query="السلام عليكم", language="ar", metadata={})
    )
    return {
        "status": "ok",
        "chatbot": chatbot.name,
        "answer": result.answer,
        "agent_meta": result.metadata,
    }
