# Build Trace Use Case
"""Use case for building execution traces."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TraceEvent:
    """A single event in the trace."""

    timestamp: datetime
    event_type: str
    component: str
    details: Dict[str, Any]


@dataclass
class BuildTraceInput:
    """Input for build trace use case."""

    query_id: str
    events: List[TraceEvent]
    final_response: Optional[str] = None


@dataclass
class BuildTraceOutput:
    """Output for build trace use case."""

    trace_id: str
    trace_data: Dict[str, Any]
    summary: Optional[Dict[str, Any]] = None


class BuildTraceUseCase:
    """Use case for building execution traces."""

    def __init__(self):
        pass

    async def execute(self, input: BuildTraceInput) -> BuildTraceOutput:
        """
        Execute the build trace use case.

        Steps:
        1. Sort events by timestamp
        2. Group events by component
        3. Generate summary statistics
        4. Format trace data
        """
        # Generate trace ID
        trace_id = f"trace_{input.query_id}_{int(datetime.now().timestamp())}"

        # Group events by component
        events_by_component: Dict[str, List[TraceEvent]] = {}
        for event in sorted(input.events, key=lambda e: e.timestamp):
            if event.component not in events_by_component:
                events_by_component[event.component] = []
            events_by_component[event.component].append(event)

        # Generate summary
        summary = {
            "total_events": len(input.events),
            "components": list(events_by_component.keys()),
            "has_response": input.final_response is not None,
        }

        trace_data = {
            "query_id": input.query_id,
            "trace_id": trace_id,
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "component": e.component,
                    "details": e.details,
                }
                for e in input.events
            ],
            "final_response": input.final_response,
        }

        return BuildTraceOutput(
            trace_id=trace_id,
            trace_data=trace_data,
            summary=summary,
        )


# Default use case instance
build_trace_use_case = BuildTraceUseCase()
