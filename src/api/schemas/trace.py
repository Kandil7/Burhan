"""
API Trace Schema for Response Tracing.

Provides structured trace information for API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    """A single span in the trace."""

    name: str = Field(description="Span name")
    start_time: datetime = Field(description="Start timestamp")
    end_time: datetime | None = Field(default=None)
    duration_ms: float | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseTrace(BaseModel):
    """Complete trace for an API response."""

    request_id: str = Field(description="Request ID")
    endpoint: str = Field(description="API endpoint")
    method: str = Field(description="HTTP method")
    start_time: datetime = Field(description="Request start time")
    end_time: datetime = Field(description="Request end time")
    duration_ms: float = Field(description="Total duration in ms")
    status_code: int = Field(description="Response status code")
    spans: list[TraceSpan] = Field(default_factory=list, description="Trace spans")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_span(self, span: TraceSpan):
        """Add a span to the trace."""
        self.spans.append(span)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "status_code": self.status_code,
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": s.duration_ms,
                    "metadata": s.metadata,
                }
                for s in self.spans
            ],
            "metadata": self.metadata,
        }


__all__ = ["TraceSpan", "ResponseTrace"]
