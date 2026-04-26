"""
Hijri Calendar Tool for Burhan Islamic QA system.

Fixes:
  - gregorian_to_hijri: year correction loop prevents negative remaining_days
  - hijri_month overflow (13) → IndexError eliminated
  - hijri_to_gregorian: input validation added
  - Removed unused constants
"""
from datetime import date, datetime

from src.config.logging_config import get_logger
from src.tools.base import BaseTool, ToolOutput

logger = get_logger()


class IslamicMonth:
    MUHARRAM       = {"en": "Muharram",         "ar": "محرم",           "number": 1}
    SAFAR          = {"en": "Safar",             "ar": "صفر",            "number": 2}
    RABI_AL_AWWAL  = {"en": "Rabi al-Awwal",     "ar": "ربيع الأول",     "number": 3}
    RABI_AL_THANI  = {"en": "Rabi al-Thani",     "ar": "ربيع الثاني",    "number": 4}
    JUMADA_AL_ULA  = {"en": "Jumada al-Ula",     "ar": "جمادى الأولى",   "number": 5}
    JUMADA_AL_THANI= {"en": "Jumada al-Thani",   "ar": "جمادى الآخرة",   "number": 6}
    RAJAB          = {"en": "Rajab",             "ar": "رجب",            "number": 7}
    SHABAN         = {"en": "Sha'ban",           "ar": "شعبان",          "number": 8}
    RAMADAN        = {"en": "Ramadan",           "ar": "رمضان",          "number": 9}
    SHAWWAL        = {"en": "Shawwal",           "ar": "شوال",           "number": 10}
    DHU_AL_QADAH   = {"en": "Dhu al-Qa'dah",     "ar": "ذو القعدة",      "number": 11}
    DHU_AL_HIJJAH  = {"en": "Dhu al-Hijjah",     "ar": "ذو الحجة",       "number": 12}

    MONTHS = [
        MUHARRAM, SAFAR, RABI_AL_AWWAL, RABI_AL_THANI,
        JUMADA_AL_ULA, JUMADA_AL_THANI, RAJAB, SHABAN,
        RAMADAN, SHAWWAL, DHU_AL_QADAH, DHU_AL_HIJJAH,
    ]


SPECIAL_DATES: dict[tuple[int, int], dict] = {
    (1,  1):  {"name_en": "Islamic New Year",                    "name_ar": "رأس السنة الهجرية"},
    (3,  12): {"name_en": "Mawlid al-Nabi",                      "name_ar": "المولد النبوي"},
    (7,  27): {"name_en": "Isra and Mi'raj",                     "name_ar": "الإسراء والمعراج"},
    (9,  1):  {"name_en": "Ramadan begins",                      "name_ar": "بداية رمضان"},
    (9,  27): {"name_en": "Laylat al-Qadr (possible)",           "name_ar": "ليلة القدر (محتمل)"},
    (10, 1):  {"name_en": "Eid al-Fitr",                         "name_ar": "عيد الفطر"},
    (12, 9):  {"name_en": "Day of Arafah",                       "name_ar": "يوم عرفة"},
    (12, 10): {"name_en": "Eid al-Adha",                         "name_ar": "عيد الأضحى"},
    (12, 11): {"name_en": "First day of Tashreeq",               "name_ar": "أول أيام التشريق"},
}

# Julian Date for 1 Muharram 1 AH (16 July 622 CE Julian calendar)
_HIJRI_EPOCH = 1948438.5


class HijriCalendarTool(BaseTool):
    """
    Hijri ↔ Gregorian conversion using tabular Umm al-Qura algorithm.
    Accurate to ±1 day (actual dates may vary based on moon sighting).
    """

    name = "hijri_calendar_tool"

    LEAP_YEAR_POSITIONS = {2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29}

    async def execute(
        self,
        query: str = "",
        gregorian_date: str | None = None,
        hijri_year: int | None = None,
        hijri_month: int | None = None,
        hijri_day: int | None = None,
        **kwargs,
    ) -> ToolOutput:
        try:
            if gregorian_date:
                g_date = datetime.strptime(gregorian_date, "%Y-%m-%d").date()
                h_year, h_month, h_day = self.gregorian_to_hijri(g_date)

            elif hijri_year and hijri_month and hijri_day:
                if not (1 <= hijri_month <= 12):
                    return ToolOutput(result={}, success=False,
                                      error=f"Invalid Hijri month: {hijri_month}. Must be 1-12.")
                max_day = self.days_in_hijri_month(hijri_year, hijri_month)
                if not (1 <= hijri_day <= max_day):
                    return ToolOutput(result={}, success=False,
                                      error=f"Invalid Hijri day: {hijri_day}. Month {hijri_month} has {max_day} days.")
                g_date = self.hijri_to_gregorian(hijri_year, hijri_month, hijri_day)
                h_year, h_month, h_day = hijri_year, hijri_month, hijri_day

            else:
                g_date = date.today()
                h_year, h_month, h_day = self.gregorian_to_hijri(g_date)

            month_info = IslamicMonth.MONTHS[h_month - 1]   # h_month guaranteed 1-12
            special    = SPECIAL_DATES.get((h_month, h_day))

            result = {
                "gregorian_date": g_date.isoformat(),
                "hijri_date": {
                    "year":          h_year,
                    "month":         h_month,
                    "day":           h_day,
                    "month_name_en": month_info["en"],
                    "month_name_ar": month_info["ar"],
                    "formatted_en":  f"{h_day} {month_info['en']} {h_year} AH",
                    "formatted_ar":  f"{h_day} {month_info['ar']} {h_year} هـ",
                },
                "is_ramadan":      h_month == 9,
                "is_dhul_hijjah":  h_month == 12,
                "is_eid":          (h_month == 10 and h_day == 1) or (h_month == 12 and h_day == 10),
                "is_leap_year":    self.is_hijri_leap_year(h_year),
                "special_day":     special,
                "days_in_month":   self.days_in_hijri_month(h_year, h_month),
            }

            logger.info("hijri.converted",
                        gregorian=g_date.isoformat(),
                        hijri=f"{h_year}-{h_month:02d}-{h_day:02d}")

            return ToolOutput(
                result=result,
                success=True,
                metadata={
                    "disclaimer": (
                        "Hijri dates use the tabular Umm al-Qura algorithm (±1 day). "
                        "Verify with local Islamic authorities for moon-sighting-based dates."
                    )
                },
            )

        except Exception as e:
            logger.error("hijri.error", error=str(e), exc_info=True)
            return ToolOutput(result={}, success=False,
                              error=f"Error converting dates: {e}")

    # ── Conversion ────────────────────────────────────────────────────────────

    def gregorian_to_hijri(self, g_date: date) -> tuple[int, int, int]:
        jd = self._gregorian_to_julian(g_date.year, g_date.month, g_date.day)

        # Initial year estimate
        days_since_epoch = jd - _HIJRI_EPOCH
        h_year = max(1, int((days_since_epoch * 30) / 10631) + 1)

        # ── Correction loop: adjust year until remaining_days is in [0, year_length) ──
        while True:
            days_in_years  = int(((h_year - 1) * 10631) / 30)
            year_length    = 355 if self.is_hijri_leap_year(h_year) else 354
            remaining_days = int(days_since_epoch) - days_in_years

            if remaining_days < 0:
                h_year -= 1          # overshot — go back one year
            elif remaining_days >= year_length:
                h_year += 1          # undershot — advance one year
            else:
                break                # remaining_days is within this year ✓

        # ── Find month ────────────────────────────────────────────────────────
        h_month = 1
        for m in range(1, 13):
            dim = self.days_in_hijri_month(h_year, m)
            if remaining_days < dim:
                h_month = m
                break
            remaining_days -= dim
        # remaining_days is now days elapsed within h_month (0-based)

        return h_year, h_month, remaining_days + 1

    def hijri_to_gregorian(self, h_year: int, h_month: int, h_day: int) -> date:
        days = int(((h_year - 1) * 10631) / 30)          # complete years
        for m in range(1, h_month):
            days += self.days_in_hijri_month(h_year, m)   # complete months
        days += h_day - 1                                  # days in current month
        return self._julian_to_gregorian(_HIJRI_EPOCH + days)

    # ── Calendar helpers ──────────────────────────────────────────────────────

    def is_hijri_leap_year(self, h_year: int) -> bool:
        cycle = h_year % 30 or 30
        return cycle in self.LEAP_YEAR_POSITIONS

    def days_in_hijri_month(self, h_year: int, h_month: int) -> int:
        if not (1 <= h_month <= 12):
            raise ValueError(f"Invalid Hijri month: {h_month}")
        if h_month == 12 and self.is_hijri_leap_year(h_year):
            return 30
        return 30 if h_month % 2 == 1 else 29

    # ── Julian date helpers ───────────────────────────────────────────────────

    def _gregorian_to_julian(self, year: int, month: int, day: int) -> float:
        if month <= 2:
            year  -= 1
            month += 12
        a  = year // 100
        b  = 2 - a + a // 4
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    def _julian_to_gregorian(self, jd: float) -> date:
        z  = int(jd + 0.5)
        f  = z + 1401 + int(int((4 * z + 274277) / 146097) * 3 / 4) - 38
        e  = 4 * f + 3
        g  = int((e % 1461) / 4)
        h  = 5 * g + 2
        day   = int((h % 153) / 5) + 1
        month = (int(h / 153) + 2) % 12 + 1
        year  = e // 1461 - 4716 + (14 - month) // 12
        return date(year, month, day)