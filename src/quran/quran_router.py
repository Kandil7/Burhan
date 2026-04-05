"""
Quran Sub-Router for Athar Islamic QA system.

Classifies Quran queries into 4 sub-intents:
- QURAN_VERSE_LOOKUP: User wants specific verse
- QURAN_INTERPRETATION: User asks for meaning/tafsir
- QURAN_ANALYTICS: User asks for statistics (NL2SQL)
- QURAN_QUOTATION_VALIDATION: User verifies text

Phase 3: Routes Quran queries to specialized handlers.
"""
from enum import Enum
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger()


class QuranSubIntent(str, Enum):
    """Sub-intents for Quran queries."""
    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"


# Keyword patterns for fast-path classification
QURAN_KEYWORD_PATTERNS = {
    QuranSubIntent.VERSE_LOOKUP: [
        "آية", "اية", "سورة", "ayah", "surah",
        "آتني", "هات", "give me", "show me"
    ],
    QuranSubIntent.INTERPRETATION: [
        "تفسير", "معنى", "ما معنى", "tafsir", "interpretation",
        "what does", "what is the meaning", "يقصد"
    ],
    QuranSubIntent.ANALYTICS: [
        "كم عدد", "عدد", "count", "how many", "how much",
        "أطول", "shortest", "longest", "أقصر",
        "كم مرة", "how many times", "mentioned"
    ],
    QuranSubIntent.QUOTATION_VALIDATION: [
        "هل هذه آية", "هل هذا قرآن", "is this a verse",
        "is this quran", "آية من القرآن", "from the quran"
    ]
}


class QuranRouterError(Exception):
    """Error in Quran routing."""
    pass


class QuranSubRouter:
    """
    Router for Quran query sub-intents.
    
    Classifies into 4 categories and routes to appropriate handler.
    
    Usage:
        router = QuranSubRouter()
        sub_intent = router.classify("كم عدد آيات سورة البقرة؟")
        # Returns: QuranSubIntent.ANALYTICS
    """
    
    LLM_CLASSIFIER_PROMPT = """You are a sub-intent classifier for Quran queries.

Classify the user's query into exactly ONE of these sub-intents:

1. VERSE_LOOKUP: User wants a specific verse or surah text
   Examples: "آتني آية الكرسي", "Show me Al-Baqarah 255", "ما الآية 2 من الفاتحة"

2. INTERPRETATION: User asks for meaning or tafsir
   Examples: "ما معنى لا إكراه في الدين؟", "What does this verse mean?", "فسر هذه الآية"

3. ANALYTICS: User asks for statistics or counts
   Examples: "كم عدد آيات سورة البقرة؟", "How many verses in Quran?", "كم سورة مكية"

4. QUOTATION_VALIDATION: User verifies if text is from Quran
   Examples: "هل هذه آية: إني جاعلك للناس إمامًا", "Is this a Quran verse?", "هل هذا من القرآن"

Rules:
- Return ONLY the sub-intent name (VERSE_LOOKUP, INTERPRETATION, ANALYTICS, QUOTATION_VALIDATION)
- No explanations

Query: {query}"""
    
    def __init__(self, llm_client=None):
        """
        Initialize router.
        
        Args:
            llm_client: OpenAI client for LLM-based classification
        """
        self.llm_client = llm_client
    
    async def classify(self, query: str) -> QuranSubIntent:
        """
        Classify Quran query into sub-intent.
        
        Args:
            query: User's Quran-related query
            
        Returns:
            QuranSubIntent enum value
        """
        # Tier 1: Keyword matching (fast path)
        keyword_result = self._keyword_match(query)
        if keyword_result:
            logger.info(
                "quran_router.keyword_match",
                sub_intent=keyword_result.value
            )
            return keyword_result
        
        # Tier 2: LLM classification
        if self.llm_client:
            try:
                llm_result = await self._llm_classify(query)
                logger.info(
                    "quran_router.llm_classify",
                    sub_intent=llm_result.value
                )
                return llm_result
            except Exception as e:
                logger.error("quran_router.llm_error", error=str(e))
        
        # Default fallback
        logger.warning(
            "quran_router.default_fallback",
            default=QuranSubIntent.VERSE_LOOKUP.value
        )
        return QuranSubIntent.VERSE_LOOKUP
    
    def _keyword_match(self, query: str) -> QuranSubIntent:
        """Match query against keyword patterns."""
        query_lower = query.lower()
        
        for sub_intent, patterns in QURAN_KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    return sub_intent
        
        return None
    
    async def _llm_classify(self, query: str) -> QuranSubIntent:
        """LLM-based sub-intent classification."""
        try:
            prompt = self.LLM_CLASSIFIER_PROMPT.format(query=query)
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=50
            )
            
            result_text = response.choices[0].message.content.strip().upper()
            
            # Map to enum
            if "VERSE_LOOKUP" in result_text:
                return QuranSubIntent.VERSE_LOOKUP
            elif "INTERPRETATION" in result_text:
                return QuranSubIntent.INTERPRETATION
            elif "ANALYTICS" in result_text:
                return QuranSubIntent.ANALYTICS
            elif "QUOTATION_VALIDATION" in result_text:
                return QuranSubIntent.QUOTATION_VALIDATION
            else:
                return QuranSubIntent.VERSE_LOOKUP
                
        except Exception as e:
            logger.error("quran_router.llm_classify_error", error=str(e))
            raise
