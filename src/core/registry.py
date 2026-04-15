"""
Agent Registry for Athar Islamic QA System.

Manages registration and retrieval of agents and tools.
Following Single Responsibility Principle - separates registration logic from orchestration.
"""

from dataclasses import dataclass, field

from src.agents.base import BaseAgent
from src.config.intents import INTENT_ROUTING, Intent
from src.config.logging_config import get_logger
from src.tools.base import BaseTool

logger = get_logger()


@dataclass
class AgentRegistration:
    """Registration info for an agent or tool."""

    name: str
    instance: BaseAgent | BaseTool
    is_agent: bool
    intents: list[Intent] = field(default_factory=list)
    description: str = ""


class AgentRegistry:
    """
    Central registry for all agents and tools.

    Provides:
    - Registration of agents and tools
    - Lookup by name
    - Lookup by intent
    - Status reporting

    Usage:
        registry = AgentRegistry()
        registry.register_agent("fiqh_agent", FiqhAgent(...))
        registry.register_tool("zakat_tool", ZakatCalculator(...))

        # Get by name
        agent = registry.get_agent("fiqh_agent")

        # Get by intent
        agent = registry.get_agent_for_intent(Intent.FIQH)
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.tools: dict[str, BaseTool] = {}
        self._registrations: dict[str, AgentRegistration] = {}
        self._initialized = False

    def register_agent(self, name: str, agent: BaseAgent, intents: list[Intent] = None, description: str = ""):
        """
        Register an agent.

        Args:
            name: Agent name (e.g., "fiqh_agent")
            agent: Agent instance
            intents: List of intents this agent handles
            description: Agent description
        """
        if intents is None:
            # Auto-detect from INTENT_ROUTING
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self.agents[name] = agent
        self._registrations[name] = AgentRegistration(
            name=name, instance=agent, is_agent=True, intents=intents, description=description
        )

        logger.info("registry.agent_registered", name=name, intents=[i.value for i in intents])

    def register_tool(self, name: str, tool: BaseTool, intents: list[Intent] = None, description: str = ""):
        """
        Register a tool.

        Args:
            name: Tool name (e.g., "zakat_tool")
            tool: Tool instance
            intents: List of intents this tool handles
            description: Tool description
        """
        if intents is None:
            # Auto-detect from INTENT_ROUTING
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self.tools[name] = tool
        self._registrations[name] = AgentRegistration(
            name=name, instance=tool, is_agent=False, intents=intents, description=description
        )

        logger.info("registry.tool_registered", name=name, intents=[i.value for i in intents])

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get agent by name."""
        return self.agents.get(name)

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self.tools.get(name)

    def get_for_intent(self, intent: Intent) -> tuple[BaseAgent | BaseTool | None, bool]:
        """
        Get agent or tool for an intent.

        Args:
            intent: The intent to look up

        Returns:
            Tuple of (instance, is_agent)
        """
        target = INTENT_ROUTING.get(intent)
        if not target:
            return None, False

        # Try agents first
        if target in self.agents:
            return self.agents[target], True

        # Then tools
        if target in self.tools:
            return self.tools[target], False

        return None, False

    def is_available(self, name: str) -> bool:
        """Check if agent or tool is available."""
        return name in self.agents or name in self.tools

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_status(self) -> dict:
        """Get registry status."""
        return {
            "agents": list(self.agents.keys()),
            "tools": list(self.tools.keys()),
            "total": len(self.agents) + len(self.tools),
            "initialized": self._initialized,
        }


# Global registry instance
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get global agent registry instance. Auto-initializes if not yet initialized."""
    global _registry
    if _registry is None or not _registry._initialized:
        _registry = initialize_registry()
    return _registry


def initialize_registry() -> AgentRegistry:
    """
    Initialize registry with all agents and tools.

    Call this during application startup.
     Refactoring: Added all RAG agents (FiqhAgent, HadithAgent, GeneralIslamicAgent, SeerahAgent)
    """
    global _registry
    _registry = AgentRegistry()

    # Import and register tools
    from src.tools.dua_retrieval_tool import DuaRetrievalTool
    from src.tools.hijri_calendar_tool import HijriCalendarTool
    from src.tools.inheritance_calculator import InheritanceCalculator
    from src.tools.prayer_times_tool import PrayerTimesTool
    from src.tools.zakat_calculator import ZakatCalculator

    # Register tools
    _registry.register_tool("zakat_tool", ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9))
    _registry.register_tool("inheritance_tool", InheritanceCalculator())
    _registry.register_tool("prayer_tool", PrayerTimesTool())
    _registry.register_tool("hijri_tool", HijriCalendarTool())
    _registry.register_tool("dua_tool", DuaRetrievalTool())

    # Import and register agents
    from src.agents.chatbot_agent import ChatbotAgent
    _registry.register_agent("chatbot_agent", ChatbotAgent())

    #  Register RAG agents
    try:
        from src.agents.fiqh_agent import FiqhAgent
        _registry.register_agent("fiqh_agent", FiqhAgent())
        logger.info("registry.fiqh_agent_registered")
    except Exception as e:
        logger.warning("registry.fiqh_agent_registration_failed", error=str(e))

    try:
        from src.agents.hadith_agent import HadithAgent
        _registry.register_agent("hadith_agent", HadithAgent())
        logger.info("registry.hadith_agent_registered")
    except Exception as e:
        logger.warning("registry.hadith_agent_registration_failed", error=str(e))

    try:
        from src.agents.general_islamic_agent import GeneralIslamicAgent
        _registry.register_agent("general_islamic_agent", GeneralIslamicAgent())
        logger.info("registry.general_agent_registered")
    except Exception as e:
        logger.warning("registry.general_agent_registration_failed", error=str(e))

    try:
        from src.agents.seerah_agent import SeerahAgent
        _registry.register_agent("seerah_agent", SeerahAgent())
        logger.info("registry.seerah_agent_registered")
    except Exception as e:
        logger.warning("registry.seerah_agent_registration_failed", error=str(e))

    _registry._initialized = True
    logger.info("registry.initialized", status=_registry.get_status())

    return _registry
