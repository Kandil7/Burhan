# Clarification Composer Module
"""Compose clarification requests."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ClarificationType(str, Enum):
    """Types of clarification requests."""

    AMBIGUOUS_INTENT = "ambiguous_intent"
    MULTIPLE_TOPICS = "multiple_topics"
    MISSING_CONTEXT = "missing_context"
    TOPIC_CHANGE = "topic_change"
    NEEDS_MORE_INFO = "needs_more_info"


@dataclass
class ClarificationOption:
    """Option for user to clarify."""

    option_id: str
    text: str
    example: Optional[str] = None


@dataclass
class ClarificationConfig:
    """Configuration for clarification."""

    max_options: int = 4
    include_examples: bool = True


class ClarificationComposer:
    """Composes clarification requests."""

    def __init__(self, config: Optional[ClarificationConfig] = None):
        self.config = config or ClarificationConfig()

    def compose(
        self,
        clarification_type: ClarificationType,
        options: Optional[List[ClarificationOption]] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compose a clarification request."""
        # Get template for type
        template = self._get_template(clarification_type)

        # Add custom message if provided
        if message:
            body = f"{template}\n\n{message}"
        else:
            body = template

        # Add options if provided
        response_options = []
        if options:
            for opt in options[: self.config.max_options]:
                response_options.append(
                    {
                        "id": opt.option_id,
                        "text": opt.text,
                        "example": opt.example if self.config.include_examples else None,
                    }
                )

        return {
            "mode": "clarify",
            "clarification_type": clarification_type.value,
            "message": body,
            "options": response_options,
        }

    def _get_template(self, clarification_type: ClarificationType) -> str:
        """Get template for clarification type."""
        templates = {
            ClarificationType.AMBIGUOUS_INTENT: (
                "Your question could have multiple meanings. Could you please clarify what you mean?"
            ),
            ClarificationType.MULTIPLE_TOPICS: (
                "Your question covers multiple topics. Which would you like me to address first?"
            ),
            ClarificationType.MISSING_CONTEXT: (
                "I need more context to answer this question accurately. Could you provide more details?"
            ),
            ClarificationType.TOPIC_CHANGE: (
                "It seems you've changed topics. Would you like me to address this new topic?"
            ),
            ClarificationType.NEEDS_MORE_INFO: ("To give you an accurate answer, I need some additional information."),
        }
        return templates.get(
            clarification_type,
            "Could you please provide more details?",
        )


# Default composer instance
clarification_composer = ClarificationComposer()
