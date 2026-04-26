"""
LLM-based Intent Classifier for Burhan Islamic QA system.

Uses any OpenAI-compatible chat completion API with JSON-mode output.
Temperature is fixed at 0.0 for deterministic, reproducible routing.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from src.application.router.hybrid_classifier import (
    _classify_quran_subintent,
    _detect_language,
    _infer_requires_retrieval,
)
from src.domain.intents import INTENT_DESCRIPTIONS, Intent, QuranSubIntent
from src.domain.models import ClassificationResult

logger = logging.getLogger(__name__)


# ============================================================================
# Prompt templates
# ============================================================================

_SYSTEM_PROMPT = (
    "You are an expert intent classifier for an Islamic QA system called Burhan. "
    "Return ONLY valid JSON — no markdown, no explanations, no code fences."
)

_USER_PROMPT = """\
Classify the user's Arabic or English query into exactly ONE intent.

Available intents:
{intent_descriptions}

Return JSON with these exact fields:
  intent            – one of the intent keys above (snake_case)
  confidence        – float 0.0–1.0
  language          – "ar" | "en" | "mixed"
  requires_retrieval – true if answering needs document retrieval, false otherwise
  sub_intent        – null UNLESS intent == "quran"; then one of:
                        "verse_lookup" | "interpretation" | "analytics" | "quotation_validation"
  reason            – one-sentence explanation
  sub_questions     – array of sub-questions if compound query, else []

━━━ Examples ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: "ما حكم ترك صلاة الجمعة عمداً؟"
{{"intent":"fiqh","confidence":0.95,"language":"ar","requires_retrieval":true,"sub_intent":null,"reason":"Asking legal ruling on abandoning Friday prayer","sub_questions":[]}}

Query: "كم عدد آيات سورة البقرة؟"
{{"intent":"quran","confidence":0.98,"language":"ar","requires_retrieval":false,"sub_intent":"analytics","reason":"Asking verse count — NL2SQL query","sub_questions":[]}}

Query: "اقرأ لي آية الكرسي"
{{"intent":"quran","confidence":0.97,"language":"ar","requires_retrieval":false,"sub_intent":"verse_lookup","reason":"User wants the text of Ayat al-Kursi","sub_questions":[]}}

Query: "Is it permissible to trade cryptocurrency?"
{{"intent":"fiqh","confidence":0.88,"language":"en","requires_retrieval":true,"sub_intent":null,"reason":"Legal ruling on crypto trading","sub_questions":[]}}

Query: "ما الفرق بين أهل السنة والشيعة من حيث العقيدة والتاريخ؟"
{{"intent":"aqeedah","confidence":0.82,"language":"ar","requires_retrieval":true,"sub_intent":null,"reason":"Theological comparison — primary aspect is creed","sub_questions":["ما عقيدة أهل السنة؟","ما عقيدة الشيعة؟","ما الفرق التاريخي بينهما؟"]}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: {query}"""


# ============================================================================
# LLMIntentClassifier
# ============================================================================


class LLMIntentClassifier:
    """
    LLM-based intent classifier conforming to the IntentClassifier protocol.

    Uses any OpenAI-compatible chat completion API with JSON-mode output.
    Temperature is fixed at 0.0 for deterministic, reproducible routing.

    Safety guarantees
    ───────────────
    • Unknown intent strings returned by the LLM are caught and mapped to ISLAMIC_KNOWLEDGE
    • Unknown sub_intent strings fall back to pattern-based Quran sub-classification
    • If raise_on_error=False (default), any API/network failure returns a safe
      ISLAMIC_KNOWLEDGE fallback instead of a 500 error.
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 350,
        raise_on_error: bool = False,
    ) -> None:
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._raise_on_error = raise_on_error

        # Pre-format intent descriptions once at init — reused on every call
        self._intent_descriptions = "\n".join(f"  {k.value}: {v}" for k, v in INTENT_DESCRIPTIONS.items())

    async def classify(self, query: str) -> ClassificationResult:
        """Classify query using LLM."""
        if not query or not query.strip():
            return _empty_query_result()

        try:
            return await self._call_llm(query)
        except Exception as exc:
            logger.error(
                "llm_classifier.error",
                exc_info=exc,
                extra={"model": self._model, "query_len": len(query)},
            )
            if self._raise_on_error:
                raise
            return _error_fallback_result(query, exc)

    async def close(self) -> None:
        """Clean up resources (no-op for this classifier)."""
        pass

    # ============================================================================
    # Private helpers
    # ============================================================================

    async def _call_llm(self, query: str) -> ClassificationResult:
        """Call LLM for classification."""
        prompt = _USER_PROMPT.format(
            intent_descriptions=self._intent_descriptions,
            query=query,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,  # 0.0 → deterministic routing
            max_tokens=self._max_tokens,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content.strip()
        logger.debug(
            "llm_classifier.response",
            extra={"preview": raw_content[:300], "model": self._model},
        )

        try:
            raw = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        return self._parse(raw, query)

    def _parse(self, raw: dict, query: str) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        # ── intent (safe cast) ────────────────────────────────────────────
        intent_str = raw.get("intent", "islamic_knowledge")
        try:
            intent = Intent(intent_str)
        except ValueError:
            logger.warning(
                "llm_classifier.unknown_intent",
                extra={"raw_intent": intent_str, "mapped_to": "islamic_knowledge"},
            )
            intent = Intent.ISLAMIC_KNOWLEDGE

        # ── scalar fields ────────────────────────────────────────────────
        confidence = float(raw.get("confidence", 0.80))
        confidence = max(0.0, min(1.0, confidence))

        language = raw.get("language") or _detect_language(query)
        if language not in ("ar", "en", "mixed"):
            language = _detect_language(query)

        requires_retrieval = bool(raw.get("requires_retrieval", True))
        reason = str(raw.get("reason", "LLM classification"))

        subquestions = raw.get("sub_questions", [])
        if not isinstance(subquestions, list):
            subquestions = []
        subquestions = [str(q) for q in subquestions if q]

        # ── Quran sub-intent (safe cast + pattern fallback) ───────────────
        q_sub: Optional[QuranSubIntent] = None
        if intent is Intent.QURAN:
            sub_str = raw.get("sub_intent")
            if sub_str:
                try:
                    q_sub = QuranSubIntent(sub_str)
                except ValueError:
                    logger.warning(
                        "llm_classifier.unknown_sub_intent",
                        extra={"raw_sub_intent": sub_str},
                    )
                    q_sub, _ = _classify_quran_subintent(query)
            else:
                q_sub, _ = _classify_quran_subintent(query)

            requires_retrieval = _infer_requires_retrieval(intent, q_sub)

        return ClassificationResult(
            intent=intent,
            confidence=round(confidence, 4),
            language=language,
            reasoning=reason,
            requires_retrieval=requires_retrieval,
            method="llm",
            quran_subintent=q_sub,
            subquestions=subquestions,
        )


# ============================================================================
# Helpers
# ============================================================================


def _empty_query_result() -> ClassificationResult:
    """Return ClassificationResult for empty query."""
    return ClassificationResult(
        intent=Intent.ISLAMIC_KNOWLEDGE,
        confidence=0.50,
        language="ar",
        reasoning="Empty query — defaulted to general Islamic knowledge.",
        requires_retrieval=False,
        method="fallback",
    )


def _error_fallback_result(query: str, exc: Exception) -> ClassificationResult:
    """Return ClassificationResult for LLM error."""
    return ClassificationResult(
        intent=Intent.ISLAMIC_KNOWLEDGE,
        confidence=0.40,
        language=_detect_language(query),
        reasoning=(
            f"LLM classification failed ({type(exc).__name__}) — graceful fallback to general Islamic knowledge."
        ),
        requires_retrieval=True,
        method="fallback",
    )
