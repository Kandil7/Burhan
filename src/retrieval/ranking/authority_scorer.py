# Authority Scorer Module
"""Authority scoring for sources based on scholarly consensus."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AuthorityLevel(str, Enum):
    """Levels of authority."""

    MUTAWATIR = "mutawatir"  # Mass-transmitted
    SAHIH = "sahih"  # Authentic
    HASAN = "hasan"  # Good
    DAIF = "daif"  # Weak
    UNKNOWN = "unknown"


@dataclass
class AuthorityScore:
    """Authority score for a source."""

    level: AuthorityLevel
    score: float
    reason: Optional[str] = None


# Authority scores for major sources
SOURCE_AUTHORITY: Dict[str, AuthorityScore] = {
    "quran": AuthorityScore(
        level=AuthorityLevel.MUTAWATIR,
        score=1.0,
        reason="Mass-transmitted from the Prophet",
    ),
    "sahih_bukhari": AuthorityScore(
        level=AuthorityLevel.SAHIH,
        score=0.95,
        reason="Most authentic hadith collection",
    ),
    "sahih_muslim": AuthorityScore(
        level=AuthorityLevel.SAHIH,
        score=0.95,
        reason="Second most authentic hadith collection",
    ),
    "hidayah": AuthorityScore(
        level=AuthorityLevel.SAHIH,
        score=0.90,
        reason="Authoritative Hanafi fiqh text",
    ),
}


def get_authority(source_id: str) -> AuthorityScore:
    """Get authority score for a source."""
    return SOURCE_AUTHORITY.get(
        source_id,
        AuthorityScore(
            level=AuthorityLevel.UNKNOWN,
            score=0.5,
            reason="Unknown source",
        ),
    )


def calculate_weighted_authority(sources: List[str]) -> float:
    """Calculate weighted authority from multiple sources."""
    if not sources:
        return 0.0

    total = sum(get_authority(s).score for s in sources)
    return total / len(sources)
