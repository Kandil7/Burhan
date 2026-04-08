"""
Aqeedah (Islamic Creed) Agent for Athar Islamic QA system.

Answers questions about Islamic theology and beliefs:
- Tawhid (Oneness of God)
- Faith pillars
- Theological concepts
- Creed differences

Phase 4: Aqeedah retrieval pipeline.
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

class AqeedahAgent(BaseAgent):
    """Aqeedah Retrieval Agent for Islamic theology questions."""
    name = "aqeedah_agent"
    COLLECTION = "aqeedah_passages"
    TOP_K_RETRIEVAL = 12
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.65
    TEMPERATURE = 0.15
    MAX_TOKENS = 2048

    SYSTEM_PROMPT = """أنت متخصص في العقيدة الإسلامية والتوحيد.
المهم:
- أجب بناءً على النصوص المسترجاعة فقط
- اذكر المراجع [C1]، [C2]
- لا تضف آراء شخصية
- إذا لم توجد نصوص كافية، قل ذلك
- أضف تنبيهاً بضرورة الرجوع لأهل العلم"""

    USER_PROMPT = """السؤال: {query}
اللغة: {language}
النصوص المسترجاعة:
{passages}
أجب بناءً على النصوص مع الالتزام بالتعليمات."""

    def __init__(self, embedding_model=None, vector_store=None, llm_client=None):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self._llm_available = True

    async def _initialize(self):
        """Initialize embedding model, vector store, and LLM client."""
        try:
            if not self.embedding_model:
                from src.knowledge.embedding_model import EmbeddingModel
                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            logger.warning("aqeedah_agent.embedding_failed", error=str(e))
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
            logger.warning("aqeedah_agent.vector_store_failed", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None
        if not self.llm_client:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning("aqeedah_agent.llm_failed", error=str(e))
                self._llm_available = False

    async def execute(self, input: AgentInput) -> AgentOutput:
        await self._initialize()
        try:
            if not self.embedding_model:
                return AgentOutput(answer="نموذج التضمين غير متاح.", metadata={"error": "No embedding"}, confidence=0.0, requires_human_review=True)
            query_emb = await self.embedding_model.encode_query(input.query)
            passages = await self.hybrid_searcher.search(query=input.query, query_embedding=query_emb, collection=self.COLLECTION, top_k=self.TOP_K_RETRIEVAL)
            good = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]
            formatted = self._format_passages(good[:self.TOP_K_RERANK])
            answer = await self._generate(input.query, formatted, input.language)
            normalized = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()
            return AgentOutput(answer=normalized, citations=citations, metadata={"retrieved": len(passages), "used": len(good)}, confidence=min(1.0, sum(p.get("score",0) for p in good[:5])/len(good) if good else 0.0), requires_human_review=len(good)==0)
        except Exception as e:
            logger.error("aqeedah_agent.error", error=str(e))
            return AgentOutput(answer=f"خطأ: {str(e)}", confidence=0.0, metadata={"error": str(e)}, requires_human_review=True)

    def _format_passages(self, passages):
        return "\n\n".join([f"[C{i}] {p.get('content','')[:500]}" for i, p in enumerate(passages, 1)])

    async def _generate(self, query, passages, language):
        """Generate answer using LLM or fallback to passages."""
        if not passages:
            return "لا توجد نصوص كافية."
        if not self._llm_available or not self.llm_client:
            return passages[:300]
        try:
            resp = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": self.USER_PROMPT.format(query=query, language=language, passages=passages)}
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("aqeedah_agent.generation_failed", error=str(e))
            return passages[:300]
