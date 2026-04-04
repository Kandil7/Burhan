"""
Hijri Calendar Tool for Athar Islamic QA system.

Converts between Gregorian and Hijri dates using the Umm al-Qura calendar algorithm.
Detects special Islamic dates (Ramadan, Eid, Arafah, etc.).

Based on Fanar-Sadiq architecture: Deterministic calculations with moon sighting disclaimer.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional

from src.tools.base import BaseTool, ToolOutput
from src.config.logging_config import get_logger

logger = get_logger()


class IslamicMonth:
    """Islamic month names in Arabic and English."""
    MUHARRAM = {"en": "Muharram", "ar": "محرم", "number": 1}
    SAFAR = {"en": "Safar", "ar": "صفر", "number": 2}
    RABI_AL_AWWAL = {"en": "Rabi' al-Awwal", "ar": "ربيع الأول", "number": 3}
    RABI_AL_THANI = {"en": "Rabi' al-Thani", "ar": "ربيع الثاني", "number": 4}
    JUMADA_AL_ULA = {"en": "Jumada al-Ula", "ar": "جمادى الأولى", "number": 5}
    JUMADA_AL_THANI = {"en": "Jumada al-Thani", "ar": "جمادى الآخرة", "number": 6}
    RAJAB = {"en": "Rajab", "ar": "رجب", "number": 7}
    SHA'BAN = {"en": "Sha'ban", "ar": "شعبان", "number": 8}
    RAMADAN = {"en": "Ramadan", "ar": "رمضان", "number": 9}
    SHAWWAL = {"en": "Shawwal", "ar": "شوال", "number": 10}
    DHU_AL_QA'DAH = {"en": "Dhu al-Qa'dah", "ar": "ذو القعدة", "number": 11}
    DHU_AL_HIJJAH = {"en": "Dhu al-Hijjah", "ar": "ذو الحجة", "number": 12}

    MONTHS = [
        MUHARRAM, SAFAR, RABI_AL_AWWAL, RABI_AL_THANI,
        JUMADA_AL_ULA, JUMADA_AL_THANI, RAJAB, SHA'BAN,
        RAMADAN, SHAWWAL, DHU_AL_QA'DAH, DHU_AL_HIJJAH
    ]


# Special Islamic dates
SPECIAL_DATES = {
    (1, 1): {"name_en": "Islamic New Year", "name_ar": "رأس السنة الهجرية"},
    (3, 12): {"name_en": "Mawlid al-Nabi (birth of Prophet Muhammad ﷺ)", "name_ar": "المولد النبوي"},
    (7, 27): {"name_en": "Isra and Mi'raj", "name_ar": "الإسراء والمعراج"},
    (9, 1): {"name_en": "Ramadan begins", "name_ar": "بداية رمضان"},
    (9, 27): {"name_en": "Laylat al-Qadr (possible)", "name_ar": "ليلة القدر (محتمل)"},
    (10, 1): {"name_en": "Eid al-Fitr", "name_ar": "عيد الفطر"},
    (12, 9): {"name_en": "Day of Arafah", "name_ar": "يوم عرفة"},
    (12, 10): {"name_en": "Eid al-Adha", "name_ar": "عيد الأضحى"},
    (12, 11): {"name_en": "First day of Tashreeq", "name_ar": "أول أيام التشريق"},
}


class HijriCalendarTool(BaseTool):
    """
    Tool for Hijri calendar conversions and Islamic date detection.
    
    Uses Umm al-Qura calendar algorithm (tabular approximation).
    Accurate to ±1 day (actual dates may vary based on moon sighting).
    
    Usage:
        tool = HijriCalendarTool()
        result = await tool.execute(gregorian_date="2025-03-01")
    """
    
    name = "hijri_calendar_tool"
    
    # Umm al-Qura calendar constants
    HIJRI_EPOCH = 1948439.5  # Julian date for 1 Muharram 1 AH (July 16, 622 CE)
    LUNAR_MONTH = 29.53059  # Average lunar month in days
    HIJRI_YEAR_DAYS = 354.36667  # Average Hijri year in days
    
    # 30-year cycle for leap years
    # Years 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29 are leap years
    LEAP_YEAR_POSITIONS = {2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29}
    
    async def execute(
        self,
        query: str = "",
        gregorian_date: Optional[str] = None,
        hijri_year: Optional[int] = None,
        hijri_month: Optional[int] = None,
        hijri_day: Optional[int] = None,
        **kwargs
    ) -> ToolOutput:
        """
        Convert between Gregorian and Hijri dates.
        
        Args:
            query: User query (not used, for compatibility)
            gregorian_date: Gregorian date in YYYY-MM-DD format
            hijri_year: Hijri year (for reverse conversion)
            hijri_month: Hijri month (1-12)
            hijri_day: Hijri day (1-30)
            
        Returns:
            ToolOutput with converted date and special day information
        """
        try:
            if gregorian_date:
                # Gregorian → Hijri
                g_date = datetime.strptime(gregorian_date, "%Y-%m-%d").date()
                h_year, h_month, h_day = self.gregorian_to_hijri(g_date)
            elif hijri_year and hijri_month and hijri_day:
                # Hijri → Gregorian
                g_date = self.hijri_to_gregorian(hijri_year, hijri_month, hijri_day)
                h_year, h_month, h_day = hijri_year, hijri_month, hijri_day
            else:
                # Default: today
                g_date = date.today()
                h_year, h_month, h_day = self.gregorian_to_hijri(g_date)
            
            # Get month info
            month_info = IslamicMonth.MONTHS[h_month - 1] if 1 <= h_month <= 12 else {}
            
            # Check for special dates
            special = SPECIAL_DATES.get((h_month, h_day))
            is_ramadan = (h_month == 9)
            is_dhul_hijjah = (h_month == 12)
            is_eid = (h_month == 10 and h_day == 1) or (h_month == 12 and h_day == 10)
            
            result = {
                "gregorian_date": g_date.isoformat(),
                "hijri_date": {
                    "year": h_year,
                    "month": h_month,
                    "day": h_day,
                    "month_name_en": month_info.get("en", ""),
                    "month_name_ar": month_info.get("ar", ""),
                    "formatted_en": f"{h_day} {month_info.get('en', '')} {h_year} AH",
                    "formatted_ar": f"{h_day} {month_info.get('ar', '')} {h_year} هـ",
                },
                "is_ramadan": is_ramadan,
                "is_dhul_hijjah": is_dhul_hijjah,
                "is_eid": is_eid,
                "is_leap_year": self.is_hijri_leap_year(h_year),
                "special_day": special,
                "days_in_month": self.days_in_hijri_month(h_year, h_month),
            }
            
            logger.info(
                "hijri.converted",
                gregorian=g_date.isoformat(),
                hijri=f"{h_year}-{h_month:02d}-{h_day:02d}"
            )
            
            return ToolOutput(
                result=result,
                success=True,
                metadata={
                    "disclaimer": (
                        "Hijri dates are calculated using the Umm al-Qura calendar "
                        "and may differ from actual dates by ±1 day based on moon sighting. "
                        "Always verify with local Islamic authorities."
                    )
                }
            )
            
        except Exception as e:
            logger.error("hijri.error", error=str(e))
            return ToolOutput(
                result={},
                success=False,
                error=f"Error converting dates: {str(e)}"
            )
    
    def gregorian_to_hijri(self, g_date: date) -> tuple[int, int, int]:
        """
        Convert Gregorian date to Hijri date.
        
        Args:
            g_date: Gregorian date
            
        Returns:
            Tuple of (hijri_year, hijri_month, hijri_day)
        """
        # Convert to Julian date
        jd = self._gregorian_to_julian(g_date.year, g_date.month, g_date.day)
        
        # Calculate Hijri date
        days_since_epoch = jd - self.HIJRI_EPOCH
        hijri_year = int((days_since_epoch * 30) / 10631) + 1
        
        # Calculate remaining days
        days_in_years = int(((hijri_year - 1) * 10631) / 30)
        remaining_days = int(jd - self.HIJRI_EPOCH - days_in_years)
        
        # Determine month
        hijri_month = 1
        while hijri_month <= 12:
            days_in_month = self.days_in_hijri_month(hijri_year, hijri_month)
            if remaining_days < days_in_month:
                break
            remaining_days -= days_in_month
            hijri_month += 1
        
        hijri_day = remaining_days + 1
        
        return (hijri_year, hijri_month, hijri_day)
    
    def hijri_to_gregorian(self, h_year: int, h_month: int, h_day: int) -> date:
        """
        Convert Hijri date to Gregorian date.
        
        Args:
            h_year: Hijri year
            h_month: Hijri month (1-12)
            h_day: Hijri day (1-30)
            
        Returns:
            Gregorian date
        """
        # Calculate days from epoch
        days = 0
        
        # Days in complete years
        years_completed = h_year - 1
        days += int((years_completed * 10631) / 30)
        
        # Days in complete months of current year
        for month in range(1, h_month):
            days += self.days_in_hijri_month(h_year, month)
        
        # Days in current month
        days += h_day - 1
        
        # Convert to Julian date
        jd = self.HIJRI_EPOCH + days
        
        # Convert Julian date to Gregorian
        return self._julian_to_gregorian(jd)
    
    def is_hijri_leap_year(self, h_year: int) -> bool:
        """
        Check if Hijri year is a leap year (30-year cycle).
        
        Leap years have 355 days instead of 354.
        """
        year_in_cycle = h_year % 30
        if year_in_cycle == 0:
            year_in_cycle = 30
        return year_in_cycle in self.LEAP_YEAR_POSITIONS
    
    def days_in_hijri_month(self, h_year: int, h_month: int) -> int:
        """
        Get number of days in a Hijri month.
        
        Months alternate between 29 and 30 days.
        Dhu al-Hijjah has 30 days in leap years.
        """
        if h_month < 1 or h_month > 12:
            return 30  # Default
        
        # Odd months have 30 days, even months have 29 days
        # Except Dhu al-Hijjah in leap year
        if h_month == 12 and self.is_hijri_leap_year(h_year):
            return 30
        elif h_month % 2 == 1:  # Odd month
            return 30
        else:  # Even month
            return 29
    
    # ==========================================
    # Julian date conversion helpers
    # ==========================================
    
    def _gregorian_to_julian(self, year: int, month: int, day: int) -> float:
        """Convert Gregorian date to Julian date."""
        if month <= 2:
            year -= 1
            month += 12
        
        a = int(year / 100)
        b = 2 - a + int(a / 4)
        
        jd = (int(365.25 * (year + 4716)) +
              int(30.6001 * (month + 1)) +
              day + b - 1524.5)
        
        return jd
    
    def _julian_to_gregorian(self, jd: float) -> date:
        """Convert Julian date to Gregorian date."""
        jd = int(jd + 0.5)
        f = jd + 1401 + int((int((4 * jd + 274277) / 146097) * 3) / 4) - 38
        e = 4 * f + 3
        g = int((e % 1461) / 4)
        h = 5 * g + 2
        day = int((h % 153) / 5) + 1
        month = (int(h / 153) + 2) % 12 + 1
        year = int(e / 1461) - 4716 + int((14 - month) / 12)
        
        return date(year, month, day)
