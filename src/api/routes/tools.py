"""
Tools endpoint for Athar Islamic QA system.

Provides deterministic tools (zakat, inheritance, prayer times, etc.).
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException

from src.api.schemas.tools import (
    DuaRequest,
    HijriRequest,
    InheritanceRequest,
    PrayerTimesRequest,
    ZakatRequest,
)
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.tools.dua_retrieval_tool import DuaRetrievalTool
from src.tools.hijri_calendar_tool import HijriCalendarTool
from src.tools.inheritance_calculator import Heirs, InheritanceCalculator
from src.tools.prayer_times_tool import PrayerTimesTool
from src.tools.zakat_calculator import Madhhab, ZakatAssets, ZakatCalculator

logger = get_logger()
tools_router = APIRouter(prefix="/tools", tags=["Tools"])


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ==========================================
# Tool Instances
# ==========================================

_zakat_tool_cache: ZakatCalculator | None = None
_inheritance_tool_cache: InheritanceCalculator | None = None
_prayer_tool_cache: PrayerTimesTool | None = None
_hijri_tool_cache: HijriCalendarTool | None = None
_dua_tool_cache: DuaRetrievalTool | None = None


def _get_zakat_calculator() -> ZakatCalculator:
    global _zakat_tool_cache
    if _zakat_tool_cache is None:
        _zakat_tool_cache = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
    return _zakat_tool_cache


def _get_inheritance_calculator() -> InheritanceCalculator:
    global _inheritance_tool_cache
    if _inheritance_tool_cache is None:
        _inheritance_tool_cache = InheritanceCalculator()
    return _inheritance_tool_cache


def _get_prayer_times_tool() -> PrayerTimesTool:
    global _prayer_tool_cache
    if _prayer_tool_cache is None:
        _prayer_tool_cache = PrayerTimesTool()
    return _prayer_tool_cache


def _get_hijri_calendar_tool() -> HijriCalendarTool:
    global _hijri_tool_cache
    if _hijri_tool_cache is None:
        _hijri_tool_cache = HijriCalendarTool()
    return _hijri_tool_cache


def _get_dua_retrieval_tool() -> DuaRetrievalTool:
    global _dua_tool_cache
    if _dua_tool_cache is None:
        _dua_tool_cache = DuaRetrievalTool()
    return _dua_tool_cache


# ==========================================
# Zakat Endpoint
# ==========================================


@tools_router.post(
    "/zakat",
    summary="Calculate Zakat",
    responses={500: {"model": ErrorResponse, "description": "Calculation error"}},
)
async def calculate_zakat(request: ZakatRequest):
    """
    Calculate Zakat on wealth, gold, silver, and other assets.

    Returns detailed breakdown with nisab calculation and madhhab-specific notes.
    """
    trace_id = _build_trace_id()
    start_time = time.time()

    try:
        calculator = _get_zakat_calculator()
        assets = ZakatAssets(**request.assets)
        madhhab = Madhhab(request.madhhab.lower())

        result = calculator.calculate(assets, debts=request.debts, madhhab=madhhab)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "trace_id": trace_id,
            "processing_time_ms": processing_time_ms,
            "nisab": {
                "gold": result.nisab_gold,
                "silver": result.nisab_silver,
                "effective": result.nisab_effective,
            },
            "total_assets": result.total_assets,
            "debts_deducted": result.debts_deducted,
            "zakatable_wealth": result.zakatable_wealth,
            "is_zakatable": result.is_zakatable,
            "zakat_amount": result.zakat_amount,
            "breakdown": {
                "cash": result.breakdown.cash,
                "gold_value": result.breakdown.gold_value,
                "silver_value": result.breakdown.silver_value,
                "trade_goods": result.breakdown.trade_goods,
                "stocks": result.breakdown.stocks,
            },
            "madhhab": result.madhhab,
            "notes": result.notes,
            "references": result.references,
        }

    except Exception as e:
        logger.error("tools.zakat_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# Inheritance Endpoint
# ==========================================


@tools_router.post(
    "/inheritance",
    summary="Calculate Inheritance",
    responses={500: {"model": ErrorResponse, "description": "Calculation error"}},
)
async def calculate_inheritance(request: InheritanceRequest):
    """
    Calculate inheritance distribution based on fara'id rules.

    Returns detailed distribution with fractions, percentages, and amounts.
    """
    trace_id = _build_trace_id()
    start_time = time.time()

    try:
        calculator = _get_inheritance_calculator()
        heirs = Heirs(**request.heirs)

        result = calculator.calculate(
            request.estate_value,
            heirs,
            madhhab=request.madhhab,
            debts=request.debts,
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "trace_id": trace_id,
            "processing_time_ms": processing_time_ms,
            "distribution": [
                {
                    "heir": share.heir_name,
                    "fraction": str(share.fraction),
                    "percentage": share.percentage,
                    "amount": share.amount,
                    "basis": share.basis,
                }
                for share in result.distribution
            ],
            "total_distributed": result.total_distributed,
            "remaining": result.remaining,
            "method": result.method,
            "school_opinion": result.school_opinion,
            "estate_value": result.estate_value,
            "total_heirs": result.total_heirs,
            "notes": result.notes,
            "references": result.references,
        }

    except Exception as e:
        logger.error("tools.inheritance_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# Prayer Times Endpoint
# ==========================================


@tools_router.post(
    "/prayer-times",
    summary="Get Prayer Times",
    responses={500: {"model": ErrorResponse, "description": "Calculation error"}},
)
async def get_prayer_times(request: PrayerTimesRequest):
    """
    Calculate prayer times and Qibla direction for a location.

    Supports multiple calculation methods (Egyptian, MWL, ISNA, etc.)
    """
    trace_id = _build_trace_id()
    start_time = time.time()

    try:
        tool = _get_prayer_times_tool()
        result = await tool.execute(
            lat=request.lat,
            lng=request.lng,
            date_str=request.date,
            method=request.method,
            timezone=request.timezone,
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        if result.success:
            return {
                "trace_id": trace_id,
                "processing_time_ms": processing_time_ms,
                **result.result,
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("tools.prayer_times_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# Hijri Calendar Endpoint
# ==========================================


@tools_router.post(
    "/hijri",
    summary="Convert Hijri Dates",
    responses={500: {"model": ErrorResponse, "description": "Conversion error"}},
)
async def convert_hijri(request: HijriRequest):
    """
    Convert between Gregorian and Hijri dates.

    Detects special Islamic dates (Ramadan, Eid, etc.)
    """
    trace_id = _build_trace_id()
    start_time = time.time()

    try:
        tool = _get_hijri_calendar_tool()
        result = await tool.execute(
            gregorian_date=request.gregorian_date,
            hijri_year=request.hijri_year,
            hijri_month=request.hijri_month,
            hijri_day=request.hijri_day,
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        if result.success:
            return {
                "trace_id": trace_id,
                "processing_time_ms": processing_time_ms,
                **result.result,
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("tools.hijri_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# Duas Endpoint
# ==========================================


@tools_router.post(
    "/duas",
    summary="Retrieve Duas",
    responses={500: {"model": ErrorResponse, "description": "Retrieval error"}},
)
async def get_duas(request: DuaRequest):
    """
    Retrieve verified duas and adhkar.

    Searches by occasion, category, or query.
    All duas from authenticated sources only.
    """
    trace_id = _build_trace_id()
    start_time = time.time()

    try:
        tool = _get_dua_retrieval_tool()
        result = await tool.execute(
            query=request.query,
            occasion=request.occasion,
            category=request.category,
            limit=request.limit,
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        if result.success:
            return {
                "trace_id": trace_id,
                "processing_time_ms": processing_time_ms,
                **result.result,
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("tools.duas_error", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
