# Verifiers Module
"""Verification framework for Islamic QA system.

Provides verifiers for:
- Exact quote matching (Quran, Hadith)
- Source attribution
- Evidence sufficiency
- Contradiction detection
- Islamic school (madhhab) consistency
- Temporal consistency
- Hadith grading
- Groundedness assessment

Usage:
    from src.verifiers import (
        VerifierPipeline,
        VerificationResult,
        VerificationReport,
        VerificationPolicy,
        VerificationLevel,
    )

    pipeline = create_verification_pipeline()
    result = await pipeline.verify_claim(claim, evidence, context)
"""

from .base import (
    BaseVerifier,
    VerificationResult,
    VerificationReport,
    VerifierType,
)
from .pipeline import (
    VerifierPipeline,
    verifier_pipeline,
    create_verification_pipeline,
)
from .policies import (
    VerificationPolicy,
    VerificationLevel,
)
from .quote_span import QuoteSpan, QuoteSpanDetector
from .exact_quote import ExactQuoteVerifier, exact_quote_verifier
from .hadith_grade import (
    HadithGradeVerifier,
    HadithGrade,
    HADITH_COLLECTIONS,
    hadith_grade_verifier,
)
from .source_attribution import SourceAttributionVerifier, source_attribution_verifier
from .evidence_sufficiency import (
    EvidenceSufficiencyVerifier,
    SufficiencyCriteria,
    evidence_sufficiency_verifier,
)
from .contradiction import ContradictionVerifier, contradiction_verifier
from .school_consistency import (
    SchoolConsistencyVerifier,
    SchoolConsistencyCriteria,
    ISLAMIC_SCHOOLS,
    school_consistency_verifier,
)
from .temporal_consistency import TemporalConsistencyVerifier, temporal_consistency_verifier
from .groundedness_judge import (
    GroundednessJudge,
    GroundednessLevel,
    GroundednessScore,
    groundedness_judge,
)

__all__ = [
    # Base classes
    "BaseVerifier",
    "VerificationResult",
    "VerificationReport",
    "VerifierType",
    # Pipeline
    "VerifierPipeline",
    "verifier_pipeline",
    "create_verification_pipeline",
    # Policies
    "VerificationPolicy",
    "VerificationLevel",
    # Quote span
    "QuoteSpan",
    "QuoteSpanDetector",
    # Verifiers
    "ExactQuoteVerifier",
    "exact_quote_verifier",
    "HadithGradeVerifier",
    "HadithGrade",
    "HADITH_COLLECTIONS",
    "hadith_grade_verifier",
    "SourceAttributionVerifier",
    "source_attribution_verifier",
    "EvidenceSufficiencyVerifier",
    "SufficiencyCriteria",
    "evidence_sufficiency_verifier",
    "ContradictionVerifier",
    "contradiction_verifier",
    "SchoolConsistencyVerifier",
    "SchoolConsistencyCriteria",
    "ISLAMIC_SCHOOLS",
    "school_consistency_verifier",
    "TemporalConsistencyVerifier",
    "temporal_consistency_verifier",
    "GroundednessJudge",
    "GroundednessLevel",
    "GroundednessScore",
    "groundedness_judge",
]
