"""
Input validation models for Athar Islamic QA System tools.

These Pydantic models ensure all tool inputs are validated before processing.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


# ==========================================
# Zakat Validation Models
# ==========================================


class ZakatAssetsInput(BaseModel):
    """Validated input for Zakat assets."""

    cash: float = Field(ge=0, le=1e12, description="Cash on hand")
    bank_accounts: float = Field(ge=0, le=1e12, description="Bank account balance")
    gold_grams: float = Field(ge=0, le=1e9, description="Gold weight in grams")
    silver_grams: float = Field(ge=0, le=1e9, description="Silver weight in grams")
    trade_goods_value: float = Field(ge=0, le=1e12, description="Trade goods value")
    stocks_value: float = Field(ge=0, le=1e12, description="Stock portfolio value")
    receivables: float = Field(ge=0, le=1e12, description="Money owed to user")
    livestock_value: float = Field(ge=0, le=1e12, description="Livestock value")
    crops_value: float = Field(ge=0, le=1e12, description="Agricultural products value")
    minerals_value: float = Field(ge=0, le=1e12, description="Minerals/treasures value")

    @field_validator("*")
    @classmethod
    def validate_positive(cls, v, info):
        """Ensure all values are non-negative."""
        if v < 0:
            raise ValueError(f"{info.field_name} cannot be negative")
        return v

    @property
    def total_wealth(self) -> float:
        """Calculate total wealth."""
        return (
            self.cash
            + self.bank_accounts
            + self.gold_grams * 75  # Approximate - should use current price
            + self.silver_grams * 0.9
            + self.trade_goods_value
            + self.stocks_value
            + self.receivables
            + self.livestock_value
            + self.crops_value
            + self.minerals_value
        )


class ZakatCalculationInput(BaseModel):
    """Validated input for Zakat calculation."""

    assets: ZakatAssetsInput
    debts: float = Field(ge=0, le=1e12, description="Outstanding debts to deduct")
    madhhab: str = Field(default="general", description="Islamic school of jurisprudence")
    crop_irrigation_type: str = Field(default="irrigated")

    @field_validator("debts")
    @classmethod
    def validate_debts(cls, v, info):
        """Validate debts are reasonable."""
        if v < 0:
            raise ValueError("Debts cannot be negative")
        return v

    @field_validator("madhhab")
    @classmethod
    def validate_madhhab(cls, v):
        """Validate madhhab is recognized."""
        valid_madhahib = ["hanafi", "maliki", "shafii", "hanbali", "general"]
        if v.lower() not in valid_madhahib:
            raise ValueError(f"Invalid madhhab. Must be one of: {valid_madhahib}")
        return v.lower()

    @field_validator("crop_irrigation_type")
    @classmethod
    def validate_irrigation(cls, v):
        """Validate irrigation type."""
        valid_types = ["irrigated", "natural"]
        if v.lower() not in valid_types:
            raise ValueError(f"Irrigation type must be 'irrigated' or 'natural'")
        return v.lower()


# ==========================================
# Inheritance Validation Models
# ==========================================


class HeirsInput(BaseModel):
    """Validated input for heirs definition."""

    # Spouse
    husband: bool = Field(default=False, description="Husband surviving")
    wife_count: int = Field(ge=0, le=4, description="Number of wives")

    # Parents
    father: bool = Field(default=False, description="Father surviving")
    mother: bool = Field(default=False, description="Mother surviving")

    # Grandparents
    paternal_grandfather: bool = Field(default=False)

    # Descendants
    sons: int = Field(ge=0, le=100, description="Number of sons")
    daughters: int = Field(ge=0, le=100, description="Number of daughters")
    grandsons: int = Field(ge=0, le=100, description="Number of grandsons")

    # Siblings
    full_brothers: int = Field(ge=0, le=100)
    full_sisters: int = Field(ge=0, le=100)
    paternal_half_brothers: int = Field(ge=0, le=100)
    paternal_half_sisters: int = Field(ge=0, le=100)
    maternal_brothers: int = Field(ge=0, le=100)
    maternal_sisters: int = Field(ge=0, le=100)

    # Others
    uterine_brothers: int = Field(ge=0, le=100)
    uterine_sisters: int = Field(ge=0, le=100)

    @field_validator("wife_count")
    @classmethod
    def validate_wife_count(cls, v):
        """Validate wife count."""
        if v > 4:
            raise ValueError("Maximum 4 wives allowed in Islam")
        return v

    @field_validator("*")
    @classmethod
    def validate_non_negative(cls, v, info):
        """Ensure all counts are non-negative."""
        if isinstance(v, int) and v < 0:
            raise ValueError(f"{info.field_name} cannot be negative")
        return v

    def has_any_heir(self) -> bool:
        """Check if any heir is defined."""
        return (
            self.husband
            or self.wife_count > 0
            or self.father
            or self.mother
            or self.paternal_grandfather
            or self.sons > 0
            or self.daughters > 0
            or self.grandsons > 0
            or self.full_brothers > 0
            or self.full_sisters > 0
            or self.paternal_half_brothers > 0
            or self.paternal_half_sisters > 0
            or self.maternal_brothers > 0
            or self.maternal_sisters > 0
            or self.uterine_brothers > 0
            or self.uterine_sisters > 0
        )


class InheritanceCalculationInput(BaseModel):
    """Validated input for inheritance calculation."""

    estate_value: float = Field(gt=0, le=1e12, description="Total estate value")
    heirs: HeirsInput
    madhhab: str = Field(default="general")
    debts: float = Field(ge=0, le=1e12, description="Debts to deduct")
    wasiyyah: float = Field(ge=0, le=1e12, description="Bequest amount")

    @field_validator("estate_value")
    @classmethod
    def validate_estate(cls, v):
        """Validate estate value."""
        if v <= 0:
            raise ValueError("Estate value must be positive")
        return v

    @field_validator("wasiyyah")
    @classmethod
    def validate_wasiyyah(cls, v, info):
        """Validate wasiyyah doesn't exceed 1/3 of estate."""
        data = info.data
        if "estate_value" in data and v > data["estate_value"] / 3:
            raise ValueError("Wasiyyah cannot exceed 1/3 of estate")
        return v

    @field_validator("madhhab")
    @classmethod
    def validate_madhhab(cls, v):
        """Validate madhhab."""
        valid_madhahib = ["hanafi", "maliki", "shafii", "hanbali", "general"]
        if v.lower() not in valid_madhahib:
            raise ValueError(f"Invalid madhhab: {v}")
        return v.lower()


# ==========================================
# Prayer Times Validation Models
# ==========================================


class LocationInput(BaseModel):
    """Validated input for location."""

    latitude: float = Field(ge=-90, le=90, description="Latitude")
    longitude: float = Field(ge=-180, le=180, description="Longitude")
    city: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range."""
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range."""
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class PrayerTimesInput(BaseModel):
    """Validated input for prayer times calculation."""

    location: LocationInput
    date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    method: str = Field(default="MWL")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v):
        """Validate prayer calculation method."""
        valid_methods = ["MWL", "ISNA", "Egypt", "Makkah", "Karachi", "Tehran"]
        if v.upper() not in valid_methods:
            raise ValueError(f"Invalid method. Must be one of: {valid_methods}")
        return v.upper()

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Validate date format."""
        from datetime import datetime

        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


# ==========================================
# Hijri Calendar Validation Models
# ==========================================


class HijriDateInput(BaseModel):
    """Validated input for Hijri date conversion."""

    gregorian_date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    hijri_year: Optional[int] = Field(default=None, ge=1, le=1500)
    hijri_month: Optional[int] = Field(default=None, ge=1, le=12)
    hijri_day: Optional[int] = Field(default=None, ge=1, le=30)

    @field_validator("gregorian_date")
    @classmethod
    def validate_gregorian_date(cls, v):
        """Validate Gregorian date format."""
        from datetime import datetime

        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    def has_valid_input(self) -> bool:
        """Check if at least one input is provided."""
        return bool(self.gregorian_date or (self.hijri_year and self.hijri_month and self.hijri_day))


# ==========================================
# Query Validation Models
# ==========================================


class QueryInput(BaseModel):
    """Validated input for general queries."""

    query: str = Field(min_length=1, max_length=1000)
    language: str = Field(default="ar")
    madhhab: Optional[str] = Field(default=None, max_length=20)
    session_id: Optional[str] = Field(default=None, max_length=100)
    location: Optional[LocationInput] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate query content."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        if len(v) < 2:
            raise ValueError("Query too short")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        """Validate language."""
        valid_languages = ["ar", "en", "both"]
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be 'ar', 'en', or 'both'")
        return v.lower()

    @field_validator("madhhab")
    @classmethod
    def validate_madhhab(cls, v):
        """Validate madhhab."""
        if v:
            valid_madhahib = ["hanafi", "maliki", "shafii", "hanbali"]
            if v.lower() not in valid_madhahib:
                raise ValueError(f"Invalid madhhab: {v}")
            return v.lower()
        return v


# ==========================================
# Tool Execution Input
# ==========================================


class ToolExecutionInput(BaseModel):
    """Generic input for tool execution."""

    tool_name: str = Field(min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v):
        """Validate tool name."""
        # Allow alphanumeric and underscore
        import re

        if not re.match(r"^[a-z_][a-z0-9_]*$", v):
            raise ValueError("Invalid tool name format")
        return v


# ==========================================
# Response Models with Validation
# ==========================================


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class SearchParams(BaseModel):
    """Search parameters."""

    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    filters: Optional[dict] = None
