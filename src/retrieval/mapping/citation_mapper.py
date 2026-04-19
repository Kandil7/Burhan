"""
Citation Mapper for Retrieval Layer.

Maps passages to citation references.
"""

from __future__ import annotations

from typing import Any

from src.agents.base import Citation


class CitationMapper:
    """
    Maps retrieval passages to Citation objects.

    Usage:
        mapper = CitationMapper()
        citations = mapper.map_citations(passages, start_index=1)
    """

    @staticmethod
    def map_citations(
        passages: list[dict[str, Any]],
        start_index: int = 1,
    ) -> list[Citation]:
        """
        Map passages to Citation list using Citation.from_passage.

        Args:
            passages: List of passage dictionaries
            start_index: Starting citation index

        Returns:
            List of Citation objects
        """
        return [Citation.from_passage(p, i) for i, p in enumerate(passages, start_index)]

    @staticmethod
    def map_citations_with_metadata(
        passages: list[dict[str, Any]],
        citation_type: str = "fiqh_book",
        start_index: int = 1,
    ) -> list[Citation]:
        """
        Map passages with custom citation type.

        Args:
            passages: List of passage dictionaries
            citation_type: Override citation type
            start_index: Starting citation index

        Returns:
            List of Citation objects
        """
        citations = []

        for i, p in enumerate(passages, start_index):
            # Create citation with custom type
            meta = p.get("metadata", {})

            citations.append(
                Citation(
                    id=f"C{i}",
                    type=citation_type,
                    source=meta.get("book_title") or meta.get("author") or "مصدر إسلامي",
                    reference=meta.get("reference", ""),
                    url=meta.get("url"),
                    text_excerpt=p.get("content", "")[:300] or None,
                )
            )

        return citations


__all__ = ["CitationMapper"]
