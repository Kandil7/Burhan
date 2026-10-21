# Tool Service Module
"""Service for handling tool operations.

Delegates to the deterministic tool implementations in :mod:`src.tools`.
Zakat and inheritance are exposed only through ``/api/v1/tools/*`` because
their payload building lives in the route layer; calling them here raises
:class:`ToolUnavailableError` instead of returning a fake success payload.
"""

from typing import Any

from src.application.use_cases.run_tool import RunToolOutput, ToolType
from src.tools.base import BaseTool


class ToolUnavailableError(RuntimeError):
    """Raised when a tool has no in-process handler."""


# Tools that only exist behind an HTTP route.
HTTP_ONLY_TOOLS: dict[ToolType, str] = {
    ToolType.ZAKAT_CALCULATOR: "/api/v1/tools/zakat",
    ToolType.INHERITANCE_CALCULATOR: "/api/v1/tools/inheritance",
}


def _build_tool(tool_type: ToolType) -> BaseTool:
    """Instantiate the tool that backs ``tool_type``."""
    if tool_type is ToolType.PRAYER_TIMES:
        from src.tools.prayer_times_tool import PrayerTimesTool

        return PrayerTimesTool()

    if tool_type is ToolType.HIJRI_CALENDAR:
        from src.tools.hijri_calendar_tool import HijriCalendarTool

        return HijriCalendarTool()

    if tool_type is ToolType.DUA_RETRIEVAL:
        from src.tools.dua_retrieval_tool import DuaRetrievalTool

        return DuaRetrievalTool()

    raise ToolUnavailableError(f"Unknown tool type: {tool_type}")


class ToolService:
    """Service for processing tool operations."""

    def __init__(self) -> None:
        self._tool_cache: dict[ToolType, BaseTool] = {}

    def get_tool(self, tool_type: ToolType) -> BaseTool:
        """Return a cached tool instance, building it on first use."""
        if tool_type in HTTP_ONLY_TOOLS:
            raise ToolUnavailableError(
                f"Tool {tool_type.value!r} is only available over HTTP at "
                f"{HTTP_ONLY_TOOLS[tool_type]} and has no in-process handler."
            )

        tool = self._tool_cache.get(tool_type)
        if tool is None:
            tool = _build_tool(tool_type)
            self._tool_cache[tool_type] = tool
        return tool

    async def run_tool(
        self,
        tool_type: ToolType,
        parameters: dict[str, Any],
    ) -> RunToolOutput:
        """
        Run a tool with parameters.

        Args:
            tool_type: Type of tool to run
            parameters: Tool parameters passed to the tool's ``execute`` method

        Returns:
            RunToolOutput with the tool result, or the failure reported by the tool
        """
        try:
            tool = self.get_tool(tool_type)
            output = await tool.execute(**parameters)
        except Exception as e:
            return RunToolOutput(
                result=None,
                tool_type=tool_type,
                success=False,
                error_message=str(e),
            )

        if not output.success:
            return RunToolOutput(
                result=output.result,
                tool_type=tool_type,
                success=False,
                error_message=output.error or "Tool execution failed",
                metadata=output.metadata,
            )

        return RunToolOutput(
            result=output.result,
            tool_type=tool_type,
            success=True,
            metadata=output.metadata,
        )


# Default service instance
tool_service = ToolService()
