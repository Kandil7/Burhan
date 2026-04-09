"""
General Islamic Knowledge RAG Agent for Athar Islamic QA system.

Answers general Islamic questions using retrieval-augmented generation:
- History questions
- Biography (seerah, companions)
- Theology/aqeedah
- Concepts and definitions

Higher temperature (0.3) for educational tone.
Phase 5: Uses settings and constants for configuration.
"""

from typing import Optional

from src.agents.base import BaseAgent, AgentInput, AgentOutput, Citation
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.config.constants import RetrievalConfig, LLMConfig
from src.infrastructure.llm_client import get_llm_client

logger = get_logger()


class GeneralIslamicAgent(BaseAgent):
    """
    General Islamic Knowledge RAG Agent.

    Answers educational questions about Islam with higher temperature.
    Temperature: 0.3 (more conversational)

    Usage:
        agent = GeneralIslamicAgent()
        result = await agent.execute(AgentInput(query="من هو عمر بن الخطاب؟"))
    """

    name = "general_islamic_agent"

    TOP_K_RETRIEVAL = 10
    TEMPERATURE = 0.3
    MAX_TOKENS = 1536
    COLLECTION = "general_islamic"

    GENERAL_SYSTEM_PROMPT = """أنت معلم للمعرفة الإسلامية.

المهم:
- قدم إجابات تعليمية بأسلوب واضح ومفهوم
- استخدم المصادر المقدمة فقط
- أضف السياق التاريخي عند الاقتضاء
- استخدم المراجع [C1]، [C2] لكل مصدر
- اعترف إذا لم تتوفر معلومات كافية"""

    GENERAL_USER_PROMPT = """السؤال: {query}

اللغة المطلوبة: {language}

المصادر:
{passages}

قدم إجابة تعليمية مبنية على المصادر أعلاه."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client=None,
    ):
        """Initialize General Islamic Agent."""
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self._llm_available = True
        self._embedding_loaded = False

    async def _initialize(self):
        """Lazy initialization."""
        # Initialize embedding model
        if self.embedding_model is None:
            try:
                from src.knowledge.embedding_model import EmbeddingModel

                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
                self._embedding_loaded = True
                logger.info("general_agent.embedding_loaded")
            except Exception as e:
                logger.warning("general_agent.embedding_unavailable", error=str(e))
                self.embedding_model = None
                self._embedding_loaded = False

        # Initialize vector store
        if self.vector_store is None:
            try:
                from src.knowledge.vector_store import VectorStore

                self.vector_store = VectorStore()
                await self.vector_store.initialize()

                if self.hybrid_searcher is None and self.vector_store:
                    from src.knowledge.hybrid_search import HybridSearcher

                    self.hybrid_searcher = HybridSearcher(self.vector_store)
            except Exception as e:
                logger.warning("general_agent.vector_store_unavailable", error=str(e))
                self.vector_store = None
                self.hybrid_searcher = None

        # Initialize LLM client
        if self.llm_client is None:
            try:
                self.llm_client = await get_llm_client()
                logger.info("general_islamic_agent.llm_initialized")
            except Exception as e:
                logger.warning("general_islamic_agent.llm_unavailable", error=str(e))
                self._llm_available = False

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute general knowledge RAG pipeline."""
        await self._initialize()

        # If embedding model failed to load, return fallback
        if not self._embedding_loaded or not self.embedding_model:
            logger.warning("general_agent.embedding_model_not_loaded", query=input.query[:50])
            return await self._fallback_response(input.query, input.language)

        try:
            # Step 1: Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)

            # Step 2: Retrieve passages
            if not self.hybrid_searcher:
                return await self._fallback_response(input.query, input.language)

            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=self.TOP_K_RETRIEVAL,
            )

            logger.info("general_agent.retrieved", query=input.query[:50], passage_count=len(passages))

            # Step 3: Format passages
            formatted_passages = self._format_passages(passages)

            # Step 4: Generate answer using LLM
            answer = await self._generate_with_llm(
                query=input.query, passages=formatted_passages, language=input.language
            )

            # Step 5: Normalize citations
            normalized_text = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()

            return AgentOutput(
                answer=normalized_text,
                citations=citations,
                metadata={
                    "retrieved_count": len(passages),
                    "collection": self.COLLECTION,
                    "llm_used": self._llm_available and self.llm_client is not None,
                },
                confidence=self._calculate_confidence(passages),
            )

        except Exception as e:
            logger.error("general_agent.error", error=str(e))
            return AgentOutput(answer=f"Error processing query: {str(e)}", confidence=0.0, metadata={"error": str(e)})

    def _format_passages(self, passages: list[dict]) -> str:
        """Format passages for answer generation."""
        formatted = []
        for i, passage in enumerate(passages, 1):
            content = passage.get("content", "")[:400]
            source = passage.get("metadata", {}).get("source", "")

            passage_text = f"[C{i}] {content}"
            if source:
                passage_text += f"\nالمصدر: {source}"

            formatted.append(passage_text)

        return "\n\n".join(formatted)

    async def _generate_with_llm(self, query: str, passages: str, language: str) -> str:
        """Generate educational answer using LLM."""
        if not passages or not passages.strip():
            return "لم يتم العثور على معلومات كافية. يرجى إعادة صياغة السؤال."

        if not self._llm_available or self.llm_client is None:
            logger.warning("general_islamic_agent.llm_unavailable_using_fallback")
            return self._generate_answer(query, passages, language)

        try:
            user_prompt = self.GENERAL_USER_PROMPT.format(
                query=query, language="العربية" if language == "ar" else "الإنجليزية", passages=passages
            )

            response = await self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.GENERAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            answer = response.choices[0].message.content
            logger.info("general_islamic_agent.llm_generated", query=query[:50])
            return answer

        except Exception as e:
            logger.error("general_islamic_agent.llm_error", error=str(e))
            return self._generate_answer(query, passages, language)

    def _generate_answer(self, query: str, formatted_passages: str, language: str) -> str:
        """Generate educational answer from passages."""
        passages_list = formatted_passages.split("\n\n")

        if not passages_list:
            return "لم يتم العثور على معلومات كافية. يرجى إعادة صياغة السؤال."

        # Build educational answer
        answer = f"📚 **إجابة تعليمية:**\n\n"

        # Add summary from first passage
        if passages_list:
            first = passages_list[0].split("] ", 1)[-1] if "] " in passages_list[0] else passages_list[0]
            answer += f"{first[:500]}...\n\n"

        # Add additional context
        if len(passages_list) > 1:
            answer += f"📖 **معلومات إضافية:**\n"
            for passage in passages_list[1:3]:
                content = passage.split("] ", 1)[-1] if "] " in passage else passage
                answer += f"• {content[:200]}...\n"

        return answer

    def _calculate_confidence(self, passages: list[dict]) -> float:
        """Calculate confidence based on passage quality."""
        if not passages:
            return 0.0

        scores = [p.get("score", 0) for p in passages[:5]]
        return min(1.0, sum(scores) / len(scores))

    async def _fallback_response(self, query: str, language: str = "ar") -> AgentOutput:
        """Generate fallback response when RAG is not available."""
        query_lower = query.lower()

        # Try to detect intent and provide targeted responses
        if any(k in query_lower for k in ["صلاة", " prayer", "صيام", "fast"]):
            return AgentOutput(
                answer="أعتذر، النظام حالياً في وضع الصيانة. للمعلومات الأساسية:\n\n• الصلاة: ركن من أركان الإسلام، يجب أداء الصلوات الخمس يومياً في أوقاتها\n• الصيام: wajib في شهر رمضان\n\nللحصول على معلومات دقيقة، يرجى مراجعة دار الإضافة المحلية.",
                citations=[],
                metadata={"fallback": "general_knowledge", "topic": "worship"},
                confidence=0.3,
            )
        elif any(k in query_lower for k in ["زكاة", "zakat", "صدقة"]):
            return AgentOutput(
                answer="أعتذر، النظام حالياً في وضع الصيانة. للمعلومات الأساسية:\n\n• الزكاة: wajib على المال عند بلوغ النصاب (ما يعادل 85g ذهب)\n• نسبة الزكاة: 2.5%\n\nللحصول على معلومات دقيقة، يرجى مراجعة دار الإضافة المحلية.",
                citations=[],
                metadata={"fallback": "general_knowledge", "topic": "zakat"},
                confidence=0.3,
            )
        elif any(k in query_lower for k in ["حج", " pilgrimage", "عمرة"]):
            return AgentOutput(
                answer="أعتذر، النظام حالياً في وضع الصيانة. للمعلومات الأساسية:\n\n• الحج: wajib مرة واحدة في العمر للمقتدر\n• العمرة: مسنونة غير wajib\n\nللحصول على معلومات دقيقة، يرجى مراجعة دار الإضافة المحلية.",
                citations=[],
                metadata={"fallback": "general_knowledge", "topic": "hajj"},
                confidence=0.3,
            )
        else:
            return AgentOutput(
                answer="أعتذر، النظام حالياً في وضع الصيانة. يمكنني مساعدتك في:\n\n• الأسئلة العامة عن الإسلام\n• أحكام العبادات والمعاملات\n• الآيات القرآنية والتفسير\n• الأذكار والأدعية\n\nللحصول على معلومات دقيقة، يرجى مراجعة أهل العلم.",
                citations=[],
                metadata={"fallback": "general_knowledge"},
                confidence=0.3,
            )
