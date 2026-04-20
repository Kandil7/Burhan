"""
Dependency injection container for Athar Islamic QA System.

Provides centralized dependency management with lazy initialization
for all infrastructure and application components.

Phase 9: Added DI container for dependency injection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from src.config.settings import settings

if TYPE_CHECKING:
    from src.infrastructure.llm_client import LLMClient
    from src.indexing.vectorstores.qdrant_store import VectorStore
    from src.indexing.embeddings.embedding_model import EmbeddingModel
    from src.infrastructure.redis import RedisManager
    from src.infrastructure.database import AsyncDatabaseManager
    from src.agents.registry import AgentRegistry


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for Athar application.

    Provides lazy-initialized singletons for all major components.

    Usage:
        container = Container()
        container.config.database_url.from_value(settings.database_url)

        # Get instances
        llm_client = container.llm_client()
        vector_store = container.vector_store()
    """

    # Configuration - loaded from settings
    config.database_url = providers.Configuration(default=settings.database_url)
    config.redis_url = providers.Configuration(default=settings.redis_url)
    config.qdrant_url = providers.Configuration(default=settings.qdrant_url)
    config.openai_api_key = providers.Configuration(default=settings.openai_api_key)
    config.llm_model = providers.Configuration(default=settings.llm_model)
    config.embedding_model = providers.Configuration(default=settings.embedding_model)

    # ==========================================
    # Infrastructure - Singletons
    # ==========================================

    llm_client = providers.Singleton(
        _create_llm_client,
        api_key=config.openai_api_key,
        model=config.llm_model,
    )

    vector_store = providers.Singleton(
        _create_vector_store,
        url=config.qdrant_url,
    )

    embedding_model = providers.Singleton(
        _create_embedding_model,
        model_name=config.embedding_model,
    )

    redis_manager = providers.Singleton(
        _create_redis_manager,
        url=config.redis_url,
    )

    async_database = providers.Singleton(
        _create_async_database,
        url=config.database_url,
    )

    # ==========================================
    # Application - Factories
    # ==========================================

    agent_registry = providers.Factory(
        _create_agent_registry,
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
    )

    # ==========================================
    # Caching
    # ==========================================

    embedding_cache = providers.Singleton(
        _create_embedding_cache,
        redis_manager=redis_manager,
        ttl=settings.embedding_cache_ttl,
    )

    query_cache = providers.Singleton(
        _create_query_cache,
        redis_manager=redis_manager,
        ttl=settings.llm_cache_ttl,
    )


# ==========================================
# Factory functions (imported lazily to avoid circular imports)
# ==========================================


def _create_llm_client(api_key: str, model: str) -> "LLMClient":
    """Create LLM client instance."""
    from src.infrastructure.llm_client import LLMClient

    return LLMClient(api_key=api_key, model=model)


def _create_vector_store(url: str) -> "VectorStore":
    """Create vector store instance."""
    from src.indexing.vector_store import VectorStore

    return VectorStore()


def _create_embedding_model(model_name: str) -> "EmbeddingModel":
    """Create embedding model instance."""
    from src.indexing.embeddings.embedding_model import EmbeddingModel

    return EmbeddingModel(model_name=model_name)


def _create_redis_manager(url: str) -> "RedisManager":
    """Create Redis manager instance."""
    from src.infrastructure.redis import RedisManager

    return RedisManager(url=url)


def _create_async_database(url: str) -> "AsyncDatabaseManager":
    """Create async database manager instance."""
    from src.infrastructure.database import AsyncDatabaseManager

    return AsyncDatabaseManager()


def _create_agent_registry(
    llm_client: "LLMClient",
    vector_store: "VectorStore",
    embedding_model: "EmbeddingModel",
) -> "AgentRegistry":
    """Create agent registry instance."""
    from src.agents.registry import AgentRegistry

    return AgentRegistry(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
    )


def _create_embedding_cache(
    redis_manager: "RedisManager",
    ttl: int,
):
    """Create embedding cache instance."""
    from src.indexing.embeddings.embedding_cache import EmbeddingCache

    return EmbeddingCache(redis_manager=redis_manager, ttl=ttl)


def _create_query_cache(
    redis_manager: "RedisManager",
    ttl: int,
):
    """Create query cache instance."""
    from src.infrastructure.query_cache import QueryCache

    return QueryCache(redis_manager=redis_manager, ttl=ttl)


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


async def initialize_container() -> None:
    """Initialize all container singletons."""
    container = get_container()

    # Initialize infrastructure
    await container.vector_store().initialize()
    await container.redis_manager().initialize()
    await container.async_database().initialize()
    await container.embedding_cache().initialize()

    # Initialize embedding model
    await container.embedding_model().initialize()


async def close_container() -> None:
    """Close all container resources."""
    global _container
    if _container is None:
        return

    # Close caches
    await _container.embedding_cache().close()
    await _container.query_cache().close()

    # Close infrastructure
    await _container.redis_manager().close()
    await _container.async_database().close()

    _container = None
