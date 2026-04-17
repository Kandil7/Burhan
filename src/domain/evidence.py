# Evidence Domain Module
"""Domain model for evidence and verification."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class EvidenceType(str, Enum):
    """Types of evidence."""

    QURAN_VERSE = "quran_verse"
    HADITH = "hadith"
    SCHOLAR_OPINION = "scholar_opinion"
    TEXTUAL_SOURCE = "textual_source"
    HISTORICAL_ACCOUNT = "historical_account"


class VerificationStatus(str, Enum):
    """Status of evidence verification."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class GroundednessLevel(str, Enum):
    """Level of grounding in sources."""

    FULL = "full"
    PARTIAL = "partial"
    UNGROUNDED = "ungrounded"


@dataclass
class Evidence:
    """Represents a piece of evidence."""

    id: str
    evidence_type: EvidenceType
    content: str
    source_id: str
    source_name: str
    reference: str
    relevance_score: float = 1.0
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_verified(self) -> bool:
        """Check if evidence is verified."""
        return self.verification_status == VerificationStatus.VERIFIED


@dataclass
class EvidenceSet:
    """Collection of evidence for a response."""

    evidences: List[Evidence] = field(default_factory=list)
    overall_groundedness: Optional[GroundednessLevel] = None
    sufficiency_score: Optional[float] = None
    notes: Optional[str] = None

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to the set."""
        self.evidences.append(evidence)

    def get_verified_evidences(self) -> List[Evidence]:
        """Get only verified evidences."""
        return [e for e in self.evidences if e.is_verified()]

    def get_unverified_evidences(self) -> List[Evidence]:
        """Get unverified evidences."""
        return [e for e in self.evidences if not e.is_verified()]

    def is_sufficient(self, threshold: float = 0.7) -> bool:
        """Check if evidence is sufficient."""
        if self.sufficiency_score is None:
            return False
        return self.sufficiency_score >= threshold
