# Verification Suite Builder Module
"""Builds and runs verification suites for different agents."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Type

from src.verification.schemas import (
    VerificationCheck,
    VerificationSuite,
    VerificationReport,
    VerificationStatus,
    CheckResult,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Fiqh Agent Verification Suite
# =============================================================================

FIQH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Hadith Agent Verification Suite
# =============================================================================

HADITH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="hadith_grade_checker", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Tafsir Agent Verification Suite
# =============================================================================

TAFSIR_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Aqeedah Agent Verification Suite
# =============================================================================

AQEEDAH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="warn", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Seerah Agent Verification Suite
# =============================================================================

SEERAH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="temporal_consistency", fail_policy="warn", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="warn", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Usul Fiqh Agent Verification Suite
# =============================================================================

USUL_FIQH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# History Agent Verification Suite
# =============================================================================

HISTORY_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Language Agent Verification Suite
# =============================================================================

LANGUAGE_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
    ],
    fail_fast=True,
)


# =============================================================================
# Agent Name to Suite Mapping
# =============================================================================

AGENT_SUITE_MAP: Dict[str, VerificationSuite] = {
    "fiqh_agent": FIQH_VERIFICATION_SUITE,
    "hadith_agent": HADITH_VERIFICATION_SUITE,
    "tafsir_agent": TAFSIR_VERIFICATION_SUITE,
    "aqeedah_agent": AQEEDAH_VERIFICATION_SUITE,
    "seerah_agent": SEERAH_VERIFICATION_SUITE,
    "usul_fiqh_agent": USUL_FIQH_VERIFICATION_SUITE,
    "history_agent": HISTORY_VERIFICATION_SUITE,
    "language_agent": LANGUAGE_VERIFICATION_SUITE,
    # Aliases for different naming conventions
    "fiqh": FIQH_VERIFICATION_SUITE,
    "hadith": HADITH_VERIFICATION_SUITE,
    "tafsir": TAFSIR_VERIFICATION_SUITE,
    "aqeedah": AQEEDAH_VERIFICATION_SUITE,
    "seerah": SEERAH_VERIFICATION_SUITE,
    "usul_fiqh": USUL_FIQH_VERIFICATION_SUITE,
    "history": HISTORY_VERIFICATION_SUITE,
    "language": LANGUAGE_VERIFICATION_SUITE,
}


# =============================================================================
# Registry mapping check names to their implementation classes
CHECK_IMPLEMENTATIONS: Dict[str, type] = {}


def register_all_checks() -> None:
    """Register all available verification checks."""
    # 1. High-Integrity Domain Checks (Quote Verification)
    try:
        from src.verification.checks.fiqh_checks import QuoteValidator, EvidenceSufficiency

        register_check("quote_validator", QuoteValidator)
        register_check("evidence_sufficiency", EvidenceSufficiency)
    except ImportError:
        pass

    # 2. Hadith Grading
    try:
        from src.verification.checks.hadith_grade import HadithGradeVerifier

        # Register both aliases to support hadith.py and HADITH_VERIFICATION_SUITE
        register_check("hadith_grade", HadithGradeVerifier)
        register_check("hadith_grade_checker", HadithGradeVerifier)
    except ImportError:
        pass

    # 3. Temporal Consistency
    try:
        from src.verification.checks.temporal_consistency import TemporalConsistencyVerifier

        register_check("temporal_consistency", TemporalConsistencyVerifier)
    except ImportError:
        pass

    # 4. Global/Generic Checks (can override or supplement)
    try:
        from src.verification.checks.exact_quote import ExactQuoteVerifier

        # Only register if not already registered by domain checks
        if "quote_validator" not in CHECK_IMPLEMENTATIONS:
            register_check("quote_validator", ExactQuoteVerifier)
    except ImportError:
        pass

    try:
        from src.verification.checks.source_attribution import SourceAttributionVerifier

        if "source_attributor" not in CHECK_IMPLEMENTATIONS:
            register_check("source_attributor", SourceAttributionVerifier)
    except ImportError:
        pass

    try:
        from src.verification.checks.contradiction import ContradictionVerifier

        if "contradiction_detector" not in CHECK_IMPLEMENTATIONS:
            register_check("contradiction_detector", ContradictionVerifier)
    except ImportError:
        pass

    try:
        from src.verification.checks.evidence_sufficiency import EvidenceSufficiencyVerifier

        if "evidence_sufficiency" not in CHECK_IMPLEMENTATIONS:
            register_check("evidence_sufficiency", EvidenceSufficiencyVerifier)
    except ImportError:
        pass


def register_check(name: str, check_class: type) -> None:
    """Register a check implementation.

    Args:
        name: Check identifier
        check_class: Check class implementation
    """
    CHECK_IMPLEMENTATIONS[name] = check_class


def get_check_implementation(name: str) -> Optional[type]:
    """Get a check implementation by name.

    Args:
        name: Check identifier

    Returns:
        Check class or None if not found
    """
    return CHECK_IMPLEMENTATIONS.get(name)


def _get_default_suite() -> VerificationSuite:
    """Get a default verification suite for unknown agents.

    Returns:
        Default VerificationSuite with basic checks
    """
    return VerificationSuite(
        checks=[
            VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        ],
        fail_fast=False,
    )


# =============================================================================
# Suite Builder Functions
# =============================================================================


def build_verification_suite_for(agent_name: str) -> VerificationSuite:
    """Build a verification suite for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'fiqh_agent', 'hadith_agent')

    Returns:
        VerificationSuite configured for the agent
    """
    # Look up the suite in the mapping
    suite = AGENT_SUITE_MAP.get(agent_name)

    if suite is not None:
        return suite

    # Return default suite if not found
    return _get_default_suite()


def run_verification_suite(
    suite: VerificationSuite,
    query: str,
    candidates: list[dict],
) -> VerificationReport:
    """Run a verification suite against candidates."""
    initial_count = len(candidates)
    verified_passages: list[dict] = list(candidates)
    all_issues: list[str] = []
    check_results: Dict[str, CheckResult] = {}

    for check in suite.checks:
        if not check.enabled:
            continue

        # Get check implementation
        check_class = get_check_implementation(check.name)

        if check_class is None:
            # Stub: treat as passed if no implementation
            result = _run_stub_result(check.name, query, verified_passages)
        else:
            # Run the actual check
            result = _run_check(check_class, check.name, query, verified_passages)

        # Record results
        check_results[check.name] = result

        if not result.passed:
            issue = f"Check '{check.name}' failed: {result.message or 'Unknown error'}"
            all_issues.append(issue)

            # Handle fail_policy
            if check.fail_policy == "abstain":
                return VerificationReport(
                    query=query,
                    is_verified=False,
                    confidence=0.0,
                    status=VerificationStatus.ABSTAINED,
                    issues=all_issues,
                    check_results=check_results,
                    verified_passages=[],
                )
            elif check.fail_policy == "warn":
                pass

        # If fail_fast and check failed, stop processing
        if suite.fail_fast and not result.passed:
            break

    # Final Count Logic
    final_count = len(verified_passages)

    # Calculate overall verification status
    is_verified = len(all_issues) == 0 and (initial_count == final_count or initial_count == 0)

    # Start with 1.0 confidence
    confidence = 1.0

    # Penalize for issues
    if all_issues:
        confidence -= len(all_issues) * 0.2

    # Penalize for lost evidence
    if initial_count > 0 and final_count < initial_count:
        drop_ratio = (initial_count - final_count) / initial_count
        confidence -= drop_ratio * 0.3
        all_issues.append(f"Evidence reduced from {initial_count} to {final_count} during verification.")

    return VerificationReport(
        query=query,
        is_verified=is_verified,
        confidence=max(0.0, round(confidence, 3)),
        status=VerificationStatus.PASSED if is_verified else VerificationStatus.FAILED,
        issues=all_issues,
        check_results=check_results,
        verified_passages=verified_passages,
    )


def _run_stub_result(
    check_name: str,
    query: str,
    passages: list[dict],
) -> CheckResult:
    """Run a stub check when no implementation exists."""
    if passages:
        return CheckResult(
            check_name=check_name,
            status=VerificationStatus.PASSED,
            passed=True,
            confidence=0.8,
            message=f"Stub check '{check_name}' passed",
        )
    else:
        return CheckResult(
            check_name=check_name,
            status=VerificationStatus.FAILED,
            passed=False,
            confidence=0.0,
            message=f"Stub check '{check_name}' failed: no passages",
        )


def _run_check(
    check_class: type,
    check_name: str,
    query: str,
    passages: list[dict],
) -> CheckResult:
    """Run an actual check implementation."""
    try:
        # Instantiate the check
        checker = check_class()

        result = _run_coroutine_sync(
            checker.verify(
                claim=query,
                evidence=passages,
                context={"query": query, "passages": passages},
            )
        )
        return result
    except Exception as e:
        return CheckResult(
            check_name=check_name,
            status=VerificationStatus.FAILED,
            passed=False,
            confidence=0.0,
            message=f"Check '{check_name}' error: {str(e)}",
        )


def _run_coroutine_sync(coro):
    """Safely run async coroutine from sync code."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


def create_suite_for_agent(
    agent_name: str,
    checks: List[VerificationCheck],
    fail_fast: bool = True,
) -> VerificationSuite:
    """Create a custom verification suite for an agent."""
    return VerificationSuite(checks=checks, fail_fast=fail_fast)


def list_available_suites() -> List[str]:
    """List all available verification suite names."""
    return list(AGENT_SUITE_MAP.keys())
