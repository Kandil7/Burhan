"""
Prayer Times Tool for Athar Islamic QA system.

Fixes:
  - _hour_angle: corrected formula sign (was producing inverted times)
  - _equation_of_time: removed erroneous % 24
  - timezone: auto-detect from longitude when not provided
"""
import math
from datetime import date, datetime
from enum import Enum

from src.config.logging_config import get_logger
from src.tools.base import BaseTool, ToolOutput

logger = get_logger()


class PrayerMethod(str, Enum):
    EGYPTIAN    = "egyptian"
    MWL         = "mwl"
    ISNA        = "isna"
    UMM_AL_QURA = "umm_al_qura"
    KARACHI     = "karachi"
    DUBAI       = "dubai"


METHOD_PARAMS: dict[PrayerMethod, dict] = {
    PrayerMethod.EGYPTIAN:    {"fajr_angle": 19.5, "isha_angle": 17.5},
    PrayerMethod.MWL:         {"fajr_angle": 18.0, "isha_angle": 17.0},
    PrayerMethod.ISNA:        {"fajr_angle": 15.0, "isha_angle": 15.0},
    PrayerMethod.UMM_AL_QURA: {"fajr_angle": 18.5, "isha_minutes": 90},
    PrayerMethod.KARACHI:     {"fajr_angle": 18.0, "isha_angle": 18.0},
    PrayerMethod.DUBAI:       {"fajr_angle": 18.2, "isha_angle": 18.2},
}

MECCA_LAT = 21.4225
MECCA_LNG = 39.8262

# Standard refraction + solar disc correction
_SUNRISE_DEPRESSION = 0.833


class PrayerTimesTool(BaseTool):
    """Calculates Islamic prayer times and Qibla direction."""

    name = "prayer_times_tool"

    async def execute(
        self,
        query: str = "",
        lat: float = 0.0,
        lng: float = 0.0,
        date_str: str | None = None,
        method: str = "egyptian",
        timezone: float | None = None,   # ← None = auto-detect from longitude
        **kwargs,
    ) -> ToolOutput:
        try:
            if not (-90 <= lat <= 90):
                return ToolOutput(result={}, success=False,
                                  error=f"Invalid latitude {lat}: must be -90..90.")
            if not (-180 <= lng <= 180):
                return ToolOutput(result={}, success=False,
                                  error=f"Invalid longitude {lng}: must be -180..180.")

            calc_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_str else date.today()
            )

            try:
                prayer_method = PrayerMethod(method.lower())
            except ValueError:
                prayer_method = PrayerMethod.EGYPTIAN

            # Auto-detect timezone from longitude (rough but usable default)
            tz = timezone if timezone is not None else round(lng / 15)

            times  = self._calculate_prayer_times(lat, lng, calc_date, prayer_method, tz)
            qibla  = self._calculate_qibla(lat, lng)

            result = {
                "date":            calc_date.isoformat(),
                "location":        {"lat": lat, "lng": lng},
                "method":          prayer_method.value,
                "timezone_used":   tz,
                "times":           times,
                "qibla_direction": round(qibla, 2),
            }

            logger.info("prayer_times.calculated",
                        date=calc_date.isoformat(), lat=lat, lng=lng,
                        method=prayer_method.value, tz=tz)

            return ToolOutput(
                result=result,
                success=True,
                metadata={
                    "method_description": self._get_method_description(prayer_method),
                    "note": "Times are approximate. Verify with local mosque for accuracy.",
                },
            )

        except Exception as e:
            logger.error("prayer_times.error", error=str(e), exc_info=True)
            return ToolOutput(result={}, success=False,
                              error=f"Error calculating prayer times: {e}")

    # ── Core calculation ──────────────────────────────────────────────────────

    def _calculate_prayer_times(
        self,
        lat: float,
        lng: float,
        calc_date: date,
        method: PrayerMethod,
        timezone: float,
    ) -> dict[str, str]:
        params = METHOD_PARAMS[method]
        jd     = self._julian_date(calc_date.year, calc_date.month, calc_date.day)

        declination    = self._sun_declination(jd)
        equation_of_time = self._equation_of_time(jd)

        # Dhuhr: solar noon adjusted for longitude and equation of time
        dhuhr = 12 + timezone - (lng / 15) - equation_of_time

        # Sunrise / Maghrib (symmetric around Dhuhr)
        ha_rise   = self._hour_angle(lat, declination, _SUNRISE_DEPRESSION)
        sunrise   = dhuhr - ha_rise / 15
        maghrib   = dhuhr + ha_rise / 15

        # Fajr
        fajr_ha = self._hour_angle(lat, declination, params["fajr_angle"])
        fajr    = dhuhr - fajr_ha / 15

        # Isha
        if method == PrayerMethod.UMM_AL_QURA:
            isha = maghrib + params.get("isha_minutes", 90) / 60
        else:
            isha_ha = self._hour_angle(lat, declination, params["isha_angle"])
            isha    = dhuhr + isha_ha / 15

        # Asr (Shafi'i shadow factor = 1; Hanafi = 2)
        asr_ha = self._asr_time(lat, declination, asr_factor=1)
        asr    = dhuhr + asr_ha / 15

        return {
            "fajr":    self._format_time(fajr),
            "sunrise": self._format_time(sunrise),
            "dhuhr":   self._format_time(dhuhr),
            "asr":     self._format_time(asr),
            "maghrib": self._format_time(maghrib),
            "isha":    self._format_time(isha),
        }

    # ── Astronomical helpers ──────────────────────────────────────────────────

    def _julian_date(self, year: int, month: int, day: int) -> float:
        if month <= 2:
            year  -= 1
            month += 12
        a  = year // 100
        b  = 2 - a + a // 4
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    def _sun_declination(self, jd: float) -> float:
        d       = jd - 2451545.0
        g_rad   = math.radians((357.529 + 0.98560028 * d) % 360)
        q       = (280.459 + 0.98564736 * d) % 360
        lon_rad = math.radians((q + 1.915 * math.sin(g_rad) + 0.020 * math.sin(2 * g_rad)) % 360)
        e_rad   = math.radians(23.439 - 0.00000036 * d)
        return math.degrees(math.asin(math.sin(e_rad) * math.sin(lon_rad)))

    def _equation_of_time(self, jd: float) -> float:
        """Equation of time in hours (typically ±0.25 h)."""
        d       = jd - 2451545.0
        g_rad   = math.radians((357.529 + 0.98560028 * d) % 360)
        q       = (280.459 + 0.98564736 * d) % 360
        lon_rad = math.radians((q + 1.915 * math.sin(g_rad) + 0.020 * math.sin(2 * g_rad)) % 360)
        e_rad   = math.radians(23.439 - 0.00000036 * d)
        ra      = math.degrees(math.atan2(math.cos(e_rad) * math.sin(lon_rad),
                                           math.cos(lon_rad))) / 15
        eqt = q / 15 - ra          # small correction — NO modulo 24
        if eqt >  12: eqt -= 24   # edge-case sanity guard only
        if eqt < -12: eqt += 24
        return eqt

    def _hour_angle(self, lat: float, declination: float, angle: float) -> float:
        """
        Hour angle for a given solar depression angle (degrees, positive = below horizon).

        Correct formula:  cos(H) = -(sin(a) + sin(φ)·sin(δ)) / (cos(φ)·cos(δ))
        """
        lat_rad   = math.radians(lat)
        dec_rad   = math.radians(declination)
        angle_rad = math.radians(angle)

        cos_ha = -(math.sin(angle_rad) + math.sin(lat_rad) * math.sin(dec_rad)) / \
                  (math.cos(lat_rad) * math.cos(dec_rad))

        cos_ha = max(-1.0, min(1.0, cos_ha))   # clamp for polar edge cases
        return math.degrees(math.acos(cos_ha))

    def _asr_time(self, lat: float, declination: float, asr_factor: float = 1.0) -> float:
        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)
        d       = math.atan(1.0 / (asr_factor + math.tan(abs(lat_rad - dec_rad))))
        return self._hour_angle(lat, declination, -math.degrees(d))  # ← negative: above horizon

    def _calculate_qibla(self, lat: float, lng: float) -> float:
        lat_rad      = math.radians(lat)
        lng_rad      = math.radians(lng)
        m_lat        = math.radians(MECCA_LAT)
        m_lng        = math.radians(MECCA_LNG)
        delta_lng    = m_lng - lng_rad
        y = math.sin(delta_lng) * math.cos(m_lat)
        x = math.cos(lat_rad) * math.sin(m_lat) - math.sin(lat_rad) * math.cos(m_lat) * math.cos(delta_lng)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def _format_time(self, decimal_hours: float) -> str:
        h = decimal_hours % 24
        hours   = int(h)
        minutes = int((h - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def _get_method_description(self, method: PrayerMethod) -> str:
        return {
            PrayerMethod.EGYPTIAN:    "Egyptian General Authority (fajr: 19.5°, isha: 17.5°)",
            PrayerMethod.MWL:         "Muslim World League (fajr: 18°, isha: 17°)",
            PrayerMethod.ISNA:        "Islamic Society of North America (fajr: 15°, isha: 15°)",
            PrayerMethod.UMM_AL_QURA: "Umm al-Qura, Makkah (fajr: 18.5°, isha: 90 min after maghrib)",
            PrayerMethod.KARACHI:     "University of Karachi (fajr: 18°, isha: 18°)",
            PrayerMethod.DUBAI:       "Dubai (fajr: 18.2°, isha: 18.2°)",
        }.get(method, "")