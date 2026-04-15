"""
Query route for Athar Islamic QA system.

Routes queries to appropriate agents based on intent using AgentRegistry.
Supports faceted search, hierarchical retrieval, and multi-language responses.
"""

from __future__ import annotations

import asyncio
import time
import traceback
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from src.agents.base import AgentInput
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import CitationResponse, QueryResponse
from src.config.intents import Intent
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
query_router = APIRouter(prefix="/query", tags=["Query"])

# FIX 8: supported languages with safe fallback
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"ar", "en"})

# FIX 1 (Option C): declare which intents route to chatbot directly
# Add Intent.GREETING here once it's enabled in the enum
_CHATBOT_INTENTS: frozenset[Intent] = frozenset()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_filters(
    *,
    author: str | None,
    era: str | None,
    book_id: int | None,
    category: str | None,
    death_year_min: int | None,
    death_year_max: int | None,
) -> dict[str, Any] | None:
    """Build optional faceted retrieval filters from query params."""
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
    """Build common AgentInput payload for downstream agents."""
    return AgentInput(
        query=request.query,
        language=language,
        metadata={
            "madhhab": request.madhhab,
            "filters": filters,
            "hierarchical": hierarchical,
        },
    )


async def execute_fallback(chatbot: Any, language: str) -> Any:
    """Fallback response when no suitable agent is found."""
    return await chatbot.execute(
        AgentInput(
            query="أعتذر، لا يمكنني الإجابة على هذا السؤال حالياً. يرجى إعادة صياغة السؤال أو السؤال عن موضوع إسلامي آخر.",
            language=language,
            metadata={},
        )
    )


def build_response_metadata(
    *,
    agent_name: str,
    processing_time_ms: int,
    classification_method: str,
    language: str,
    hierarchical: bool,
    agent_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge response metadata without letting agent keys clobber routing keys.

    FIX 5: follow_up_suggestions is stripped from agent_metadata here since
    it's already surfaced as a top-level field on QueryResponse.
    """
    agent_meta_clean = {k: v for k, v in agent_metadata.items() if k != "follow_up_suggestions"}
    return {
        "agent": agent_name,
        "processing_time_ms": processing_time_ms,
        "classification_method": classification_method,
        "language": language,
        "hierarchical": hierarchical,
        "agent_metadata": agent_meta_clean,
    }


async def _run_with_timeout(coro, *, timeout: float, label: str, query_id: str) -> Any:
    """
    Await a coroutine with a timeout, raising HTTP 504 on expiry.
    Centralises timeout handling so each branch stays readable.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(
            "query.agent_timeout",
            query_id=query_id,
            agent=label,
            timeout_seconds=timeout,
        )
        raise HTTPException(
            status_code=504,
            detail="The query took too long to process. Please try again.",
        )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@query_router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
)
async def handle_query(
    raw_request: Request,  # FIX 3+4: access app.state for injected singletons
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
    start_time = time.time()
    query_id = str(uuid.uuid4())
    agent_name: str = "unknown"  # FIX 9: safe default — never UnboundLocalError

    try:
        logger.info(
            "query.received",
            query_id=query_id,
            query=request.query[:100],
            requested_language=request.language,
        )

        # FIX 3+4: singletons live on app.state, built once during lifespan startup.
        # The API layer no longer constructs infrastructure objects.
        app_state = raw_request.app.state
        chatbot = app_state.chatbot
        router = app_state.router
        registry = app_state.registry  # FIX 3: not rebuilt on every request

        # Router returns a RoutingDecision, not ClassificationResult
        router_decision = await router.route(request.query)
        intent = router_decision.result.intent

        # FIX 8: validate language, fall back to Arabic
        raw_language = request.language or router_decision.result.language
        language = raw_language if raw_language in SUPPORTED_LANGUAGES else "ar"
        if language != raw_language:
            logger.warning(
                "query.unsupported_language",
                query_id=query_id,
                requested=raw_language,
                fallback=language,
            )

        logger.info(
            "query.classified",
            query_id=query_id,
            intent=intent.value,
            confidence=router_decision.result.confidence,
            method=router_decision.result.method,
            language=language,
        )

        # DEBUG: Print what's happening before registry lookup
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"DEBUG: Looking up intent={intent.value} in registry\n")

        filters = build_filters(
            author=author,
            era=era,
            book_id=book_id,
            category=category,
            death_year_min=death_year_min,
            death_year_max=death_year_max,
        )
        if filters:
            logger.info("query.filters_applied", query_id=query_id, filters=filters)

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

        timeout = settings.agent_timeout_seconds  # FIX 7: from settings, not hardcoded

        # FIX 1: GREETING branch replaced with _CHATBOT_INTENTS set —
        # no more AttributeError risk; just add the intent to the set when ready.
        if agent is not None:
            agent_result = await _run_with_timeout(
                agent.execute(agent_input),
                timeout=timeout,
                label=getattr(agent, "name", agent.__class__.__name__),
                query_id=query_id,
            )
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            logger.info(
                "query.routed_to_agent",
                query_id=query_id,
                intent=intent.value,
                agent=agent_name,
                is_agent=is_agent,
            )

        elif intent in _CHATBOT_INTENTS:
            agent_result = await _run_with_timeout(
                chatbot.execute(agent_input),
                timeout=timeout,
                label="chatbot_agent",
                query_id=query_id,
            )
            agent_name = "chatbot_agent"
            logger.info("query.chatbot_intent", query_id=query_id, intent=intent.value)

        else:
            agent_result = await _run_with_timeout(
                execute_fallback(chatbot, language),
                timeout=timeout,
                label="chatbot_fallback",
                query_id=query_id,
            )
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
            intent_confidence=router_decision.result.confidence,
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
            metadata=build_response_metadata(
                agent_name=agent_name,
                processing_time_ms=processing_time,
                classification_method=router_decision.result.method,
                language=language,
                hierarchical=hierarchical,
                agent_metadata=agent_result.metadata,  # FIX 5: stripped inside helper
            ),
            follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
        )

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning("query.validation_error", query_id=query_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        # Write error to file for debugging
        import os

        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "error.log")
            with open(log_path, "a", encoding="utf-8") as f:
                import traceback

                f.write(f"ERROR: {type(e).__name__}: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass

        logger.error(  # FIX 6: exc_info=True alone — no duplicate traceback field
            "query.error",
            query_id=query_id,
            error=str(e),
            error_type=type(e).__name__,
            agent=agent_name,  # helps pinpoint which agent failed
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing the query",
        ) from e


# ---------------------------------------------------------------------------
# Test endpoint
# ---------------------------------------------------------------------------


@query_router.get("/test")
async def test_query(raw_request: Request):
    """Test endpoint to verify query router is working."""
    chatbot = raw_request.app.state.chatbot
    result = await chatbot.execute(AgentInput(query="السلام عليكم", language="ar", metadata={}))
    return {
        "status": "ok",
        "chatbot": chatbot.name,
        "answer": result.answer,
        "agent_meta": result.metadata,
    }
