"""
Schemas for request tracing and trace viewing.

Provides models for trace metadata and trace retrieval.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    """Individual span in a trace."""

    name: str = Field(..., description="Span name")
    start_time_ms: int = Field(..., description="Start time relative to request start")
    duration_ms: int = Field(..., description="Span duration in milliseconds")
    status: str = Field(
        ...,
        description="Span status",
        examples=["ok", "error", "pending"],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Span-specific metadata",
    )


class TraceInfo(BaseModel):
    """Complete trace information."""

    trace_id: str = Field(
        ...,
        description="Unique trace identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    query: str = Field(..., description="Original query")
    intent: str = Field(..., description="Detected intent")
    status: str = Field(
        ...,
        description="Overall trace status",
        examples=["completed", "failed", "timeout"],
    )
    total_duration_ms: int = Field(
        ...,
        ge=0,
        description="Total trace duration",
    )
    spans: list[TraceSpan] = Field(
        default_factory=list,
        description="Trace spans",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional trace metadata",
    )


class TraceListResponse(BaseModel):
    """Response for listing traces."""

    traces: list[TraceInfo] = Field(
        ...,
        description="List of traces",
    )
    total: int = Field(..., ge=0, description="Total traces")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Page size")


class TraceDetailResponse(BaseModel):
    """Response for trace details."""

    trace: TraceInfo = Field(..., description="Trace information")
    request: dict[str, Any] = Field(
        default_factory=dict,
        description="Original request",
    )
    response: dict[str, Any] = Field(
        default_factory=dict,
        description="Response data",
    )


# ============================================================================
# Tracing configuration
# ============================================================================


class TraceConfig(BaseModel):
    """Configuration for request tracing."""

    enabled: bool = Field(
        default=True,
        description="Whether tracing is enabled",
    )
    sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Sample rate for tracing (0.0-1.0)",
    )
    include_spans: bool = Field(
        default=True,
        description="Whether to include span details",
    )
    max_spans: int = Field(
        default=100,
        ge=1,
        description="Maximum number of spans to store",
    )
