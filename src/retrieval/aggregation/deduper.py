# Deduper Module
"""Deduplication of retrieval results."""

from typing import List, Dict, Any, Set
from dataclasses import dataclass


@dataclass
class DedupeConfig:
    """Configuration for deduplication."""

    similarity_threshold: float = 0.9
    use_embedding_similarity: bool = True
    use_text_exact_match: bool = True


class Deduplicator:
    """Removes duplicate documents from retrieval results."""

    def __init__(self, config: Optional[DedupeConfig] = None):
        self.config = config or DedupeConfig()
        self.seen_texts: Set[str] = set()

    def deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates from results."""
        deduplicated = []

        for result in results:
            text = result.get("text", "")

            # Check exact text match
            if self.config.use_text_exact_match:
                if text in self.seen_texts:
                    continue
                self.seen_texts.add(text)

            deduplicated.append(result)

        return deduplicated

    def reset(self) -> None:
        """Reset the deduplicator."""
        self.seen_texts = set()


# Default deduplicator instance
deduplicator = Deduplicator()
