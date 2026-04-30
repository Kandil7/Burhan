# Citations Domain Module
"""Domain model for citations and source attribution."""

from dataclasses import dataclass


@dataclass
class Citation:
    """Represents a citation in a response."""

    source_id: str
    source_name: str
    reference: str
    text: str
    chapter: str | None = None
    verse: str | None = None
    hadith_number: str | None = None
    page: str | None = None
    authority_weight: float = 1.0


@dataclass
class CitationChain:
    """Represents a chain of citations supporting a claim."""

    citations: list[Citation]
    is_verified: bool = False
    verification_notes: str | None = None

    def add_citation(self, citation: Citation) -> None:
        """Add a citation to the chain."""
        self.citations.append(citation)

    def get_all_sources(self) -> list[str]:
        """Get all unique source IDs."""
        return list({c.source_id for c in self.citations})


class SourceAttribution:
    """Handles source attribution for responses."""

    def __init__(self):
        self.citations: list[Citation] = []

    def add_citation(self, citation: Citation) -> None:
        """Add a citation."""
        self.citations.append(citation)

    def get_citations(self) -> list[Citation]:
        """Get all citations."""
        return self.citations

    def format_citations(self) -> list[str]:
        """Format citations for display."""
        return [f"[{c.source_name}] {c.reference}" for c in self.citations]
