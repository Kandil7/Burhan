"""
Detector for Quranic text misattributed to non-Quran sources.

Catches the third violation class:
  - Quranic text (صحيح قرآنياً) cited as [CX] where CX is a seerah/fiqh book
  - Quranic text inside «» with no citation but attributed via narrative context
  - distinct from source_attribution_violation (which catches "سورة: آية" refs)
  - distinct from strict_grounding_violation (which checks evidence presence)

Misattribution detection modes:
  MODE A — Explicit: ﴿...﴾ or «...» followed by [CX] within 60 chars
           → citation points to non-Quran book → flag
  MODE B — Implicit: «...» contains Quran verse, no [CX] follows,
           but narrative context attributes it to a person/book
           → flag as implicit_misattribution
  MODE C — Unattributed Quran in «»: verse inside «» with no [CX] at all
           → flag as delimiter_confusion (should use ﴿﴾ not «»)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.verifiers.exact_quote import ExactQuoteVerifier

logger = logging.getLogger(__name__)

# ── Patterns ──────────────────────────────────────────────────────────────────

# ﴿...﴾ — Quranic brackets only (strict)
_QURAN_BRACKETS_RE = re.compile(r"﴿(.{10,500}?)﴾", re.DOTALL)

# «...» — Arabic quotes (may contain hadith OR misused Quran)
_ARABIC_QUOTES_RE = re.compile(r"«(.{10,300}?)»", re.DOTALL)

# [CX] citation tag
_CITATION_TAG_RE = re.compile(r"\[C(\d+)\]")

# Narrative attribution patterns — "كما ذكرها X" / "قال X" / "كما قال"
# Used for MODE B detection
_NARRATIVE_ATTRIBUTION_RE = re.compile(
    r"(?:كما\s+(?:ذكرها|قالها|أوردها|رواها)\s+[\u0600-\u06FF\s]{3,30})"
    r"|(?:قال\s+(?:له|عنه)?\s*[\u0600-\u06FF\s]{3,20}[::]\s*[«﴿])"
    r"|(?:وصف(?:ه|ته|ها)?\s+(?:في\s+)?(?:التوراة|الإنجيل|الكتب\s+المقدسة))",
    re.UNICODE,
)

# Quran-source indicators — citations pointing to these are OK
_QURAN_SOURCE_KEYWORDS = {
    "القرآن الكريم",
    "المصحف",
    "quran",
    "سورة",
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _is_quran_citation(source_id: str, citations: list[dict]) -> bool:
    """Return True if the citation points to a Quran/tafsir source."""
    for c in citations:
        if c.get("source_id") == source_id:
            book = (c.get("book_title") or "").lower()
            collection = c.get("metadata", {}).get("collection", "")
            if any(k in book for k in _QURAN_SOURCE_KEYWORDS):
                return True
            if "quran" in collection.lower() or "tafsir" in collection.lower():
                return True
    return False


def _find_citation_after(answer: str, end_pos: int) -> str | None:
    """Return CX id if [CX] appears within 60 chars after end_pos."""
    tail = answer[end_pos: end_pos + 60]
    m = _CITATION_TAG_RE.search(tail)
    return f"C{m.group(1)}" if m else None


def _find_narrative_attribution_before(answer: str, start_pos: int) -> bool:
    """Return True if a narrative attribution pattern appears within 120 chars before start_pos."""
    prefix = answer[max(0, start_pos - 120): start_pos]
    return bool(_NARRATIVE_ATTRIBUTION_RE.search(prefix))


def _extract_all_quoted_segments(answer: str) -> list[dict]:
    """
    Extract all quoted segments with metadata.

    Returns list of dicts:
      {quote, delimiter_type, start, end, citation_id, has_narrative_attribution}
    """
    results = []

    for pattern, dtype in (
        (_QURAN_BRACKETS_RE, "quran"),
        (_ARABIC_QUOTES_RE, "arabic"),
    ):
        for match in pattern.finditer(answer):
            quote = match.group(1).strip()
            citation_id = _find_citation_after(answer, match.end())
            has_narrative = _find_narrative_attribution_before(answer, match.start())
            results.append(
                {
                    "quote": quote,
                    "delimiter_type": dtype,
                    "start": match.start(),
                    "end": match.end(),
                    "citation_id": citation_id,
                    "has_narrative_attribution": has_narrative,
                }
            )

    results.sort(key=lambda x: x["start"])
    return results


# ── Public API ────────────────────────────────────────────────────────────────


async def detect_misattributed_quran(
    answer: str,
    citations: list[dict],
    exact_quote_verifier: "ExactQuoteVerifier",
    min_length: int = 10,
) -> list[dict]:
    """
    Detect Quranic text misattributed to non-Quran sources.

    Three detection modes:

    MODE A — Explicit citation misattribution:
      ﴿...﴾ or «...» followed by [CX] pointing to non-Quran book
      → "quran_text_attributed_to_non_quran_source"

    MODE B — Implicit narrative misattribution:
      «...» contains Quran verse + narrative attribution context
      (كما ذكرها / وصفه في التوراة / قال عنه...)
      → "quran_text_implicitly_misattributed"

    MODE C — Delimiter confusion:
      Quran verse inside «» with no citation and no narrative context
      (should use ﴿﴾ not «»)
      → "quran_verse_in_wrong_delimiter"

    Args:
        answer:               Generated answer text
        citations:            List of citation dicts from AgentOutput
        exact_quote_verifier: Instance with is_quran_text() method
        min_length:           Minimum quote length to check

    Returns:
        List of violation dicts, empty if clean.
    """
    segments = _extract_all_quoted_segments(answer)
    violations: list[dict] = []

    for seg in segments:
        quote = seg["quote"]
        citation_id = seg["citation_id"]
        delimiter_type = seg["delimiter_type"]
        has_narrative = seg["has_narrative_attribution"]

        if len(quote) < min_length:
            continue

        # ﴿﴾ with correct Quran citation → skip
        if delimiter_type == "quran" and citation_id:
            if _is_quran_citation(citation_id, citations):
                continue

        # Expensive DB check — run only when above guards don't clear it
        try:
            is_quran = await exact_quote_verifier.is_quran_text(quote)
        except Exception:
            logger.warning(
                "misattribution_quran_check_failed for quote: %s",
                quote[:60],
                exc_info=True,
            )
            continue

        if not is_quran:
            continue

        # ── Quran text confirmed — determine violation mode ──

        matched_citation = next(
            (c for c in citations if c.get("source_id") == citation_id),
            None,
        )
        book_title = (
            matched_citation.get("book_title", "unknown")
            if matched_citation
            else "unknown"
        )

        # MODE A: Explicit [CX] → non-Quran book
        if citation_id and not _is_quran_citation(citation_id, citations):
            violations.append(
                {
                    "quote": quote,
                    "attributed_to": citation_id,
                    "book_title": book_title,
                    "issue": "quran_text_attributed_to_non_quran_source",
                    "mode": "explicit",
                }
            )
            logger.warning(
                "misattributed_quran [mode=explicit] quote='%s…' cited_as=%s book='%s'",
                quote[:40], citation_id, book_title,
            )

        # MODE B: «» + narrative attribution (e.g. attributed to Torah/person)
        elif delimiter_type == "arabic" and has_narrative:
            violations.append(
                {
                    "quote": quote,
                    "attributed_to": "narrative_context",
                    "book_title": "unknown",
                    "issue": "quran_text_implicitly_misattributed",
                    "mode": "implicit",
                }
            )
            logger.warning(
                "misattributed_quran [mode=implicit] quote='%s…' — "
                "Quran verse attributed via narrative (Torah/person)",
                quote[:40],
            )

        # MODE C: «» with no citation and no narrative — wrong delimiter
        elif delimiter_type == "arabic" and not citation_id and not has_narrative:
            violations.append(
                {
                    "quote": quote,
                    "attributed_to": None,
                    "book_title": "unknown",
                    "issue": "quran_verse_in_wrong_delimiter",
                    "mode": "delimiter_confusion",
                }
            )
            logger.warning(
                "misattributed_quran [mode=delimiter_confusion] quote='%s…' — "
                "Quran verse should use ﴿﴾ not «»",
                quote[:40],
            )

    return violations


__all__ = ["detect_misattributed_quran"]