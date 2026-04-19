# Tafsir Prompt Module
"""Prompts for Tafsir (Quranic exegesis) responses."""

from typing import Dict, Any, Optional


TAFSIR_SYSTEM_PROMPT = """You are an expert in Quranic exegesis (Tafsir).
Your responses should:
- Explain Quranic verses with their meanings
- Reference classical tafsirs (Ibn Kathir, Jalalayn, etc.)
- Provide Arabic text of verses when relevant
- Explain context (asbab al-nuzul) when applicable
- Discuss linguistic and rhetorical aspects
- Present multiple scholarly interpretations when appropriate"""


TAFSIR_USER_PROMPT_TEMPLATE = """Based on the following Quranic verses and question, provide a scholarly tafsir.

Question: {question}

Quranic Verses:
{verses}

Provide a detailed explanation based on classical Quranic exegesis."""


def get_tafsir_prompt(
    question: str,
    verses: str,
    tafsir_source: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a Tafsir-specific prompt."""
    user_prompt = TAFSIR_USER_PROMPT_TEMPLATE.format(
        question=question,
        verses=verses,
    )

    # Add tafsir source preference if provided
    if tafsir_source:
        user_prompt += f"\n\nReference the {tafsir_source} tafsir where relevant."

    return {
        "system": TAFSIR_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "domain": "tafsir",
            "source": tafsir_source,
        },
    }


# Tafsir-specific keywords for routing
TAFSIR_KEYWORDS = [
    "tafsir",
    "تفسير",
    "quran",
    "قرآن",
    "verse",
    "آية",
    "aya",
    "surah",
    "سورة",
    "book",
    "chapter",
    "revelation",
    "نزول",
    "ibn kathir",
    "jalalayn",
    "tabari",
    "qurtubi",
    "zikr",
    "asbab al-nuzul",
    "context",
    "occasion of revelation",
    "meanings",
    "interpretation",
    "exegesis",
]
