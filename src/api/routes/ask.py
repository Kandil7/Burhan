"""
Ask endpoint for Athar Islamic QA system.

Thin transport layer that delegates to application services/use-cases.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Request

from src.api.schemas.ask import AskRequest, AskResponse
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.services.citation_service import enrich_response_with_citations 
logger = get_logger()
ask_router = APIRouter(prefix="/ask", tags=["Ask"])


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
async def handle_ask(raw_request: Request, request: AskRequest) -> AskResponse:
    start_time = time.time()
    trace_id = str(uuid.uuid4())

    logger.info("ask.received", trace_id=trace_id, query=request.query[:100])

    service = raw_request.app.state.ask_service

    output = await service.process_query(
        query=request.query,
        madhhab=request.madhhab,
        language=request.language,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    # نفترض أن output لديه method to_dict أو هو dict بالفعل
    if hasattr(output, "to_dict"):
        base = output.to_dict()
    elif isinstance(output, dict):
        base = output
    else:
        base = {
            "intent": output.intent,
            "confidence": output.confidence,
            "answer": output.answer,
            "citations": output.citations,
            "metadata": getattr(output, "metadata", {}) or {},
            "follow_up_suggestions": getattr(output, "follow_up_suggestions", []),
            "requires_human_review": getattr(output, "requires_human_review", False),
        }

    # enrich: answer_clean + citations_structured + footnotes + citation_stats
    enriched = enrich_response_with_citations(base)

    agent_meta = enriched.get("metadata") or {}
    sub_intent = agent_meta.get("sub_intent")
    answer_mode = agent_meta.get("answer_mode", "answer")
    requires_human_review = bool(enriched.get("requires_human_review", False))

    return AskResponse(
        query_id=trace_id,
        intent=enriched["intent"],
        sub_intent=sub_intent,
        intent_confidence=enriched.get("confidence", 0.0),
        answer=enriched["answer"],  # raw (فيه [C1] لو أنت لسه بتحبها)
        answer_clean=enriched.get("answer_clean"),
        answer_mode=answer_mode,
        citations=enriched.get("citations_structured", enriched.get("citations", [])),
        citation_chunks=enriched.get("citation_chunks", []),
        citations_footnotes=enriched.get("citations_footnotes", []),
        metadata={
            **agent_meta,
            "trace_id": trace_id,
        },
        follow_up_suggestions=enriched.get("follow_up_suggestions", []),
        requires_human_review=requires_human_review,
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


@ask_router.get("/health")
async def health_check():
    """Simple health check for the ask router."""
    return {"status": "ok", "service": "ask"}
