# Answer Policy Module
"""Policies for controlling answer generation."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class AnswerMode(str, Enum):
    """Modes for answer generation."""

    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


@dataclass
class AnswerPolicyConfig:
    """Configuration for answer policy."""

    min_confidence: float = 0.7
    require_verification: bool = True
    max_clarification_attempts: int = 2
    abstain_on_uncertainty: bool = False


class AnswerPolicy:
    """Policy for controlling answer generation."""

    def __init__(self, config: Optional[AnswerPolicyConfig] = None):
        self.config = config or AnswerPolicyConfig()

    def determine_mode(
        self,
        confidence: float,
        verification_passed: bool,
        can_clarify: bool = True,
    ) -> AnswerMode:
        """
        Determine the appropriate response mode.

        Args:
            confidence: Confidence score for the answer
            verification_passed: Whether verification passed
            can_clarify: Whether clarification is possible

        Returns:
            AnswerMode to use
        """
        # If verification failed, abstain
        if self.config.require_verification and not verification_passed:
            return AnswerMode.ABSTAIN

        # If confidence is too low, either clarify or abstain
        if confidence < self.config.min_confidence:
            if can_clarify and not self.config.abstain_on_uncertainty:
                return AnswerMode.CLARIFY
            return AnswerMode.ABSTAIN

        # Otherwise, provide answer
        return AnswerMode.ANSWER

    def should_clarify(self, confidence: float) -> bool:
        """Check if clarification should be requested."""
        return (
            confidence < self.config.min_confidence and confidence >= 0.5  # Not completely uncertain
        )

    def should_abstain(self, confidence: float) -> bool:
        """Check if the system should abstain."""
        return confidence < 0.5 or (self.config.abstain_on_uncertainty and confidence < self.config.min_confidence)

    def get_confidence_threshold(self) -> float:
        """Get the minimum confidence threshold."""
        return self.config.min_confidence


# Default policy instance
answer_policy = AnswerPolicy()
