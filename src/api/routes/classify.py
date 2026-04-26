"""
Classify endpoint for Burhan Islamic QA system.

Thin transport layer for intent classification.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.schemas.classify import ClassifyRequest, ClassifyResponse
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger

logger = get_logger("Burhan.api.classify")

classify_router = APIRouter(prefix="", tags=["Classify"])


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Lazy import to avoid circular dependency ─────────────────────────────


def get_router(request: Request):
    """Inject the shared RouterAgent from app state."""
    if hasattr(request.app.state, "router"):
        return request.app.state.router
    if hasattr(request.app.state, "classifier"):
        return request.app.state.classifier

    raise RuntimeError(f"Classifier not initialized. Available state: {list(request.app.state.__dict__.keys())}")


# ── Route: POST /classify ───────────────────────────────────────────────────


@classify_router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify a query and return intent + route",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def classify(
    request: Request,
    req: ClassifyRequest,
    router_agent=Depends(get_router),
) -> ClassifyResponse:
    """
    Classify a user query and return the routing decision.

    This endpoint provides fast classification without full RAG pipeline.
    For full query handling, use the /ask endpoint instead.

    Returns:
        - Detected intent with confidence
        - Recommended route
        - Additional metadata for agent selection
    """
    start_time = time.time()
    trace_id = _build_trace_id()

    try:
        logger.info("classify.received", trace_id=trace_id, query=req.query[:100])

        # Delegate to application layer (use-case: classify_query)
        decision = await router_agent.route(req.query)

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "classify.completed",
            trace_id=trace_id,
            intent=decision.result.intent.value,
            confidence=decision.result.confidence,
            method=decision.result.method,
            processing_time_ms=processing_time_ms,
        )

        # Return response with trace metadata
        return ClassifyResponse(
            result={
                "intent": decision.result.intent.value,
                "confidence": decision.result.confidence,
                "language": decision.result.language,
                "reasoning": decision.result.reasoning,
                "requires_retrieval": decision.result.requires_retrieval,
                "method": decision.result.method,
                "quran_subintent": (decision.result.quran_subintent.value if decision.result.quran_subintent else None),
                "subquestions": decision.result.subquestions,
            },
            route=decision.route,
            agent_metadata=decision.agent_metadata,
            # Trace metadata
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "classify.error",
            trace_id=trace_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": "Internal server error during classification",
                "trace_id": trace_id,
            },
        ) from e
