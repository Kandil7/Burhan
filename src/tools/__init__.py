"""
Tools Module for Burhan Islamic QA system.

This module contains all utility tools:
- base: Base tool interface
- dua_retrieval_tool: Duas and supplications retrieval
- hijri_calendar_tool: Hijri calendar conversion
- inheritance_calculator: Islamic inheritance calculation
- prayer_times_tool: Prayer times calculation
- zakat_calculator: Zakat calculation
"""

from src.tools.base import BaseTool, ToolInput, ToolOutput
from src.tools.dua_retrieval_tool import DuaRetrievalTool
from src.tools.hijri_calendar_tool import HijriCalendarTool
from src.tools.inheritance_calculator import InheritanceCalculator
from src.tools.prayer_times_tool import PrayerTimesTool
from src.tools.zakat_calculator import ZakatCalculator

__all__ = [
    # Base
    "BaseTool",
    "ToolInput",
    "ToolOutput",
    # Tools
    "DuaRetrievalTool",
    "HijriCalendarTool",
    "InheritanceCalculator",
    "PrayerTimesTool",
    "ZakatCalculator",
]
