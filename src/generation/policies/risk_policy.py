# Risk Policy Module
"""Policies for controlling response risk assessment."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """Risk levels for responses."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class RiskAssessment:
    """Assessment of risk for a response."""

    level: RiskLevel
    concerns: List[str]
    recommendations: List[str]


# Topics that require careful handling
SENSITIVE_TOPICS = {
    "politics": RiskLevel.MEDIUM,
    "sectarian": RiskLevel.HIGH,
    "violence": RiskLevel.HIGH,
    "extreme": RiskLevel.BLOCKED,
    "medical": RiskLevel.MEDIUM,
    "legal": RiskLevel.MEDIUM,
    "personal": RiskLevel.MEDIUM,
}


# Blocked content patterns
BLOCKED_PATTERNS = [
    r"violence.*promote",
    r"terrorism.*support",
    r"extreme.*ideology",
]


class RiskPolicy:
    """Policy for assessing and managing response risk."""

    def __init__(self):
        self.sensitive_topics = SENSITIVE_TOPICS
        self.blocked_patterns = BLOCKED_PATTERNS

    def assess_risk(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """Assess the risk level of a response."""
        concerns = []
        recommendations = []

        # Check for sensitive topics
        query_lower = query.lower()
        for topic, level in self.sensitive_topics.items():
            if topic in query_lower:
                concerns.append(f"Topic involves {topic}")
                if level == RiskLevel.HIGH:
                    recommendations.append("Add disclaimer about consulting scholars")
                elif level == RiskLevel.BLOCKED:
                    recommendations.append("Block or abstain from this response")

        # Check response for potential issues
        response_lower = response.lower()

        # Check for overconfidence in uncertain matters
        uncertain_indicators = [
            "definitely",
            "certainly",
            "always",
            "never",
            "guaranteed",
            "absolute",
        ]
        if any(ind in response_lower for ind in uncertain_indicators):
            concerns.append("Response may show overconfidence")
            recommendations.append("Add appropriate qualifiers")

        # Determine overall risk level
        if any(c.startswith("Topic involves extreme") or c.startswith("Topic involves violence") for c in concerns):
            level = RiskLevel.BLOCKED
        elif any(c.startswith("Topic involves sectarian") for c in concerns):
            level = RiskLevel.HIGH
        elif concerns:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskAssessment(
            level=level,
            concerns=concerns,
            recommendations=recommendations,
        )

    def should_block(self, risk_assessment: RiskAssessment) -> bool:
        """Determine if response should be blocked."""
        return risk_assessment.level == RiskLevel.BLOCKED

    def should_add_disclaimer(
        self,
        risk_assessment: RiskAssessment,
    ) -> bool:
        """Determine if disclaimer should be added."""
        return risk_assessment.level == RiskLevel.HIGH or risk_assessment.level == RiskLevel.MEDIUM


# Default policy instance
risk_policy = RiskPolicy()
