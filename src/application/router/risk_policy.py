# Risk Policy Module
"""Risk assessment policies for the router."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """Risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class RiskAssessment:
    """Assessment of query risk."""

    level: RiskLevel
    reasons: List[str]
    recommendations: List[str]


# Sensitive query patterns
SENSITIVE_PATTERNS = {
    "sectarian": [
        "sunni",
        "shi'a",
        "rawafid",
        "wahhab",
        "salafi",
        "خوارج",
        "روافض",
        "moderate",
        "extreme",
    ],
    "political": [
        "government",
        "politics",
        "islamic state",
        "terrorism",
        "political",
        "governance",
        "دولة",
        "سياسة",
    ],
    "medical": [
        "treatment",
        "cure",
        "disease",
        "illness",
        " doctor",
        "علاج",
        "مرض",
        "طبيب",
    ],
    "legal": [
        "court",
        "lawsuit",
        "legal",
        "police",
        "jail",
        "محكمة",
        "قانون",
        "شرطة",
    ],
}


class RiskPolicy:
    """Policy for assessing and managing query risk."""

    def __init__(self):
        self.sensitive_patterns = SENSITIVE_PATTERNS

    def assess_risk(self, query: str) -> RiskAssessment:
        """Assess the risk level of a query."""
        query_lower = query.lower()
        reasons = []

        # Check for sensitive patterns
        for category, patterns in self.sensitive_patterns.items():
            matches = [p for p in patterns if p in query_lower]
            if matches:
                reasons.append(f"Contains {category} keywords: {matches}")

        # Determine risk level
        if any("sectarian" in r or "political" in r for r in reasons):
            level = RiskLevel.HIGH
            recommendations = [
                "Route to general Islamic agent",
                "Add scholarly disclaimer",
                "Avoid controversial positions",
            ]
        elif reasons:
            level = RiskLevel.MEDIUM
            recommendations = [
                "Add appropriate disclaimer",
                "Recommend consulting scholars for specific advice",
            ]
        else:
            level = RiskLevel.LOW
            recommendations = []

        return RiskAssessment(
            level=level,
            reasons=reasons,
            recommendations=recommendations,
        )

    def should_block(self, risk: RiskAssessment) -> bool:
        """Determine if query should be blocked."""
        return risk.level == RiskLevel.BLOCKED

    def should_add_disclaimer(self, risk: RiskAssessment) -> bool:
        """Determine if disclaimer should be added."""
        return risk.level in (RiskLevel.HIGH, RiskLevel.MEDIUM)

    def get_filtered_response(
        self,
        query: str,
        risk: RiskAssessment,
    ) -> Optional[str]:
        """Get filtered response based on risk."""
        if risk.level == RiskLevel.BLOCKED:
            return "I'm sorry, but I cannot help with this query. Please consult with a qualified scholar."
        return None


# Default risk policy instance
risk_policy = RiskPolicy()
