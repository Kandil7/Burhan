"""
Base RAG Agent for Athar Islamic QA system.

Provides shared implementation for all RAG-based agents:
- Initialization (embedding model, vector store, LLM client)
- Retrieval (embedding + hybrid search)
- Generation (LLM with system/user prompts)
- Citation normalization
- Confidence calculation
- Error handling

Agents inherit and override only:
- COLLECTION name
- System/user prompts
- Temperature, max_tokens, thresholds
- Agent name

"""
from typing import Any

from src.agents.base import AgentInput, AgentOutput, BaseAgent
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.core.citation import CitationNormalizer
from src.infrastructure.llm_client import get_llm_client
from src.knowledge.book_weighter import BookImportanceWeighter
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.hadith_grader import HadithAuthenticityGrader
from src.knowledge.hierarchical_retriever import HierarchicalRetriever
from src.knowledge.hybrid_search import HybridSearcher
from src.knowledge.title_loader import TitleLoader
from src.knowledge.vector_store import VectorStore

logger = get_logger()


class BaseRAGAgent(BaseAgent):
    """
    Base class for all RAG-based agents.

    Subclasses must define:
    - COLLECTION: str (e.g., "fiqh_passages")
    - SYSTEM_PROMPT: str (Arabic system prompt)
    - USER_PROMPT: str (User prompt with {query}, {language}, {passages})

    Optional overrides:
    - TOP_K_RETRIEVAL: int (default: 12)
    - TOP_K_RERANK: int (default: 5)
    - SCORE_THRESHOLD: float (default: 0.65)
    - TEMPERATURE: float (default: 0.15)
    - MAX_TOKENS: int (default: 2048)
    - FALLBACK_MESSAGE: str (default: "النموذج غير متاح.")
    """

    # Required (must be overridden)
    COLLECTION: str = ""
    SYSTEM_PROMPT: str = ""
    USER_PROMPT: str = ""

    # Optional (with sensible defaults)
    TOP_K_RETRIEVAL: int = 12
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.65
    TEMPERATURE: float = 0.15
    MAX_TOKENS: int = 2048
    FALLBACK_MESSAGE: str = "النموذج غير متاح."
    NO_PASSAGES_MESSAGE: str = "لا توجد نصوص كافية."

    def __init__(
        self,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ):
        """Initialize with optional dependency injection."""
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()
        self.hierarchical_retriever = HierarchicalRetriever()
        self.title_loader = TitleLoader()
        self.hadith_grader = HadithAuthenticityGrader()
        self.book_weighter = BookImportanceWeighter()
        self._llm_available = True
        self._initialized = False

    async def _initialize(self):
        """Initialize embedding model, vector store, and LLM client."""
        if self._initialized:
            return

        # Initialize embedding model
        try:
            if not self.embedding_model:
                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            logger.warning(f"{self.name}.embedding_failed", error=str(e))
            self.embedding_model = None

        # Initialize vector store and hybrid searcher
        try:
            if not self.vector_store:
                self.vector_store = VectorStore()
                await self.vector_store.initialize()
            if not self.hybrid_searcher and self.vector_store:
                self.hybrid_searcher = HybridSearcher(self.vector_store)
        except Exception as e:
            logger.warning(f"{self.name}.vector_store_failed", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None

        # Initialize LLM client
        if not self.llm_client:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning(f"{self.name}.llm_failed", error=str(e))
                self._llm_available = False

        self._initialized = True

    async def execute(
        self,
        input: AgentInput,
        filters: dict[str, Any] | None = None,
        hierarchical: bool = False,
    ) -> AgentOutput:
        """
        Execute RAG pipeline with optional facet filtering and hierarchical retrieval:
        1. Initialize dependencies
        2. Encode query
        3. Retrieve passages (with optional filters or hierarchical)
        4. Generate answer
        5. Normalize and enrich citations
        6. Return result with confidence

        Args:
            input: AgentInput with query and language
            filters: Optional dict with facet filters (author, era, book, etc.)
            hierarchical: If True, use hierarchical retrieval for better context
        """
        await self._initialize()

        try:
            # Check embedding model availability
            if not self.embedding_model:
                return AgentOutput(
                    answer=self.FALLBACK_MESSAGE,
                    metadata={"error": "No embedding model"},
                    confidence=0.0,
                    requires_human_review=True,
                )

            # Encode query
            query_embedding = await self.embedding_model.encode_query(input.query)

            # Retrieve passages (with optional facet filtering or hierarchical)
            if hierarchical and self.hybrid_searcher:
                # Get expanded results for hierarchical processing
                expanded_passages = await self.hybrid_searcher.search_with_facets(
                    query=input.query,
                    query_embedding=query_embedding,
                    collection=self.COLLECTION,
                    top_k=self.TOP_K_RETRIEVAL * 3,
                    filters=filters,
                )

                # Apply hierarchical retrieval
                hierarchical_results = self.hierarchical_retriever.retrieve_hierarchical(
                    passages=expanded_passages,
                    top_k_books=3,
                    top_k_pages_per_book=self.TOP_K_RERANK,
                )

                # Convert back to flat passages with hierarchy context
                good_passages = self.hierarchical_retriever.get_flat_passages(
                    hierarchical_results, max_passages=self.TOP_K_RERANK
                )
            elif filters and self.hybrid_searcher:
                passages = await self.hybrid_searcher.search_with_facets(
                    query=input.query,
                    query_embedding=query_embedding,
                    collection=self.COLLECTION,
                    top_k=self.TOP_K_RETRIEVAL,
                    filters=filters,
                )
                good_passages = [
                    p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD
                ][:self.TOP_K_RERANK]
            else:
                passages = await self.hybrid_searcher.search(
                    query=input.query,
                    query_embedding=query_embedding,
                    collection=self.COLLECTION,
                    top_k=self.TOP_K_RETRIEVAL,
                )
                good_passages = [
                    p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD
                ][:self.TOP_K_RERANK]

            # Enrich passages with title/chapter context
            if good_passages:
                good_passages = self.title_loader.enrich_passages(good_passages)
                # Enrich hadith passages with authenticity grades
                good_passages = self.hadith_grader.enrich_passages_with_authenticity(good_passages)
                # Weight passages by book importance
                good_passages = self.book_weighter.weight_passages_by_importance(good_passages)

            # Format passages for LLM
            formatted_passages = self._format_passages(good_passages[: self.TOP_K_RERANK])

            # Generate answer
            answer = await self._generate(input.query, formatted_passages, input.language)

            # Normalize citations
            normalized_answer = self.citation_normalizer.normalize(answer)
            citations = self.citation_normalizer.get_citations()

            # Enrich citations with passage metadata
            if good_passages:
                citations = self.citation_normalizer.enrich_citations(good_passages)

            # Calculate confidence
            confidence = self._calculate_confidence(good_passages)

            return AgentOutput(
                answer=normalized_answer,
                citations=citations,
                metadata={
                    "retrieved": len(passages),
                    "used": len(good_passages),
                    "collection": self.COLLECTION,
                },
                confidence=confidence,
                requires_human_review=len(good_passages) == 0,
            )

        except Exception as e:
            logger.error(f"{self.name}.execution_failed", error=str(e))
            return AgentOutput(
                answer=f"خطأ: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True,
            )

    def _format_passages(self, passages: list) -> str:
        """Format passages for LLM input with citation markers."""
        if not passages:
            return ""
        return "\n\n".join(
            [f"[C{i}] {p.get('content', '')[:500]}" for i, p in enumerate(passages, 1)]
        )

    async def _generate(self, query: str, passages: str, language: str) -> str:
        """Generate answer using LLM or fallback to passages."""
        if not passages:
            return self.NO_PASSAGES_MESSAGE

        if not self._llm_available or not self.llm_client:
            return passages[:300]

        try:
            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": self.USER_PROMPT.format(
                            query=query, language=language, passages=passages
                        ),
                    },
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"{self.name}.generation_failed", error=str(e))
            return passages[:300]

    def _calculate_confidence(self, passages: list) -> float:
        """Calculate confidence score based on passage scores."""
        if not passages:
            return 0.0
        # Average top 5 passage scores
        top_scores = [p.get("score", 0) for p in passages[:5]]
        avg_score = sum(top_scores) / len(top_scores)
        return min(1.0, avg_score)
