# Abstain Prompt Module
"""Prompts for abstention responses."""

from typing import Dict, Any, Optional


ABSTAIN_SYSTEM_PROMPT = """You are a responsible AI assistant that knows its limitations.
When you cannot provide a reliable answer, you should:
- Clearly state why you cannot answer
- Be honest about uncertainty
- Suggest alternatives when possible
- Never make up information
- Recommend consulting experts when appropriate"""


ABSTAIN_USER_PROMPT_TEMPLATE = """The system cannot provide a reliable answer to this question.

Question: {question}

Reason for abstention: {reason}

Generate an appropriate abstention response that:
- Explains why the answer cannot be provided
- Is helpful and respectful
- Suggests alternatives if possible"""


# Reasons for abstention
ABSTENTION_REASONS = {
    "out_of_scope": "This question is outside my area of expertise",
    "unverifiable": "I cannot verify the accuracy of this information",
    "harmful": "This question could lead to harm",
    "uncertain": "I am not certain about the correct answer",
    "sensitive": "This is a sensitive topic requiring expert handling",
    "no_sources": "I could not find reliable sources to base an answer on",
}


def get_abstain_prompt(
    question: str,
    reason: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """Get an abstention prompt."""
    reason_description = ABSTENTION_REASONS.get(reason, reason)

    user_prompt = ABSTAIN_USER_PROMPT_TEMPLATE.format(
        question=question,
        reason=reason_description,
    )

    if details:
        user_prompt += f"\n\nAdditional details: {details}"

    return {
        "system": ABSTAIN_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "mode": "abstain",
            "reason": reason,
        },
    }


# Alternative suggestions by reason
ALTERNATIVE_SUGGESTIONS = {
    "out_of_scope": "You might try asking about Islamic topics such as Quran, hadith, fiqh, or Islamic history.",
    "uncertain": "For accurate information on this matter, please consult with a qualified Islamic scholar.",
    "unverifiable": "I recommend verifying this information with authoritative Islamic sources or scholars.",
}
