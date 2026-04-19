"""
Schemas for /tools endpoints.

Request/response models for tool-based operations (zakat, inheritance, prayer times, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Zakat Calculator
# ============================================================================


class ZakatRequest(BaseModel):
    """Request model for Zakat calculation."""

    assets: dict = Field(
        ...,
        description="Asset values: cash, gold_grams, silver_grams, etc.",
        examples=[
            {
                "cash": 10000,
                "gold_grams": 50,
                "silver_grams": 500,
                "trade_goods": 5000,
                "stocks": 20000,
            }
        ],
    )
    debts: float = Field(
        default=0.0,
        ge=0,
        description="Outstanding debts to deduct",
    )
    madhhab: str = Field(
        default="general",
        pattern="^(hanafi|maliki|shafii|hanbali|general)$",
        description="School of jurisprudence",
    )


class ZakatResponse(BaseModel):
    """Response model for Zakat calculation."""

    nisab: dict = Field(..., description="Nisab thresholds")
    total_assets: float = Field(..., description="Total asset value")
    debts_deducted: float = Field(..., description="Total debts deducted")
    zakatable_wealth: float = Field(..., description="Wealth subject to Zakat")
    is_zakatable: bool = Field(..., description="Whether Zakat is due")
    zakat_amount: float = Field(..., description="Calculated Zakat amount")
    breakdown: dict = Field(..., description="Asset breakdown")
    madhhab: str = Field(..., description="Madhhab used for calculation")
    notes: list[str] = Field(
        default_factory=list,
        description="Additional notes",
    )
    references: list[str] = Field(
        default_factory=list,
        description="Religious references",
    )


# ============================================================================
# Inheritance Calculator
# ============================================================================


class InheritanceRequest(BaseModel):
    """Request model for inheritance calculation."""

    estate_value: float = Field(
        ...,
        gt=0,
        description="Total estate value",
        examples=[100000],
    )
    heirs: dict = Field(
        ...,
        description="Heirs definition: husband, wife_count, sons, daughters, etc.",
        examples=[
            {
                "husband": 1,
                "wife_count": 1,
                "sons": 2,
                "daughters": 1,
            }
        ],
    )
    madhhab: str = Field(
        default="general",
        pattern="^(hanafi|maliki|shafii|hanbali|general)$",
        description="School of jurisprudence",
    )
    debts: float = Field(
        default=0.0,
        ge=0,
        description="Debts to deduct from estate",
    )


class InheritanceShare(BaseModel):
    """Individual heir's inheritance share."""

    heir: str = Field(..., description="Heir name")
    fraction: str = Field(..., description="Fraction share")
    percentage: float = Field(..., description="Percentage of estate")
    amount: float = Field(..., description="Monetary amount")
    basis: str = Field(..., description="Religious basis for share")


class InheritanceResponse(BaseModel):
    """Response model for inheritance calculation."""

    distribution: list[InheritanceShare] = Field(
        ...,
        description="Distribution of inheritance",
    )
    total_distributed: float = Field(..., description="Total amount distributed")
    remaining: float = Field(..., description="Remaining undistributed amount")
    method: str = Field(..., description="Calculation method used")
    school_opinion: str = Field(..., description="School of jurisprudence opinion")
    estate_value: float = Field(..., description="Original estate value")
    total_heirs: int = Field(..., ge=0, description="Total number of heirs")
    notes: list[str] = Field(
        default_factory=list,
        description="Additional notes",
    )
    references: list[str] = Field(
        default_factory=list,
        description="Religious references",
    )


# ============================================================================
# Prayer Times
# ============================================================================


class PrayerTimesRequest(BaseModel):
    """Request model for prayer times."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude", examples=[25.2854])
    lng: float = Field(..., ge=-180, le=180, description="Longitude", examples=[51.5310])
    date: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date in YYYY-MM-DD format (default: today)",
    )
    method: str = Field(
        default="egyptian",
        description="Calculation method",
        examples=["egyptian", "mwl", "isna", "karachi"],
    )
    timezone: float = Field(
        default=0.0,
        description="UTC offset in hours",
        examples=[3.0],
    )


class PrayerTimesResponse(BaseModel):
    """Response model for prayer times."""

    date: str = Field(..., description="Prayer times date")
    times: dict = Field(..., description="Prayer times (fajr, sunrise, dhuhr, asr, maghrib, isha)")
    qibla_direction: float = Field(..., description="Qibla direction in degrees")
    location: dict = Field(..., description="Location used")


# ============================================================================
# Hijri Calendar
# ============================================================================


class HijriRequest(BaseModel):
    """Request model for Hijri calendar conversion."""

    gregorian_date: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Gregorian date YYYY-MM-DD",
    )
    hijri_year: int | None = Field(
        None,
        ge=1,
        description="Hijri year",
    )
    hijri_month: int | None = Field(
        None,
        ge=1,
        le=12,
        description="Hijri month (1-12)",
    )
    hijri_day: int | None = Field(
        None,
        ge=1,
        le=30,
        description="Hijri day (1-30)",
    )


class HijriResponse(BaseModel):
    """Response model for Hijri conversion."""

    gregorian: dict = Field(..., description="Gregorian date")
    hijri: dict = Field(..., description="Hijri date")
    special_days: list[str] = Field(
        default_factory=list,
        description="Special Islamic days",
    )


# ============================================================================
# Duas Retrieval
# ============================================================================


class DuaRequest(BaseModel):
    """Request model for duas retrieval."""

    query: str | None = Field(
        None,
        description="Search query for duas",
    )
    occasion: str | None = Field(
        None,
        description="Occasion filter",
        examples=["morning", "evening", "sleep", "travel"],
    )
    category: str | None = Field(
        None,
        description="Category filter",
        examples=["adhkar", "supplications", "forgiveness"],
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max results to return",
    )


class DuaResponse(BaseModel):
    """Response model for duas retrieval."""

    duas: list[dict] = Field(
        ...,
        description="Retrieved duas",
    )
    count: int = Field(..., description="Number of duas returned")
    metadata: dict = Field(
        default_factory=dict,
        description="Response metadata",
    )
