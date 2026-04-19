"""
Quote span detection for Athar verification pipeline.

Design contract (enforced by tests):
  ✅  ﴿...﴾   — Quranic brackets        → extract inner text (strict match)
  ✅  «...»   — Arabic quotation marks  → extract inner text (strict match)
  ✅  "..."   — Neutral double quotes   → extract inner text (relaxed match)
  ❌  [CX] sentence...  — citation + narrative  → NOT a quote
  ❌  sentence... [CX]  — narrative + citation  → NOT a quote
  ❌  كما ورد في [CX]  — paraphrase prefix     → NOT a quote

Delimiter policy (consumed by ExactQuoteVerifier):
  quran / arabic → strict exact substring match required
  neutral        → relaxed fuzzy match (0.75) — may be LLM paraphrase
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class QuoteSpan:
    """Represents a span of explicitly delimited quoted text."""

    start: int
    end: int
    text: str
    delimiter_type: str = "unknown"  # quran | arabic | neutral
    is_arabic: bool = False
    validation_status: Optional[str] = None


# ── Compiled patterns (delimiter-pair based only) ────────────────────────────

# ﴿...﴾ — Quranic verses, 5–500 chars
_QURAN_RE = re.compile(r"﴿(.{5,500}?)﴾", re.DOTALL | re.UNICODE)

# «...» — Arabic quotation marks, 5–300 chars
_ARABIC_RE = re.compile(r"«(.{5,300}?)»", re.DOTALL | re.UNICODE)

# "..." — neutral double quotes, 3–150 chars
# Upper bound intentionally tight to exclude narrative sentences.
# NOTE: Neutral quotes are treated as LLM paraphrase candidates —
# ExactQuoteVerifier applies relaxed (fuzzy) matching for this type.
_NEUTRAL_RE = re.compile(r'"(.{3,150}?)"', re.DOTALL | re.UNICODE)

# Union for has_quotes() fast check
_ANY_QUOTE_RE = re.compile(
    r'﴿.{5,500}?﴾|«.{5,300}?»|".{3,150}?"',
    re.DOTALL | re.UNICODE,
)

_PATTERNS: list[tuple[re.Pattern, str, bool]] = [
    (_QURAN_RE,   "quran",   True),
    (_ARABIC_RE,  "arabic",  True),
    (_NEUTRAL_RE, "neutral", False),
]

# delimiter_type values that require strict exact match in the verifier
STRICT_DELIMITER_TYPES: frozenset[str] = frozenset({"quran", "arabic"})

# delimiter_type values where relaxed fuzzy match is acceptable
RELAXED_DELIMITER_TYPES: frozenset[str] = frozenset({"neutral"})


class QuoteSpanDetector:
    """
    Detects explicitly delimited quotations in Arabic/Islamic text.

    Only recognises text enclosed in a matched delimiter pair:
        ﴿﴾  «»  ""

    Intentionally ignores:
        - Narrative sentences attributed to [CX] citations
        - Paraphrase introduced by كما ورد / أشار / ذكر
        - Any text not inside a recognised opening+closing delimiter

    Delimiter semantics for downstream verifiers:
        quran / arabic → strict exact match (Quran verses, hadiths)
        neutral        → relaxed fuzzy match (may be LLM summary)
    """

    # ── Public API ────────────────────────────────────────────────────────

    def extract_quote_content(self, text: str) -> list[str]:
        """
        Extract inner content of all delimited quotations.

        Returns deduplicated list in order of appearance.
        Returns [] if no delimited quotes are found.

        NOTE: Downstream callers that need match-strictness info
        should use extract_with_spans() instead.

        Examples:
            >>> d = QuoteSpanDetector()
            >>> d.extract_quote_content('قال ﴿وما أرسلناك إلا رحمة﴾ وأضاف «المتوكل»')
            ['وما أرسلناك إلا رحمة', 'المتوكل']

            >>> d.extract_quote_content('كما ورد في النص [C6] أن القوم نقضوا.')
            []
        """
        if not text:
            return []

        seen: set[str] = set()
        results: list[str] = []

        for pattern, _, _ in _PATTERNS:
            for match in pattern.finditer(text):
                content = match.group(1).strip()
                if content and content not in seen:
                    seen.add(content)
                    results.append(content)

        return results

    def detect_quotes(self, text: str) -> list[QuoteSpan]:
        """
        Detect all delimited quote spans with position metadata.

        Returns list of QuoteSpan sorted by start position.
        """
        if not text:
            return []

        seen: set[str] = set()
        spans: list[QuoteSpan] = []

        for pattern, dtype, is_arabic in _PATTERNS:
            for match in pattern.finditer(text):
                content = match.group(1).strip()
                if content and content not in seen:
                    seen.add(content)
                    spans.append(
                        QuoteSpan(
                            start=match.start(),
                            end=match.end(),
                            text=content,
                            delimiter_type=dtype,
                            is_arabic=is_arabic,
                        )
                    )

        spans.sort(key=lambda s: s.start)
        return spans

    def extract_with_spans(self, text: str) -> list[dict]:
        """
        Extract quotes with their character spans and delimiter type.

        Used by ExactQuoteVerifier to apply per-type match strictness:
          - delimiter_type in STRICT_DELIMITER_TYPES  → exact match
          - delimiter_type in RELAXED_DELIMITER_TYPES → fuzzy match

        Returns:
            List of dicts sorted by start position:
            {content, start, end, delimiter_type, requires_strict_match}
        """
        return [
            {
                "content": s.text,
                "start": s.start,
                "end": s.end,
                "delimiter_type": s.delimiter_type,
                "requires_strict_match": s.delimiter_type in STRICT_DELIMITER_TYPES,
            }
            for s in self.detect_quotes(text)
        ]

    def has_quotes(self, text: str) -> bool:
        """Return True if text contains any delimited quotation."""
        return bool(_ANY_QUOTE_RE.search(text)) if text else False

    def validate_span(
        self,
        span: QuoteSpan,
        source_text: str,
    ) -> bool:
        """
        Validate that a quote span's text appears in source_text.

        Args:
            span:        QuoteSpan to validate
            source_text: Reference text to search in

        Returns:
            True if span.text is a substring of source_text
        """
        if not source_text:
            return False
        return span.text in source_text


# Default singleton
quote_span_detector = QuoteSpanDetector()

__all__ = [
    "QuoteSpan",
    "QuoteSpanDetector",
    "quote_span_detector",
    "STRICT_DELIMITER_TYPES",
    "RELAXED_DELIMITER_TYPES",
]