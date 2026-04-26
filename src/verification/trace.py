"""
Verification Trace for Burhan Islamic QA system.

Provides structured tracing for the verification pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VerificationStep(BaseModel):
    """A single step in the verification pipeline."""

    step_name: str = Field(description="Name of the step")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = Field(default=None)
    status: str = Field(default="running")  # running, completed, failed
    details: dict[str, Any] = Field(default_factory=dict)

    def complete(self, status: str = "completed", details: dict[str, Any] | None = None):
        """Mark step as complete."""
        self.end_time = datetime.utcnow()
        self.status = status
        if details:
            self.details.update(details)


class VerificationTrace(BaseModel):
    """Complete trace of a verification pipeline execution."""

    trace_id: str = Field(description="Unique trace ID")
    query: str = Field(description="Original query")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = Field(default=None)
    steps: list[VerificationStep] = Field(default_factory=list)
    total_passages: int = Field(default=0)
    verified_passages: int = Field(default=0)
    overall_status: str = Field(default="running")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_step(self, step: VerificationStep):
        """Add a step to the trace."""
        self.steps.append(step)

    def complete(self, status: str, metadata: dict[str, Any] | None = None):
        """Mark trace as complete."""
        self.end_time = datetime.utcnow()
        self.overall_status = status
        if metadata:
            self.metadata.update(metadata)

    def get_timing_summary(self) -> dict[str, float]:
        """Get timing summary for all steps."""
        total_ms = 0.0
        step_times = {}

        for step in self.steps:
            if step.end_time and step.start_time:
                duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                step_times[step.step_name] = duration_ms
                total_ms += duration_ms

        return {
            "total_ms": total_ms,
            "steps": step_times,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.overall_status,
            "total_passages": self.total_passages,
            "verified_passages": self.verified_passages,
            "steps": [
                {
                    "name": s.step_name,
                    "status": s.status,
                    "duration_ms": (
                        (s.end_time - s.start_time).total_seconds() * 1000 if s.end_time and s.start_time else None
                    ),
                }
                for s in self.steps
            ],
            "timing": self.get_timing_summary(),
            "metadata": self.metadata,
        }


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    import uuid

    return f"vrf_{uuid.uuid4().hex[:12]}"


__all__ = ["VerificationStep", "VerificationTrace", "generate_trace_id"]
