# Formatting Policy Module
"""Policies for controlling response formatting."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class OutputFormat(str, Enum):
    """Output format types."""

    MARKDOWN = "markdown"
    PLAIN = "plain"
    HTML = "html"
    JSON = "json"


class CitationFormat(str, Enum):
    """Citation format types."""

    Burhan = "Burhan"
    APA = "apa"
    CHICAGO = "chicago"
    FOOTNOTE = "footnote"


@dataclass
class FormattingPolicyConfig:
    """Configuration for formatting policy."""

    output_format: OutputFormat = OutputFormat.MARKDOWN
    citation_format: CitationFormat = CitationFormat.Burhan
    include_arabic: bool = True
    include_transliteration: bool = True
    max_citations: int = 10
    include_sources_list: bool = True


class FormattingPolicy:
    """Policy for controlling response formatting."""

    def __init__(self, config: Optional[FormattingPolicyConfig] = None):
        self.config = config or FormattingPolicyConfig()

    def format_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format response according to policy."""
        if self.config.output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(content, metadata)
        elif self.config.output_format == OutputFormat.PLAIN:
            return self._format_plain(content)
        elif self.config.output_format == OutputFormat.HTML:
            return self._format_html(content, metadata)
        return content

    def _format_markdown(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """Format as Markdown."""
        # Add title if provided
        if metadata and "title" in metadata:
            content = f"# {metadata['title']}\n\n{content}"

        # Add sources section if enabled
        if self.config.include_sources_list and metadata and "sources" in metadata:
            sources = metadata["sources"][: self.config.max_citations]
            content += "\n\n## Sources\n"
            for i, src in enumerate(sources, 1):
                content += f"{i}. {src}\n"

        return content

    def _format_plain(self, content: str) -> str:
        """Format as plain text."""
        # Remove markdown formatting
        content = content.replace("# ", "")
        content = content.replace("## ", "")
        return content

    def _format_html(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """Format as HTML."""
        # Basic markdown to HTML conversion
        html = content
        # This would need a proper converter
        return f"<div class='response'>{html}</div>"

    def get_citation_format(self) -> CitationFormat:
        """Get configured citation format."""
        return self.config.citation_format

    def get_output_format(self) -> OutputFormat:
        """Get configured output format."""
        return self.config.output_format


# Default policy instance
formatting_policy = FormattingPolicy()
