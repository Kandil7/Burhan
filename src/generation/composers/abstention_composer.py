# Abstention Composer Module
"""Compose abstention responses."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class AbstentionReason(str, Enum):
    """Reasons for abstention."""

    OUT_OF_SCOPE = "out_of_scope"
    UNVERIFIABLE = "unverifiable"
    HARMFUL = "harmful"
    UNCERTAIN = "uncertain"
    SENSITIVE = "sensitive"


@dataclass
class AbstentionConfig:
    """Configuration for abstention."""

    include_alternative: bool = True
    suggest_alternative: bool = True


class AbstentionComposer:
    """Composes abstention responses."""

    def __init__(self, config: Optional[AbstentionConfig] = None):
        self.config = config or AbstentionConfig()

    def compose(
        self,
        reason: AbstentionReason,
        query: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compose an abstention response."""
        # Get template for reason
        template = self._get_template(reason)

        # Add custom message if provided
        if message:
            body = f"{template}\n\n{message}"
        else:
            body = template

        # Add alternative suggestion if enabled
        alternative = None
        if self.config.suggest_alternative:
            alternative = self._get_alternative_suggestion(reason, query)

        return {
            "mode": "abstain",
            "reason": reason.value,
            "message": body,
            "alternative": alternative,
        }

    def _get_template(self, reason: AbstentionReason) -> str:
        """Get template for abstention reason."""
        templates = {
            AbstentionReason.OUT_OF_SCOPE: (
                "This question is outside my area of expertise. "
                "I'm designed to answer questions about Islamic sciences "
                "and related topics."
            ),
            AbstentionReason.UNVERIFIABLE: (
                "I cannot provide a verified answer to this question as I couldn't find sufficient reliable sources."
            ),
            AbstentionReason.HARMFUL: ("I'm sorry, but I cannot answer this question as it may lead to harm."),
            AbstentionReason.UNCERTAIN: (
                "I'm not certain about the answer to this question. "
                "For accurate information, please consult with a qualified scholar."
            ),
            AbstentionReason.SENSITIVE: (
                "This is a sensitive topic that requires careful consideration. "
                "I recommend consulting with a knowledgeable scholar."
            ),
        }
        return templates.get(
            reason,
            "I'm unable to answer this question at this time.",
        )

    def _get_alternative_suggestion(
        self,
        reason: AbstentionReason,
        query: str,
    ) -> Optional[str]:
        """Get alternative suggestion based on reason."""
        if reason == AbstentionReason.OUT_OF_SCOPE:
            return "You might try asking about Quran, hadith, fiqh, Islamic history, or other Islamic topics."
        elif reason == AbstentionReason.UNCERTAIN:
            return "Please consult with a qualified Islamic scholar for reliable guidance on this matter."
        return None


# Default composer instance
abstention_composer = AbstentionComposer()
