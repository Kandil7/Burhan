"""
Common schemas for Athar API.

Includes shared response models, error schemas, and metadata structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Trace Metadata
# ============================================================================


class TraceMetadata(BaseModel):
    """Request tracing metadata included in all responses."""

    trace_id: str = Field(
        ...,
        description="Unique identifier for the request",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp when request was processed",
        examples=["2024-01-15T10:30:00Z"],
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds",
    )
    routing: RoutingMetadata = Field(
        ...,
        description="Routing information for the request",
    )


class RoutingMetadata(BaseModel):
    """Metadata about how the request was routed."""

    endpoint: str = Field(
        ...,
        description="API endpoint that handled the request",
        examples=["/api/v1/ask"],
    )
    method: str = Field(
        ...,
        description="HTTP method used",
        examples=["POST"],
    )
    version: str = Field(
        default="v1",
        description="API version",
    )


# ============================================================================
# Error Responses
# ============================================================================


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(
        ...,
        description="Error code for programmatic handling",
        examples=["VALIDATION_ERROR", "TIMEOUT", "NOT_FOUND"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    field: str | None = Field(
        None,
        description="Field that caused the error (for validation errors)",
        examples=["query", "language"],
    )
    details: dict[str, Any] | None = Field(
        None,
        description="Additional error context",
    )


class ErrorResponse(BaseModel):
    """
    Standard error response for all API errors.

    All endpoints return errors in this format for consistent client handling.
    """

    error: str = Field(
        ...,
        description="Error type",
        examples=["ValidationError", "TimeoutError", "InternalError"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    trace_id: str | None = Field(
        None,
        description="Request trace ID for debugging",
    )
    details: list[ErrorDetail] | None = Field(
        None,
        description="Detailed error information (for validation errors)",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO timestamp of error",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error": "ValidationError",
                    "message": "Query is required",
                    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                    "details": [
                        {
                            "code": "MISSING_FIELD",
                            "message": "Query is required",
                            "field": "query",
                        }
                    ],
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            ]
        }


# ============================================================================
# Common Response Wrappers
# ============================================================================


class ApiResponse(BaseModel):
    """Generic API response wrapper."""

    data: Any = Field(..., description="Response data")
    meta: TraceMetadata = Field(..., description="Response metadata")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# ============================================================================
# Health Response
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", examples=["ok", "degraded", "error"])
    version: str = Field(default="0.1.0", description="API version")
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependent services",
    )


# ============================================================================
# Citation Schema (shared)
# ============================================================================


class CitationResponse(BaseModel):
    """Citation in API response."""

    id: str = Field(
        description="Citation ID",
        examples=["C1", "C2", "C3"],
    )
    type: str = Field(
        description="Source type",
        examples=["quran", "hadith", "fatwa", "fiqh_book", "dua", "seerah", "tafsir", "aqeedah"],
    )
    source: str = Field(description="Normalized source name")
    reference: str = Field(description="Specific reference")
    url: str | None = Field(
        None,
        description="External URL for verification",
    )
    text_excerpt: str | None = Field(
        None,
        description="Quoted passage from source",
    )
