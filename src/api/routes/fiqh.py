"""
Fiqh endpoint for Athar Islamic QA system.

Provides a dedicated endpoint for Fiqh (Islamic Jurisprudence) queries
with collection-aware RAG capabilities.

Phase 2.2: Fiqh API route endpoint.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from src.agents.base import AgentInput
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.config.settings import settings


logger = get_logger()
fiqh_router = APIRouter(prefix="/fiqh", tags=["Fiqh"])

# ── Regex patterns ─────────────────────────────────────────────────────────
_THINK_RE = re.compile(r"<think>.*?", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove thinking blocks from LLM output."""
    return _THINK_RE.sub("", text).strip()


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Request/Response Models ────────────────────────────────────────────────


class FiqhRequest(BaseModel):
    """Request model for POST /fiqh/answer endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's Fiqh question in Arabic or English",
        examples=["ما حكم الزكاة؟", "Is interest (riba) halal?"],
    )
    language: str = Field(
        default="ar",
        pattern="^(ar|en)$",
        description="Response language",
    )
    madhhab: str | None = Field(
        default=None,
        pattern="^(hanafi|maliki|shafii|hanbali|auto)$",
        description="Preferred Islamic school of jurisprudence",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        # Remove HTML tags
        v = re.sub(r"<[^>]+>", "", v)
        return v.strip()


class FiqhResponse(BaseModel):
    """Response model for POST /fiqh/answer endpoint."""

    answer: str = Field(..., description="Generated answer text")
    citations: list[dict] = Field(
        default_factory=list,
        description="List of citations with structured references",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    ikhtilaf_detected: bool = Field(
        default=False,
        description="Whether any Islamic scholarly disagreement (ikhtilaf) was detected",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Processing metadata (agent, time, madhhab, etc.)",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


# ── Dependencies ────────────────────────────────────────────────────────────


def get_fiqh_agent(request: Request):
    """Get FiQH agent from app state."""
    agent = getattr(request.app.state, "fiqh_agent", None)
    if agent is None:
        raise HTTPException(503, detail="FiqhAgent is not initialized.")
    return agent


# ── Helper Functions ────────────────────────────────────────────────────────


def _build_filters(
    *,
    author: str | None,
    era: str | None,
    book_id: int | None,
) -> dict[str, Any] | None:
    """Build filter dict from query parameters."""
    filters: dict[str, Any] = {}
    if author:
        filters["author"] = author
    if era:
        filters["era"] = era
    if book_id is not None:
        filters["book_id"] = book_id
    return filters or None


def _build_agent_input(
    query: str,
    language: str,
    *,
    madhhab: str | None,
    filters: dict[str, Any] | None,
) -> AgentInput:
    """Build agent input from request parameters."""
    return AgentInput(
        query=query,
        language=language,
        metadata={
            "madhhab": madhhab,
            "filters": filters,
        },
    )


def _build_response_metadata(
    *,
    agent_name: str,
    processing_time_ms: int,
    language: str,
    madhhab: str | None,
    agent_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build response metadata dict."""
    return {
        "agent": agent_name,
        "processing_time_ms": processing_time_ms,
        "language": language,
        "madhhab": madhhab,
        "agent_metadata": {k: v for k, v in agent_metadata.items() if k != "follow_up_suggestions"},
    }


# ── Route: POST /fiqh/answer ───────────────────────────────────────────────


@fiqh_router.post(
    "/answer",
    response_model=FiqhResponse,
    summary="Answer Fiqh question",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
        504: {"model": ErrorResponse, "description": "Timeout error"},
    },
)
async def handle_fiqh_question(
    request: Request,
    fiqh_request: FiqhRequest,
    author: str | None = Query(
        None,
        description="Filter by author name",
        examples=["الشاطبي", "ابن عثيمين"],
    ),
    era: str | None = Query(
        None,
        description="Filter by historical era",
        examples=["القرن الرابع الهجري", "العصر الحديث"],
    ),
    book_id: int | None = Query(
        None,
        ge=1,
        description="Filter by book ID",
    ),
    agent=Depends(get_fiqh_agent),
) -> FiqhResponse:
    """
    Submit a Fiqh (Islamic Jurisprudence) question to the Athar system.

    The endpoint:
    1. Validates the request
    2. Routes to the FiqhCollectionAgent with collection-aware RAG
    3. Returns structured response with citations and metadata
    4. Detects and reports scholarly disagreement (ikhtilaf)
    5. Includes tracing metadata (trace_id, processing_time_ms)

    Query Parameters (optional filters):
    - author: Filter by author name (e.g., "الشاطبي", "ابن عثيمين")
    - era: Filter by historical era (e.g., "القرن الرابع الهجري")
    - book_id: Filter by specific book ID
    """
    start_time = time.time()
    trace_id = _build_trace_id()
    agent_name: str = "fiqh_collection_agent"

    try:
        logger.info("fiqh.received", trace_id=trace_id, query=fiqh_request.query[:100])

        # Build filters from query parameters
        filters = _build_filters(
            author=author,
            era=era,
            book_id=book_id,
        )

        # Build agent input
        agent_input = _build_agent_input(
            query=fiqh_request.query,
            language=fiqh_request.language,
            madhhab=fiqh_request.madhhab,
            filters=filters,
        )

        # Execute agent with timeout
        timeout = settings.agent_timeout_seconds

        import asyncio

        try:
            agent_result = await asyncio.wait_for(
                agent.execute(agent_input),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                "fiqh.agent_timeout",
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

        # Calculate timing
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Detect ikhtilaf from agent metadata
        ikhtilaf_detected = agent_result.metadata.get("ikhtilaf_detected", False) or (
            len(agent_result.citations) > 1
            and any(c.source != agent_result.citations[0].source for c in agent_result.citations[1:])
        )

        logger.info(
            "fiqh.completed",
            trace_id=trace_id,
            agent=agent_name,
            processing_time_ms=processing_time_ms,
            ikhtilaf_detected=ikhtilaf_detected,
            citations_count=len(agent_result.citations),
        )

        # Build response
        return FiqhResponse(
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
            confidence=agent_result.confidence,
            ikhtilaf_detected=ikhtilaf_detected,
            metadata=_build_response_metadata(
                agent_name=agent_name,
                processing_time_ms=processing_time_ms,
                language=fiqh_request.language,
                madhhab=fiqh_request.madhhab,
                agent_metadata=agent_result.metadata,
            ),
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning("fiqh.validation_error", trace_id=trace_id, error=str(e))
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
            "fiqh.error",
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


# ── Route: GET /fiqh/test ───────────────────────────────────────────────────


@fiqh_router.get("/test")
async def test_fiqh(request: Request, agent=Depends(get_fiqh_agent)):
    """Test endpoint for the fiqh router."""
    result = await agent.execute(
        AgentInput(
            query="ما حكم الزكاة؟",
            language="ar",
            metadata={},
        )
    )
    return {
        "status": "ok",
        "agent": agent.name,
        "answer": result.answer[:200],
        "citations_count": len(result.citations),
    }
