"""
Tafsir RAG Agent for Athar Islamic QA system.

Provides Quran interpretation from major tafsir sources:
- Ibn Kathir
- Al-Jalalayn
- Al-Qurtubi

Phase 4: Tafsir retrieval and explanation.
"""

from typing import Optional

from src.agents.base import BaseAgent, AgentInput, AgentOutput
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer
from src.config.logging_config import get_logger
from src.infrastructure.llm_client import get_llm_client

logger = get_logger()


class TafsirAgent(BaseAgent):
    """
    Tafsir Retrieval Agent.

    Provides Quran interpretation from scholarly sources.

    Usage:
        agent = TafsirAgent()
        result = await agent.execute(AgentInput(query="ما معنى البسملة؟"))
    """

    name = "tafsir_agent"

    COLLECTION = "quran_tafsir"
    TOP_K_RETRIEVAL = 10
    TOP_K_RERANK = 3
    SCORE_THRESHOLD = 0.65
    TEMPERATURE = 0.1
    MAX_TOKENS = 2048

    TAFSIR_SYSTEM_PROMPT = """أنت مفسر للقرآن الكريم تعتمد على تفاسير العلماء المعتبرين.

المهم:
- اعرض التفسير من النصوص المسترجاعة فقط
- اذكر اسم المفسر (ابن كثير، الجلالين، القرطبي)
- لا تضف تفسيرات شخصية
- استخدم المراجع [C1]، [C2] لكل تفسير
- إذا لم يوجد تفسير كافٍ، قل ذلك صراحة
- أضف تنبيهاً بضرورة الرجوع للمفسرين المتخصصين"""

    TAFSIR_USER_PROMPT = """الآية أو السؤال: {query}

اللغة المطلوبة: {language}

التفاسير المسترجاعة:
{passages}

اعرض التفسير المناسب مع ذكر المفسر."""

    def __init__(self, embedding_model=None, vector_store=None, llm_client=None):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self._llm_available = True

    async def _initialize(self):
        try:
            if not self.embedding_model:
                from src.knowledge.embedding_model import EmbeddingModel
                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            self.embedding_model = None

        try:
            if not self.vector_store:
                from src.knowledge.vector_store import VectorStore
                self.vector_store = VectorStore()
                await self.vector_store.initialize()
            if not self.hybrid_searcher and self.vector_store:
                from src.knowledge.hybrid_search import HybridSearcher
                self.hybrid_searcher = HybridSearcher(self.vector_store)
        except Exception as e:
            self.vector_store = None
            self.hybrid_searcher = None

        if not self.llm_client:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning("tafsir_agent.llm_failed", error=str(e))
                self._llm_available = False

    async def execute(self, input: AgentInput) -> AgentOutput:
        await self._initialize()
        try:
            if not self.embedding_model:
                return AgentOutput(
                    answer="نموذج التضمين غير متاح.",
                    metadata={"error": "Embedding unavailable"},
                    confidence=0.0,
                    requires_human_review=True
                )

            query_embedding = await self.embedding_model.encode_query(input.query)
            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=self.TOP_K_RETRIEVAL,
            )

            logger.info("tafsir_agent.retrieved", query=input.query[:50], count=len(passages))
            good = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]
            formatted = self._format_passages(good[:self.TOP_K_RERANK])
            answer = await self._generate_with_llm(input.query, formatted, input.language)
            normalized = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()

            return AgentOutput(
                answer=normalized,
                citations=citations,
                metadata={"retrieved": len(passages), "used": len(good), "collection": self.COLLECTION},
                confidence=min(1.0, sum(p.get("score", 0) for p in good[:5]) / len(good) if good else 0.0),
                requires_human_review=len(good) == 0,
            )
        except Exception as e:
            logger.error("tafsir_agent.error", error=str(e))
            return AgentOutput(
                answer=f"خطأ في التفسير: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True,
            )

    def _format_passages(self, passages):
        formatted = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")[:500]
            source = p.get("metadata", {}).get("tafsir_source", "")
            text = f"[C{i}] {content}"
            if source:
                text += f"\nالمفسر: {source}"
            formatted.append(text)
        return "\n\n".join(formatted)

    async def _generate_with_llm(self, query, passages, language):
        if not passages:
            return "لم يتم العثور على تفسير كافٍ. يرجى الرجوع إلى كتب التفسير."
        if not self._llm_available or not self.llm_client:
            return passages[:300]
        try:
            resp = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.TAFSIR_SYSTEM_PROMPT},
                    {"role": "user", "content": self.TAFSIR_USER_PROMPT.format(query=query, language=language, passages=passages)},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("tafsir_agent.generation_failed", error=str(e))
            return passages[:300]
