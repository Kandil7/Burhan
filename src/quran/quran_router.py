"""
Quran Sub-Router for Athar Islamic QA system.

Fixes:
  - _keyword_match: specific patterns evaluated BEFORE generic ones
    (QUOTATION_VALIDATION and INTERPRETATION checked first)
  - _keyword_match return type corrected to QuranSubIntent | None
  - _llm_classify: exact token match replaces loose `in` substring check
"""
from __future__ import annotations

from src.config.intents import QuranSubIntent
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


# ── Keyword patterns ───────────────────────────────────────────────────────────
# ORDER MATTERS: more-specific patterns must appear before generic ones.
# Evaluated top-to-bottom; first match wins.
#
# Wrong order example:
#   VERSE_LOOKUP has "آية" → catches "هل هذه آية؟" before QUOTATION_VALIDATION runs.
#
# Correct order: QUOTATION_VALIDATION → INTERPRETATION → ANALYTICS → VERSE_LOOKUP

QURAN_KEYWORD_PATTERNS: list[tuple[QuranSubIntent, list[str]]] = [
    # 1. Most specific — explicit verification phrasing
    (
        QuranSubIntent.QUOTATION_VALIDATION,
        [
            "هل هذه آية",       # "هل هذه آية من القرآن؟"
            "هل هذا قرآن",
            "هل هذا من القرآن",
            "is this a verse",
            "is this quran",
            "is this from the quran",
            "آية من القرآن",
            "verify",
            "تحقق",
        ],
    ),
    # 2. Interpretation / tafsir
    (
        QuranSubIntent.INTERPRETATION,
        [
            "تفسير",
            "ما معنى",
            "معنى",
            "يقصد",
            "tafsir",
            "interpretation",
            "what does",
            "what is the meaning",
            "explain",
            "اشرح",
            "فسر",
        ],
    ),
    # 3. Statistics / analytics
    (
        QuranSubIntent.ANALYTICS,
        [
            "كم عدد",
            "عدد آيات",
            "كم مرة",
            "كم سورة",
            "كم آية",
            "how many",
            "how much",
            "count",
            "أطول",
            "أقصر",
            "longest",
            "shortest",
            "mentioned",
            "statistics",
            "إحصاء",
        ],
    ),
    # 4. Generic verse lookup — LAST (contains broad terms like "آية", "سورة")
    (
        QuranSubIntent.VERSE_LOOKUP,
        [
            "اقرأ",
            "آتني",
            "أعطني",
            "هات",
            "اعرض",
            "give me",
            "show me",
            "read",
            "fetch",
            "surah",
            "سورة",
            "ayah",
            "آية",         # generic — must stay LAST
            "اية",
        ],
    ),
]

# ── LLM prompt ────────────────────────────────────────────────────────────────

_LLM_PROMPT = """\
You are a sub-intent classifier for Quran queries.

Classify the user's query into exactly ONE of these sub-intents:

VERSE_LOOKUP         – User wants a specific verse or surah text.
                       e.g. "آتني آية الكرسي", "Show me Al-Baqarah 255"

INTERPRETATION       – User asks for meaning or tafsir.
                       e.g. "ما معنى لا إكراه في الدين؟", "What does this verse mean?"

ANALYTICS            – User asks for statistics or counts.
                       e.g. "كم عدد آيات سورة البقرة؟", "How many Meccan surahs?"

QUOTATION_VALIDATION – User verifies whether text is from the Quran.
                       e.g. "هل هذه آية: إني جاعلك للناس إمامًا"

Return ONLY the sub-intent name. No punctuation. No explanation.

Query: {query}"""

# Valid LLM responses (exact set)
_VALID_LLM_TOKENS: dict[str, QuranSubIntent] = {
    "VERSE_LOOKUP":          QuranSubIntent.VERSE_LOOKUP,
    "INTERPRETATION":        QuranSubIntent.INTERPRETATION,
    "ANALYTICS":             QuranSubIntent.ANALYTICS,
    "QUOTATION_VALIDATION":  QuranSubIntent.QUOTATION_VALIDATION,
}


class QuranRouterError(Exception):
    """Error in Quran routing."""


class QuranSubRouter:
    """
    Two-tier classifier for Quran query sub-intents.

    Tier 1: Keyword matching (zero latency, deterministic).
    Tier 2: LLM classification (when keywords are ambiguous).
    Fallback: VERSE_LOOKUP.
    """

    def __init__(self, llm_client=None) -> None:
        self.llm_client = llm_client

    # ── Public API ─────────────────────────────────────────────────────────────

    async def classify(self, query: str) -> QuranSubIntent:
        """
        Classify a Quran-related query into a QuranSubIntent.

        Args:
            query: Raw user query.

        Returns:
            QuranSubIntent enum value.
        """
        # Tier 1: keyword match
        keyword_result = self._keyword_match(query)
        if keyword_result is not None:
            logger.info("quran_router.keyword_match",
                        query=query[:60], sub_intent=keyword_result.value)
            return keyword_result

        # Tier 2: LLM
        if self.llm_client:
            try:
                llm_result = await self._llm_classify(query)
                logger.info("quran_router.llm_classify",
                            query=query[:60], sub_intent=llm_result.value)
                return llm_result
            except Exception as e:
                logger.error("quran_router.llm_error", error=str(e), exc_info=True)

        # Fallback
        logger.warning("quran_router.default_fallback",
                       query=query[:60], default=QuranSubIntent.VERSE_LOOKUP.value)
        return QuranSubIntent.VERSE_LOOKUP

    # ── Tier 1: keyword ────────────────────────────────────────────────────────

    def _keyword_match(self, query: str) -> QuranSubIntent | None:
        """
        Evaluate patterns in priority order (specific → generic).

        Returns the first matching QuranSubIntent, or None.
        """
        query_lower = query.lower()

        for sub_intent, patterns in QURAN_KEYWORD_PATTERNS:
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    return sub_intent

        return None

    # ── Tier 2: LLM ───────────────────────────────────────────────────────────

    async def _llm_classify(self, query: str) -> QuranSubIntent:
        """
        Call the LLM and parse its response into a QuranSubIntent.

        Raises QuranRouterError if the response is unrecognised.
        """
        prompt = _LLM_PROMPT.format(query=query)

        response = await self.llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=20,          # sub-intent name is ≤ 25 chars
        )

        raw = response.choices[0].message.content.strip().upper()

        # Exact token match first (most reliable)
        if raw in _VALID_LLM_TOKENS:
            return _VALID_LLM_TOKENS[raw]

        # Substring fallback — check longest token first to avoid partial hits
        for token in sorted(_VALID_LLM_TOKENS, key=len, reverse=True):
            if token in raw:
                return _VALID_LLM_TOKENS[token]

        # Unrecognised response — log and raise so caller uses fallback
        logger.warning("quran_router.llm_unknown_response", raw=raw)
        raise QuranRouterError(f"LLM returned unrecognised sub-intent: {raw!r}")