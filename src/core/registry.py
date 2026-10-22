from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.agents.base import BaseAgent
from src.config.logging_config import get_logger
from src.domain.intents import INTENT_ROUTING, Intent
from src.tools.base import BaseTool

logger = get_logger()


@dataclass
class AgentRegistration:
    """Registration info for an agent or tool."""

    name: str
    instance: BaseAgent | BaseTool | None = None
    factory: Callable[[], BaseAgent | BaseTool] | None = None
    is_agent: bool = True
    intents: list[Intent] = field(default_factory=list)
    description: str = ""


class AgentRegistry:
    """
    Central registry for all agents and tools with Lazy Initialization support.
    """

    def __init__(self) -> None:
        self._registrations: dict[str, AgentRegistration] = {}
        self._initialized = False

    def register_agent(
        self,
        name: str,
        agent: BaseAgent | None = None,
        factory: Callable[[], BaseAgent] | None = None,
        intents: list[Intent] | None = None,
        description: str = "",
    ) -> None:
        if intents is None:
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self._registrations[name] = AgentRegistration(
            name=name,
            instance=agent,
            factory=factory,
            is_agent=True,
            intents=intents,
            description=description,
        )
        logger.info("registry.agent_registered", name=name, lazy=bool(factory))

    def register_tool(
        self,
        name: str,
        tool: BaseTool | None = None,
        factory: Callable[[], BaseTool] | None = None,
        intents: list[Intent] | None = None,
        description: str = "",
    ) -> None:
        if intents is None:
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self._registrations[name] = AgentRegistration(
            name=name,
            instance=tool,
            factory=factory,
            is_agent=False,
            intents=intents,
            description=description,
        )
        logger.info("registry.tool_registered", name=name, lazy=bool(factory))

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get agent by name, initializing if necessary."""
        reg = self._registrations.get(name)
        if not reg or not reg.is_agent:
            return None

        if reg.instance is None and reg.factory:
            logger.info("registry.lazy_init", name=name)
            reg.instance = reg.factory()

        return reg.instance  # type: ignore

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name, initializing if necessary."""
        reg = self._registrations.get(name)
        if not reg:
            return None

        if reg.instance is None and reg.factory:
            logger.info("registry.lazy_init_tool", name=name)
            reg.instance = reg.factory()

        return reg.instance  # type: ignore

    def get_for_intent(self, intent: Intent) -> tuple[BaseAgent | BaseTool | None, bool]:
        """Get agent or tool for an intent with lazy resolution."""
        target = INTENT_ROUTING.get(intent)
        if not target:
            return None, False

        reg = self._registrations.get(target)
        if not reg:
            return None, False

        instance = self.get_agent(target) if reg.is_agent else self.get_tool(target)
        return instance, reg.is_agent

    def get_status(self) -> dict:
        """Get registry status."""
        return {
            "registered": list(self._registrations.keys()),
            "initialized_count": sum(1 for r in self._registrations.values() if r.instance),
            "total": len(self._registrations),
        }

    def names(self, agents: bool) -> list[str]:
        """Registered names for agents or for tools, without building them."""
        return [name for name, reg in self._registrations.items() if reg.is_agent == agents]


# Infrastructure dependencies for the lazy agent factories. The composition
# root (src.composition) sets these at startup; nothing here reaches back into
# the API layer, which used to be the root of the largest import cycle.
_registry_dependencies: dict[str, Any] = {}


def set_registry_dependencies(deps: dict[str, Any]) -> None:
    """Provide the objects the lazy agent factories need to build."""
    global _registry_dependencies
    _registry_dependencies = dict(deps)


# Global registry instance
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = initialize_registry()
    return _registry


def initialize_registry() -> AgentRegistry:
    """Initialize registry with Lazy Injection mappings for V2 Agents."""
    registry = AgentRegistry()

    # Helpers for dependencies
    def get_deps() -> Any:
        return dict(_registry_dependencies)

    # Helpers for lazy instantiation
    def build_zakat() -> Any:
        from src.tools.zakat_calculator import ZakatCalculator

        return ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)

    def build_inheritance() -> Any:
        from src.tools.inheritance_calculator import InheritanceCalculator

        return InheritanceCalculator()

    def build_prayer() -> Any:
        from src.tools.prayer_times_tool import PrayerTimesTool

        return PrayerTimesTool()

    def build_hijri() -> Any:
        from src.tools.hijri_calendar_tool import HijriCalendarTool

        return HijriCalendarTool()

    def build_dua() -> Any:
        from src.tools.dua_retrieval_tool import DuaRetrievalTool

        return DuaRetrievalTool()

    # Register tools lazily
    registry.register_tool("zakat_tool", factory=build_zakat)
    registry.register_tool("inheritance_tool", factory=build_inheritance)
    registry.register_tool("prayer_tool", factory=build_prayer)
    registry.register_tool("hijri_tool", factory=build_hijri)
    registry.register_tool("dua_tool", factory=build_dua)

    # Register collection agents lazily: one spec-driven RAGPipeline per
    # config/agents/<name>.yaml (hardening Phase 5).
    def build_pipeline(spec_name: str) -> Any:
        def factory() -> Any:
            from src.agents.pipeline import RAGPipeline
            from src.agents.spec_loader import load_all_agent_specs

            deps = get_deps()
            spec = load_all_agent_specs()[spec_name]
            return RAGPipeline(
                spec=spec,
                search=deps.get("vector_store"),
                embed=deps.get("embedding_model"),
                llm_client=deps.get("llm_client"),
            )

        return factory

    agent_registry_names = {
        "fiqh_agent": "fiqh",
        "hadith_agent": "hadith",
        "general_islamic_agent": "general",
        "seerah_agent": "seerah",
        "tafsir_agent": "tafsir",
        "aqeedah_agent": "aqeedah",
        "usul_fiqh_agent": "usul_fiqh",
        "history_agent": "history",
        "language_agent": "language",
        "tazkiyah_agent": "tazkiyah",
    }
    for registry_name, spec_name in agent_registry_names.items():
        registry.register_agent(registry_name, factory=build_pipeline(spec_name))

    def build_chatbot() -> Any:
        from src.agents.chatbot_agent import ChatbotAgent

        return ChatbotAgent()

    registry.register_agent("chatbot_agent", factory=build_chatbot)

    registry._initialized = True
    logger.info("registry.initialized.v2")
    return registry
