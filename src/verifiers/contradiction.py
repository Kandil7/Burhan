# Contradiction Verifier Module
"""Verifier for detecting contradictions in claims."""

import re
from typing import Optional, Dict, Any, List
from .base import BaseVerifier, VerificationResult, VerifierType


class ContradictionVerifier(BaseVerifier):
    """Detects contradictions between claim and evidence."""

    def __init__(self):
        self.verifier_type = VerifierType.CONTRADICTION

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Check for contradictions."""
        # Extract claim statements
        claims = self._extract_statements(claim)

        # Check each claim against evidence
        contradictions = []

        for statement in claims:
            if self._has_contradiction(statement, evidence):
                contradictions.append(statement)

        if contradictions:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Found {len(contradictions)} contradictions",
                details={"contradictions": contradictions},
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.9,
            message="No contradictions found",
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return evidence is not None

    def _extract_statements(self, claim: str) -> List[str]:
        """Extract statements from claim."""
        parts = [p.strip() for p in re.split(r"[.!?؟\n]+", claim) if p.strip()]
        return parts or [claim]

    def _has_contradiction(
        self,
        statement: str,
        evidence: Any,
    ) -> bool:
        """Check if statement contradicts evidence."""
        evidence_text = self._normalize_evidence_text(evidence)
        if not evidence_text:
            return False

        stmt = statement.lower()
        ev = evidence_text.lower()

        # Heuristic 1: simple negation polarity conflict on same topic phrase.
        neg_terms = [" not ", " no ", " never ", "ليس", "لا ", "لم ", "لن "]
        stmt_neg = any(term in f" {stmt} " for term in neg_terms)
        ev_neg = any(term in f" {ev} " for term in neg_terms)
        if stmt_neg != ev_neg:
            stmt_tokens = set(re.findall(r"\w+", stmt))
            ev_tokens = set(re.findall(r"\w+", ev))
            overlap = stmt_tokens.intersection(ev_tokens)
            if len(overlap) >= 3:
                return True

        # Heuristic 2: numeric conflict when same unit appears.
        stmt_nums = {n for n in re.findall(r"\b\d+\b", stmt)}
        ev_nums = {n for n in re.findall(r"\b\d+\b", ev)}
        if stmt_nums and ev_nums and stmt_nums.isdisjoint(ev_nums):
            units = {"ayah", "ayat", "verses", "surah", "year", "years", "آية", "آيات", "سورة", "سنة"}
            if any(unit in stmt for unit in units) and any(unit in ev for unit in units):
                return True

        return False

    def _normalize_evidence_text(self, evidence: Any) -> str:
        """Flatten evidence into one text block for lightweight contradiction checks."""
        if evidence is None:
            return ""
        if isinstance(evidence, str):
            return evidence
        if isinstance(evidence, dict):
            return " ".join(str(v) for v in evidence.values() if isinstance(v, str))
        if isinstance(evidence, list):
            parts: list[str] = []
            for item in evidence:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    for key in ("text", "content", "excerpt"):
                        val = item.get(key)
                        if isinstance(val, str) and val:
                            parts.append(val)
                            break
            return " ".join(parts)
        return ""


# Default verifier instance
contradiction_verifier = ContradictionVerifier()
