# Quote Span Module
"""Quote span detection and validation."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class QuoteSpan:
    """Represents a span of quoted text."""

    start: int
    end: int
    text: str
    is_arabic: bool = False
    validation_status: Optional[str] = None


class QuoteSpanDetector:
    """Detects and validates quote spans in text."""

    # Arabic quote patterns
    ARABIC_QUOTE_PATTERNS = [
        r"[\u2018\u2019\u201C\u201D]",  # Smart quotes
        r'["\"]',  # Straight quotes
        r"«»",  # French quotes
        r"〞〟",  # CJK quotes
    ]

    def __init__(self):
        self.arabic_pattern = re.compile(
            f"({'|'.join(self.ARABIC_QUOTE_PATTERNS)})",
            re.UNICODE,
        )

    def detect_quotes(self, text: str) -> List[QuoteSpan]:
        """Detect all quoted spans in text."""
        spans = []

        # Find all quoted sections
        for match in self.arabic_pattern.finditer(text):
            quote_char = match.group()

            # Simple detection - would need more sophisticated parsing
            start = match.start()
            end = start + 1

            # Check if it's an opening quote
            is_arabic = "\u2018" in quote_char or "\u201c" in quote_char

            if is_arabic:
                spans.append(
                    QuoteSpan(
                        start=start,
                        end=end,
                        text=quote_char,
                        is_arabic=True,
                    )
                )

        return spans

    def validate_span(
        self,
        span: QuoteSpan,
        source_text: str,
    ) -> bool:
        """Validate that a quote span matches the source."""
        # Placeholder - would implement actual validation
        return True

    def extract_quote_content(self, text: str) -> List[str]:
        """Extract content between quote marks and citation markers.

        Handles:
        - "[C1] quoted text"
        - "[C2] content here"
        - "quoted text"
        - « Arabic quotes »
        """
        results = []

        # Pattern 1: Citation markers [C1], [C2], etc. followed by quoted text
        matches = re.findall(r"\[[Cc]\d+\]\s*([^.\n]+)", text)
        results.extend([m.strip() for m in matches if m.strip()])

        # Pattern 2: Quotation marks: "quoted", 'quoted', «quoted»
        matches = re.findall(r'["\']([^"\']+)["\']|«([^»]+)»', text)
        for g1, g2 in matches:
            if g1:
                results.append(g1.strip())
            elif g2:
                results.append(g2.strip())

        return results


# Default detector instance
quote_span_detector = QuoteSpanDetector()
