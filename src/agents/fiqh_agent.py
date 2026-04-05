"""
Fiqh RAG Agent for Athar Islamic QA system.

Answers fiqh questions using retrieval-augmented generation:
1. Retrieve top-15 passages from fiqh corpus
2. Re-rank to top-5 with cross-encoder
3. Generate grounded answer with citations
4. Normalize citations to [C1], [C2] format

Phase 4: Core RAG pipeline for fiqh questions.
"""
from typing import Optional

import numpy as np

from src.agents.base import BaseAgent, AgentInput, AgentOutput, Citation
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer
from src.config.logging_config import get_logger

logger = get_logger()


class FiqhAgent(BaseAgent):
    """
    Fiqh RAG Agent.
    
    Answers Islamic jurisprudence questions using verified sources only.
    Temperature: 0.1 (very deterministic)
    
    Usage:
        agent = FiqhAgent()
        result = await agent.execute(AgentInput(query="ما حكم زكاة الأسهم؟"))
    """
    
    name = "fiqh_agent"
    
    TOP_K_RETRIEVAL = 15
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.7
    TEMPERATURE = 0.1
    
    FIQH_GENERATION_PROMPT = """أنت مساعد إسلامي متخصص في الفقه. أجب بناءً ONLY على النصوص المسترجاعة.

السؤال: {query}
اللغة: {language}

النصوص المسترجاعة:
{passages}

التعليمات:
1. أجب بناءً على النصوص فقط
2. اذكر الافتراضات إن وجدت
3. إذا كانت النصوص لا تجيب بشكل كافٍ، قل ذلك صراحة
4. اذكر المذهب إذا كان موجوداً في النصوص
5. استخدم المراجع [C1]، [C2]، إلخ. لكل دليل
6. لا تخترع أو تضيف مصادر خارجية
7. إذا كانت هناك آراء مختلفة، اذكرها
8. أضف تنبيه باستشارة العالم للحالات الخاصة

أجب بـ {language}."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """Initialize Fiqh Agent."""
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
    
    async def _initialize(self):
        """Lazy initialization of dependencies."""
        if self.embedding_model is None:
            self.embedding_model = EmbeddingModel()
            await self.embedding_model.load_model()
        
        if self.vector_store is None:
            self.vector_store = VectorStore()
            await self.vector_store.initialize()
        
        if self.hybrid_searcher is None:
            self.hybrid_searcher = HybridSearcher(self.vector_store)
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute fiqh RAG pipeline.
        
        Steps:
        1. Encode query
        2. Retrieve passages
        3. Format passages for LLM
        4. Generate answer
        5. Normalize citations
        
        Args:
            input: AgentInput with query
            
        Returns:
            AgentOutput with answer, citations, metadata
        """
        await self._initialize()
        
        try:
            # Step 1: Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)
            
            # Step 2: Retrieve passages with hybrid search
            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection="fiqh_passages",
                top_k=self.TOP_K_RETRIEVAL
            )
            
            logger.info(
                "fiq h_agent.retrieved",
                query=input.query[:50],
                passage_count=len(passages)
            )
            
            # Step 3: Filter by score threshold
            good_passages = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]
            
            # Step 4: Format passages for LLM
            formatted_passages = self._format_passages(good_passages[:self.TOP_K_RERANK])
            
            # Step 5: Generate answer (will be implemented when LLM client is available)
            # For Phase 4, we'll return retrieved passages directly
            answer = self._generate_answer_from_passages(
                input.query,
                formatted_passages,
                input.language
            )
            
            # Step 6: Normalize citations
            normalized_text, citations = self.citation_normalizer.normalize(answer)
            
            # Step 7: Add disclaimer
            final_answer = self._add_disclaimer(normalized_text)
            
            return AgentOutput(
                answer=final_answer,
                citations=citations,
                metadata={
                    "retrieved_count": len(passages),
                    "used_count": len(good_passages),
                    "collection": "fiqh_passages",
                    "madhhab_filter": input.metadata.get("madhhab"),
                    "scores": [p.get("score", 0) for p in good_passages[:5]],
                },
                confidence=self._calculate_confidence(good_passages),
                requires_human_review=len(good_passages) == 0
            )
            
        except Exception as e:
            logger.error("fiqh_agent.error", error=str(e), exc_info=True)
            return AgentOutput(
                answer=f"Error processing fiqh query: {str(e)}\n\nPlease consult a qualified scholar.",
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True
            )
    
    def _format_passages(self, passages: list[dict]) -> str:
        """Format passages for LLM prompt."""
        formatted = []
        for i, passage in enumerate(passages, 1):
            content = passage.get("content", "")[:500]
            source = passage.get("metadata", {}).get("source", "Unknown")
            madhhab = passage.get("metadata", {}).get("madhhab", "")
            
            passage_text = f"[C{i}] {content}"
            if madhhab:
                passage_text += f"\nالمذهب: {madhhab}"
            if source:
                passage_text += f"\nالمصدر: {source}"
            
            formatted.append(passage_text)
        
        return "\n\n".join(formatted)
    
    def _generate_answer_from_passages(
        self,
        query: str,
        formatted_passages: str,
        language: str
    ) -> str:
        """
        Generate answer from passages.
        
        Phase 4: Simple template-based answer
        Phase 5: Will use LLM generation
        """
        # Extract key information from passages
        passages_list = formatted_passages.split("\n\n")
        
        if not passages_list:
            return "لا توجد نصوص كافية للإجابة على هذا السؤال. يرجى استفتاء عالم متخصص."
        
        # Build answer from retrieved passages
        answer = f"بناءً على النصوص المسترجاعة:\n\n"
        
        for i, passage in enumerate(passages_list[:3], 1):
            # Extract citation marker
            if passage.startswith("[C"):
                marker = passage.split("]")[0] + "]"
                content = passage.split("] ", 1)[-1]
                answer += f"{marker} {content[:300]}...\n\n"
        
        answer += f"\n⚠️ تنبيه: هذه الإجابة مبنية على النصوص المسترجاعة فقط. "
        answer += "يرجى استفتاء عالم متخصص للحالات الخاصة."
        
        return answer
    
    def _add_disclaimer(self, text: str) -> str:
        """Add fiqh disclaimer to answer."""
        disclaimer = (
            "\n\n---\n"
            "⚠️ **تنبيه مهم**: هذه الإجابة مبنية على النصوص المسترجاعة من المصادر المتاحة. "
            "يجب استفتاء عالم متخصص للتأكد من الحكم في حالتك الخاصة، "
            "خاصة في المسائل التي تختلف فيها المذاهب."
        )
        
        return text + disclaimer
    
    def _calculate_confidence(self, passages: list[dict]) -> float:
        """Calculate confidence based on retrieval quality."""
        if not passages:
            return 0.0
        
        # Average score of top passages
        scores = [p.get("score", 0) for p in passages[:5]]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Scale to 0-1
        return min(1.0, avg_score)
