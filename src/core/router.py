"""
Hybrid Intent Classifier for Athar Islamic QA system.

Implements a three-tier classification approach:
1. Keyword matching (fast path for clear signals)
2. LLM classification (primary path with structured JSON)
3. Embedding similarity (fallback for low confidence)

Based on Fanar-Sadiq architecture achieving ~90% accuracy.
"""
import json
from typing import Optional

from pydantic import BaseModel, Field

from src.config.intents import (
    Intent,
    INTENT_DESCRIPTIONS,
    KEYWORD_PATTERNS,
)
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()


class RouterResult(BaseModel):
    """Result from intent classification."""
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    method: str = Field(description="Classification method: keyword, llm, or embedding")
    language: str = Field(default="ar", description="Detected language: ar or en")
    requires_retrieval: bool = Field(
        default=True,
        description="Whether this query needs document retrieval (RAG)"
    )
    sub_intent: Optional[str] = Field(
        default=None,
        description="Sub-intent for Quran queries (verse_lookup, interpretation, etc.)"
    )
    reason: str = Field(default="", description="Reasoning for classification")


class HybridQueryClassifier:
    """
    Three-tier hybrid intent classifier.
    
    Tier 1: Keyword matching (fast path, confidence >= 0.90)
    Tier 2: LLM classification (primary path, confidence >= threshold)
    Tier 3: Embedding similarity (fallback when LLM confidence is low)
    
    Usage:
        classifier = HybridQueryClassifier(llm_client=openai_client)
        result = await classifier.classify("ما حكم زكاة المال؟")
        # RouterResult(intent=Intent.ZAKAT, confidence=0.92, method="keyword")
    """
    
    CONFIDENCE_THRESHOLD = 0.75
    
    LLM_CLASSIFIER_PROMPT = """You are an expert intent classifier for an Islamic QA system called Athar.

Your task is to classify the user's query into exactly ONE intent from the list below.

Available Intents:
{intent_descriptions}

Rules:
- Return ONLY valid JSON with these exact fields:
  - intent: one of the valid intents above (lowercase, with underscores)
  - confidence: float between 0.0 and 1.0 (your confidence in this classification)
  - language: "ar" if the query is mostly Arabic script, "en" otherwise
  - requires_retrieval: true if answering requires retrieving documents (fatwas, hadith, etc.), false otherwise
  - sub_intent: null unless intent is "quran", then use one of:
    - "verse_lookup" (user wants a specific verse/surah text)
    - "interpretation" (user asks for meaning/tafsir)
    - "analytics" (user asks for statistics: count, length, etc.)
    - "quotation_validation" (user asks if some text is a Quran verse)
  - reason: brief explanation of why you chose this intent
  - sub_questions: array of sub-questions if the query is compound (can be empty [])

Examples:

Query: "ما حكم ترك صلاة الجمعة عمداً؟"
Output:
{{"intent":"fiqh","confidence":0.95,"language":"ar","requires_retrieval":true,"sub_intent":null,"reason":"Asking legal ruling about Friday prayer obligation","sub_questions":[]}}

Query: "كم عدد آيات سورة البقرة؟"
Output:
{{"intent":"quran","confidence":0.98,"language":"ar","requires_retrieval":false,"sub_intent":"analytics","reason":"Asking for count of verses in Surah Al-Baqarah","sub_questions":[]}}

Query: "How do I calculate zakat on my savings?"
Output:
{{"intent":"zakat","confidence":0.93,"language":"en","requires_retrieval":false,"sub_intent":null,"reason":"User wants to calculate zakat amount","sub_questions":[]}}

Query: "Is it permissible to trade cryptocurrency?"
Output:
{{"intent":"fiqh","confidence":0.88,"language":"en","requires_retrieval":true,"sub_intent":null,"reason":"Asking legal ruling on cryptocurrency trading","sub_questions":[]}}

Now classify this query. Return ONLY valid JSON, no explanations.

Query: {query}"""
    
    def __init__(self, llm_client=None, embed_client=None):
        """
        Initialize the classifier.
        
        Args:
            llm_client: OpenAI-compatible client for classification
            embed_client: Embedding client for fallback (Phase 5)
        """
        self.llm_client = llm_client
        self.embed_client = embed_client
    
    async def classify(self, query: str) -> RouterResult:
        """
        Classify user query using three-tier approach.
        
        Args:
            query: User's question
            
        Returns:
            RouterResult with intent, confidence, and metadata
        """
        if not query or not query.strip():
            return RouterResult(
                intent=Intent.GREETING,
                confidence=0.5,
                method="fallback",
                reason="Empty query, defaulting to greeting"
            )
        
        # ==========================================
        # Tier 1: Keyword matching (fast path)
        # ==========================================
        keyword_result = self._keyword_match(query)
        if keyword_result and keyword_result.confidence >= 0.90:
            logger.info(
                "router.keyword_match",
                intent=keyword_result.intent.value,
                confidence=keyword_result.confidence,
                method="keyword"
            )
            return keyword_result
        
        # ==========================================
        # Tier 2: LLM classification (primary)
        # ==========================================
        if self.llm_client:
            try:
                llm_result = await self._llm_classify(query)
                if llm_result.confidence >= self.CONFIDENCE_THRESHOLD:
                    logger.info(
                        "router.llm_classify",
                        intent=llm_result.intent.value,
                        confidence=llm_result.confidence,
                        method="llm"
                    )
                    return llm_result
            except Exception as e:
                logger.error("router.llm_error", error=str(e))
                # Continue to fallback
        
        # ==========================================
        # Tier 3: Embedding fallback (backup)
        # ==========================================
        if self.embed_client and settings.router_fallback_enabled:
            try:
                embed_result = await self._embedding_classify(query)
                logger.info(
                    "router.embedding_classify",
                    intent=embed_result.intent.value,
                    confidence=embed_result.confidence,
                    method="embedding"
                )
                return embed_result
            except Exception as e:
                logger.error("router.embedding_error", error=str(e))
        
        # ==========================================
        # Default fallback
        # ==========================================
        logger.warning(
            "router.default_fallback",
            query=query[:100],
            default_intent=Intent.ISLAMIC_KNOWLEDGE.value
        )
        
        return RouterResult(
            intent=Intent.ISLAMIC_KNOWLEDGE,
            confidence=0.5,
            method="fallback",
            language=self._detect_language(query),
            reason="No classifier matched with sufficient confidence, defaulting to general knowledge"
        )
    
    def _keyword_match(self, query: str) -> Optional[RouterResult]:
        """
        Fast keyword-based intent detection.
        
        Checks query against known keyword patterns for each intent.
        Returns result if match found with high confidence.
        """
        query_lower = query.lower()
        language = self._detect_language(query)
        
        for intent, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    return RouterResult(
                        intent=intent,
                        confidence=0.92,
                        method="keyword",
                        language=language,
                        requires_retrieval=intent in [
                            Intent.FIQH,
                            Intent.ISLAMIC_KNOWLEDGE,
                            Intent.QURAN,
                        ],
                        reason=f"Keyword match: '{pattern}'"
                    )
        
        return None
    
    async def _llm_classify(self, query: str) -> RouterResult:
        """
        LLM-based intent classification.
        
        Sends structured prompt to LLM and parses JSON response.
        """
        try:
            # Build prompt with intent descriptions
            intent_descriptions = "\n".join(
                f"- {k.value}: {v}" for k, v in INTENT_DESCRIPTIONS.items()
            )
            
            prompt = self.LLM_CLASSIFIER_PROMPT.format(
                intent_descriptions=intent_descriptions,
                query=query
            )
            
            # Call LLM
            response = await self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent classifier. Return ONLY valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = json.loads(content)
            
            # Validate and normalize
            intent = Intent(result.get("intent", Intent.ISLAMIC_KNOWLEDGE))
            confidence = float(result.get("confidence", 0.8))
            language = result.get("language", self._detect_language(query))
            requires_retrieval = result.get("requires_retrieval", True)
            sub_intent = result.get("sub_intent")
            reason = result.get("reason", "LLM classification")
            
            return RouterResult(
                intent=intent,
                confidence=confidence,
                method="llm",
                language=language,
                requires_retrieval=requires_retrieval,
                sub_intent=sub_intent,
                reason=reason
            )
            
        except json.JSONDecodeError as e:
            logger.error("router.llm_json_error", error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error("router.llm_error", error=str(e))
            raise
    
    async def _embedding_classify(self, query: str) -> RouterResult:
        """
        Embedding-based fallback classification.
        
        Compares query embedding to labeled examples.
        To be implemented in Phase 5 with embedding pipeline.
        """
        # Phase 1: Placeholder implementation
        # Phase 5: Will use Qwen3-Embedding + cosine similarity to labeled queries
        
        logger.warning("router.embedding_not_implemented", fallback="islamic_knowledge")
        
        return RouterResult(
            intent=Intent.ISLAMIC_KNOWLEDGE,
            confidence=0.6,
            method="embedding",
            reason="Embedding classifier not yet implemented (Phase 5)"
        )
    
    def _detect_language(self, query: str) -> str:
        """
        Detect if query is Arabic or English.
        
        Uses Unicode range detection for Arabic script.
        """
        arabic_chars = sum(
            1 for char in query
            if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F'
        )
        
        total_chars = len(query.replace(" ", ""))
        if total_chars == 0:
            return "ar"
        
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"
