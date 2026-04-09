"""
Fiqh RAG Agent for Athar Islamic QA system.

Answers fiqh questions using retrieval-augmented generation:
1. Retrieve top-15 passages from fiqh corpus
2. Re-rank to top-5 with cross-encoder
3. Generate grounded answer with LLM
4. Normalize citations to [C1], [C2] format

Phase 4: Core RAG pipeline for fiqh questions.
Phase 5: Uses settings for LLM model configuration.
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

    # Use centralized constants
    TOP_K_RETRIEVAL = RetrievalConfig.TOP_K_FIQH
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = RetrievalConfig.SEMANTIC_SCORE_THRESHOLD
    TEMPERATURE = LLMConfig.FIQH_TEMPERATURE
    MAX_TOKENS = LLMConfig.DEFAULT_MAX_TOKENS

    FIQH_SYSTEM_PROMPT = """أنت مساعد إسلامي متخصص في الفقه الإسلامي.

المهم:
- أجب بناءً ONLY على النصوص المسترجاعة المقدمة
- لا تختلق أي معلومات غير موجودة في النصوص
- استخدم المراجع [C1]، [C2]، إلخ لكل مصدر تستشهد به
- إذا لم تكن هناك نص sufficiently يجيب على السؤال، قل ذلك صراحة
- أضف تنبيه باستشارة عالم متخصص للحالات الخاصة
- اذكر المذهب الإسلامي إن وُجد في النصوص"""

    FIQH_USER_PROMPT = """السؤال: {query}

اللغة المطلوبة: {language}

النصوص المسترجاعة:
{passages}

أجب بناءً على النصوص أعلاه مع الالتزام بالتعليمات."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client=None,
    ):
        """Initialize Fiqh Agent.

        Args:
            embedding_model: Optional embedding model (will create if not provided)
            vector_store: Optional vector store (will create if not provided)
            llm_client: Optional LLM client for answer generation
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self._llm_available = True  # Track LLM availability

    async def _initialize(self):
        """Lazy initialization of dependencies."""
        try:
            if self.embedding_model is None:
                from src.knowledge.embedding_model import EmbeddingModel

                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            logger.warning("fiqh_agent.embedding_unavailable", error=str(e))
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
            logger.warning("fiqh_agent.vector_store_unavailable", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None

        # Initialize LLM client if not provided
        if self.llm_client is None:
            try:
                self.llm_client = await get_llm_client()
                logger.info("fiqh_agent.llm_initialized")
            except Exception as e:
                logger.warning("fiqh_agent.llm_unavailable", error=str(e))
                self._llm_available = False

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
            # If no embedding model, return fallback response
            if not self.embedding_model:
                return AgentOutput(
                    answer="الرجاء تثبيت نموذج التضمين للبحث في النصوص. التثبيت: pip install torch transformers",
                    metadata={"error": "Embedding model not available", "fix": "pip install torch transformers"},
                    confidence=0.0,
                    requires_human_review=True,
                )

            # Step 1: Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)

            # Step 2: Retrieve passages with hybrid search
            passages = await self.hybrid_searcher.search(
                query=input.query,
                query_embedding=query_embedding,
                collection="fiqh_passages",
                top_k=self.TOP_K_RETRIEVAL,
            )

            logger.info("fiq h_agent.retrieved", query=input.query[:50], passage_count=len(passages))

            # Step 3: Filter by score threshold
            good_passages = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]

            # Step 4: Format passages for LLM
            formatted_passages = self._format_passages(good_passages[: self.TOP_K_RERANK])

            # Step 5: Generate answer using LLM
            answer = await self._generate_with_llm(
                query=input.query, passages=formatted_passages, language=input.language
            )

            # Step 6: Normalize citations
            normalized_text = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()

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
                    "llm_used": self._llm_available and self.llm_client is not None,
                },
                confidence=self._calculate_confidence(good_passages),
                requires_human_review=len(good_passages) == 0,
            )

        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            logger.error("fiqh_agent.error", error=str(e), traceback=error_traceback, exc_info=True)
            return AgentOutput(
                answer=f"Error processing fiqh query: {str(e)}\n\nPlease consult a qualified scholar.",
                confidence=0.0,
                metadata={"error": str(e), "traceback": error_traceback.split("\n")[-5:]},
                requires_human_review=True,
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

    async def _generate_with_llm(self, query: str, passages: str, language: str) -> str:
        """
        Generate answer using LLM with retrieved passages as context.

        Args:
            query: User's question
            passages: Formatted retrieved passages with [C1], [C2], etc.
            language: Response language (ar/en)

        Returns:
            Generated answer text
        """
        # Check if passages are available
        if not passages or not passages.strip():
            return "لا توجد نصوص كافية للإجابة على هذا السؤال. يرجى استفتاء عالم متخصص."

        # Check if LLM is available
        if not self._llm_available or self.llm_client is None:
            logger.warning("fiqh_agent.llm_unavailable_using_fallback")
            return self._generate_answer_from_passages(query, passages, language)

        try:
            # Build prompt
            user_prompt = self.FIQH_USER_PROMPT.format(
                query=query, language="العربية" if language == "ar" else "الإنجليزية", passages=passages
            )

            # Call LLM - use settings for model
            response = await self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.FIQH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            answer = response.choices[0].message.content

            logger.info("fiqh_agent.llm_generated", query=query[:50], answer_length=len(answer))

            return answer

        except Exception as e:
            logger.error("fiqh_agent.llm_error", error=str(e))
            # Fallback to template-based answer
            return self._generate_answer_from_passages(query, passages, language)

    def _generate_answer_from_passages(self, query: str, formatted_passages: str, language: str) -> str:
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
