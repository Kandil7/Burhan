"""
Application lifespan management for Athar Islamic QA system.

Builds all shared singletons once at startup and attaches to app.state.
This is the only place that constructs infrastructure objects.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.config.logging_config import get_logger

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Build all shared singletons once at startup and attach to app.state.

    This is the only place that constructs infrastructure objects.
    Imports are local so startup failure is explicit, not silent.
    """
    logger.info("lifespan.startup.begin")

    # ========================================
    # Chatbot Agent (always needed)
    # ========================================
    from src.agents.chatbot_agent import ChatbotAgent

    app.state.chatbot = ChatbotAgent()
    logger.info("lifespan.chatbot.initialised")

    # ========================================
    # Classifier (by backend)
    # ========================================
    try:
        from src.application.classifier_factory import build_classifier
        from src.application.router import RouterAgent

        classifier = build_classifier()
        app.state.classifier = RouterAgent(classifier=classifier)
        logger.info(
            "lifespan.classifier.initialised",
            classifier_type=type(classifier).__name__,
        )
    except Exception as e:
        logger.warning(
            "lifespan.classifier.failed",
            error=str(e),
            falling_back="hybrid",
        )
        # Fall back to hybrid classifier
        from src.application.hybrid_classifier import HybridIntentClassifier
        from src.application.router import RouterAgent

        classifier = HybridIntentClassifier(low_conf_threshold=0.55)
        app.state.classifier = RouterAgent(classifier=classifier)
        logger.info("lifespan.classifier.fallback.hybrid")

    # ========================================
    # Agent Registry (always needed)
    # ========================================
    from src.core.registry import build_registry

    app.state.registry = build_registry()
    logger.info(
        "lifespan.startup.complete",
        registry_status=app.state.registry.get_status(),
    )

    yield  # app is running

    # ========================================
    # Cleanup on shutdown
    # ========================================
    logger.info("lifespan.shutdown.begin")

    # Close classifier if it has cleanup method
    if hasattr(app.state.classifier, "close"):
        await app.state.classifier.close()

    logger.info("lifespan.shutdown.complete")


# ========================================
# Helper functions for dependency injection
# ========================================


def get_chatbot(app: FastAPI) -> ChatbotAgent:
    """Get chatbot from app state."""
    return app.state.chatbot


def get_classifier(app: FastAPI) -> RouterAgent:
    """Get classifier router from app state."""
    return app.state.classifier


def get_registry(app: FastAPI):
    """Get agent registry from app state."""
    return app.state.registry
