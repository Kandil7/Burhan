"""
Base Tool abstraction for Athar Islamic QA system.

All tools (Zakat, Inheritance, Prayer Times, Hijri, Dua) inherit from BaseTool
and implement the execute() method with standardized input/output.

Tools are deterministic and don't require document retrieval.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """
    Standardized input for all tools.
    
    Tools receive query text plus optional parameters
    depending on their specific requirements.
    """
    query: str = Field(description="User's question")
    metadata: dict = Field(
        default_factory=dict,
        description="Tool-specific parameters (location, assets, heirs, etc.)"
    )


class ToolOutput(BaseModel):
    """
    Standardized output for all tools.
    
    Contains result data that will be formatted by the agent/orchestrator.
    """
    result: dict[str, Any] = Field(description="Tool calculation result")
    success: bool = Field(default=True, description="Whether tool execution succeeded")
    error: str = Field(default="", description="Error message if failed")
    metadata: dict = Field(
        default_factory=dict,
        description="Tool-specific metadata (calculation method, assumptions)"
    )


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools are deterministic utilities that perform specific calculations
    or retrieve fixed data. Examples: ZakatCalculator, InheritanceCalculator,
    PrayerTimesTool, HijriCalendarTool, DuaRetrievalTool.
    
    Unlike agents, tools:
    - Don't use LLMs for generation
    - Are deterministic (same input → same output)
    - Don't require document retrieval
    - Return structured data
    
    Usage:
        class ZakatCalculator(BaseTool):
            name = "zakat_tool"
            
            async def execute(self, **kwargs) -> ToolOutput:
                assets = kwargs.get("assets", {})
                debts = kwargs.get("debts", 0)
                # Calculate zakat...
                return ToolOutput(result={"zakat_amount": 1000.0})
        
        tool = ZakatCalculator()
        result = await tool.execute(assets={"cash": 50000}, debts=5000)
    """
    
    name: str = "base_tool"
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute tool logic and return result.
        
        Args:
            **kwargs: Tool-specific parameters from metadata
            
        Returns:
            ToolOutput with result data
        """
        pass
    
    async def __call__(self, **kwargs) -> ToolOutput:
        """Allow tool to be called directly like a function."""
        return await self.execute(**kwargs)
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
