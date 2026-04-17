"""
Application lifespan management for Athar Islamic QA system.

Single source of truth for all infrastructure construction.
Everything is injected — no agent builds its own dependencies.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from fastapi import FastAPI
from src.config.logging_config import get_logger

if TYPE_CHECKING:
    from src.agents.chatbot_agent import ChatbotAgent
    from src.application.router import RouterAgent
    from src.core.registry import AgentRegistry

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("lifespan.startup.begin")

    # ── 1. LLM Clients ────────────────────────────────────────────────────────
    from src.infrastructure.llm_client import LLMClients

    llm_clients = await LLMClients.create()
    app.state.llm_clients = llm_clients
    app.state.llm_client = llm_clients.client  # For RAG endpoints
    logger.info("lifespan.llm.initialised")

    # ── 2. Chatbot Agent ──────────────────────────────────────────────────────
    from src.agents.chatbot_agent import ChatbotAgent

    app.state.chatbot = ChatbotAgent()
    logger.info("lifespan.chatbot.initialised")

    # ── 3. Classifier + Router ────────────────────────────────────────────────
    try:
        from src.application.classifier_factory import build_classifier
        from src.application.router.router_agent import RouterAgent

        classifier = build_classifier()
    except Exception as e:
        logger.warning("lifespan.classifier.failed", error=str(e), falling_back="hybrid")
        from src.application.hybrid_classifier import HybridIntentClassifier
        from src.application.router.router_agent import RouterAgent

        classifier = HybridIntentClassifier(low_conf_threshold=0.55)

    app.state.router = RouterAgent(classifier=classifier)
    logger.info(
        "lifespan.classifier.initialised",
        classifier_type=type(classifier).__name__,
    )

    # ── 4. Embedding Model + Vector Store ─────────────────────────────────────
    embedding_model = None
    vector_store = None

    try:
        from src.knowledge.embedding_model import EmbeddingModel
        from src.knowledge.vector_store import VectorStore

        embedding_model = EmbeddingModel(cache_enabled=True)
        await embedding_model.load_model()
        logger.info("lifespan.embedding.initialised")

        vector_store = VectorStore()
        await vector_store.initialize()
        logger.info("lifespan.vector_store.initialised")

    except Exception as e:
        logger.warning("lifespan.rag_infra.failed", error=str(e))

    app.state.embedding_model = embedding_model
    app.state.vector_store = vector_store

    # ── 5. RAG Agents ─────────────────────────────────────────────────────────────
    _rag_kwargs = dict(
        embedding_model=embedding_model,
        vector_store=vector_store,
        llm_client=llm_clients.client,
    )

    from src.agents.fiqh_agent import FiqhAgent
    from src.agents.general_islamic_agent import GeneralIslamicAgent
    from src.agents.hadith_agent import HadithAgent
    from src.agents.seerah_agent import SeerahAgent

    try:
        app.state.fiqh_agent = FiqhAgent(**_rag_kwargs)
        app.state.general_agent = GeneralIslamicAgent(**_rag_kwargs)
        app.state.hadith_agent = HadithAgent(**_rag_kwargs)
        app.state.seerah_agent = SeerahAgent(**_rag_kwargs)
        logger.info("lifespan.rag_agents.initialised")
    except Exception as e:
        logger.warning("lifespan.rag_agents.failed", error=str(e))
        app.state.fiqh_agent = app.state.general_agent = app.state.hadith_agent = app.state.seerah_agent = None

    # ── 6. Tools + Registry ───────────────────────────────────────────────────────
    from src.core.registry import AgentRegistry
    from src.tools.zakat_calculator import ZakatCalculator
    from src.tools.inheritance_calculator import InheritanceCalculator
    from src.tools.prayer_times_tool import PrayerTimesTool
    from src.tools.hijri_calendar_tool import HijriCalendarTool
    from src.tools.dua_retrieval_tool import DuaRetrievalTool

    registry = AgentRegistry()

    # Tools — لا تحتاج embedding
    registry.register_tool("zakat_tool", ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9))
    registry.register_tool("inheritance_tool", InheritanceCalculator())
    registry.register_tool("prayer_tool", PrayerTimesTool())
    registry.register_tool("hijri_tool", HijriCalendarTool())
    registry.register_tool("dua_tool", DuaRetrievalTool())

    # RAG Agents — محقونة بالـ embedding_model
    if app.state.fiqh_agent:
        registry.register_agent("fiqh_agent", app.state.fiqh_agent)
    if app.state.general_agent:
        registry.register_agent("general_islamic_agent", app.state.general_agent)
    if app.state.hadith_agent:
        registry.register_agent("hadith_agent", app.state.hadith_agent)
    if app.state.seerah_agent:
        registry.register_agent("seerah_agent", app.state.seerah_agent)

    app.state.registry = registry
    logger.info("lifespan.startup.complete", registry_status=registry.get_status())

    yield  # ── app is running ─────────────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("lifespan.shutdown.begin")

    if hasattr(app.state, "llm_clients"):
        await app.state.llm_clients.close()
        logger.info("lifespan.llm.closed")

    if vector_store and hasattr(vector_store, "close"):
        await vector_store.close()
        logger.info("lifespan.vector_store.closed")

    if hasattr(classifier, "close"):
        await classifier.close()

    logger.info("lifespan.shutdown.complete")


# ── Dependency helpers (TYPE_CHECKING avoids circular imports) ────────────────


def get_chatbot_from_state(app: FastAPI) -> "ChatbotAgent":
    return app.state.chatbot


def get_router_from_state(app: FastAPI) -> "RouterAgent":
    return app.state.router


def get_registry_from_state(app: FastAPI) -> "AgentRegistry":
    return app.state.registry
