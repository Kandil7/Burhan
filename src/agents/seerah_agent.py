"""
Seerah (Prophet Biography) Agent for Athar Islamic QA system.

Provides information about Prophet Muhammad's life and events.
Phase 4: Seerah retrieval pipeline.
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

class SeerahAgent(BaseAgent):
    """Seerah Retrieval Agent for Prophet biography questions."""
    name = "seerah_agent"
    COLLECTION = "seerah_passages"
    TOP_K_RETRIEVAL = 12
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.65
    TEMPERATURE = 0.2
    MAX_TOKENS = 2048
    SYSTEM = "أنت متخصص في السيرة النبوية.\nالمهم: اعرض المعلومات من النصوص فقط مع المراجع [C1]، [C2]."
    USER = "السؤال: {query}\nاللغة: {language}\nالنصوص:\n{passages}\nأجب بناءً على النصوص."

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
            logger.warning("seerah_agent.embedding_failed", error=str(e))
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
            logger.warning("seerah_agent.vector_store_failed", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None
        if not self.llm_client:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning("seerah_agent.llm_failed", error=str(e))
                self._llm_available = False

    async def execute(self, input: AgentInput) -> AgentOutput:
        await self._initialize()
        try:
            if not self.embedding_model:
                return AgentOutput(answer="النموذج غير متاح.", metadata={"error":"No model"}, confidence=0.0, requires_human_review=True)
            qe = await self.embedding_model.encode_query(input.query)
            passages = await self.hybrid_searcher.search(query=input.query, query_embedding=qe, collection=self.COLLECTION, top_k=self.TOP_K_RETRIEVAL)
            good = [p for p in passages if p.get("score",0) >= self.SCORE_THRESHOLD]
            fmt = "\n\n".join([f"[C{i}] {p.get('content','')[:500]}" for i,p in enumerate(good[:self.TOP_K_RERANK],1)])
            ans = await self._gen(input.query, fmt, input.language)
            norm = self.citation_normalizer.normalize(ans)
            cits = self.citation_normalizer.get_citations()
            return AgentOutput(answer=norm, citations=cits, metadata={"retrieved":len(passages),"used":len(good)}, confidence=min(1.0, sum(p.get("score",0) for p in good[:5])/len(good) if good else 0.0), requires_human_review=len(good)==0)
        except Exception as e:
            return AgentOutput(answer=f"خطأ: {e}", confidence=0.0, metadata={"error":str(e)}, requires_human_review=True)

    async def _gen(self, q, p, lang):
        if not p: return "لا توجد معلومات كافية."
        if not self._llm_available or not self.llm_client: return p[:300]
        try:
            r = await self.llm_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":self.SYSTEM},{"role":"user","content":self.USER.format(query=q,language=lang,passages=p)}], temperature=self.TEMPERATURE, max_tokens=self.MAX_TOKENS)
            return r.choices[0].message.content
        except Exception as e:
            logger.warning("seerah_agent.generation_failed", error=str(e))
            return p[:300]
