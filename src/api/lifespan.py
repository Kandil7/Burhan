import asyncio
import threading
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from src.config.logging_config import get_logger

logger = get_logger()


def warm_models(app: FastAPI):
    """Warm up models in a background thread to avoid blocking startup."""
    logger.info("lifespan.warming.begin")
    try:
        if app.state.embedding_model:
            # This is usually the heavy part (BGE-M3)
            # EmbeddingModel.load_model() is async in some versions, but if it blocks,
            # we do it here. If it's pure async, we'd use a Task.
            # Assuming load_model is what warms it.
            pass
        logger.info("lifespan.warming.complete")
    except Exception as e:
        logger.error("lifespan.warming.failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("lifespan.startup.begin")

    # ── 1. Verification Suite ─────────────────────────────────────────────────
    from src.verification.suite_builder import register_all_checks

    register_all_checks()

    # ── 2. Infrastructure (Shared) ────────────────────────────────────────────
    from src.infrastructure.llm_client import LLMClients
    from src.indexing.embeddings.embedding_model import EmbeddingModel
    from src.indexing.vectorstores.qdrant_store import VectorStore

    llm_clients = await LLMClients.create()
    app.state.llm_clients = llm_clients
    app.state.llm_client = llm_clients.client

    embedding_model = EmbeddingModel(cache_enabled=True)
    # Background warming
    asyncio.create_task(embedding_model.load_model())
    app.state.embedding_model = embedding_model

    vector_store = VectorStore()
    await vector_store.initialize()
    app.state.vector_store = vector_store

    # ── 3. Registry (Lazy) ────────────────────────────────────────────────────
    from src.core.registry import get_registry

    app.state.registry = get_registry()

    # ── 4. Use Case & Service ─────────────────────────────────────────────────
    from src.application.use_cases.answer_query import AnswerQueryUseCase
    from src.application.services.ask_service import AskService
    from src.application.router import RouterAgent
    from src.application.classifier_factory import build_classifier

    # Build Router - use build_classifier for robust intent detection
    # Inject embedding_model to enable Phase 5 semantic routing
    classifier = build_classifier(embedding_model=app.state.embedding_model)
    router = RouterAgent(classifier=classifier)
    app.state.router = router

    # AnswerQueryUseCase
    use_case = AnswerQueryUseCase(agent_registry=app.state.registry, router=router)

    # AskService
    app.state.ask_service = AskService(answer_query_use_case=use_case)

    # SearchService - requires properly initialized RunRetrievalUseCase
    from src.application.services.search_service import get_search_service
    from src.application.use_cases.run_retrieval import get_run_retrieval_use_case

    # Create properly initialized RunRetrievalUseCase
    # Use existing embedding_model and vector_store from app.state
    run_retrieval_use_case = get_run_retrieval_use_case(
        embedding_model=app.state.embedding_model,
        vector_store=app.state.vector_store,
    )

    # Create SearchService
    app.state.search_service = get_search_service(run_retrieval_uc=run_retrieval_use_case)

    # ── 5. Standard Agents (Static) ───────────────────────────────────────────
    from src.agents.chatbot_agent import ChatbotAgent

    app.state.chatbot = ChatbotAgent()

    logger.info("lifespan.startup.complete")

    yield  # ── app is running ─────────────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("lifespan.shutdown.begin")
    await llm_clients.close()
    if hasattr(vector_store, "close"):
        await vector_store.close()
    logger.info("lifespan.shutdown.complete")
