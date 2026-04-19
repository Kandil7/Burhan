# src/verifiers/misattribution.py
"""
Detector for Quranic text misattributed to non-Quran sources.

Catches the third violation class:
  - Quranic text (صحيح قرآنياً) cited as [CX] where CX is a seerah/fiqh book
  - distinct from source_attribution_violation (which catches "سورة: آية" refs)
  - distinct from strict_grounding_violation (which checks evidence presence)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.verifiers.exact_quote import ExactQuoteVerifier

logger = logging.getLogger(__name__)

# ── Patterns ─────────────────────────────────────────────────────────────────

# Captures text inside ﴿…﴾ or «…» or "…"
_QURAN_BRACKETS_RE = re.compile(
    r"[﴿«\"](.{10,200}?)[﴾»\"]",
    re.DOTALL,
)

# Captures citation tag immediately after the quote: [C1], [C2], …
# Must be within 60 chars of the closing bracket
_CITATION_TAG_RE = re.compile(r"\[C(\d+)\]")

# Quran-source indicators — if the citation points to these, it's OK
_QURAN_SOURCE_KEYWORDS = {
    "القرآن الكريم",
    "المصحف",
    "quran",
    "سورة",
}


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


def _extract_quoted_segments_with_citations(
    answer: str,
) -> list[dict]:
    """
    Extract (quote_text, citation_id) pairs from answer.

    Looks for text in ﴿﴾ / «» / "" followed by [CX] within 60 chars.
    Returns list of dicts: {quote, citation_id}
    """
    results = []
    for match in _QURAN_BRACKETS_RE.finditer(answer):
        quote = match.group(1).strip()
        # Search for [CX] in the 60 chars after the closing bracket
        tail = answer[match.end() : match.end() + 60]
        cit_match = _CITATION_TAG_RE.search(tail)
        citation_id = f"C{cit_match.group(1)}" if cit_match else None
        results.append({"quote": quote, "citation_id": citation_id})
    return results


async def detect_misattributed_quran(
    answer: str,
    citations: list[dict],
    exact_quote_verifier: "ExactQuoteVerifier",
    min_length: int = 10,
) -> list[dict]:
    """
    Detect Quranic text attributed to non-Quran citations.

    A segment is flagged when ALL three conditions hold:
      1. It's enclosed in Quran-style brackets (﴿﴾ / «» / "")
      2. It matches a Quranic verse via QuotationValidator
      3. The following citation [CX] points to a non-Quran book

    Args:
        answer:               Generated answer text
        citations:            List of citation dicts from AgentOutput
        exact_quote_verifier: Instance with is_quran_text() method
        min_length:           Minimum quote length to check (avoids noise)

    Returns:
        List of violation dicts, empty if clean.
    """
    segments = _extract_quoted_segments_with_citations(answer)
    violations: list[dict] = []

    for seg in segments:
        quote = seg["quote"]
        citation_id = seg["citation_id"]

        if len(quote) < min_length:
            continue

        # Skip if no citation follows (handled by source_attribution check)
        if not citation_id:
            continue

        # Skip if citation already points to Quran source
        if _is_quran_citation(citation_id, citations):
            continue

        # Expensive check last — only call DB if above filters pass
        try:
            is_quran = await exact_quote_verifier.is_quran_text(quote)
        except Exception:
            logger.warning(
                "misattribution_quran_check_failed for quote: %s",
                quote[:60],
                exc_info=True,
            )
            continue

        if is_quran:
            # Find matching citation metadata for reporting
            matched_citation = next(
                (c for c in citations if c.get("source_id") == citation_id),
                None,
            )
            violations.append(
                {
                    "quote": quote,
                    "attributed_to": citation_id,
                    "book_title": (
                        matched_citation.get("book_title", "unknown")
                        if matched_citation
                        else "unknown"
                    ),
                    "issue": "quran_text_attributed_to_non_quran_source",
                }
            )
            logger.warning(
                "misattributed_quran_detected: quote='%s…' cited_as=%s book='%s'",
                quote[:40],
                citation_id,
                matched_citation.get("book_title", "") if matched_citation else "",
            )

    return violations


__all__ = ["detect_misattributed_quran"]