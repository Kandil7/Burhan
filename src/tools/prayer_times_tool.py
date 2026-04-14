"""
Prayer Times Tool for Athar Islamic QA system.

Calculates daily prayer times and Qibla direction using astronomical algorithms.
Supports multiple calculation methods (Egyptian, MWL, ISNA, Umm al-Qura).

Based on Fanar-Sadiq architecture: Deterministic calculations, no LLM generation.
"""
import math
from datetime import date, datetime
from enum import Enum

from src.config.logging_config import get_logger
from src.tools.base import BaseTool, ToolOutput

logger = get_logger()


class PrayerMethod(str, Enum):
    """Prayer time calculation methods."""
    EGYPTIAN = "egyptian"
    MWL = "mwl"
    ISNA = "isna"
    UMM_AL_QURA = "umm_al_qura"
    KARACHI = "karachi"
    DUBAI = "dubai"


# ==========================================
# Method parameters
# ==========================================
METHOD_PARAMS = {
    PrayerMethod.EGYPTIAN: {"fajr_angle": 19.5, "isha_angle": 17.5},
    PrayerMethod.MWL: {"fajr_angle": 18.0, "isha_angle": 17.0},
    PrayerMethod.ISNA: {"fajr_angle": 15.0, "isha_angle": 15.0},
    PrayerMethod.UMM_AL_QURA: {"fajr_angle": 18.5, "isha_minutes": 90},
    PrayerMethod.KARACHI: {"fajr_angle": 18.0, "isha_angle": 18.0},
    PrayerMethod.DUBAI: {"fajr_angle": 18.2, "isha_angle": 18.2},
}

# Mecca coordinates
MECCA_LAT = 21.4225
MECCA_LNG = 39.8262


class PrayerTimesTool(BaseTool):
    """
    Tool for calculating prayer times and Qibla direction.

    Usage:
        tool = PrayerTimesTool()
        result = await tool.execute(
            lat=25.2854,
            lng=51.5310,
            date="2025-01-01",
            method="egyptian"
        )
    """

    name = "prayer_times_tool"

    async def execute(
        self,
        query: str = "",
        lat: float = 0.0,
        lng: float = 0.0,
        date_str: str | None = None,
        method: str = "egyptian",
        timezone: float = 0.0,
        **kwargs
    ) -> ToolOutput:
        """
        Calculate prayer times for a location and date.

        Args:
            query: User query (not used, for compatibility)
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)
            date_str: Date in YYYY-MM-DD format (default: today)
            method: Calculation method name
            timezone: UTC offset in hours (default: auto-detect)

        Returns:
            ToolOutput with prayer times and Qibla direction
        """
        try:
            # Validate inputs
            if not (-90 <= lat <= 90):
                return ToolOutput(
                    result={},
                    success=False,
                    error=f"Invalid latitude: {lat}. Must be between -90 and 90."
                )

            if not (-180 <= lng <= 180):
                return ToolOutput(
                    result={},
                    success=False,
                    error=f"Invalid longitude: {lng}. Must be between -180 and 180."
                )

            # Parse date
            if date_str:
                calc_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                calc_date = date.today()

            # Parse method
            try:
                prayer_method = PrayerMethod(method.lower())
            except ValueError:
                prayer_method = PrayerMethod.EGYPTIAN

            # Calculate prayer times
            times = self._calculate_prayer_times(
                lat, lng, calc_date, prayer_method, timezone
            )

            # Calculate Qibla direction
            qibla = self._calculate_qibla(lat, lng)

            # Format results
            result = {
                "date": calc_date.isoformat(),
                "location": {"lat": lat, "lng": lng},
                "method": prayer_method.value,
                "times": {
                    "fajr": times["fajr"],
                    "sunrise": times["sunrise"],
                    "dhuhr": times["dhuhr"],
                    "asr": times["asr"],
                    "maghrib": times["maghrib"],
                    "isha": times["isha"],
                },
                "qibla_direction": round(qibla, 2),
            }

            logger.info(
                "prayer_times.calculated",
                date=calc_date.isoformat(),
                lat=lat,
                lng=lng,
                method=prayer_method.value
            )

            return ToolOutput(
                result=result,
                success=True,
                metadata={
                    "method_description": self._get_method_description(prayer_method),
                    "note": "Times are approximate. Verify with local mosque for accuracy."
                }
            )

        except Exception as e:
            logger.error("prayer_times.error", error=str(e))
            return ToolOutput(
                result={},
                success=False,
                error=f"Error calculating prayer times: {str(e)}"
            )

    def _calculate_prayer_times(
        self,
        lat: float,
        lng: float,
        calc_date: date,
        method: PrayerMethod,
        timezone: float
    ) -> dict:
        """
        Calculate all prayer times for a given date and location.

        Returns dict with fajr, sunrise, dhuhr, asr, maghrib, isha times.
        """
        params = METHOD_PARAMS[method]

        # Calculate Julian date
        jd = self._julian_date(calc_date.year, calc_date.month, calc_date.day)

        # Sun position
        declination = self._sun_declination(jd)
        equation_of_time = self._equation_of_time(jd)

        # Dhuhr (midday)
        dhuhr = 12 + timezone - (lng / 15) - equation_of_time

        # Sunrise and Sunset
        sunrise_angle = 0.833  # Standard sunrise angle
        sunrise_time = self._hour_angle(lat, declination, sunrise_angle)
        sunset_time = self._hour_angle(lat, declination, sunrise_angle)

        sunrise = dhuhr - sunrise_time / 15
        maghrib = dhuhr + sunset_time / 15

        # Fajr
        fajr_angle = params["fajr_angle"]
        fajr_time = self._hour_angle(lat, declination, fajr_angle)
        fajr = dhuhr - fajr_time / 15

        # Isha
        if method == PrayerMethod.UMM_AL_QURA:
            # 90 minutes after maghrib (120 in Ramadan)
            isha_minutes = params.get("isha_minutes", 90)
            isha = maghrib + (isha_minutes / 60)
        else:
            isha_angle = params["isha_angle"]
            isha_time = self._hour_angle(lat, declination, isha_angle)
            isha = dhuhr + isha_time / 15

        # Asr (Shafii: shadow factor 1, Hanafi: shadow factor 2)
        asr_time = self._asr_time(lat, declination, asr_factor=1)
        asr = dhuhr + asr_time / 15

        return {
            "fajr": self._format_time(fajr),
            "sunrise": self._format_time(sunrise),
            "dhuhr": self._format_time(dhuhr),
            "asr": self._format_time(asr),
            "maghrib": self._format_time(maghrib),
            "isha": self._format_time(isha),
        }

    def _calculate_qibla(self, lat: float, lng: float) -> float:
        """
        Calculate Qibla direction (degrees from North).

        Uses great-circle bearing formula.
        """
        # Convert to radians
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)
        mecca_lat_rad = math.radians(MECCA_LAT)
        mecca_lng_rad = math.radians(MECCA_LNG)

        # Difference in longitude
        delta_lng = mecca_lng_rad - lng_rad

        # Great-circle bearing formula
        y = math.sin(delta_lng) * math.cos(mecca_lat_rad)
        x = (math.cos(lat_rad) * math.sin(mecca_lat_rad) -
             math.sin(lat_rad) * math.cos(mecca_lat_rad) * math.cos(delta_lng))

        bearing = math.atan2(y, x)
        bearing_degrees = math.degrees(bearing)

        # Normalize to 0-360
        return (bearing_degrees + 360) % 360

    # ==========================================
    # Astronomical calculation helpers
    # ==========================================

    def _julian_date(self, year: int, month: int, day: int) -> float:
        """Calculate Julian Date from Gregorian calendar."""
        if month <= 2:
            year -= 1
            month += 12

        a = int(year / 100)
        b = 2 - a + int(a / 4)

        jd = (int(365.25 * (year + 4716)) +
              int(30.6001 * (month + 1)) +
              day + b - 1524.5)

        return jd

    def _sun_declination(self, jd: float) -> float:
        """Calculate sun declination angle."""
        # Days from J2000.0
        d = jd - 2451545.0

        # Mean anomaly
        g = (357.529 + 0.98560028 * d) % 360
        g_rad = math.radians(g)

        # Ecliptic longitude
        q = (280.459 + 0.98564736 * d) % 360
        lon = (q + 1.915 * math.sin(g_rad) +
               0.020 * math.sin(2 * g_rad)) % 360
        lon_rad = math.radians(lon)

        # Obliquity of ecliptic
        e = 23.439 - 0.00000036 * d
        e_rad = math.radians(e)

        # Declination
        return math.degrees(math.asin(math.sin(e_rad) * math.sin(l_rad)))

    def _equation_of_time(self, jd: float) -> float:
        """Calculate equation of time (in hours)."""
        d = jd - 2451545.0
        g = (357.529 + 0.98560028 * d) % 360
        g_rad = math.radians(g)

        q = (280.459 + 0.98564736 * d) % 360

        lon = (q + 1.915 * math.sin(g_rad) +
               0.020 * math.sin(2 * g_rad)) % 360
        lon_rad = math.radians(lon)

        e = 23.439 - 0.00000036 * d
        e_rad = math.radians(e)

        ra = math.degrees(math.atan2(
            math.cos(e_rad) * math.sin(lon_rad),
            math.cos(lon_rad)
        )) / 15

        return (q / 15 - ra) % 24

    def _hour_angle(
        self,
        lat: float,
        declination: float,
        angle: float
    ) -> float:
        """Calculate hour angle for a given sun angle."""
        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)
        angle_rad = math.radians(angle)

        cos_ha = (math.sin(angle_rad) -
                  math.sin(lat_rad) * math.sin(dec_rad)) / \
                 (math.cos(lat_rad) * math.cos(dec_rad))

        # Clamp to valid range
        cos_ha = max(-1, min(1, cos_ha))

        return math.degrees(math.acos(cos_ha))

    def _asr_time(
        self,
        lat: float,
        declination: float,
        asr_factor: float = 1.0
    ) -> float:
        """Calculate Asr time (hour angle)."""
        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)

        # Asr angle calculation
        d = math.atan(1.0 / (asr_factor + math.tan(abs(lat_rad - dec_rad))))

        return self._hour_angle(lat, declination, math.degrees(d))

    def _format_time(self, decimal_hours: float) -> str:
        """Format decimal hours to HH:MM string."""
        # Normalize to 0-24
        decimal_hours = decimal_hours % 24

        hours = int(decimal_hours)
        minutes = int((decimal_hours - hours) * 60)

        return f"{hours:02d}:{minutes:02d}"

    def _get_method_description(self, method: PrayerMethod) -> str:
        """Get human-readable description of calculation method."""
        descriptions = {
            PrayerMethod.EGYPTIAN: "Egyptian General Authority (fajr: 19.5°, isha: 17.5°)",
            PrayerMethod.MWL: "Muslim World League (fajr: 18°, isha: 17°)",
            PrayerMethod.ISNA: "Islamic Society of North America (fajr: 15°, isha: 15°)",
            PrayerMethod.UMM_AL_QURA: "Umm al-Qura, Makkah (fajr: 18.5°, isha: 90 min after maghrib)",
            PrayerMethod.KARACHI: "University of Karachi (fajr: 18°, isha: 18°)",
            PrayerMethod.DUBAI: "Dubai (fajr: 18.2°, isha: 18.2°)",
        }
        return descriptions.get(method, "")
