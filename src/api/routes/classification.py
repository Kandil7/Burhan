"""
Classification route for Athar Islamic QA system.

Provides a dedicated /classify endpoint that uses the new
HybridIntentClassifier for fast, accurate intent classification.

This endpoint provides fast classification without full RAG pipeline.
For full query handling, use the /query endpoint instead.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from src.api.schemas.classification import (
    ClassificationResultSchema,
    ClassifyRequest,
    HealthResponse,
    RoutingDecisionSchema,
)
from src.application.hybrid_classifier import HybridIntentClassifier
from src.application.router import RouterAgent
from src.infrastructure.logging.logger import get_logger

logger = get_logger("athar.api.classification")

APP_VERSION = "1.0.0"

router = APIRouter(prefix="", tags=["Classification"])


# ============================================================================
# Route dependency injection
# ============================================================================


def get_router(request: Request) -> RouterAgent:
    """Inject the shared RouterAgent from app state."""
    return request.app.state.router


# ============================================================================
# Exception handler
# ============================================================================


@router.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    logger.error("unhandled_error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again."},
    )


# ============================================================================
# Routes
# ============================================================================


@router.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    """Health check endpoint for classification service."""
    return HealthResponse(status="ok", version=APP_VERSION)


@router.post(
    "/classify",
    response_model=RoutingDecisionSchema,
    summary="Classify a query and return intent + route",
    tags=["router"],
)
async def classify(
    req: ClassifyRequest,
    router_agent: RouterAgent = Depends(get_router),
) -> RoutingDecisionSchema:
    """
    Classify a user query and return the routing decision.

    This endpoint uses the new HybridIntentClassifier which provides:
    - Fast keyword-based classification for clear signals
    - Jaccard similarity fallback for ambiguous queries
    - Quran sub-intent detection

    For queries requiring full RAG pipeline, use the /query endpoint instead.
    """
    decision = await router_agent.route(req.query)

    return RoutingDecisionSchema(
        result=ClassificationResultSchema(
            intent=decision.result.intent.value,
            confidence=decision.result.confidence,
            language=decision.result.language,
            reasoning=decision.result.reasoning,
            requires_retrieval=decision.result.requires_retrieval,
            method=decision.result.method,
            quran_subintent=(decision.result.quran_subintent.value if decision.result.quran_subintent else None),
            subquestions=decision.result.subquestions,
        ),
        route=decision.route,
        agent_metadata=decision.agent_metadata,
    )
