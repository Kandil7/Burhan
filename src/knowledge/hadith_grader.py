# Compatibility shim for hadith_grader
"""Hadith Grader - Re-exports from verifiers module for backward compatibility.

This module is deprecated. Please use:
    from src.verifiers.hadith_grade import HadithGradeVerifier, HadithGrade

The original HadithAuthenticityGrader is preserved here for backward compatibility
but all new code should use the verifier framework.
"""

# Re-export from new location for backward compatibility
from src.verifiers.hadith_grade import (
    HadithGradeVerifier,
    HadithGrade,
    HADITH_COLLECTIONS,
    hadith_grade_verifier,
)

# Keep the original class for legacy code
from src.knowledge.hadith_grader_original import HadithAuthenticityGrader

__all__ = [
    "HadithAuthenticityGrader",
    "HadithGradeVerifier",
    "HadithGrade",
    "HADITH_COLLECTIONS",
    "hadith_grade_verifier",
]
