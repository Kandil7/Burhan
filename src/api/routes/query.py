"""
Query route for Athar Islamic QA system.

Routes queries to appropriate agents based on intent using AgentRegistry.
Supports faceted search, hierarchical retrieval, and multi-language responses.

Refactoring goals:
- Lazy singleton initialization for chatbot and classifier
- Dynamic routing through AgentRegistry
- Cleaner separation of concerns
- Better fallback and error handling
"""

from __future__ import annotations

import time
import traceback
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.agents.base import AgentInput
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import CitationResponse, QueryResponse
from src.config.intents import Intent
from src.config.logging_config import get_logger
from src.core.registry import get_registry
from src.infrastructure.llm_client import get_llm_client
from src.utils.lazy_singleton import LazySingleton

logger = get_logger()
router = APIRouter(prefix="/query", tags=["Query"])


_chatbot = LazySingleton(
    lambda: __import__(
        "src.agents.chatbot_agent",
        fromlist=["ChatbotAgent"]
    ).ChatbotAgent()
)


async def _build_classifier():
    from src.core.router import HybridQueryClassifier
    llm_client = await get_llm_client()
    return HybridQueryClassifier(llm_client=llm_client)


_classifier = LazySingleton(_build_classifier)


async def get_classifier():
    """
    Get or create query classifier.

    Supports lazy async initialization through LazySingleton.
    """
    classifier = _classifier.get()
    if hasattr(classifier, "__await__"):
        classifier = await classifier
        _classifier._instance = classifier
    return classifier


def build_filters(
    *,
    author: str | None,
    era: str | None,
    book_id: int | None,
    category: str | None,
    death_year_min: int | None,
    death_year_max: int | None,
) -> dict[str, Any] | None:
    """
    Build optional faceted retrieval filters from query params.
    """
    filters: dict[str, Any] = {}

    if author:
        filters["author"] = author
    if era:
        filters["era"] = era
    if book_id is not None:
        filters["book_id"] = book_id
    if category:
        filters["category"] = category
    if death_year_min is not None:
        filters["author_death_min"] = death_year_min
    if death_year_max is not None:
        filters["author_death_max"] = death_year_max

    return filters or None


def build_agent_input(
    request: QueryRequest,
    *,
    language: str,
    filters: dict[str, Any] | None,
    hierarchical: bool,
) -> AgentInput:
    """
    Build common AgentInput payload for downstream agents/tools.
    """
    return AgentInput(
        query=request.query,
        language=language,
        metadata={
            "madhhab": request.madhhab,
            "filters": filters,
            "hierarchical": hierarchical,
        },
    )


async def execute_fallback(chatbot, request: QueryRequest, language: str):
    """
    Fallback response when no suitable agent is found.
    """
    return await chatbot.execute(
        AgentInput(
            query=(
                "أعتذر، لا يمكنني الإجابة على هذا السؤال حالياً. "
                "يرجى إعادة صياغة السؤال أو السؤال عن موضوع إسلامي آخر.\n\n"
                f"{request.query}"
            ),
            language=language,
            metadata={"madhhab": request.madhhab},
        )
    )


@router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
)
async def handle_query(
    request: QueryRequest,
    author: str | None = Query(None, description="Filter by author name"),
    era: str | None = Query(
        None,
        description="Filter by scholarly era (prophetic, tabiun, classical, medieval, ottoman, modern)",
    ),
    book_id: int | None = Query(None, description="Filter by specific book ID"),
    category: str | None = Query(None, description="Filter by category/madhhab"),
    death_year_min: int | None = Query(None, description="Minimum author death year (Hijri)"),
    death_year_max: int | None = Query(None, description="Maximum author death year (Hijri)"),
    hierarchical: bool = Query(False, description="Use hierarchical retrieval for coherent results"),
):
    """
    Handle user query with intent-based routing and optional faceted search.

    Flow:
    1. Classify intent
    2. Build filters
    3. Resolve target agent via AgentRegistry
    4. Execute target
    5. Return structured response
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())

    try:
        logger.info(
            "query.received",
            query_id=query_id,
            query=request.query[:100],
            requested_language=request.language,
        )

        chatbot = _chatbot.get()
        classifier = await get_classifier()

        router_result = await classifier.classify(request.query)
        intent = router_result.intent
        language = request.language or router_result.language

        logger.info(
            "query.classified",
            query_id=query_id,
            intent=intent.value,
            confidence=router_result.confidence,
            method=router_result.method,
            language=language,
        )

        filters = build_filters(
            author=author,
            era=era,
            book_id=book_id,
            category=category,
            death_year_min=death_year_min,
            death_year_max=death_year_max,
        )

        if filters:
            logger.info(
                "query.filters_applied",
                query_id=query_id,
                filters=filters,
            )

        registry = get_registry()
        agent, is_agent = registry.get_for_intent(intent)

        logger.info(
            "query.registry_lookup",
            query_id=query_id,
            intent=intent.value,
            resolved=bool(agent),
            is_agent=is_agent,
            registry_status=registry.get_status(),
        )

        agent_input = build_agent_input(
            request,
            language=language,
            filters=filters,
            hierarchical=hierarchical,
        )

        if agent is not None:
            agent_result = await agent.execute(agent_input)
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            logger.info(
                "query.routed_to_agent",
                query_id=query_id,
                intent=intent.value,
                agent=agent_name,
                is_agent=is_agent,
            )
        elif intent == Intent.GREETING:
            agent_result = await chatbot.execute(agent_input)
            agent_name = "chatbot_agent"
            logger.info(
                "query.greeting_fallback",
                query_id=query_id,
                agent=agent_name,
            )
        else:
            agent_result = await execute_fallback(chatbot, request, language)
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
                    id=c.id,
                    type=c.type,
                    source=c.source,
                    reference=c.reference,
                    url=c.url,
                    text_excerpt=c.text_excerpt,
                )
                for c in agent_result.citations
            ],
            metadata={
                "agent": agent_name,
                "processing_time_ms": processing_time,
                "classification_method": router_result.method,
                "language": language,
                "hierarchical": hierarchical,
                **agent_result.metadata,
            },
            follow_up_suggestions=agent_result.metadata.get(
                "follow_up_suggestions", []
            ),
        )

    except ValueError as e:
        logger.warning(
            "query.validation_error",
            query_id=query_id,
            error=str(e),
        )
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
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing the query",
        ) from e


@router.get("/test")
async def test_query():
    """
    Test endpoint to verify query router is working.
    """
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