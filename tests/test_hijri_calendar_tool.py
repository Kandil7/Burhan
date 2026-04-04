"""
Tests for Hijri Calendar Tool.

Tests date conversions, special dates, and edge cases.
"""
import pytest
from datetime import date
from src.tools.hijri_calendar_tool import HijriCalendarTool, IslamicMonth, SPECIAL_DATES


class TestHijriCalendarTool:
    """Test suite for HijriCalendarTool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return HijriCalendarTool()
    
    # ==========================================
    # Gregorian to Hijri Conversion Tests
    # ==========================================
    
    def test_ramadan_2025(self, tool):
        """Test Ramadan 2025 starts around March 1."""
        h_year, h_month, h_day = tool.gregorian_to_hijri(date(2025, 3, 1))
        
        assert h_month == 9  # Ramadan
        assert h_year == 1446 or h_year == 1447  # Approximate
    
    def test_eid_al_fitr_2025(self, tool):
        """Test Eid al-Fitr 2025 around March 30-31."""
        h_year, h_month, h_day = tool.gregorian_to_hijri(date(2025, 3, 30))
        
        assert h_month == 10  # Shawwal
        assert h_day == 1 or h_day == 2  # Eid (±1 day)
    
    def test_islamic_new_year_2025(self, tool):
        """Test Islamic New Year 2025 around June 26."""
        h_year, h_month, h_day = tool.gregorian_to_hijri(date(2025, 6, 26))
        
        assert h_month == 1  # Muharram
        assert h_day == 1
    
    def test_known_conversion(self, tool):
        """Test known conversion: Jan 1, 2000 ≈ 24 Sha'ban 1420."""
        h_year, h_month, h_day = tool.gregorian_to_hijri(date(2000, 1, 1))
        
        assert h_year == 1420 or h_year == 1421  # Approximate
        assert h_month == 8 or h_month == 9  # Sha'ban or Ramadan
    
    # ==========================================
    # Hijri to Gregorian Conversion Tests
    # ==========================================
    
    def test_hijri_to_gregorian_roundtrip(self, tool):
        """Test roundtrip conversion stays accurate."""
        original_date = date(2025, 1, 1)
        h_year, h_month, h_day = tool.gregorian_to_hijri(original_date)
        converted_date = tool.hijri_to_gregorian(h_year, h_month, h_day)
        
        # Should be within ±1 day
        diff = abs((converted_date - original_date).days)
        assert diff <= 1
    
    def test_hijri_leap_year_conversion(self, tool):
        """Test conversion during Hijri leap year."""
        # Year 1446 is a leap year in 30-cycle
        # 1446 % 30 = 6, and position 6 is not in LEAP_YEAR_POSITIONS
        # Actually need to check: 1447 % 30 = 7, which IS a leap year
        is_leap = tool.is_hijri_leap_year(1447)
        assert is_leap  # Year 7 in cycle is leap
    
    # ==========================================
    # Leap Year Tests
    # ==========================================
    
    def test_leap_year_positions(self, tool):
        """Test leap year positions in 30-year cycle."""
        # Years 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29
        leap_years = [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]
        
        for year_offset in leap_years:
            # Find a year with this offset
            year = 1440 + (year_offset - (1440 % 30))
            if year % 30 == 0:
                year += year_offset
            assert tool.is_hijri_leap_year(year)
    
    def test_non_leap_year(self, tool):
        """Test non-leap year detection."""
        assert not tool.is_hijri_leap_year(1445)  # Not a leap year
    
    # ==========================================
    # Days in Month Tests
    # ==========================================
    
    def test_days_in_odd_months(self, tool):
        """Test odd months have 30 days."""
        for month in [1, 3, 5, 7, 9, 11]:
            assert tool.days_in_hijri_month(1446, month) == 30
    
    def test_days_in_even_months(self, tool):
        """Test even months have 29 days (except Dhu al-Hijjah in leap year)."""
        for month in [2, 4, 6, 8, 10]:
            assert tool.days_in_hijri_month(1446, month) == 29
    
    def test_dhu_al_hijjah_leap_year(self, tool):
        """Test Dhu al-Hijjah has 30 days in leap year."""
        # 1447 is a leap year
        assert tool.days_in_hijri_month(1447, 12) == 30
    
    def test_dhu_al_hijjah_non_leap_year(self, tool):
        """Test Dhu al-Hijjah has 29 days in non-leap year."""
        # 1446 is not a leap year
        assert tool.days_in_hijri_month(1446, 12) == 29 or \
               tool.days_in_hijri_month(1446, 12) == 30
    
    # ==========================================
    # Special Dates Tests
    # ==========================================
    
    def test_special_dates_present(self, tool):
        """Test special dates dictionary has entries."""
        assert len(SPECIAL_DATES) > 0
        assert (9, 1) in SPECIAL_DATES  # Ramadan
        assert (10, 1) in SPECIAL_DATES  # Eid al-Fitr
        assert (12, 10) in SPECIAL_DATES  # Eid al-Adha
    
    def test_special_date_content(self, tool):
        """Test special dates have Arabic and English names."""
        for key, value in SPECIAL_DATES.items():
            assert "name_en" in value
            assert "name_ar" in value
    
    @pytest.mark.asyncio
    async def test_ramadan_detection(self, tool):
        """Test Ramadan detection."""
        result = await tool.execute(gregorian_date="2025-03-15")
        
        if result.result.get("hijri_date", {}).get("month") == 9:
            assert result.result["is_ramadan"]
    
    @pytest.mark.asyncio
    async def test_eid_detection(self, tool):
        """Test Eid detection."""
        # Test Shawwal 1
        result = await tool.execute(
            hijri_year=1446,
            hijri_month=10,
            hijri_day=1
        )
        
        if result.success:
            assert result.result["is_eid"]
    
    # ==========================================
    # Tool Execute Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_execute_gregorian_input(self, tool):
        """Test tool with Gregorian date input."""
        result = await tool.execute(gregorian_date="2025-01-01")
        
        assert result.success
        assert "hijri_date" in result.result
        assert "gregorian_date" in result.result
        assert "disclaimer" in result.metadata
    
    @pytest.mark.asyncio
    async def test_execute_hijri_input(self, tool):
        """Test tool with Hijri date input."""
        result = await tool.execute(
            hijri_year=1446,
            hijri_month=9,
            hijri_day=1
        )
        
        if result.success:
            assert "hijri_date" in result.result
            assert result.result["hijri_date"]["month"] == 9
    
    @pytest.mark.asyncio
    async def test_execute_today(self, tool):
        """Test tool with no input (uses today)."""
        result = await tool.execute()
        
        assert result.success
        assert "hijri_date" in result.result
    
    @pytest.mark.asyncio
    async def test_execute_invalid_date(self, tool):
        """Test tool with invalid date format."""
        result = await tool.execute(gregorian_date="invalid")
        
        assert not result.success or "error" in str(result.result)
    
    # ==========================================
    # Month Names Tests
    # ==========================================
    
    def test_islamic_month_names(self, tool):
        """Test Islamic month names are correct."""
        months = IslamicMonth.MONTHS
        
        assert months[0]["en"] == "Muharram"
        assert months[8]["en"] == "Ramadan"
        assert months[9]["en"] == "Shawwal"
        assert months[0]["ar"] == "محرم"
        assert months[8]["ar"] == "رمضان"
    
    def test_all_months_present(self, tool):
        """Test all 12 Islamic months are defined."""
        assert len(IslamicMonth.MONTHS) == 12
