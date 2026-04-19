# Evidence Aggregator Module
"""Aggregating evidence from multiple retrieval sources."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AggregatedEvidence:
    """Aggregated evidence from multiple sources."""

    source_id: str
    source_name: str
    text: str
    reference: str
    relevance_score: float = 0.0
    authority_weight: float = 1.0
    combined_score: float = 0.0


class EvidenceAggregator:
    """Aggregates evidence from multiple retrieval results."""

    def __init__(self):
        self.evidences: List[AggregatedEvidence] = []

    def add_results(
        self,
        results: List[Dict[str, Any]],
        source_id: str,
        source_name: str,
    ) -> None:
        """Add retrieval results from a source."""
        for result in results:
            evidence = AggregatedEvidence(
                source_id=source_id,
                source_name=source_name,
                text=result.get("text", ""),
                reference=result.get("reference", ""),
                relevance_score=result.get("score", 0.0),
                authority_weight=result.get("authority_weight", 1.0),
            )
            # Calculate combined score
            evidence.combined_score = evidence.relevance_score * evidence.authority_weight
            self.evidences.append(evidence)

    def get_top_evidences(
        self,
        top_k: int = 10,
    ) -> List[AggregatedEvidence]:
        """Get top-k aggregated evidences."""
        sorted_evidences = sorted(
            self.evidences,
            key=lambda e: e.combined_score,
            reverse=True,
        )
        return sorted_evidences[:top_k]

    def clear(self) -> None:
        """Clear all aggregated evidence."""
        self.evidences = []


# Default aggregator instance
evidence_aggregator = EvidenceAggregator()
