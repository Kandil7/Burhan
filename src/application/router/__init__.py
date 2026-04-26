"""
Application Router Module - Consolidated.

This module provides:
- RouterAgent: Main routing agent
- Multi-agent orchestration
- Intent classification (Hybrid, Keyword, Embedding)
- Risk policy for content moderation

This is the CANONICAL router module - use this for all routing needs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

# Re-export core components
from src.application.router.router_agent import (
    RouterAgent,
    router_agent,
    get_router_agent,
    init_router_agent,
    SimpleRoutingDecision,
)

# Re-export classification
from src.application.router.classifier_factory import (
    KeywordBasedClassifier,
    MasterHybridClassifier,
    HybridIntentClassifier,
    ClassifierFactory,
    INTENT_KEYWORDS,
    classifier_factory,
    QueryClassifier,
)
from src.domain.intents import normalize_arabic, detect_language

# Re-export embedding classifier
from src.application.router.embedding_classifier import EmbeddingClassifier

# Re-export orchestration
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

# Re-export multi-agent
from src.application.router.multi_agent import (
    MultiAgentRouter,
    create_multi_agent_router,
)

# Re-export risk policy
from src.application.router.risk_policy import (
    RiskPolicy,
    risk_policy,
    RiskLevel,
    RiskAssessment,
    SENSITIVE_PATTERNS,
)

# Re-export intent router (canonical)
from src.application.routing.intent_router import (
    IntentRouter,
    get_intent_router,
    INTENT_TO_AGENT,
)

# Re-export planner and executor
from src.application.routing.planner import QueryPlan, QueryPlanner
from src.application.routing.executor import ExecutionResult, AgentExecutor


__all__ = [
    # Router agent
    "RouterAgent",
    "router_agent",
    "get_router_agent",
    "init_router_agent",
    "SimpleRoutingDecision",
    # Classification
    "QueryClassifier",
    "KeywordBasedClassifier",
    "EmbeddingClassifier",
    "MasterHybridClassifier",
    "HybridIntentClassifier",
    "ClassifierFactory",
    "classifier_factory",
    "normalize_arabic",
    "detect_language",
    "INTENT_KEYWORDS",
    # Intent routing
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
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
    # Multi-agent
    "MultiAgentRouter",
    "create_multi_agent_router",
    # Risk policy
    "RiskPolicy",
    "risk_policy",
    "RiskLevel",
    "RiskAssessment",
    "SENSITIVE_PATTERNS",
    # Planning & execution
    "QueryPlan",
    "QueryPlanner",
    "ExecutionResult",
    "AgentExecutor",
]


# Build classifier function - for app initialization
def build_classifier(embedding_model=None):
    """Build the default classifier (hybrid with optional embedding)."""
    from src.application.classifier_factory import build_classifier as _build

    return _build(embedding_model)
