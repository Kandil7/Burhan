"""
Answer Policy Module for Athar Islamic QA system.

Determines the final response mode (answer, clarify, abstain) 
based on confidence and verification status.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class AnswerMode(str, Enum):
    """Modes for response generation."""
    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class AnswerPolicy:
    """
    Policy engine to decide how to respond to a user query.
    
    Rules:
    1. If no verified evidence exists -> ABSTAIN.
    2. If verification failed -> ABSTAIN.
    3. If confidence is very low -> CLARIFY or ABSTAIN.
    """

    def __init__(
        self, 
        min_confidence: float = 0.65, 
        abstain_threshold: float = 0.4
    ):
        self.min_confidence = min_confidence
        self.abstain_threshold = abstain_threshold

    def determine_mode(
        self,
        confidence: float,
        verification_passed: bool,
        has_evidence: bool = True,
    ) -> AnswerMode:
        """
        Determine the appropriate response mode.
        """
        # Rule 1: No evidence = No answer
        if not has_evidence:
            return AnswerMode.ABSTAIN

        # Rule 2: Explicit verification failure
        if not verification_passed:
            return AnswerMode.ABSTAIN

        # Rule 3: Low confidence handling
        if confidence < self.abstain_threshold:
            return AnswerMode.ABSTAIN
            
        if confidence < self.min_confidence:
            return AnswerMode.CLARIFY

        return AnswerMode.ANSWER
