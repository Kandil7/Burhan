# Clarify Prompt Module
"""Prompts for clarification requests."""

from typing import Dict, Any, List, Optional


CLARIFY_SYSTEM_PROMPT = """You are helping clarify user intent when questions are ambiguous.
Your goal is to:
- Identify the specific ambiguity in the question
- Provide clear options for the user to choose from
- Ask follow-up questions that help narrow down the intent
- Be helpful and patient in the clarification process"""


CLARIFY_USER_PROMPT_TEMPLATE = """The user's question is ambiguous and needs clarification.

Original Question: {question}

Detected Ambiguities:
{ambiguities}

Generate clarification options to help the user specify their intent."""


# Types of ambiguities that might need clarification
AMBIGUITY_TYPES = {
    "topic": "The question covers multiple topics",
    "scope": "The scope of the question is unclear",
    "context": "Missing context needed to answer accurately",
    "reference": "The reference/source is unclear",
    "intent": "The user's intent is unclear",
}


def get_clarify_prompt(
    question: str,
    ambiguities: List[str],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get a clarification prompt."""
    ambiguity_descriptions = [AMBIGUITY_TYPES.get(amb, amb) for amb in ambiguities]

    user_prompt = CLARIFY_USER_PROMPT_TEMPLATE.format(
        question=question,
        ambiguities="\n".join(f"- {a}" for a in ambiguity_descriptions),
    )

    return {
        "system": CLARIFY_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "mode": "clarify",
            "ambiguity_types": ambiguities,
        },
    }


# Example clarification options by type
CLARIFICATION_OPTIONS = {
    "topic": [
        "Please tell me which topic you'd like to focus on: [topic1] or [topic2]",
        "Your question covers multiple areas. Which would you like me to address?",
    ],
    "scope": [
        "Are you looking for a brief answer or a detailed explanation?",
        "Would you like the general rule or specific details?",
    ],
    "context": [
        "Can you provide more context about your situation?",
        "Who is this question for?",
    ],
}
