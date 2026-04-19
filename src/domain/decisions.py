# Decisions Domain Module
"""Domain model for query routing and agent selection decisions."""

from typing import Optional, List, Dict, Any
from enum import Enum


class DecisionType(str, Enum):
    """Types of routing decisions."""

    AGENT_SELECTION = "agent_selection"
    COLLECTION_SELECTION = "collection_selection"
    RETRIEVAL_STRATEGY = "retrieval_strategy"
    VERIFICATION_MODE = "verification_mode"
    RESPONSE_MODE = "response_mode"


class ResponseMode(str, Enum):
    """Final response modes for the system."""

    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class Decision:
    """Represents a routing decision."""

    def __init__(
        self,
        decision_type: DecisionType,
        value: Any,
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
    ):
        self.decision_type = decision_type
        self.value = value
        self.confidence = confidence
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return f"Decision({self.decision_type.value}={self.value!r}, confidence={self.confidence})"


class AgentDecision(Decision):
    """Decision about which agent to use."""

    def __init__(
        self,
        agent_id: str,
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
    ):
        super().__init__(
            decision_type=DecisionType.AGENT_SELECTION,
            value=agent_id,
            confidence=confidence,
            reasoning=reasoning,
        )


class CollectionDecision(Decision):
    """Decision about which collections to query."""

    def __init__(
        self,
        collection_ids: List[str],
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
    ):
        super().__init__(
            decision_type=DecisionType.COLLECTION_SELECTION,
            value=collection_ids,
            confidence=confidence,
            reasoning=reasoning,
        )


class ResponseModeDecision(Decision):
    """Decision about the final response mode."""

    def __init__(
        self,
        mode: ResponseMode,
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
    ):
        super().__init__(
            decision_type=DecisionType.RESPONSE_MODE,
            value=mode.value,
            confidence=confidence,
            reasoning=reasoning,
        )
