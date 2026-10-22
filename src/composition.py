"""
Composition root: the only place that wires concrete adapters to the
application.

Everything under src/ is a layer; this module is the seam that stands above
them and may import any of them. Only the API lifespan calls it. It replaces
the three former wiring points: the lazy factories in ``src.core.registry``,
the construction block in ``src.api.lifespan``, and the per-route helpers.

The container exposes the four ports from ``src.application.ports`` and the
services the routes still use directly. The plan behind it is
docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md, Phase 3.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from src.application.ports import EmbeddingPort, LLMPort, ToolPort, VectorSearchPort
from src.config.settings import Settings
from src.config.settings import settings as default_settings


class _RegistryView(Mapping[str, Any]):
    """Lazy name-to-object view over the registry, preserving lazy builds."""

    def __init__(self, registry: Any, *, agents: bool) -> None:
        self._registry = registry
        self._agents = agents

    def __getitem__(self, name: str) -> Any:
        value = self._registry.get_agent(name) if self._agents else self._registry.get_tool(name)
        if value is None:
            raise KeyError(name)
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._registry.names(agents=self._agents))

    def __len__(self) -> int:
        return len(self._registry.names(agents=self._agents))


@dataclass(frozen=True)
class Container:
    """The application object graph, built once at startup."""

    settings: Settings

    # The four ports. Concrete clients satisfy them structurally today.
    embedding: EmbeddingPort
    search: VectorSearchPort
    llm: LLMPort
    tools: Mapping[str, ToolPort]
    agents: Mapping[str, Any]

    # Services the routes and use cases still consume directly.
    registry: Any
    router: Any
    answer_query: Any
    ask_service: Any
    search_service: Any
    chatbot: Any

    # Concrete lifecycle handle for shutdown and the transitional app.state
    # mirrors. Same object as ``llm``.
    llm_clients: Any

    async def aclose(self) -> None:
        """Release the shared clients this container built."""
        close_llm = getattr(self.llm_clients, "close", None)
        if close_llm is not None:
            await close_llm()
        close_search = getattr(self.search, "close", None)
        if close_search is not None:
            await close_search()


async def build_container(settings: Settings | None = None) -> Container:
    """Build the whole application graph and return it.

    Startup order mirrors the old lifespan exactly: verification checks,
    then shared infrastructure, then the registry, then the routing and
    service layer.
    """
    from src.agents.chatbot_agent import ChatbotAgent
    from src.application.classifier_factory import build_classifier
    from src.application.router import RouterAgent
    from src.application.services.ask_service import AskService
    from src.application.services.search_service import get_search_service
    from src.application.use_cases.answer_query import AnswerQueryUseCase
    from src.application.use_cases.run_retrieval import get_run_retrieval_use_case
    from src.core.registry import get_registry, set_registry_dependencies
    from src.indexing.embeddings.embedding_model import EmbeddingModel
    from src.indexing.vectorstores.qdrant_store import VectorStore
    from src.infrastructure.llm_client import LLMClients
    from src.verification.suite_builder import register_all_checks

    resolved = settings or default_settings

    register_all_checks()

    # The exact-quote check validates Quran quotations through its port; the
    # adapter is the only thing allowed to open the database for it.
    from src.adapters.quran_validator import QuranQuotationAdapter
    from src.verification.checks.exact_quote import exact_quote_verifier

    exact_quote_verifier.set_quran_validator(QuranQuotationAdapter())

    llm_clients = await LLMClients.create()
    embedding_model = EmbeddingModel(cache_enabled=True)
    # Warm the embedding model in the background; it is heavy to load.
    asyncio.create_task(embedding_model.load_model())
    vector_store = VectorStore()
    await vector_store.initialize()

    # The lazy agent factories in the registry take these three objects.
    set_registry_dependencies(
        {
            "embedding_model": embedding_model,
            "vector_store": vector_store,
            "llm_client": llm_clients.client,
        }
    )
    registry = get_registry()

    classifier = build_classifier(embedding_model=None)
    router = RouterAgent(classifier=classifier)
    answer_query = AnswerQueryUseCase(agent_registry=registry, router=router)
    ask_service = AskService(answer_query_use_case=answer_query)

    run_retrieval = get_run_retrieval_use_case(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )
    search_service = get_search_service(run_retrieval_uc=run_retrieval)

    return Container(
        settings=resolved,
        embedding=embedding_model,
        search=vector_store,
        llm=llm_clients,
        tools=_RegistryView(registry, agents=False),
        agents=_RegistryView(registry, agents=True),
        registry=registry,
        router=router,
        answer_query=answer_query,
        ask_service=ask_service,
        search_service=search_service,
        chatbot=ChatbotAgent(),
        llm_clients=llm_clients,
    )
