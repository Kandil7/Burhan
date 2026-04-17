# Hadith Prompt Module
"""Prompts for Hadith responses."""

from typing import Dict, Any, Optional


HADITH_SYSTEM_PROMPT = """You are an expert in Hadith literature and sciences.
Your responses should:
- Reference authentic hadith collections (Bukhari, Muslim, etc.)
- Mention the grade of hadith (Sahih, Hasan, Daif)
- Provide proper attribution (book, number, narrator chain)
- Explain the meaning and context of hadith
- Be precise about hadith grading and authenticity"""


HADITH_USER_PROMPT_TEMPLATE = """Based on the following hadith sources and question, provide a scholarly answer.

Question: {question}

Hadith Sources:
{sources}

Provide a detailed explanation of the hadith, its authenticity, and its implications."""


def get_hadith_prompt(
    question: str,
    sources: str,
    collection: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a Hadith-specific prompt."""
    user_prompt = HADITH_USER_PROMPT_TEMPLATE.format(
        question=question,
        sources=sources,
    )

    # Add collection-specific instruction if provided
    if collection:
        user_prompt += f"\n\nFocus primarily on the {collection} collection."

    return {
        "system": HADITH_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "domain": "hadith",
            "collection": collection,
        },
    }


# Hadith-specific keywords for routing
HADITH_KEYWORDS = [
    "hadith",
    "حديث",
    "sunnah",
    "سنة",
    "prophet",
    "نبي",
    "rasul",
    "رسول",
    "sahabi",
    "صحابي",
    "tabei",
    "تابعين",
    "sahih",
    "صحيح",
    "hasan",
    "حسن",
    "daif",
    "ضعيف",
    "bukhari",
    "مسلم",
    "abu dawud",
    "nasai",
    "ibn majah",
    "tirmidhi",
    "hadith grading",
    "science of hadith",
    "علم الحديث",
]
