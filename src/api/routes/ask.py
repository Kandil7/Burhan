"""
Ask endpoint for Athar Islamic QA system.

Thin transport layer that delegates to application services/use-cases.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from src.agents.base import AgentInput, AgentOutput
from src.api.schemas.ask import AskRequest, AskResponse
from src.api.schemas.common import CitationResponse, ErrorResponse
from src.domain.intents import Intent
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
ask_router = APIRouter(prefix="/ask", tags=["Ask"])

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"ar", "en"})

_THINK_RE = re.compile(r"<think>.*?", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove thinking blocks from LLM output."""
    return _THINK_RE.sub("", text).strip()


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Helper functions (should be moved to application layer) ───────────────


def _build_filters(
    *,
    author: str | None,
    era: str | None,
    book_id: int | None,
    category: str | None,
    death_year_min: int | None,
    death_year_max: int | None,
) -> dict[str, Any] | None:
    """Build filter dict from query parameters."""
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


def _build_agent_input(
    request: AskRequest,
    *,
    language: str,
    filters: dict[str, Any] | None,
    hierarchical: bool,
) -> AgentInput:
    """Build agent input from request."""
    return AgentInput(
        query=request.query,
        language=language,
        metadata={
            "madhhab": request.madhhab,
            "filters": filters,
            "hierarchical": hierarchical,
        },
    )


def _build_fallback_output(language: str) -> AgentOutput:
    """Return a static fallback when no agent is available."""
    msg = (
        "أعتذر، لا يمكنني الإجابة على هذا السؤال حالياً. يرجى السؤال عن أحكام فقهية أو آيات قرآنية أو أحاديث نبوية."
        if language == "ar"
        else "I'm unable to answer this question. Please ask about Islamic rulings, Quran, or Hadith."
    )
    return AgentOutput(
        answer=msg,
        citations=[],
        confidence=0.0,
        metadata={"agent": "fallback"},
        requires_human_review=False,
    )


def _build_response_metadata(
    *,
    agent_name: str,
    processing_time_ms: int,
    classification_method: str,
    language: str,
    hierarchical: bool,
    agent_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build response metadata dict."""
    return {
        "agent": agent_name,
        "processing_time_ms": processing_time_ms,
        "classification_method": classification_method,
        "language": language,
        "hierarchical": hierarchical,
        "agent_metadata": {k: v for k, v in agent_metadata.items() if k != "follow_up_suggestions"},
    }


# ── Route: POST /ask ────────────────────────────────────────────────────────


@ask_router.post(
    "",
    response_model=AskResponse,
    summary="Submit query to Athar Islamic QA system",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        504: {"model": ErrorResponse, "description": "Timeout error"},
    },
)
async def handle_ask(
    raw_request: Request,
    request: AskRequest,
    author: str | None = Query(None),
    era: str | None = Query(None),
    book_id: int | None = Query(None),
    category: str | None = Query(None),
    death_year_min: int | None = Query(None),
    death_year_max: int | None = Query(None),
    hierarchical: bool = Query(False),
) -> AskResponse:
    """
    Submit a query to the Athar Islamic QA system.

    The endpoint:
    1. Validates the request
    2. Routes to appropriate agent via application layer
    3. Returns structured response with citations and metadata
    4. Includes tracing metadata (trace_id, processing_time_ms)
    """
    start_time = time.time()
    trace_id = _build_trace_id()
    agent_name: str = "unknown"

    try:
        logger.info("ask.received", trace_id=trace_id, query=request.query[:100])

        # Get application services from app state
        app_state = raw_request.app.state
        router = app_state.router
        registry = app_state.registry

        # ── Step 1: Route and classify (use-case: classify_query)
        router_decision = await router.route(request.query)
        intent = router_decision.result.intent

        # ── Step 2: Resolve language
        raw_language = request.language or router_decision.result.language
        language = raw_language if raw_language in SUPPORTED_LANGUAGES else "ar"
        if language != raw_language:
            logger.warning(
                "ask.unsupported_language",
                trace_id=trace_id,
                requested=raw_language,
                fallback=language,
            )

        logger.info(
            "ask.classified",
            trace_id=trace_id,
            intent=intent.value,
            confidence=router_decision.result.confidence,
            method=router_decision.result.method,
            language=language,
        )

        # ── Step 3: Build agent input (use-case: answer_query)
        filters = _build_filters(
            author=author,
            era=era,
            book_id=book_id,
            category=category,
            death_year_min=death_year_min,
            death_year_max=death_year_max,
        )
        agent_input = _build_agent_input(
            request,
            language=language,
            filters=filters,
            hierarchical=hierarchical,
        )

        # ── Step 4: Execute agent (use-case: run_agent)
        timeout = settings.agent_timeout_seconds
        agent, is_agent = registry.get_for_intent(intent)
        logger.info(
            "ask.registry_lookup",
            trace_id=trace_id,
            intent=intent.value,
            resolved=bool(agent),
            is_agent=is_agent,
        )

        if agent is not None:
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            # Import asyncio for timeout handling
            import asyncio

            try:
                agent_result = await asyncio.wait_for(
                    agent.execute(agent_input),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.error(
                    "ask.agent_timeout",
                    trace_id=trace_id,
                    agent=agent_name,
                    timeout_seconds=timeout,
                )
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error": "TimeoutError",
                        "message": "The query took too long. Please try again.",
                        "trace_id": trace_id,
                    },
                )
        else:
            agent_name = "chatbot_fallback"
            agent_result = _build_fallback_output(language)
            logger.warning(
                "ask.no_agent_for_intent",
                trace_id=trace_id,
                intent=intent.value,
            )

        # ── Step 5: Calculate timing
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "ask.completed",
            trace_id=trace_id,
            intent=intent.value,
            agent=agent_name,
            processing_time_ms=processing_time_ms,
        )

        # ── Step 6: Build response with trace metadata
        return AskResponse(
            query_id=trace_id,
            intent=intent.value,
            intent_confidence=router_decision.result.confidence,
            answer=_strip_thinking(agent_result.answer),
            citations=[
                {
                    "id": c.id,
                    "type": c.type,
                    "source": c.source,
                    "reference": c.reference,
                    "url": c.url,
                    "text_excerpt": c.text_excerpt,
                }
                for c in agent_result.citations
            ],
            metadata=_build_response_metadata(
                agent_name=agent_name,
                processing_time_ms=processing_time_ms,
                classification_method=router_decision.result.method,
                language=language,
                hierarchical=hierarchical,
                agent_metadata=agent_result.metadata,
            ),
            follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
            # Trace metadata
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning("ask.validation_error", trace_id=trace_id, error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "trace_id": trace_id,
            },
        ) from e

    except Exception as e:
        logger.error(
            "ask.error",
            trace_id=trace_id,
            error=str(e),
            error_type=type(e).__name__,
            agent=agent_name,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": "Internal server error while processing the query",
                "trace_id": trace_id,
            },
        ) from e


# ── Route: GET /ask/test ────────────────────────────────────────────────────


@ask_router.get("/test")
async def test_ask(raw_request: Request):
    """Test endpoint for the ask router."""
    chatbot = raw_request.app.state.chatbot
    result = await chatbot.execute(AgentInput(query="السلام عليكم", language="ar", metadata={}))
    return {
        "status": "ok",
        "chatbot": chatbot.name,
        "answer": result.answer,
    }
