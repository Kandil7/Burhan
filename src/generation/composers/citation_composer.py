# Citation Composer Module
"""Compose citations for answers."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.domain.citations import Citation


@dataclass
class CitationConfig:
    """Configuration for citation formatting."""

    format_style: str = "athar"  # athar, apa, chicago
    include_arabic: bool = True
    show_authority: bool = True


class CitationComposer:
    """Composes formatted citations."""

    def __init__(self, config: Optional[CitationConfig] = None):
        self.config = config or CitationConfig()

    def compose(
        self,
        citations: List[Citation],
    ) -> List[str]:
        """Compose formatted citations."""
        if self.config.format_style == "athar":
            return self._compose_athar_style(citations)
        elif self.config.format_style == "apa":
            return self._compose_apa_style(citations)
        elif self.config.format_style == "chicago":
            return self._compose_chicago_style(citations)
        return [str(c) for c in citations]

    def _compose_athar_style(self, citations: List[Citation]) -> List[str]:
        """Compose in Athar style."""
        formatted = []
        for cit in citations:
            text = f"[{cit.source_name}] {cit.reference}"
            if cit.verse:
                text += f" (verse {cit.verse})"
            if cit.hadith_number:
                text += f" (hadith {cit.hadith_number})"
            if self.config.show_authority:
                text += f" [authority: {cit.authority_weight:.2f}]"
            formatted.append(text)
        return formatted

    def _compose_apa_style(self, citations: List[Citation]) -> List[str]:
        """Compose in APA style."""
        formatted = []
        for cit in citations:
            text = f"{cit.source_name}. ({cit.reference})"
            formatted.append(text)
        return formatted

    def _compose_chicago_style(self, citations: List[Citation]) -> List[str]:
        """Compose in Chicago style."""
        formatted = []
        for cit in citations:
            text = f'{cit.source_name}. "{cit.reference}."'
            if cit.page:
                text += f" p. {cit.page}."
            formatted.append(text)
        return formatted

    def compose_inline(
        self,
        citations: List[Citation],
    ) -> str:
        """Compose inline citations."""
        return ", ".join(f"[{cit.source_name}]" for cit in citations)


# Default composer instance
citation_composer = CitationComposer()
