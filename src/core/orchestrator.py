"""
Response Orchestrator for Athar Islamic QA system.

Main orchestrator that:
1. Receives classified queries from the router
2. Routes to appropriate agents/tools
3. Assembles final responses with citations
4. Handles fallback and error cases

This is the central coordination point for the multi-agent system.
Phase 2: All tools registered and functional.
"""

from typing import Optional

from src.config.intents import Intent, INTENT_ROUTING
from src.config.logging_config import get_logger
from src.agents.base import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    Citation,
)
from src.tools.base import BaseTool, ToolOutput

logger = get_logger()


class ResponseOrchestrator:
    """
    Main orchestrator that routes queries to appropriate agents/tools.

    The orchestrator:
    1. Receives query with classified intent
    2. Looks up target agent/tool from routing map
    3. Executes agent/tool with appropriate parameters
    4. Assembles final response with citations and metadata

    Phase 1: Basic routing (agents/tools not yet implemented)
    Phase 2+: Full agent execution with RAG, calculators, etc.

    Usage:
        orchestrator = ResponseOrchestrator()
        orchestrator.register_agent("fiqh_agent", FiqhAgent())
        orchestrator.register_tool("zakat_tool", ZakatCalculator())

    Phase 2: Full agent execution with calculators and tools

    Usage:
        orchestrator = ResponseOrchestrator()
        result = await orchestrator.route_query(
            query="ما حكم الصلاة؟",
            intent=Intent.FIQH,
            language="ar"
        )
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.tools: dict[str, BaseTool] = {}
        self._register_default_fallbacks()

    def _register_default_fallbacks(self):
        """Register default fallback agents and all Phase 2-4 tools."""
        # Phase 2: Register all tools
        from src.tools.zakat_calculator import ZakatCalculator
        from src.tools.inheritance_calculator import InheritanceCalculator
        from src.tools.prayer_times_tool import PrayerTimesTool
        from src.tools.hijri_calendar_tool import HijriCalendarTool
        from src.tools.dua_retrieval_tool import DuaRetrievalTool
        from src.agents.chatbot_agent import ChatbotAgent

        # Register tools (Phase 2)
        self.register_tool("zakat_tool", ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9))
        self.register_tool("inheritance_tool", InheritanceCalculator())
        self.register_tool("prayer_tool", PrayerTimesTool())
        self.register_tool("hijri_tool", HijriCalendarTool())
        self.register_tool("dua_tool", DuaRetrievalTool())

        # Register chatbot agent (Phase 2)
        self.register_agent("chatbot_agent", ChatbotAgent())

        # Phase 3-4: Register RAG agents if dependencies available
        # Track whether RAG actually initialized successfully
        self._rag_initialized = self._register_rag_agents()

        # If RAG agents failed to initialize, use chatbot as fallback
        # for general knowledge queries instead of failing completely
        if not self._rag_initialized:
            logger.warning("orchestrator.rag_agents_unavailable", using_fallback="chatbot_agent")
            self._rag_fallback_to_chatbot = True
        else:
            self._rag_fallback_to_chatbot = False

        logger.info(
            "orchestrator.agents_registered",
            tools=["zakat_tool", "inheritance_tool", "prayer_tool", "hijri_tool", "dua_tool"],
            agents=list(self.agents.keys()),
            rag_available=self._rag_initialized,
            rag_fallback=self._rag_fallback_to_chatbot,
        )

    def _register_rag_agents(self) -> bool:
        """Conditionally register RAG agents if dependencies available.

        Returns True if RAG agents initialized successfully, False otherwise.
        """
        # First check if transformers can actually load the model
        try:
            from transformers import AutoModel, AutoTokenizer

            # Quick test - just check if we can import without errors
            logger.info("orchestrator.transformers_available")
        except ImportError:
            logger.warning(
                "orchestrator.transformers_unavailable",
                reason="transformers not installed. Install with: pip install transformers",
            )
            return False

        # Also check torch
        try:
            import torch

            logger.info("orchestrator.torch_available", version=torch.__version__)
        except ImportError:
            logger.warning("orchestrator.torch_unavailable")
            return False

        try:
            from src.agents.fiqh_agent import FiqhAgent
            from src.agents.general_islamic_agent import GeneralIslamicAgent

            # Try to initialize embedding model and test it
            try:
                from src.knowledge.embedding_model import EmbeddingModel

                embedding_model = EmbeddingModel()
                # Try to actually load the model to verify it works
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, create a task
                        import concurrent.futures

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, embedding_model.load_model())
                            future.result()
                    else:
                        asyncio.run(embedding_model.load_model())
                except Exception as model_load_error:
                    logger.warning("orchestrator.embedding_model_load_failed", error=str(model_load_error))
                    return False

                from src.knowledge.vector_store import VectorStore

                vector_store = VectorStore()

                # Register Fiqh agent
                self.register_agent("fiqh_agent", FiqhAgent(embedding_model=embedding_model, vector_store=vector_store))

                # Register General Islamic agent
                self.register_agent(
                    "general_islamic_agent",
                    GeneralIslamicAgent(embedding_model=embedding_model, vector_store=vector_store),
                )

                logger.info("orchestrator.rag_agents_registered", agents=["fiqh_agent", "general_islamic_agent"])
                return True  # RAG initialized successfully
            except Exception as e:
                # RAG components exist but failed to initialize
                logger.warning("orchestrator.rag_components_init_error", error=str(e), fallback_to_chatbot=True)
                return False  # RAG failed to initialize

        except ImportError as e:
            logger.warning(
                "orchestrator.rag_agents_unavailable",
                reason=f"Import error: {str(e)}",
            )
            return False  # RAG not available

    def register_agent(self, name: str, agent: BaseAgent):
        """
        Register an agent with the orchestrator.

        Args:
            name: Agent name (e.g., "fiqh_agent")
            agent: Agent instance
        """
        self.agents[name] = agent
        logger.info("orchestrator.agent_registered", name=name)

    def register_tool(self, name: str, tool: BaseTool):
        """
        Register a tool with the orchestrator.

        Args:
            name: Tool name (e.g., "zakat_tool")
            tool: Tool instance
        """
        self.tools[name] = tool
        logger.info("orchestrator.tool_registered", name=name)

    async def route_query(
        self,
        query: str,
        intent: Intent,
        language: str = "ar",
        location: Optional[dict] = None,
        madhhab: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgentOutput:
        """
        Route query to appropriate agent/tool based on intent.

        Args:
            query: User's question
            intent: Classified intent
            language: Response language
            location: Location data (for prayer times, qibla)
            madhhab: Islamic school of jurisprudence
            session_id: Session ID for conversation context

        Returns:
            AgentOutput with answer, citations, and metadata
        """
        target = INTENT_ROUTING.get(intent)

        # If RAG agents are not available, fallback to chatbot_agent for general intents
        if not target:
            logger.warning("orchestrator.unknown_intent", intent=intent.value, query=query[:100])
            return await self._fallback_response(query, "Unknown intent")

        # For FIQH and ISLAMIC_KNOWLEDGE intents, route to RAG agents if available
        requires_rag = intent in [Intent.FIQH, Intent.ISLAMIC_KNOWLEDGE]

        if requires_rag and self._rag_initialized:
            # RAG is available, keep original target (fiqh_agent or general_islamic_agent)
            logger.info("orchestrator.using_rag", intent=intent.value, target=target)
        else:
            # RAG not available, fallback to chatbot
            target = "chatbot_agent"
            logger.info(
                "orchestrator.using_chatbot_fallback", intent=intent.value, reason=f"rag_init={self._rag_initialized}"
            )

        logger.info(
            "orchestrator.routing",
            intent=intent.value,
            target=target,
            language=language,
            rag_initialized=self._rag_initialized,
        )

        # ==========================================
        # Route to agent
        # ==========================================
        if target in self.agents:
            logger.warning(f"EXECUTING AGENT: {target} (rag_init={self._rag_initialized})")
            agent = self.agents[target]
            try:
                result = await agent.execute(
                    AgentInput(
                        query=query,
                        language=language,
                        metadata={
                            "location": location,
                            "madhhab": madhhab,
                            "session_id": session_id,
                        },
                    )
                )

                # Check if result indicates RAG failure and fallback is needed
                # Fallback if: RAG agent was used AND there was an error AND RAG fallback is enabled
                is_rag_agent = target in ["fiqh_agent", "general_islamic_agent"]
                has_error = result.metadata.get("error") or "embedding" in result.answer.lower()

                if is_rag_agent and has_error and self._rag_fallback_to_chatbot:
                    logger.info("orchestrator.rag_runtime_fallback", original_agent=target)
                    # Fallback to chatbot
                    fallback_agent = self.agents.get("chatbot_agent")
                    if fallback_agent:
                        return await fallback_agent.execute(
                            AgentInput(
                                query=query,
                                language=language,
                                metadata={
                                    "fallback": "rag_failed",
                                    "location": location,
                                    "madhhab": madhhab,
                                    "session_id": session_id,
                                },
                            )
                        )

                # Add agent name to metadata
                result.metadata["agent"] = target

                return result

            except Exception as e:
                logger.error("orchestrator.agent_error", agent=target, error=str(e), exc_info=True)
                return await self._fallback_response(query, f"Agent error: {str(e)}")

        # ==========================================
        # Route to tool
        # ==========================================
        elif target in self.tools:
            tool = self.tools[target]
            try:
                result = await tool.execute(
                    query=query, language=language, location=location, madhhab=madhhab, session_id=session_id
                )

                if result.success:
                    # Format tool result as AgentOutput
                    answer = self._format_tool_result(result.result)
                    return AgentOutput(
                        answer=answer,
                        metadata={
                            "tool": target,
                            **result.metadata,
                        },
                    )
                else:
                    return await self._fallback_response(query, f"Tool error: {result.error}")

            except Exception as e:
                logger.error("orchestrator.tool_error", tool=target, error=str(e), exc_info=True)
                return await self._fallback_response(query, f"Tool error: {str(e)}")

        # ==========================================
        # Fallback: Agent/tool not implemented
        # ==========================================
        else:
            logger.warning("orchestrator.not_implemented", target=target, intent=intent.value)
            return await self._fallback_response(query, f"Feature not yet implemented: {target}")

    def _format_tool_result(self, result: dict) -> str:
        """Format tool result dictionary into readable text."""
        import json

        # For Phase 2, return JSON-formatted string
        # Phase 4: Will use LLM to format naturally
        return json.dumps(result, indent=2, ensure_ascii=False)

    async def _fallback_response(self, query: str, reason: str) -> AgentOutput:
        """
        Generate fallback response when routing fails.

        Args:
            query: Original user query
            reason: Reason for fallback

        Returns:
            AgentOutput with apologetic message
        """
        return AgentOutput(
            answer=(
                "أعتذر، لم أتمكن من معالجة سؤالك بشكل كامل في الوقت الحالي. "
                "هذا النوع من الأسئلة يتطلب مكونات لم يتم تنفيذها بعد في النظام.\n\n"
                "Please try asking about:\n"
                "- Islamic rulings (fiqh)\n"
                "- Quran verses or surahs\n"
                "- Zakat calculation\n"
                "- Inheritance distribution\n"
                "- Prayer times\n"
                "- Islamic dates\n"
                "- Duas and adhkar"
            ),
            citations=[],
            metadata={
                "agent": "fallback",
                "error": reason,
                "requires_implementation": True,
            },
            confidence=0.0,
            requires_human_review=True,
        )
