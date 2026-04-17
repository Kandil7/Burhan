# Citations Domain Module
"""Domain model for citations and source attribution."""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Citation:
    """Represents a citation in a response."""

    source_id: str
    source_name: str
    reference: str
    text: str
    chapter: Optional[str] = None
    verse: Optional[str] = None
    hadith_number: Optional[str] = None
    page: Optional[str] = None
    authority_weight: float = 1.0


@dataclass
class CitationChain:
    """Represents a chain of citations supporting a claim."""

    citations: List[Citation]
    is_verified: bool = False
    verification_notes: Optional[str] = None

    def add_citation(self, citation: Citation) -> None:
        """Add a citation to the chain."""
        self.citations.append(citation)

    def get_all_sources(self) -> List[str]:
        """Get all unique source IDs."""
        return list(set(c.source_id for c in self.citations))


class SourceAttribution:
    """Handles source attribution for responses."""

    def __init__(self):
        self.citations: List[Citation] = []

    def add_citation(self, citation: Citation) -> None:
        """Add a citation."""
        self.citations.append(citation)

    def get_citations(self) -> List[Citation]:
        """Get all citations."""
        return self.citations

    def format_citations(self) -> List[str]:
        """Format citations for display."""
        return [f"[{c.source_name}] {c.reference}" for c in self.citations]
