"""
Query route for Athar Islamic QA system.
"""
from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from src.agents.base import AgentInput, AgentOutput
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import CitationResponse, QueryResponse
from src.config.intents import Intent
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
query_router = APIRouter(prefix="/query", tags=["Query"])

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"ar", "en"})

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

def _strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_filters(
    *,
    author: str | None,
    era: str | None,
    book_id: int | None,
    category: str | None,
    death_year_min: int | None,
    death_year_max: int | None,
) -> dict[str, Any] | None:
    filters: dict[str, Any] = {}
    if author:                     filters["author"]           = author
    if era:                        filters["era"]              = era
    if book_id is not None:        filters["book_id"]          = book_id
    if category:                   filters["category"]         = category
    if death_year_min is not None: filters["author_death_min"] = death_year_min
    if death_year_max is not None: filters["author_death_max"] = death_year_max
    return filters or None


def build_agent_input(
    request: QueryRequest,
    *,
    language: str,
    filters: dict[str, Any] | None,
    hierarchical: bool,
) -> AgentInput:
    return AgentInput(
        query=request.query,
        language=language,
        metadata={
            "madhhab":      request.madhhab,
            "filters":      filters,
            "hierarchical": hierarchical,
        },
    )


def build_fallback_output(language: str) -> AgentOutput:
    """Return a static fallback — never calls ChatbotAgent."""
    msg = (
        "أعتذر، لا يمكنني الإجابة على هذا السؤال حالياً. "
        "يرجى السؤال عن أحكام فقهية أو آيات قرآنية أو أحاديث نبوية."
        if language == "ar" else
        "I'm unable to answer this question. "
        "Please ask about Islamic rulings, Quran, or Hadith."
    )
    return AgentOutput(
        answer=msg,
        citations=[],
        confidence=0.0,
        metadata={"agent": "fallback"},
        requires_human_review=False,
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
    return {
        "agent":                 agent_name,
        "processing_time_ms":    processing_time_ms,
        "classification_method": classification_method,
        "language":              language,
        "hierarchical":          hierarchical,
        "agent_metadata":        {
            k: v for k, v in agent_metadata.items()
            if k != "follow_up_suggestions"
        },
    }


async def _run_with_timeout(coro, *, timeout: float, label: str, query_id: str) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("query.agent_timeout", query_id=query_id,
                     agent=label, timeout_seconds=timeout)
        raise HTTPException(status_code=504,
                            detail="The query took too long. Please try again.")


# ── Route ─────────────────────────────────────────────────────────────────────

@query_router.post("", response_model=QueryResponse,
                   summary="Submit query to Athar Islamic QA system")
async def handle_query(
    raw_request:    Request,
    request:        QueryRequest,
    author:         str | None = Query(None),
    era:            str | None = Query(None),
    book_id:        int | None = Query(None),
    category:       str | None = Query(None),
    death_year_min: int | None = Query(None),
    death_year_max: int | None = Query(None),
    hierarchical:   bool       = Query(False),
):
    start_time = time.time()
    query_id   = str(uuid.uuid4())
    agent_name: str = "unknown"

    try:
        logger.info("query.received", query_id=query_id, query=request.query[:100])

        app_state = raw_request.app.state
        router    = app_state.router
        registry  = app_state.registry

        router_decision = await router.route(request.query)
        intent          = router_decision.result.intent

        raw_language = request.language or router_decision.result.language
        language     = raw_language if raw_language in SUPPORTED_LANGUAGES else "ar"
        if language != raw_language:
            logger.warning("query.unsupported_language", query_id=query_id,
                           requested=raw_language, fallback=language)

        logger.info("query.classified", query_id=query_id, intent=intent.value,
                    confidence=router_decision.result.confidence,
                    method=router_decision.result.method, language=language)

        filters     = build_filters(
            author=author, era=era, book_id=book_id, category=category,
            death_year_min=death_year_min, death_year_max=death_year_max,
        )
        agent_input = build_agent_input(
            request, language=language, filters=filters, hierarchical=hierarchical,
        )
        timeout = settings.agent_timeout_seconds

        agent, is_agent = registry.get_for_intent(intent)
        logger.info("query.registry_lookup", query_id=query_id, intent=intent.value,
                    resolved=bool(agent), is_agent=is_agent)

        if agent is not None:
            agent_name   = getattr(agent, "name", agent.__class__.__name__)   # before execute
            agent_result = await _run_with_timeout(
                agent.execute(agent_input), timeout=timeout,
                label=agent_name, query_id=query_id,
            )

        else:
            agent_name   = "chatbot_fallback"
            agent_result = build_fallback_output(language)
            logger.warning("query.no_agent_for_intent",
                           query_id=query_id, intent=intent.value)

        processing_time = int((time.time() - start_time) * 1000)
        logger.info("query.completed", query_id=query_id, intent=intent.value,
                    agent=agent_name, processing_time_ms=processing_time)

        return QueryResponse(
            query_id=query_id,
            intent=intent.value,
            intent_confidence=router_decision.result.confidence,
            answer=_strip_thinking(agent_result.answer),
            citations=[
                CitationResponse(
                    id=c.id, type=c.type, source=c.source,
                    reference=c.reference, url=c.url,
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
                agent_metadata=agent_result.metadata,
            ),
            follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
        )

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning("query.validation_error", query_id=query_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        logger.error("query.error", query_id=query_id, error=str(e),
                     error_type=type(e).__name__, agent=agent_name, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing the query",
        ) from e


# ── Test endpoint ─────────────────────────────────────────────────────────────

@query_router.get("/test")
async def test_query(raw_request: Request):
    chatbot = raw_request.app.state.chatbot
    result  = await chatbot.execute(
        AgentInput(query="السلام عليكم", language="ar", metadata={})
    )
    return {"status": "ok", "chatbot": chatbot.name, "answer": result.answer}