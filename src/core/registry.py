from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.agents.base import BaseAgent
from src.config.logging_config import get_logger
from src.domain.intents import INTENT_ROUTING, Intent
from src.tools.base import BaseTool

logger = get_logger()


@dataclass
class AgentRegistration:
    """Registration info for an agent or tool."""

    name: str
    instance: Optional[Union[BaseAgent, BaseTool]] = None
    factory: Optional[Callable[[], Union[BaseAgent, BaseTool]]] = None
    is_agent: bool = True
    intents: List[Intent] = field(default_factory=list)
    description: str = ""


class AgentRegistry:
    """
    Central registry for all agents and tools with Lazy Initialization support.
    """

    def __init__(self) -> None:
        self._registrations: Dict[str, AgentRegistration] = {}
        self._initialized = False

    def register_agent(
        self,
        name: str,
        agent: Optional[BaseAgent] = None,
        factory: Optional[Callable[[], BaseAgent]] = None,
        intents: Optional[List[Intent]] = None,
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
        tool: Optional[BaseTool] = None,
        factory: Optional[Callable[[], BaseTool]] = None,
        intents: Optional[List[Intent]] = None,
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

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name, initializing if necessary."""
        reg = self._registrations.get(name)
        if not reg or not reg.is_agent:
            return None

        if reg.instance is None and reg.factory:
            logger.info("registry.lazy_init", name=name)
            reg.instance = reg.factory()

        return reg.instance  # type: ignore

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name, initializing if necessary."""
        reg = self._registrations.get(name)
        if not reg or reg.is_agent:
            return None

        if reg.instance is None and reg.factory:
            logger.info("registry.lazy_init_tool", name=name)
            reg.instance = reg.factory()

        return reg.instance  # type: ignore

    def get_for_intent(self, intent: Intent) -> Tuple[Optional[Union[BaseAgent, BaseTool]], bool]:
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


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = initialize_registry()
    return _registry


def initialize_registry() -> AgentRegistry:
    """Initialize registry with Lazy Injection mappings."""
    registry = AgentRegistry()

    # Helpers for lazy instantiation
    def build_zakat():
        from src.tools.zakat_calculator import ZakatCalculator
        return ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)

    def build_inheritance():
        from src.tools.inheritance_calculator import InheritanceCalculator
        return InheritanceCalculator()

    def build_prayer():
        from src.tools.prayer_times_tool import PrayerTimesTool
        return PrayerTimesTool()

    def build_hijri():
        from src.tools.hijri_calendar_tool import HijriCalendarTool
        return HijriCalendarTool()

    def build_dua():
        from src.tools.dua_retrieval_tool import DuaRetrievalTool
        return DuaRetrievalTool()

    # Register tools lazily
    registry.register_tool("zakat_tool", factory=build_zakat)
    registry.register_tool("inheritance_tool", factory=build_inheritance)
    registry.register_tool("prayer_tool", factory=build_prayer)
    registry.register_tool("hijri_tool", factory=build_hijri)
    registry.register_tool("dua_tool", factory=build_dua)

    # Register Agents lazily
    def build_fiqh():
        from src.agents.collection import FiqhCollectionAgent
        return FiqhCollectionAgent()

    def build_hadith():
        from src.agents.collection import HadithCollectionAgent
        return HadithCollectionAgent()

    def build_general():
        from src.agents.collection import GeneralCollectionAgent
        return GeneralCollectionAgent()

    def build_seerah():
        from src.agents.collection import SeerahCollectionAgent
        return SeerahCollectionAgent()

    registry.register_agent("fiqh_agent", factory=build_fiqh)
    registry.register_agent("hadith_agent", factory=build_hadith)
    registry.register_agent("general_islamic_agent", factory=build_general)
    registry.register_agent("seerah_agent", factory=build_seerah)

    registry._initialized = True
    logger.info("registry.initialized.lazy")
    return registry
