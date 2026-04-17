# Application Router Module
"""
Router module for query routing and classification.

This module includes:
- RouterAgent: Main routing agent
- Multi-agent orchestration: For complex queries requiring multiple agents
- Various classifiers: Hybrid, Keyword-based, LLM-based
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.router.router_agent import RouterAgent
    from src.application.router.hybrid_classifier import HybridIntentClassifier
    from src.application.router.classifier_factory import ClassifierFactory
    from src.application.router.risk_policy import RiskPolicy

# Re-export from local modules for backwards compatibility
from src.application.router.router_agent import (
    RouterAgent,
    router_agent,
    get_router_agent,
    init_router_agent,
    SimpleRoutingDecision,
)

# Re-export from orchestration module
from src.application.router.orchestration import (
    OrchestrationPattern,
    AgentTask,
    OrchestrationPlan,
    create_orchestration_plan,
    MultiAgentOrchestrator,
    route_via_decision_tree,
    PRIMARY_THRESHOLD,
    SECONDARY_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
)

# Re-export from multi_agent module
from src.application.router.multi_agent import (
    MultiAgentRouter,
    create_multi_agent_router,
)


# These are lazy-loaded to avoid circular imports
def __getattr__(name):
    if name == "HybridIntentClassifier":
        from src.application.router.hybrid_classifier import HybridIntentClassifier

        return HybridIntentClassifier
    if name == "ClassifierFactory":
        from src.application.router.classifier_factory import ClassifierFactory

        return ClassifierFactory
    if name == "classifier_factory":
        from src.application.router.classifier_factory import classifier_factory

        return classifier_factory
    if name == "build_classifier":
        from src.application.router.classifier_factory import build_classifier

        return build_classifier
    if name == "QueryClassifier":
        from src.application.router.classifier_factory import QueryClassifier

        return QueryClassifier
    if name == "KeywordBasedClassifier":
        from src.application.router.classifier_factory import KeywordBasedClassifier

        return KeywordBasedClassifier
    if name == "LLMBasedClassifier":
        from src.application.router.classifier_factory import LLMBasedClassifier

        return LLMBasedClassifier
    if name == "RiskPolicy":
        from src.application.router.risk_policy import RiskPolicy

        return RiskPolicy
    if name == "risk_policy":
        from src.application.router.risk_policy import risk_policy

        return risk_policy
    if name == "RiskLevel":
        from src.application.router.risk_policy import RiskLevel

        return RiskLevel
    if name == "RiskAssessment":
        from src.application.router.risk_policy import RiskAssessment

        return RiskAssessment
    if name == "SENSITIVE_PATTERNS":
        from src.application.router.risk_policy import SENSITIVE_PATTERNS

        return SENSITIVE_PATTERNS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Router agent
    "RouterAgent",
    "router_agent",
    "get_router_agent",
    "init_router_agent",
    "SimpleRoutingDecision",
    # Orchestration
    "OrchestrationPattern",
    "AgentTask",
    "OrchestrationPlan",
    "create_orchestration_plan",
    "MultiAgentOrchestrator",
    "route_via_decision_tree",
    "PRIMARY_THRESHOLD",
    "SECONDARY_THRESHOLD",
    "LOW_CONFIDENCE_THRESHOLD",
    # Multi-agent router
    "MultiAgentRouter",
    "create_multi_agent_router",
    # Lazy-loaded exports
    "HybridIntentClassifier",
    "ClassifierFactory",
    "classifier_factory",
    "build_classifier",
    "QueryClassifier",
    "KeywordBasedClassifier",
    "LLMBasedClassifier",
    "RiskPolicy",
    "risk_policy",
    "RiskLevel",
    "RiskAssessment",
    "SENSITIVE_PATTERNS",
]
