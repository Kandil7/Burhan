"""
Config-Backed Router Agent

This module provides a router that uses YAML configurations
to route queries to the appropriate agent based on keyword patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Keywords for Rule-Based Routing
# ============================================================================

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "fiqh": [
        "حكم",
        " يجوز",
        "لا يجوز",
        "حرام",
        "حلال",
        "فتوى",
        "مكروه",
        "واجب",
        "fiqh",
        "halal",
        "haram",
        "fatwa",
        "حكم",
        "صلاة",
        "صيام",
        "زكاة",
        "حج",
        "طهارة",
        "نجاسة",
        "وضوء",
        "غسل",
        "إمامة",
        "جماعة",
    ],
    "hadith": [
        "حديث",
        "الحديث",
        "سند",
        "إسناد",
        "تخريج",
        "صحيح",
        "ضعيف",
        "موضوع",
        "hadith",
        "sunnah",
        "narrated",
        "sanad",
        "matn",
        "الرسول",
        "النبي",
        "البخاري",
        "مسلم",
        "الترمذي",
        "النسائي",
        "ابن ماجه",
        "أبو داود",
    ],
    "tafsir": [
        "آية",
        "اية",
        "سورة",
        "سوره",
        "قرآن",
        "تفسير",
        "فسير",
        "quran",
        "surah",
        "ayah",
        "verse",
        "tafsir",
        "tafseer",
        "الله",
        "تبارك",
        "تعالي",
        "قوله",
    ],
    "aqeedah": [
        "عقيدة",
        "عقيده",
        "توحيد",
        "إيمان",
        "كفر",
        "شرك",
        "رمي",
        "aqeedah",
        "tawhid",
        "iman",
        " kufr",
        "shirk",
        "believe",
        "الله",
        "الرب",
        "الأسماء",
        "الصفات",
        "الأسماء والصفات",
        "قدر",
        "قضاء",
        " destiny",
        "رجحان",
        "عقيدة أهل السنة",
    ],
    "seerah": [
        "سيرة",
        "سيره",
        "غزوة",
        "غزوه",
        "هجرة",
        "نبوي",
        "seerah",
        "sirah",
        "prophet",
        "biography",
        "battle",
        "بدر",
        "أحد",
        "الخندق",
        "فتح",
        "مكة",
        "الحديبية",
        "الغزوات",
        "السيرة النبوية",
        " life of",
    ],
    "usul_fiqh": [
        "أصول الفقه",
        "اصول الفقه",
        "قياس",
        "استحسان",
        "استصحاب",
        "usul",
        "fiqh principles",
        "qiyas",
        "istihsan",
        "istishab",
        "القياس",
        "المصلحة",
        "المرسلة",
        "العرف",
        "الشرع",
        "اجتهاد",
        "تقليد",
        "مذهب",
        "خلاف",
    ],
    "history": [
        "تاريخ",
        "historical",
        "دولة",
        "خلافة",
        "حضارة",
        "dynasty",
        "caliphate",
        "empire",
        "islamic history",
        "الخلفاء",
        "الراشدين",
        "الأموي",
        " العباسي",
        "العثماني",
        "معركة",
        "حدث",
        " epoch",
        "عصر",
    ],
    "language": [
        "نحو",
        "صرف",
        "بلاغة",
        "إعراب",
        " morphology",
        "grammar",
        "syntax",
        "rhetoric",
        "arabic language",
        "الصفة",
        "المبتدأ",
        "الخبر",
        "الفعل",
        "الاسم",
        "إعراب",
        "بناء",
        "مفعول",
        "فاعل",
        "مصدر",
    ],
    "tazkiyah": [
        "تزكية",
        "رقاقة",
        "أخلاق",
        "معاملة",
        "的心",
        "tazkiyah",
        "spiritual",
        "character",
        "ethics",
        "morals",
        "صبر",
        "شكر",
        "توبة",
        "إخلاص",
        "رياء",
        "قسوة",
        "الخوف",
        "الرجاء",
        "المحبة",
        "الزهد",
        "الورع",
    ],
    "general": [],  # Default fallback
}


# ============================================================================
# Routing Result
# ============================================================================


@dataclass
class ConfigRoutingDecision:
    """
    Routing decision based on config-backed rules.

    Attributes:
        agent_name: Name of the agent to route to
        confidence: Confidence score for the routing decision
        matched_keywords: List of keywords that matched
        primary_domain: Primary domain detected
    """

    agent_name: str
    confidence: float
    matched_keywords: list[str]
    primary_domain: str


# ============================================================================
# Config-Backed Router
# ============================================================================


class ConfigRouter:
    """
    Rule-based router that uses keyword patterns from config.

    This router:
    1. Uses keyword matching from DOMAIN_KEYWORDS
    2. Supports both Arabic and English keywords
    3. Returns confidence based on keyword matches
    4. Falls back to general_islamic_agent when no match
    """

    # Agent name mapping from domain to agent
    AGENT_MAP: dict[str, str] = {
        "fiqh": "fiqh_agent",
        "hadith": "hadith_agent",
        "tafsir": "tafsir_agent",
        "aqeedah": "aqeedah_agent",
        "seerah": "seerah_agent",
        "usul_fiqh": "usul_fiqh_agent",
        "history": "history_agent",
        "language": "language_agent",
        "tazkiyah": "tazkiyah_agent",
        "general": "general_islamic_agent",
    }

    def __init__(self):
        """Initialize the config router."""
        self._domain_keywords = DOMAIN_KEYWORDS

    def route(self, query: str) -> ConfigRoutingDecision:
        """
        Route a query to the appropriate agent.

        Args:
            query: User query string

        Returns:
            ConfigRoutingDecision with routing info
        """
        query_lower = query.lower()

        # Track matches per domain
        domain_matches: dict[str, list[str]] = {}

        for domain, keywords in self._domain_keywords.items():
            if domain == "general":
                continue

            matched = []
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    matched.append(keyword)

            if matched:
                domain_matches[domain] = matched

        if not domain_matches:
            # No match found - use general agent
            return ConfigRoutingDecision(
                agent_name=self.AGENT_MAP["general"],
                confidence=0.3,
                matched_keywords=[],
                primary_domain="general",
            )

        # Find domain with most matches
        primary_domain = max(domain_matches.keys(), key=lambda d: len(domain_matches[d]))
        matched_keywords = domain_matches[primary_domain]

        # Calculate confidence based on number of matches
        confidence = min(0.3 + (len(matched_keywords) * 0.15), 0.95)

        return ConfigRoutingDecision(
            agent_name=self.AGENT_MAP[primary_domain],
            confidence=confidence,
            matched_keywords=matched_keywords,
            primary_domain=primary_domain,
        )

    def route_multi(self, query: str) -> list[ConfigRoutingDecision]:
        """
        Route to multiple agents if query spans multiple domains.

        Args:
            query: User query string

        Returns:
            List of routing decisions (primary first)
        """
        query_lower = query.lower()

        domain_matches: dict[str, list[str]] = {}

        for domain, keywords in self._domain_keywords.items():
            if domain == "general":
                continue

            matched = [kw for kw in keywords if kw.lower() in query_lower]
            if matched:
                domain_matches[domain] = matched

        if not domain_matches:
            return [self.route(query)]

        # Sort by number of matches
        sorted_domains = sorted(
            domain_matches.keys(),
            key=lambda d: len(domain_matches[d]),
            reverse=True,
        )

        results = []
        for domain in sorted_domains[:3]:  # Max 3 agents
            matched = domain_matches[domain]
            confidence = min(0.3 + (len(matched) * 0.15), 0.95)

            results.append(
                ConfigRoutingDecision(
                    agent_name=self.AGENT_MAP[domain],
                    confidence=confidence,
                    matched_keywords=matched,
                    primary_domain=domain,
                )
            )

        # Add general agent if only 1 match
        if len(results) == 1:
            results.append(
                ConfigRoutingDecision(
                    agent_name=self.AGENT_MAP["general"],
                    confidence=0.2,
                    matched_keywords=[],
                    primary_domain="general",
                )
            )

        return results


# ============================================================================
# Singleton Instance
# ============================================================================


_config_router: Optional[ConfigRouter] = None


def get_config_router() -> ConfigRouter:
    """Get the global config router instance."""
    global _config_router
    if _config_router is None:
        _config_router = ConfigRouter()
    return _config_router


__all__ = [
    "ConfigRouter",
    "ConfigRoutingDecision",
    "get_config_router",
    "DOMAIN_KEYWORDS",
]
