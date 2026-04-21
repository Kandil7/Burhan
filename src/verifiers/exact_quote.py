# Shim for backward compatibility - re-exports from src.verification.checks.exact_quote
from src.verification.checks.exact_quote import ExactQuoteVerifier, exact_quote_verifier

__all__ = ["ExactQuoteVerifier", "exact_quote_verifier"]
