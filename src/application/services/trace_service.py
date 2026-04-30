# Trace Service Module
"""Service for handling execution traces."""

from datetime import datetime
from typing import Any

from src.application.use_cases.build_trace import (
    BuildTraceInput,
    BuildTraceOutput,
    TraceEvent,
)


class TraceService:
    """Service for managing execution traces."""

    def __init__(self):
        self.active_traces: dict[str, list[TraceEvent]] = {}

    def start_trace(self, query_id: str) -> str:
        """Start a new trace."""
        if query_id not in self.active_traces:
            self.active_traces[query_id] = []
        return query_id

    def add_event(
        self,
        query_id: str,
        event_type: str,
        component: str,
        details: dict[str, Any],
    ) -> None:
        """Add an event to the trace."""
        if query_id not in self.active_traces:
            self.active_traces[query_id] = []

        event = TraceEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            component=component,
            details=details,
        )
        self.active_traces[query_id].append(event)

    async def build_trace(
        self,
        query_id: str,
        final_response: str | None = None,
    ) -> BuildTraceOutput:
        """Build and finalize the trace."""
        events = self.active_traces.get(query_id, [])

        BuildTraceInput(
            query_id=query_id,
            events=events,
            final_response=final_response,
        )

        # Clear trace after building
        if query_id in self.active_traces:
            del self.active_traces[query_id]

        # Return placeholder
        return BuildTraceOutput(
            trace_id=f"trace_{query_id}",
            trace_data={"events": []},
            summary={"total_events": len(events)},
        )

    def get_active_trace(self, query_id: str) -> list[TraceEvent]:
        """Get active trace events."""
        return self.active_traces.get(query_id, [])


# Default service instance
trace_service = TraceService()
