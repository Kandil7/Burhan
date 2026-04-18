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
async def handle_ask(
    raw_request: Request,
    request: AskRequest,
) -> AskResponse:
    """
    Submit a query to the Athar Islamic QA system.
    Delegates to AskService which orchestrates AnswerQueryUseCase.
    """
    start_time = time.time()
    trace_id = str(uuid.uuid4())

    logger.info("ask.received", trace_id=trace_id, query=request.query[:100])

    # Get application services from app state
    service = raw_request.app.state.ask_service

    # Execute Use Case via Service
    output = await service.process_query(
        query=request.query,
        madhhab=request.madhhab,
        language=request.language,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    # Build response from Use Case output
    return AskResponse(
        query_id=trace_id,
        intent=output.intent,
        intent_confidence=output.confidence,
        answer=output.answer,
        citations=output.citations,
        metadata={
            **output.metadata,
            "processing_time_ms": processing_time_ms,
            "trace_id": trace_id,
        },
        follow_up_suggestions=output.metadata.get("follow_up_suggestions", []),
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


@ask_router.get("/health")
async def health_check():
    """Simple health check for the ask router."""
    return {"status": "ok", "service": "ask"}
