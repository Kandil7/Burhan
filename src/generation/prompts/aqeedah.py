# Aqeedah Prompt Module
"""Prompts for Aqeedah (Islamic creed) responses."""

from typing import Dict, Any, Optional


AQEEDAH_SYSTEM_PROMPT = """You are an expert in Islamic Theology (Aqeedah).
Your responses should:
- Be based on the Quran and authentic Sunnah
- Follow the creed of the Salaf (early scholars)
- Explain the attributes of Allah correctly
- Discuss matters of faith (Iman) comprehensively
- Address theological matters with precision
- Avoid innovation (bid'ah) in beliefs"""


AQEEDAH_USER_PROMPT_TEMPLATE = """Based on the following sources and question, provide a scholarly answer about Islamic creed.

Question: {question}

Sources:
{sources}

Provide a detailed explanation based on Islamic Aqeedah."""


def get_aqeedah_prompt(
    question: str,
    sources: str,
    focus: Optional[str] = None,
) -> Dict[str, Any]:
    """Get an Aqeedah-specific prompt."""
    user_prompt = AQEEDAH_USER_PROMPT_TEMPLATE.format(
        question=question,
        sources=sources,
    )

    # Add focus area if provided
    if focus:
        user_prompt += f"\n\nFocus particularly on the aspect of {focus}."

    return {
        "system": AQEEDAH_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "domain": "aqeedah",
            "focus": focus,
        },
    }


# Aqeedah-specific keywords for routing
AQEEDAH_KEYWORDS = [
    "aqeedah",
    "عقيدة",
    "creed",
    "belief",
    "faith",
    "إيمان",
    "tawhid",
    "توحيد",
    "shirk",
    "شرك",
    "polytheism",
    "islam",
    "إسلام",
    "iman",
    "إيمان",
    "ihsan",
    "إحسان",
    "attributes",
    "asma",
    "asma allah",
    "صفات الله",
    "allah",
    "الله",
    "god",
    "رب",
    "rububiyyah",
    "prophethood",
    "risalah",
    "رسالة",
    "messenger",
    "predestination",
    "qadar",
    "قدر",
    "divine decree",
    "hereafter",
    "akhirah",
    "آخراة",
    "paradise",
    "hell",
]
