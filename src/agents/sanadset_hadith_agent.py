"""
Sanadset Hadith Agent for Athar Islamic QA system.

Retrieves hadith from the Sanadset 368K dataset with:
- Full sanad (chain of narration)
- Matn (text)
- Book attribution
- Hadith number
- Narrator extraction

Usage:
    agent = SanadsetHadithAgent()
    await agent.initialize()
    result = await agent.execute(AgentInput(query="ما حكم الصلاة؟"))
"""
from typing import Optional
import csv
import re
from pathlib import Path
from src.agents.base import BaseAgent, AgentInput, AgentOutput, Citation
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer
from src.config.logging_config import get_logger
from src.infrastructure.llm_client import get_llm_client

logger = get_logger()

# Sanadset CSV path
SANADSET_PATH = Path(__file__).parent.parent.parent / "datasets" / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators" / "sanadset.csv"


class SanadsetHadithAgent(BaseAgent):
    """
    Hadith Retrieval Agent using Sanadset 368K dataset.
    
    Searches hadith by:
    - Matn (text) similarity
    - Narrator names in sanad
    - Book name
    - Keywords
    
    Returns hadith with full metadata.
    """

    name = "sanadset_hadith_agent"
    COLLECTION = "hadith_passages"
    TOP_K_RETRIEVAL = 20
    TOP_K_RERANK = 10
    SCORE_THRESHOLD = 0.4
    TEMPERATURE = 0.1
    MAX_TOKENS = 2048

    HADITH_SYSTEM_PROMPT = """أنت متخصص في علم الحديث ورواياته.

المهم:
- اعرض الأحاديث من النصوص المسترجاعة فقط
- لا تختلق أي أحاديث أو معلومات
- اذكر السند والمتن إذا كانا متاحين
- اذكر مصدر الحديث (الكتاب) ورقمه
- استخدم المراجع [C1]، [C2] لكل حديث
- إذا لم توجد أحاديث كافية، قل ذلك صراحة
- أضف تنبيهاً بضرورة الرجوع لأهل العلم"""

    HADITH_USER_PROMPT = """السؤال: {query}

اللغة المطلوبة: {language}

الأحاديث المسترجاعة:
{passages}

اعرض الأحاديث المناسبة مع ذكر المصدر والسند."""

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
        self._initialized = False

    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return

        try:
            if not self.embedding_model:
                from src.knowledge.embedding_model import EmbeddingModel
                self.embedding_model = EmbeddingModel()
                await self.embedding_model.load_model()
        except Exception as e:
            logger.warning("sanadset_hadith.embedding_failed", error=str(e))
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
            logger.warning("sanadset_hadith.vector_store_failed", error=str(e))
            self.vector_store = None
            self.hybrid_searcher = None

        if not self.llm_client:
            try:
                self.llm_client = await get_llm_client()
            except Exception as e:
                logger.warning("sanadset_hadith.llm_failed", error=str(e))
                self._llm_available = False

        self._initialized = True
        logger.info("sanadset_hadith.initialized", embedding=bool(self.embedding_model), vector_store=bool(self.vector_store))

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute hadith retrieval."""
        await self.initialize()

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

            logger.info("sanadset_hadith.retrieved", query=input.query[:50], passage_count=len(passages))

            # Filter by threshold
            good_passages = [p for p in passages if p.get("score", 0) >= self.SCORE_THRESHOLD]

            if not good_passages:
                return AgentOutput(
                    answer="لم يتم العثور على أحاديث كافية. يرجى إعادة صياغة السؤال.",
                    citations=[],
                    metadata={"retrieved_count": len(passages), "used_count": 0},
                    confidence=0.0,
                    requires_human_review=True,
                )

            # Format passages
            formatted = self._format_passages(good_passages[:self.TOP_K_RERANK])

            # Generate answer with LLM
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
                    "scores": [p.get("score", 0) for p in good_passages[:5]],
                    "llm_used": self._llm_available,
                },
                confidence=self._calculate_confidence(good_passages),
                requires_human_review=len(good_passages) == 0,
            )

        except Exception as e:
            logger.error("sanadset_hadith.error", error=str(e), exc_info=True)
            return AgentOutput(
                answer=f"خطأ في البحث عن الحديث: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True,
            )

    def _format_passages(self, passages: list[dict]) -> str:
        """Format hadith passages for LLM prompt."""
        formatted = []
        for i, p in enumerate(passages, 1):
            meta = p.get("metadata", {})
            
            # Build hadith display
            parts = []
            parts.append(f"[C{i}]")
            
            # Book and number
            book = meta.get("book", "Unknown")
            num = meta.get("num_hadith", "")
            if book and num:
                parts.append(f"**{book} - حديث رقم {num}**")
            elif book:
                parts.append(f"**{book}**")
            
            # Sanad if available
            sanad = meta.get("sanad", "")
            if sanad and sanad != "No SANAD":
                parts.append(f"السند: {sanad[:200]}")
            
            # Matn (text)
            matn = meta.get("matn", p.get("content", ""))
            if matn:
                parts.append(f"المتن: {matn[:400]}")
            
            # Sanad length
            sanad_len = meta.get("sanad_length", "")
            if sanad_len:
                parts.append(f"(طول السند: {sanad_len} رواة)")
            
            formatted.append("\n".join(parts))
        
        return "\n\n".join(formatted)

    async def _generate_with_llm(self, query: str, passages: str, language: str) -> str:
        """Generate answer using LLM."""
        if not passages or not passages.strip():
            return "لم يتم العثور على أحاديث كافية. يرجى استفتاء عالم متخصص."

        if not self._llm_available or not self.llm_client:
            return self._format_answer_manually(query, passages)

        try:
            user_prompt = self.HADITH_USER_PROMPT.format(
                query=query,
                language="العربية" if language == "ar" else "English",
                passages=passages
            )

            response = await self.llm_client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": self.HADITH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("sanadset_hadith.llm_error", error=str(e))
            return self._format_answer_manually(query, passages)

    def _format_answer_manually(self, query: str, passages: str) -> str:
        """Format answer without LLM."""
        return f"الأحاديث المسترجاعة:\n\n{passages}\n\n⚠️ يرجى الرجوع لأهل العلم للتحقق."

    def _calculate_confidence(self, passages: list[dict]) -> float:
        """Calculate confidence based on retrieval quality."""
        if not passages:
            return 0.0
        scores = [p.get("score", 0) for p in passages[:5]]
        return min(1.0, sum(scores) / len(scores) if scores else 0.0)


# Utility function to parse Sanadset CSV
def parse_sanadset_csv(csv_path: Path = SANADSET_PATH, limit: int = None) -> list[dict]:
    """
    Parse Sanadset CSV into hadith documents for embedding.
    
    Each hadith becomes one chunk with full metadata.
    
    Args:
        csv_path: Path to sanadset.csv
        limit: Maximum number of hadith to process (None = all)
    
    Returns:
        List of document dicts ready for embedding
    """
    documents = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            
            # Clean sanad - remove XML-like tags
            sanad_raw = row.get('Sanad', '')
            sanad_clean = re.sub(r'<[^>]+>', '', sanad_raw).strip()
            
            # Extract matn
            matn = row.get('Matn', '').strip()
            
            # Build content for embedding (combine matn + sanad + book)
            content_parts = []
            if matn:
                content_parts.append(matn)
            if sanad_clean and sanad_clean != "No SANAD":
                content_parts.append(sanad_clean)
            book = row.get('Book', '')
            if book:
                content_parts.append(book)
            
            content = " | ".join(content_parts)
            
            doc = {
                "chunk_index": i,
                "content": content,
                "metadata": {
                    "type": "hadith",
                    "book": book,
                    "num_hadith": row.get('Num_hadith', ''),
                    "matn": matn,
                    "sanad": sanad_clean,
                    "sanad_length": row.get('Sanad_Length', ''),
                    "dataset": "sanadset_368k",
                    "language": "ar",
                }
            }
            documents.append(doc)
    
    logger.info("sanadset.csv_parsed", total=len(documents), path=str(csv_path))
    return documents
