# Quran module - compatibility re-exports for verification framework
"""Quran module with compatibility exports for verification framework.

This module maintains backward compatibility while the verification
framework is being adopted.
"""

# Import original classes (these are from quotation_validator.py)
from src.quran.quotation_validator import QuotationValidator, QuotationValidatorError

__all__ = [
    "QuotationValidator",
    "QuotationValidatorError",
]
