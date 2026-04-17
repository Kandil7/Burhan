# Answer Composer Module
"""Compose final answer responses."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class AnswerStyle(str, Enum):
    """Styles of answers."""

    CONCISE = "concise"
    DETAILED = "detailed"
    SCHOLARLY = "scholarly"
    SIMPLE = "simple"


@dataclass
class AnswerConfig:
    """Configuration for answer composition."""

    style: AnswerStyle = AnswerStyle.DETAILED
    include_citations: bool = True
    max_length: Optional[int] = None
    include_arabic: bool = True


class AnswerComposer:
    """Composes final answers from retrieved content."""

    def __init__(self, config: Optional[AnswerConfig] = None):
        self.config = config or AnswerConfig()

    def compose(
        self,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compose final answer."""
        # Apply style
        styled_content = self._apply_style(content)

        # Add citations if enabled
        if self.config.include_citations and citations:
            formatted_citations = self._format_citations(citations)
            styled_content += f"\n\n{formatted_citations}"

        # Truncate if needed
        if self.config.max_length:
            styled_content = styled_content[: self.config.max_length]

        return {
            "content": styled_content,
            "style": self.config.style.value,
            "citations_count": len(citations) if citations else 0,
            "metadata": metadata or {},
        }

    def _apply_style(self, content: str) -> str:
        """Apply configured style to content."""
        if self.config.style == AnswerStyle.CONCISE:
            # Return first paragraph only
            return content.split("\n\n")[0]
        elif self.config.style == AnswerStyle.SCHOLARLY:
            # Add scholarly formatting
            return f"# Answer\n\n{content}"
        return content

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for display."""
        lines = ["## Sources"]
        for i, cit in enumerate(citations, 1):
            source = cit.get("source_name", "Unknown")
            reference = cit.get("reference", "")
            lines.append(f"{i}. [{source}] {reference}")
        return "\n".join(lines)


# Default composer instance
answer_composer = AnswerComposer()
