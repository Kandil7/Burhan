"""
Response Orchestrator for Athar Islamic QA system.

Main orchestrator that:
1. Receives classified queries from the router
2. Routes to appropriate agents/tools
3. Assembles final responses with citations
4. Handles fallback and error cases

This is the central coordination point for the multi-agent system.
Phase 5: Uses AgentRegistry for cleaner separation of concerns.
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
from src.core.registry import AgentRegistry, get_registry, initialize_registry

logger = get_logger()


class ResponseOrchestrator:
    """
    Main orchestrator that routes queries to appropriate agents/tools.

    The orchestrator:
    1. Receives query with classified intent
    2. Looks up target agent/tool from registry
    3. Executes agent/tool with appropriate parameters
    4. Assembles final response with citations and metadata

    Phase 5: Uses AgentRegistry for better separation of concerns.

    Usage:
        orchestrator = ResponseOrchestrator()
        result = await orchestrator.route_query(
            query="ما حكم الصلاة؟",
            intent=Intent.FIQH,
            language="ar"
        )
    """

    def __init__(self, use_registry: bool = True):
        """
        Initialize orchestrator.

        Args:
            use_registry: Whether to use the global registry (recommended)
        """
        # ALWAYS initialize registry first, before anything else
        initialize_registry()
        
        if use_registry:
            # Use global registry
            self.registry = get_registry()
            self._ensure_initialized()
        else:
            # Create local registry for this instance
            self.registry = AgentRegistry()
            self._register_default_fallbacks()

        # RAG availability tracking
        self._rag_initialized = False
        self._rag_fallback_to_chatbot = False

        # Check RAG availability (runs async when event loop starts)
        import asyncio
        try:
            asyncio.get_running_loop()
            # We're in an async context, schedule the check
            asyncio.create_task(self._check_rag_availability())
        except RuntimeError:
            # No running loop yet, will be checked on first request
            logger.info("orchestrator.rag_check_deferred")

    def _ensure_initialized(self):
        """Ensure registry is initialized with base agents and tools."""
        if not self.registry._initialized:
            # Reinitialize the global registry with all base agents and tools
            initialize_registry()
            # Update our reference to use the newly initialized registry
            self.registry = get_registry()

    async def _check_rag_availability(self):
        """Check if RAG agents are available."""
        # Check if transformers can actually load the model
        try:
            from transformers import AutoModel, AutoTokenizer

            logger.info("orchestrator.transformers_available")
        except ImportError:
            logger.warning(
                "orchestrator.transformers_unavailable",
                reason="transformers not installed. Install with: pip install transformers",
            )
            self._rag_initialized = False
            return

        # Check torch
        try:
            import torch

            logger.info("orchestrator.torch_available", version=torch.__version__)
        except ImportError:
            logger.warning("orchestrator.torch_unavailable")
            self._rag_initialized = False
            return

        # Try to initialize RAG agents
        self._rag_initialized = await self._register_rag_agents()

        if not self._rag_initialized:
            logger.warning("orchestrator.rag_agents_unavailable", using_fallback="chatbot_agent")
            self._rag_fallback_to_chatbot = True

    def _register_default_fallbacks(self):
        """Register default fallback agents and all Phase 2-4 tools."""
        if self.registry._initialized:
            return

        initialize_registry()

    async def _register_rag_agents(self) -> bool:
        """Conditionally register RAG agents if dependencies available."""
        try:
            from src.agents.fiqh_agent import FiqhAgent
            from src.agents.general_islamic_agent import GeneralIslamicAgent
            from src.agents.hadith_agent import HadithAgent
            from src.agents.tafsir_agent import TafsirAgent
            from src.agents.aqeedah_agent import AqeedahAgent
            from src.agents.seerah_agent import SeerahAgent
            from src.agents.islamic_history_agent import IslamicHistoryAgent
            from src.agents.fiqh_usul_agent import FiqhUsulAgent
            from src.agents.arabic_language_agent import ArabicLanguageAgent
            from src.agents.sanadset_hadith_agent import SanadsetHadithAgent
            from src.knowledge.embedding_model import EmbeddingModel
            from src.knowledge.vector_store import VectorStore

            # Initialize embedding model and vector store
            # Using await instead of asyncio.run() to prevent event loop conflicts
            try:
                embedding_model = EmbeddingModel()
                await embedding_model.load_model()
                logger.info("orchestrator.embedding_model_loaded")
            except Exception as e:
                logger.warning("orchestrator.embedding_failed", error=str(e))
                embedding_model = None

            # Initialize vector store
            try:
                vector_store = VectorStore()
                await vector_store.initialize()
                logger.info("orchestrator.vector_store_initialized")
            except Exception as e:
                logger.warning("orchestrator.vector_store_failed", error=str(e))
                vector_store = None

            # Register all RAG agents
            agents_to_register = [
                ("fiqh_agent", FiqhAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.FIQH]),
                ("general_islamic_agent", GeneralIslamicAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.ISLAMIC_KNOWLEDGE]),
                ("hadith_agent", HadithAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.HADITH]),
                ("tafsir_agent", TafsirAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.TAFSIR]),
                ("aqeedah_agent", AqeedahAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.AQEEDAH]),
                ("seerah_agent", SeerahAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.SEERAH]),
                ("islamic_history_agent", IslamicHistoryAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.ISLAMIC_HISTORY]),
                ("usul_fiqh_agent", FiqhUsulAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.USUL_FIQH]),
                ("arabic_language_agent", ArabicLanguageAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.ARABIC_LANGUAGE]),
                ("sanadset_hadith_agent", SanadsetHadithAgent(embedding_model=embedding_model, vector_store=vector_store), [Intent.HADITH]),
            ]

            for name, agent, intents in agents_to_register:
                try:
                    self.registry.register_agent(name, agent, intents=intents)
                    logger.info("orchestrator.agent_registered", agent=name, intents=[i.value for i in intents])
                except Exception as e:
                    logger.warning("orchestrator.agent_registration_failed", agent=name, error=str(e))

            logger.info("orchestrator.rag_agents_registered", agents=[a[0] for a in agents_to_register])
            return True

        except Exception as e:
            logger.warning("orchestrator.rag_agents_init_error", error=str(e), fallback_to_chatbot=True)
            return False

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

        if not target:
            logger.warning("orchestrator.unknown_intent", intent=intent.value, query=query[:100])
            return await self._fallback_response(query, "Unknown intent")

        # For FIQH, ISLAMIC_KNOWLEDGE, and new specialized intents, route to RAG agents if available
        requires_rag = intent in [
            Intent.FIQH, Intent.ISLAMIC_KNOWLEDGE,
            Intent.HADITH, Intent.TAFSIR, Intent.AQEEDAH,
            Intent.SEERAH, Intent.ISLAMIC_HISTORY, Intent.USUL_FIQH,
            Intent.ARABIC_LANGUAGE
        ]

        if requires_rag and not self._rag_initialized:
            # RAG not available, fallback to chatbot
            target = "chatbot_agent"
            logger.info(
                "orchestrator.using_chatbot_fallback", intent=intent.value, reason=f"rag_init={self._rag_initialized}"
            )

        # DIRECT FIX: For greeting intent, always create ChatbotAgent directly
        if intent == Intent.GREETING:
            try:
                from src.agents.chatbot_agent import ChatbotAgent
                instance = ChatbotAgent()
                is_agent = True
                logger.info("orchestrator.chatbot_created_directly")
            except Exception as e:
                logger.error("orchestrator.chatbot_direct_creation_failed", error=str(e))
                return await self._fallback_response(query, f"Failed to create chatbot: {str(e)}")
        else:
            # Get from registry for other intents
            instance, is_agent = self.registry.get_for_intent(intent)
            
            # Fallback if needed
            if not instance and target == "chatbot_agent":
                instance, is_agent = self.registry.get_for_intent(Intent.GREETING)
            
            # Create on fly if needed
            if not instance and target == "chatbot_agent":
                try:
                    from src.agents.chatbot_agent import ChatbotAgent
                    instance = ChatbotAgent()
                    is_agent = True
                    self.registry.register_agent("chatbot_agent", instance, intents=[Intent.GREETING])
                except Exception as e:
                    logger.error("orchestrator.chatbot_creation_failed", error=str(e))

        if not instance:
            return await self._fallback_response(query, f"Feature not yet implemented: {target}")

        # Route to agent
        if is_agent:
            return await self._route_to_agent(instance, query, language, location, madhhab, session_id, target)
        else:
            return await self._route_to_tool(instance, query, language, location, madhhab, session_id, target)

    async def _route_to_agent(
        self,
        agent: BaseAgent,
        query: str,
        language: str,
        location: Optional[dict],
        madhhab: Optional[str],
        session_id: Optional[str],
        agent_name: str,
    ) -> AgentOutput:
        """Route to an agent."""
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
            has_error = result.metadata.get("error") or "embedding" in result.answer.lower()

            if agent_name in ["fiqh_agent", "general_islamic_agent"] and has_error and self._rag_fallback_to_chatbot:
                logger.info("orchestrator.rag_runtime_fallback", original_agent=agent_name)
                # Fallback to chatbot
                chatbot, _ = self.registry.get_for_intent(Intent.GREETING)
                if chatbot:
                    return await chatbot.execute(
                        AgentInput(
                            query=query,
                            language=language,
                            metadata={"fallback": "rag_failed"},
                        )
                    )

            result.metadata["agent"] = agent_name
            return result

        except Exception as e:
            logger.error("orchestrator.agent_error", agent=agent_name, error=str(e), exc_info=True)
            return await self._fallback_response(query, f"Agent error: {str(e)}")

    async def _route_to_tool(
        self,
        tool: BaseTool,
        query: str,
        language: str,
        location: Optional[dict],
        madhhab: Optional[str],
        session_id: Optional[str],
        tool_name: str,
    ) -> AgentOutput:
        """Route to a tool."""
        try:
            result = await tool.execute(
                query=query, language=language, location=location, madhhab=madhhab, session_id=session_id
            )

            if result.success:
                answer = self._format_tool_result(result.result)
                return AgentOutput(
                    answer=answer,
                    metadata={"tool": tool_name, **result.metadata},
                )
            else:
                return await self._fallback_response(query, f"Tool error: {result.error}")

        except Exception as e:
            logger.error("orchestrator.tool_error", tool=tool_name, error=str(e), exc_info=True)
            return await self._fallback_response(query, f"Tool error: {str(e)}")

    def _format_tool_result(self, result: dict) -> str:
        """Format tool result dictionary into readable text."""
        import json

        return json.dumps(result, indent=2, ensure_ascii=False)

    async def _fallback_response(self, query: str, reason: str) -> AgentOutput:
        """Generate fallback response when routing fails."""
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
