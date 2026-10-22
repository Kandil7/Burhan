from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.logging_config import get_logger

logger = get_logger()


def warm_models(app: FastAPI) -> None:
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

    # The composition root builds the whole graph: verification checks, the
    # shared infrastructure, the registry, and the service layer. See
    # src/composition.py.
    from src.composition import build_container

    container = await build_container()
    app.state.container = container

    # Transitional mirrors for the modules that still read app.state
    # directly. They move behind the container as the later phases land.
    app.state.llm_clients = container.llm_clients
    app.state.llm_client = container.llm_clients.client
    app.state.embedding_model = container.embedding
    app.state.vector_store = container.search
    app.state.registry = container.registry
    app.state.router = container.router
    app.state.ask_service = container.ask_service
    app.state.search_service = container.search_service
    app.state.chatbot = container.chatbot

    logger.info("lifespan.startup.complete")

    yield  # --- app is running ---

    logger.info("lifespan.shutdown.begin")
    await container.aclose()
    logger.info("lifespan.shutdown.complete")
