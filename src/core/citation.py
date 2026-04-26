"""
Core citation domain models for Burhan.

- Citation: internal canonical representation.
- CitationStats: simple stats for evaluation/metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Citation:
    """
    Internal citation representation used inside Burhan.

    This is the canonical format that all agents/services should use.
    """

    source_id: str               # e.g. book_id or Quran/Hadith ID
    source_name: str             # normalized source name (book/surah/collection)
    reference: str               # human readable reference (section title, "ص 528", etc.)
    text: str                    # snippet/quote from the source

    
    chapter: Optional[str] = None
    verse: Optional[str] = None
    hadith_number: Optional[str] = None
    page: Optional[str] = None

    # Burhan-specific metadata
    collection: Optional[str] = None      # e.g. seerah_passages, fiqh_passages
    category: Optional[str] = None        # e.g. "السيرة النبوية"
    content_type: Optional[str] = None    # e.g. "title", "page", "ayah", "hadith"

    # For future weighting / authority ranking
    authority_weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict (useful for JSON serialization)."""
        return asdict(self)


@dataclass
class CitationStats:
    """
    Simple statistics over a list of citations.
    Useful for evaluation and attaching to metadata.
    """

    num_citations: int
    num_unique_sources: int
    avg_authority_weight: float
    collections: List[str]
    categories: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_citation_stats(citations: List[Citation]) -> CitationStats:
    """Compute basic statistics from a list of citations."""
    num = len(citations)
    unique_sources = {c.source_id for c in citations if c.source_id}
    collections = {c.collection for c in citations if c.collection}
    categories = {c.category for c in citations if c.category}

    avg_auth = (
        sum(c.authority_weight for c in citations) / num
        if num > 0 else 0.0
    )

    return CitationStats(
        num_citations=num,
        num_unique_sources=len(unique_sources),
        avg_authority_weight=avg_auth,
        collections=sorted(collections),
        categories=sorted(categories),
    )