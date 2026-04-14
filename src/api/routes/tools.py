"""
Tool API endpoints for Athar Islamic QA system.

Provides direct access to tools bypassing the intent router.
Useful for frontend forms (Zakat form, Prayer times form, etc.)
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.tools.dua_retrieval_tool import DuaRetrievalTool
from src.tools.hijri_calendar_tool import HijriCalendarTool
from src.tools.inheritance_calculator import Heirs, InheritanceCalculator
from src.tools.prayer_times_tool import PrayerTimesTool
from src.tools.zakat_calculator import Madhhab, ZakatAssets, ZakatCalculator

logger = get_logger()
router = APIRouter(prefix="/tools", tags=["Tools"])

# ==========================================
# Request/Response Models
# ==========================================

class ZakatRequest(BaseModel):
    assets: dict = Field(..., description="Asset values: cash, gold_grams, silver_grams, etc.")
    debts: float = Field(0.0, description="Outstanding debts")
    madhhab: str = Field("general", description="School of jurisprudence")

class InheritanceRequest(BaseModel):
    estate_value: float = Field(..., gt=0, description="Total estate value")
    heirs: dict = Field(..., description="Heirs definition: husband, wife_count, sons, daughters, etc.")
    madhhab: str = Field("general", description="School of jurisprudence")
    debts: float = Field(0.0, description="Debts to deduct")

class PrayerTimesRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    date: str | None = Field(None, description="Date in YYYY-MM-DD format (default: today)")
    method: str = Field("egyptian", description="Calculation method")
    timezone: float = Field(0.0, description="UTC offset in hours")

class HijriRequest(BaseModel):
    gregorian_date: str | None = Field(None, description="Gregorian date YYYY-MM-DD")
    hijri_year: int | None = Field(None, description="Hijri year")
    hijri_month: int | None = Field(None, description="Hijri month (1-12)")
    hijri_day: int | None = Field(None, description="Hijri day (1-30)")

class DuaRequest(BaseModel):
    query: str | None = Field(None, description="Search query")
    occasion: str | None = Field(None, description="Occasion filter")
    category: str | None = Field(None, description="Category filter")
    limit: int = Field(5, ge=1, le=20, description="Max results")


# ==========================================
# Tool Instances
# ==========================================
# Note: In production, these should be initialized once and reused
zakat_tool_cache = None
inheritance_tool_cache = None
prayer_tool_cache = None
hijri_tool_cache = None
dua_tool_cache = None

def get_zakat_calculator() -> ZakatCalculator:
    global zakat_tool_cache
    if zakat_tool_cache is None:
        # Default prices - in production, fetch from API
        zakat_tool_cache = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
    return zakat_tool_cache

def get_inheritance_calculator() -> InheritanceCalculator:
    global inheritance_tool_cache
    if inheritance_tool_cache is None:
        inheritance_tool_cache = InheritanceCalculator()
    return inheritance_tool_cache

def get_prayer_times_tool() -> PrayerTimesTool:
    global prayer_tool_cache
    if prayer_tool_cache is None:
        prayer_tool_cache = PrayerTimesTool()
    return prayer_tool_cache

def get_hijri_calendar_tool() -> HijriCalendarTool:
    global hijri_tool_cache
    if hijri_tool_cache is None:
        hijri_tool_cache = HijriCalendarTool()
    return hijri_tool_cache

def get_dua_retrieval_tool() -> DuaRetrievalTool:
    global dua_tool_cache
    if dua_tool_cache is None:
        dua_tool_cache = DuaRetrievalTool()
    return dua_tool_cache


# ==========================================
# Zakat Endpoint
# ==========================================

@router.post("/zakat")
async def calculate_zakat(request: ZakatRequest):
    """
    Calculate zakat on wealth, gold, silver, and other assets.

    Returns detailed breakdown with nisab calculation and madhhab-specific notes.
    """
    calculator = get_zakat_calculator()

    assets = ZakatAssets(**request.assets)
    madhhab = Madhhab(request.madhhab.lower())

    result = calculator.calculate(assets, debts=request.debts, madhhab=madhhab)

    return {
        "nisab": {
            "gold": result.nisab_gold,
            "silver": result.nisab_silver,
            "effective": result.nisab_effective
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
        "references": result.references
    }


# ==========================================
# Inheritance Endpoint
# ==========================================

@router.post("/inheritance")
async def calculate_inheritance(request: InheritanceRequest):
    """
    Calculate inheritance distribution based on fara'id rules.

    Returns detailed distribution with fractions, percentages, and amounts.
    """
    calculator = get_inheritance_calculator()

    heirs = Heirs(**request.heirs)

    result = calculator.calculate(
        request.estate_value,
        heirs,
        madhhab=request.madhhab,
        debts=request.debts
    )

    return {
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
        "references": result.references
    }


# ==========================================
# Prayer Times Endpoint
# ==========================================

@router.post("/prayer-times")
async def get_prayer_times(request: PrayerTimesRequest):
    """
    Calculate prayer times and Qibla direction for a location.

    Supports multiple calculation methods (Egyptian, MWL, ISNA, etc.)
    """
    tool = get_prayer_times_tool()

    result = await tool.execute(
        lat=request.lat,
        lng=request.lng,
        date_str=request.date,
        method=request.method,
        timezone=request.timezone
    )

    if result.success:
        return result.result
    else:
        return {"error": result.error}


# ==========================================
# Hijri Calendar Endpoint
# ==========================================

@router.post("/hijri")
async def convert_hijri(request: HijriRequest):
    """
    Convert between Gregorian and Hijri dates.

    Detects special Islamic dates (Ramadan, Eid, etc.)
    """
    tool = get_hijri_calendar_tool()

    result = await tool.execute(
        gregorian_date=request.gregorian_date,
        hijri_year=request.hijri_year,
        hijri_month=request.hijri_month,
        hijri_day=request.hijri_day
    )

    if result.success:
        return result.result
    else:
        return {"error": result.error}


# ==========================================
# Duas Endpoint
# ==========================================

@router.post("/duas")
async def get_duas(request: DuaRequest):
    """
    Retrieve verified duas and adhkar.

    Searches by occasion, category, or query.
    All duas from authenticated sources only.
    """
    tool = get_dua_retrieval_tool()

    result = await tool.execute(
        query=request.query,
        occasion=request.occasion,
        category=request.category,
        limit=request.limit
    )

    if result.success:
        return result.result
    else:
        return {"error": result.error}
