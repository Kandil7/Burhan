"""
Tests for Prayer Times Tool.

Tests astronomical calculations and Qibla direction.
"""
import pytest
from datetime import date
from src.tools.prayer_times_tool import PrayerTimesTool, PrayerMethod


class TestPrayerTimesTool:
    """Test suite for PrayerTimesTool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return PrayerTimesTool()
    
    # ==========================================
    # Qibla Direction Tests
    # ==========================================
    
    def test_qibla_from_cairo(self, tool):
        """Test Qibla direction from Cairo (should be ~135°)."""
        qibla = tool._calculate_qibla(30.0444, 31.2357)
        # Cairo to Mecca is roughly southeast
        assert 130 < qibla < 150
    
    def test_qibla_from_doha(self, tool):
        """Test Qibla direction from Doha (should be ~225°)."""
        qibla = tool._calculate_qibla(25.2854, 51.5310)
        # Doha to Mecca is roughly southwest
        assert 200 < qibla < 250
    
    def test_qibla_from_new_york(self, tool):
        """Test Qibla direction from New York (should be ~58°)."""
        qibla = tool._calculate_qibla(40.7128, -74.0060)
        # New York to Mecca is roughly northeast
        assert 40 < qibla < 80
    
    def test_qibla_from_mecca(self, tool):
        """Test Qibla from Mecca itself (should be 0° or undefined)."""
        qibla = tool._calculate_qibla(21.4225, 39.8262)
        # At Mecca, direction is undefined (or 0)
        assert 0 <= qibla <= 360
    
    # ==========================================
    # Astronomical Calculation Tests
    # ==========================================
    
    def test_julian_date(self, tool):
        """Test Julian date calculation."""
        jd = tool._julian_date(2000, 1, 1)
        # J2000.0 epoch
        assert abs(jd - 2451544.5) < 1
    
    def test_julian_date_known(self, tool):
        """Test Julian date for known date."""
        jd = tool._julian_date(2025, 1, 1)
        assert jd > 2451544.5  # After J2000.0
    
    def test_sun_declination_range(self, tool):
        """Test sun declination is within valid range."""
        jd = tool._julian_date(2025, 6, 21)  # Summer solstice
        dec = tool._sun_declination(jd)
        assert -23.5 <= dec <= 23.5
    
    def test_equation_of_time_range(self, tool):
        """Test equation of time is within valid range."""
        jd = tool._julian_date(2025, 1, 1)
        eot = tool._equation_of_time(jd)
        assert -0.5 <= eot <= 0.5  # Within ±30 minutes
    
    # ==========================================
    # Prayer Times Tests
    # ==========================================
    
    def test_prayer_times_doha(self, tool):
        """Test prayer times for Doha, Qatar."""
        times = tool._calculate_prayer_times(
            lat=25.2854,
            lng=51.5310,
            calc_date=date(2025, 1, 1),
            method=PrayerMethod.EGYPTIAN,
            timezone=3.0
        )
        
        # Verify structure
        assert "fajr" in times
        assert "sunrise" in times
        assert "dhuhr" in times
        assert "asr" in times
        assert "maghrib" in times
        assert "isha" in times
        
        # Verify format (HH:MM)
        for time_str in times.values():
            assert ":" in time_str
            hours, minutes = time_str.split(":")
            assert 0 <= int(hours) < 24
            assert 0 <= int(minutes) < 60
    
    def test_prayer_times_order(self, tool):
        """Test prayer times are in correct order."""
        times = tool._calculate_prayer_times(
            lat=25.2854,
            lng=51.5310,
            calc_date=date(2025, 1, 1),
            method=PrayerMethod.EGYPTIAN,
            timezone=3.0
        )
        
        # Convert to minutes for comparison
        def to_minutes(time_str):
            h, m = time_str.split(":")
            return int(h) * 60 + int(m)
        
        fajr = to_minutes(times["fajr"])
        sunrise = to_minutes(times["sunrise"])
        dhuhr = to_minutes(times["dhuhr"])
        asr = to_minutes(times["asr"])
        maghrib = to_minutes(times["maghrib"])
        isha = to_minutes(times["isha"])
        
        assert fajr < sunrise < dhuhr < asr < maghrib < isha or isha < fajr
    
    def test_different_methods(self, tool):
        """Test different calculation methods produce different times."""
        times_egyptian = tool._calculate_prayer_times(
            lat=25.2854, lng=51.5310,
            calc_date=date(2025, 1, 1),
            method=PrayerMethod.EGYPTIAN,
            timezone=3.0
        )
        
        times_isna = tool._calculate_prayer_times(
            lat=25.2854, lng=51.5310,
            calc_date=date(2025, 1, 1),
            method=PrayerMethod.ISNA,
            timezone=3.0
        )
        
        # ISNA has lower fajr angle, so fajr should be later
        assert times_egyptian["fajr"] != times_isna["fajr"]
    
    def test_umm_al_qura_isha(self, tool):
        """Test Umm al-Qura isha is 90 min after maghrib."""
        times = tool._calculate_prayer_times(
            lat=21.4225, lng=39.8262,
            calc_date=date(2025, 1, 1),
            method=PrayerMethod.UMM_AL_QURA,
            timezone=3.0
        )
        
        def to_minutes(time_str):
            h, m = time_str.split(":")
            return int(h) * 60 + int(m)
        
        maghrib_min = to_minutes(times["maghrib"])
        isha_min = to_minutes(times["isha"])
        
        # Isha should be ~90 minutes after maghrib
        diff = (isha_min - maghrib_min) % (24 * 60)
        assert 85 <= diff <= 95  # Within ±5 minutes
    
    # ==========================================
    # Tool Execute Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_execute_valid_location(self, tool):
        """Test tool execution with valid location."""
        result = await tool.execute(
            lat=25.2854,
            lng=51.5310,
            date_str="2025-01-01",
            method="egyptian"
        )
        
        assert result.success
        assert "times" in result.result
        assert "qibla_direction" in result.result
    
    @pytest.mark.asyncio
    async def test_execute_invalid_lat(self, tool):
        """Test tool execution with invalid latitude."""
        result = await tool.execute(lat=100, lng=51.5310)
        
        assert not result.success
        assert "error" in result.result or result.error
    
    @pytest.mark.asyncio
    async def test_execute_today(self, tool):
        """Test tool execution without date (uses today)."""
        result = await tool.execute(lat=25.2854, lng=51.5310)
        
        assert result.success
        assert "date" in result.result
    
    # ==========================================
    # Format Tests
    # ==========================================
    
    def test_format_time(self, tool):
        """Test time formatting."""
        assert tool._format_time(5.5) == "05:30"
        assert tool._format_time(12.0) == "12:00"
        assert tool._format_time(23.75) == "23:45"
    
    def test_format_time_normalization(self, tool):
        """Test time wraps at 24 hours."""
        assert tool._format_time(25.0) == "01:00"
        assert tool._format_time(-1.0) == "23:00"
    
    def test_method_description(self, tool):
        """Test method descriptions are present."""
        desc = tool._get_method_description(PrayerMethod.EGYPTIAN)
        assert "Egyptian" in desc
        assert "19.5" in desc
