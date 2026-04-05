"""
General Islamic Knowledge RAG Agent for Athar Islamic QA system.

Answers general Islamic questions using retrieval-augmented generation:
- History questions
- Biography (seerah, companions)
- Theology/aqeedah
- Concepts and definitions

Higher temperature (0.3) for educational tone.
Phase 4: Core RAG pipeline for general Islamic knowledge.
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
    COLLECTION = "general_islamic"
    
    GENERAL_KNOWLEDGE_PROMPT = """أنت معلم للمعرفة الإسلامية. قدم إجابات تعليمية بناءً على المصادر.

السؤال: {query}

المصادر:
{passages}

التعليمات:
1. أجب بأسلوب تعليمي informative
2. استخدم المصادر المقدمة
3. أضف السياق التاريخي عند الاقتضاء
4. اذكر المصادر بوضوح
5. إذا كانت المعلومات غير كافية، اعترف بذلك

أجب بـ {language}."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """Initialize General Islamic Agent."""
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
    
    async def _initialize(self):
        """Lazy initialization."""
        if self.embedding_model is None:
            self.embedding_model = EmbeddingModel()
            await self.embedding_model.load_model()
        
        if self.vector_store is None:
            self.vector_store = VectorStore()
            await self.vector_store.initialize()
        
        if self.hybrid_searcher is None:
            self.hybrid_searcher = HybridSearcher(self.vector_store)
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute general knowledge RAG pipeline."""
        await self._initialize()
        
        try:
            # Step 1: Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)
            
            # Step 2: Retrieve passages
            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=self.TOP_K_RETRIEVAL
            )
            
            logger.info(
                "general_agent.retrieved",
                query=input.query[:50],
                passage_count=len(passages)
            )
            
            # Step 3: Format passages
            formatted_passages = self._format_passages(passages)
            
            # Step 4: Generate answer
            answer = self._generate_answer(input.query, formatted_passages, input.language)
            
            # Step 5: Normalize citations
            normalized_text, citations = self.citation_normalizer.normalize(answer)
            
            return AgentOutput(
                answer=normalized_text,
                citations=citations,
                metadata={
                    "retrieved_count": len(passages),
                    "collection": self.COLLECTION,
                },
                confidence=self._calculate_confidence(passages)
            )
            
        except Exception as e:
            logger.error("general_agent.error", error=str(e))
            return AgentOutput(
                answer=f"Error processing query: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
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
    
    def _generate_answer(
        self,
        query: str,
        formatted_passages: str,
        language: str
    ) -> str:
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
