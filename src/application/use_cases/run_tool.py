# Run Tool Use Case
"""Use case for running deterministic tools.

Dispatches to the implementations in :mod:`src.tools` and reports the tool's
own success flag. Zakat and inheritance are HTTP-only (see
``src.application.services.tool_service``); requesting them here fails with an
explicit message instead of a placeholder success.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.application.services.tool_service import ToolService


class ToolType(str, Enum):
    """Types of available tools."""

    ZAKAT_CALCULATOR = "zakat_calculator"
    INHERITANCE_CALCULATOR = "inheritance_calculator"
    PRAYER_TIMES = "prayer_times"
    HIJRI_CALENDAR = "hijri_calendar"
    DUA_RETRIEVAL = "dua_retrieval"


@dataclass
class RunToolInput:
    """Input for run tool use case."""

    tool_type: ToolType
    parameters: dict[str, Any]


@dataclass
class RunToolOutput:
    """Output for run tool use case."""

    result: Any
    tool_type: ToolType
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class RunToolUseCase:
    """Use case for running deterministic tools."""

    def __init__(self) -> None:
        self._service: ToolService | None = None

    @property
    def tool_service(self) -> ToolService:
        """Lazily build the tool service to avoid an import cycle at module load."""
        if self._service is None:
            from src.application.services.tool_service import ToolService

            self._service = ToolService()
        return self._service

    async def execute(self, input: RunToolInput) -> RunToolOutput:
        """
        Execute the tool use case.

        Steps:
        1. Resolve the tool implementation
        2. Execute it with the supplied parameters
        3. Report the result or the tool's failure

        Args:
            input: Tool type and parameters

        Returns:
            RunToolOutput describing the result or the failure
        """
        return await self.tool_service.run_tool(input.tool_type, input.parameters)


# Default use case instance
run_tool_use_case = RunToolUseCase()
