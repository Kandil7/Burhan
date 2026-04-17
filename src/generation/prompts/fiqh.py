# Fiqh Prompt Module
"""Prompts for Fiqh (Islamic jurisprudence) responses."""

from typing import Dict, Any, Optional


FIQH_SYSTEM_PROMPT = """You are an expert in Islamic Fiqh (jurisprudence).
Your responses should:
- Be based on the four major Sunni schools (Hanafi, Maliki, Shafi, Hanbali)
- Reference primary sources (Quran, hadith) where applicable
- Distinguish between clear evidences and scholarly opinions
- Present differences of opinion when they exist
- Be accurate and well-grounded in Islamic scholarship"""


FIQH_USER_PROMPT_TEMPLATE = """Based on the following context and question, provide a scholarly answer about Islamic law and jurisprudence.

Question: {question}

Context:
{context}

Provide a detailed answer based on Islamic Fiqh principles."""


def get_fiqh_prompt(
    question: str,
    context: str,
    school: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a Fiqh-specific prompt."""
    user_prompt = FIQH_USER_PROMPT_TEMPLATE.format(
        question=question,
        context=context,
    )

    # Add school-specific instruction if provided
    if school:
        user_prompt += f"\n\nPlease present the view of the {school} school if there are differing opinions."

    return {
        "system": FIQH_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "domain": "fiqh",
            "school": school,
        },
    }


# Fiqh-specific keywords for routing
FIQH_KEYWORDS = [
    "fiqh",
    "jurisprudence",
    "حكم",
    "فتوى",
    "مذهب",
    "prayer",
    "salat",
    "صلاة",
    "fasting",
    "صوم",
    "zakat",
    "زكاة",
    "hajj",
    "حج",
    "umrah",
    "عمرة",
    "nikah",
    "marriage",
    "طلاق",
    "divorce",
    "inheritance",
    "مواريث",
    "transactions",
    "معاملات",
    "buying",
    "selling",
    "بيع",
    "شراء",
]
