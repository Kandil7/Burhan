"""
Citation service layer for Athar.

- Adapter from raw API payloads to core.Citation.
- Formatting (inline + footnotes).
- Stats computation for metadata/evaluation.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import List, Dict, Any, Tuple

from src.core.citation import Citation, compute_citation_stats, CitationStats


# --------- 1. Adapter: raw API JSON -> Citation --------- #

def citation_from_raw(raw: Dict[str, Any]) -> Citation:
    """
    Convert a raw citation payload (current Athar response format)
    into a clean Citation object.

    Expected raw format (example):
      {
        "source_id": "C6",
        "text": "...",
        "book_title": "...",
        "page": 528,
        "metadata": {
          "book_id": 122396,
          "page_number": 528,
          "section_title": "...",
          "collection": "seerah_passages",
          "category": "السيرة النبوية",
          "content_type": "page",
          ...
        }
      }
    """
    md = raw.get("metadata", {}) or {}

    book_id = md.get("book_id")
    page_number = md.get("page_number")
    section_title = md.get("section_title")

    # Human-friendly reference
    if section_title:
        reference = section_title
        if page_number:
            reference += f" (ص {page_number})"
    elif page_number:
        reference = f"ص {page_number}"
    else:
        snippet = (raw.get("text") or "").strip().replace("\n", " ")
        reference = snippet[:40] + ("..." if len(snippet) > 40 else "")

    return Citation(
        source_id=str(book_id) if book_id is not None else str(raw.get("source_id", "")),
        source_name=raw.get("book_title", ""),
        reference=reference,
        text=raw.get("text", "") or "",
        chapter=md.get("chapter"),
        verse=None,
        hadith_number=None,
        page=str(page_number) if page_number is not None else None,
        collection=md.get("collection"),
        category=md.get("category"),
        content_type=md.get("content_type"),
        authority_weight=1.0,  # tweak later if needed
    )


def citations_from_response(resp: Dict[str, Any]) -> List[Citation]:
    """Extract all citations from a full Athar agent response dict."""
    raw_list = resp.get("citations", []) or []
    return [citation_from_raw(c) for c in raw_list]


# --------- 2. Formatting: inline + footnotes --------- #

INLINE_PATTERN = re.compile(r"\[(C\d+)\]")  # matches [C1], [C6], ...


def _citation_key(c: Citation) -> Tuple[str, str]:
    """Key for deduplication: (source_id, page)."""
    return (c.source_id or "", c.page or "")


def dedupe_citations(citations: List[Citation]) -> List[Citation]:
    """Deduplicate citations by (source_id, page)."""
    seen: Dict[Tuple[str, str], Citation] = {}
    for c in citations:
        key = _citation_key(c)
        if key not in seen:
            seen[key] = c
    return list(seen.values())


def format_citation_bracket(c: Citation) -> str:
    """
    Format a single citation as a bracketed string for user display.

    Example:
      [السيرة النبوية الصحيحة محاولة لتطبيق قواعد المحدثين في نقد روايات السيرة النبوية، ص 528]
    """
    parts = []
    if c.source_name:
        parts.append(c.source_name)
    if c.reference:
        parts.append(c.reference)
    elif c.page:
        parts.append(f"ص {c.page}")
    text = "، ".join(parts) if parts else c.source_id
    return f"[{text}]"


def build_footnotes(citations: List[Citation]) -> List[str]:
    """
    Build a numbered footnote list without duplicates.

    Example:
      "1. السيرة النبوية الصحيحة ... – ص 528"
    """
    unique = dedupe_citations(citations)
    footnotes: List[str] = []
    for idx, c in enumerate(unique, start=1):
        ref = c.reference or (f"ص {c.page}" if c.page else "")
        ref_str = f" – {ref}" if ref else ""
        footnotes.append(f"{idx}. {c.source_name}{ref_str}")
    return footnotes


def _build_id_map(raw_citations: List[Dict[str, Any]]) -> Dict[str, Citation]:
    """
    Build a mapping from inline IDs (C1, C2, ...) to Citation objects
    based on raw payload's `source_id`.
    """
    id_map: Dict[str, Citation] = {}
    for raw in raw_citations:
        cid = raw.get("source_id")
        if not cid:
            continue
        id_map[str(cid)] = citation_from_raw(raw)
    return id_map


def render_inline_citations(answer: str, raw_citations: List[Dict[str, Any]]) -> str:
    """
    Replace inline [C1], [C2] markers inside the answer text
    with human-friendly citation labels.

    If a marker has no matching citation, it's left as-is.
    """
    id_map = _build_id_map(raw_citations)

    def repl(match: re.Match) -> str:
        cid = match.group(1)  # "C1"
        c = id_map.get(cid)
        if not c:
            return match.group(0)
        return format_citation_bracket(c)

    return INLINE_PATTERN.sub(repl, answer)


# --------- 3. High-level API for agents/endpoints --------- #

def enrich_response_with_citations(resp: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level helper to enrich an Athar agent response with:

    - answer_clean: answer text with human-friendly inline citations.
    - citations_structured: list of Citation as dicts.
    - citations_footnotes: list of formatted footnotes.
    - metadata.citation_stats: simple stats over the citations.

    It does NOT remove or change existing fields.
    """
    raw_citations = resp.get("citations", []) or []
    citations = [citation_from_raw(c) for c in raw_citations]

    answer_raw = resp.get("answer", "") or ""
    answer_clean = render_inline_citations(answer_raw, raw_citations)

    footnotes = build_footnotes(citations)
    stats: CitationStats = compute_citation_stats(citations)

    # structured dataclasses -> dicts
    citations_structured = [c.to_dict() for c in citations]

    enriched = dict(resp)  # shallow copy
    enriched["answer_clean"] = answer_clean
    enriched["citations_structured"] = citations_structured
    enriched["citations_footnotes"] = footnotes

    meta = enriched.get("metadata") or {}
    meta["citation_stats"] = stats.to_dict()
    enriched["metadata"] = meta

    return enriched