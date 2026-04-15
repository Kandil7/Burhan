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
    # LLM Clients (always needed)
    # ========================================
    from src.infrastructure.llm_client import LLMClients

    llm_clients = await LLMClients.create()
    app.state.llm_clients = llm_clients
    # Also expose as llm_client for RAG routes (use .client property)
    app.state.llm_client = llm_clients.client
    logger.info("lifespan.llm.initialised")

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
        # Store as 'router' for consistency with classification route
        app.state.router = RouterAgent(classifier=classifier)
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
        app.state.router = RouterAgent(classifier=classifier)
        logger.info("lifespan.classifier.fallback.hybrid")

    # ========================================
    # Vector Store & Embedding Model (for RAG)
    # ========================================
    try:
        from src.knowledge.embedding_model import EmbeddingModel
        from src.knowledge.vector_store import VectorStore

        embedding_model = EmbeddingModel(cache_enabled=True)
        await embedding_model.load_model()
        app.state.embedding_model = embedding_model
        logger.info("lifespan.embedding.initialised")

        vector_store = VectorStore()
        await vector_store.initialize()
        app.state.vector_store = vector_store
        logger.info("lifespan.vector_store.initialised")
    except Exception as e:
        logger.warning("lifespan.rag_init_failed", error=str(e))
        app.state.embedding_model = None
        app.state.vector_store = None

    # ========================================
    # RAG Agents (Fiqh & General Islamic)
    # ========================================
    try:
        from src.agents.fiqh_agent import FiqhAgent
        from src.agents.general_islamic_agent import GeneralIslamicAgent

        app.state.fiqh_agent = FiqhAgent()
        app.state.general_agent = GeneralIslamicAgent()
        logger.info("lifespan.rag_agents.initialised")
    except Exception as e:
        logger.warning("lifespan.rag_agents_failed", error=str(e))
        app.state.fiqh_agent = None
        app.state.general_agent = None

    # ========================================
    # Agent Registry (always needed)
    # ========================================
    from src.core.registry import get_registry

    app.state.registry = get_registry()
    logger.info(
        "lifespan.startup.complete",
        registry_status=app.state.registry.get_status(),
    )

    yield  # app is running

    # ========================================
    # Cleanup on shutdown
    # ========================================
    logger.info("lifespan.shutdown.begin")

    # Close LLM clients
    if hasattr(app.state, "llm_clients"):
        await app.state.llm_clients.close()

    # Close classifier if it has cleanup method
    if hasattr(app.state, "classifier") and hasattr(app.state.classifier, "close"):
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
