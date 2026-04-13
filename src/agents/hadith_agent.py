"""
Hadith RAG Agent for Athar Islamic QA system.

Retrieves and presents hadith from authenticated sources with:
- Sanad (chain of narration)
- Matn (text)
- Grade/authentication
- Source book references

Phase 4: Core hadith retrieval pipeline.
"""

from typing import Optional

from src.agents.base import BaseAgent, AgentInput, AgentOutput, Citation
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.infrastructure.llm_client import get_llm_client

logger = get_logger()


class HadithAgent(BaseAgent):
    """
    Hadith Retrieval Agent.

    Answers questions using authenticated hadith collections.
    Returns hadith with sanad, matn, grade, and source.

    Usage:
        agent = HadithAgent()
        result = await agent.execute(AgentInput(query="ما حكم الصلاة؟"))
    """

    name = "hadith_agent"

    COLLECTION = "hadith_passages"
    TOP_K_RETRIEVAL = 10
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.6
    TEMPERATURE = 0.1
    MAX_TOKENS = 2048

    HADITH_SYSTEM_PROMPT = """أنت متخصص في علم الحديث ورواياته.

المهم:
- اعرض الأحاديث من النصوص المسترجاعة فقط
- لا تختلق أي أحاديث أو معلومات
- اذكر السند والمتن إذا كانا متاحين
- اذكر درجة الحديث (صحيح، حسن، ضعيف) إذا كانت متوفرة
- اذكر مصدر الحديث (صحيح البخاري، مسلم، إلخ)
- استخدم المراجع [C1]، [C2] لكل حديث
- إذا لم توجد أحاديث كافية، قل ذلك صراحة
- أضف تنبيهاً بضرورة الرجوع لأهل العلم"""

    HADITH_USER_PROMPT = """السؤال: {query}

اللغة المطلوبة: {language}

الأحاديث المسترجاعة:
{passages}

اعرض الأحاديث المناسبة مع ذكر المصدر والدرجة."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client=None,
    ):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self._llm_available = True

    async def _initialize(self):
        """Lazy initialization."""
        try:
            if self.embedding_model is None:
                from src.knowledge.embedding_model import EmbeddingModel
                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            logger.warning("hadith_agent.embedding_unavailable", error=str(e))
            self.embedding_model = None

        try:
            if self.vector_store is None:
                from src.knowledge.vector_store import VectorStore
                self.vector_store = VectorStore()
                await self.vector_store.initialize()

            if self.hybrid_searcher is None and self.vector_store:
                from src.knowledge.hybrid_search import HybridSearcher
                self.hybrid_searcher = HybridSearcher(self.vector_store)
        except Exception as e:
            logger.warning("hadith_agent.vector_store_unavailable", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None

        if self.llm_client is None:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning("hadith_agent.llm_unavailable", error=str(e))
                self._llm_available = False

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute hadith retrieval."""
        await self._initialize()

        try:
            if not self.embedding_model:
                return AgentOutput(
                    answer="الرجاء تثبيت نموذج التضمين للبحث في الأحاديث.",
                    metadata={"error": "Embedding model not available"},
                    confidence=0.0,
                    requires_human_review=True
                )

            # Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)

            # Retrieve hadith
            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=self.TOP_K_RETRIEVAL,
            )

            logger.info("hadith_agent.retrieved", query=input.query[:50], passage_count=len(passages))

            # Filter by threshold
            good_passages = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]

            # Format
            formatted = self._format_passages(good_passages[:self.TOP_K_RERANK])

            # Generate answer
            answer = await self._generate_with_llm(input.query, formatted, input.language)

            # Normalize citations
            normalized = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()

            return AgentOutput(
                answer=normalized,
                citations=citations,
                metadata={
                    "retrieved_count": len(passages),
                    "used_count": len(good_passages),
                    "collection": self.COLLECTION,
                },
                confidence=self._calculate_confidence(good_passages),
                requires_human_review=len(good_passages) == 0,
            )

        except Exception as e:
            logger.error("hadith_agent.error", error=str(e))
            return AgentOutput(
                answer=f"خطأ في البحث عن الحديث: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True,
            )

    def _format_passages(self, passages: list[dict]) -> str:
        """Format hadith passages for display."""
        formatted = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")[:600]
            source = p.get("metadata", {}).get("source", "")
            grade = p.get("metadata", {}).get("grade", "")
            
            text = f"[C{i}] {content}"
            if source:
                text += f"\nالمصدر: {source}"
            if grade:
                text += f"\nالدرجة: {grade}"
            
            formatted.append(text)
        
        return "\n\n".join(formatted)

    async def _generate_with_llm(self, query: str, passages: str, language: str) -> str:
        """Generate answer using LLM."""
        if not passages or not passages.strip():
            return "لم يتم العثور على أحاديث كافية. يرجى استفتاء عالم متخصص."

        if not self._llm_available or self.llm_client is None:
            return self._format_answer_manually(query, passages)

        try:
            user_prompt = self.HADITH_USER_PROMPT.format(
                query=query,
                language="العربية" if language == "ar" else "English",
                passages=passages
            )

            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": self.HADITH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("hadith_agent.llm_error", error=str(e))
            return self._format_answer_manually(query, passages)

    def _format_answer_manually(self, query: str, passages: str) -> str:
        """Format answer without LLM."""
        passages_list = passages.split("\n\n")
        if not passages_list:
            return "لم يتم العثور على أحاديث كافية."

        answer = f"الأحاديث المسترجاعة:\n\n"
        for p in passages_list[:3]:
            answer += f"{p}\n\n"

        answer += "\n⚠️ تنبيه: يرجى الرجوع لأهل العلم للتحقق."
        return answer

    def _calculate_confidence(self, passages: list[dict]) -> float:
        """Calculate confidence based on retrieval quality."""
        if not passages:
            return 0.0
        scores = [p.get("score", 0) for p in passages[:5]]
        return min(1.0, sum(scores) / len(scores) if scores else 0.0)
