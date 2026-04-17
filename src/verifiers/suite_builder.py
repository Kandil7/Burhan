# Verification Suite Builder Module
"""Builds and runs verification suites for different agents."""

from typing import List, Dict, Any

from src.agents.collection_agent import (
    VerificationCheck,
    VerificationSuite,
    VerificationReport,
)


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
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="temporal_consistency", fail_policy="warn", enabled=True),
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
# Check Implementations Registry
# =============================================================================

# Registry mapping check names to their implementation classes
CHECK_IMPLEMENTATIONS: Dict[str, type] = {}


def register_check(name: str, check_class: type) -> None:
    """Register a check implementation.

    Args:
        name: Check identifier
        check_class: Check class implementation
    """
    CHECK_IMPLEMENTATIONS[name] = check_class


def get_check_implementation(name: str) -> type | None:
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

    Examples:
        >>> suite = build_verification_suite_for('fiqh_agent')
        >>> len(suite.checks)
        4
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
    """Run a verification suite against candidates.

    Args:
        suite: VerificationSuite to run
        query: Original query string
        candidates: List of candidate passage dictionaries

    Returns:
        VerificationReport with verified passages

    The function iterates through checks in the suite:
    - abstain: Return empty verified_passages on failure
    - warn: Log warning and continue
    - proceed: Continue regardless of failure
    """
    verified_passages: list[dict] = list(candidates)
    all_issues: list[str] = []
    check_results: Dict[str, Any] = {}

    for check in suite.checks:
        if not check.enabled:
            continue

        # Get check implementation
        check_class = get_check_implementation(check.name)

        if check_class is None:
            # Stub: treat as passed if no implementation
            result = _run_stub_check(check.name, query, verified_passages)
        else:
            # Run the actual check
            result = _run_check(check_class, check.name, query, verified_passages)

        # Record results
        check_results[check.name] = result

        if not result["passed"]:
            issue = f"Check '{check.name}' failed: {result.get('message', 'Unknown error')}"
            all_issues.append(issue)

            # Handle fail_policy
            if check.fail_policy == "abstain":
                # Return empty report on failure
                return VerificationReport(
                    is_verified=False,
                    confidence=0.0,
                    issues=all_issues,
                    details=check_results,
                    verified_passages=[],
                )
            elif check.fail_policy == "warn":
                # Log warning but continue
                # Issue already added to all_issues
                pass
            # proceed: continue regardless

        # If fail_fast and check failed, stop processing
        if suite.fail_fast and not result["passed"]:
            break

    # Calculate overall verification status
    is_verified = len(all_issues) == 0
    confidence = round(1.0 - (len(all_issues) * 0.2), 3) if all_issues else 1.0

    return VerificationReport(
        is_verified=is_verified,
        confidence=min(confidence, 1.0),
        issues=all_issues,
        details=check_results,
        verified_passages=verified_passages,
    )


def _run_stub_check(
    check_name: str,
    query: str,
    passages: list[dict],
) -> Dict[str, Any]:
    """Run a stub check when no implementation exists.

    Args:
        check_name: Name of the check
        query: Query string
        passages: List of passage dictionaries

    Returns:
        Dict with check results
    """
    # Basic stub: pass if there are passages
    if passages:
        return {
            "passed": True,
            "confidence": 0.8,
            "message": f"Stub check '{check_name}' passed",
            "check_name": check_name,
        }
    else:
        return {
            "passed": False,
            "confidence": 0.0,
            "message": f"Stub check '{check_name}' failed: no passages",
            "check_name": check_name,
        }


def _run_check(
    check_class: type,
    check_name: str,
    query: str,
    passages: list[dict],
) -> Dict[str, Any]:
    """Run an actual check implementation.

    Args:
        check_class: Check class implementation
        check_name: Name of the check
        query: Query string
        passages: List of passage dictionaries

    Returns:
        Dict with check results
    """
    try:
        # Instantiate the check
        checker = check_class()

        # Run the check (simplified synchronous wrapper)
        import asyncio

        result = asyncio.run(
            checker.verify(
                claim=query,
                evidence=passages,
                context={"query": query, "passages": passages},
            )
        )

        return {
            "passed": result.passed,
            "confidence": result.confidence,
            "message": result.message,
            "details": result.details,
            "check_name": check_name,
        }
    except Exception as e:
        return {
            "passed": False,
            "confidence": 0.0,
            "message": f"Check '{check_name}' error: {str(e)}",
            "check_name": check_name,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def create_suite_for_agent(
    agent_name: str,
    checks: List[VerificationCheck],
    fail_fast: bool = True,
) -> VerificationSuite:
    """Create a custom verification suite for an agent.

    Args:
        agent_name: Name of the agent
        checks: List of verification checks
        fail_fast: Whether to stop on first failure

    Returns:
        Custom VerificationSuite
    """
    return VerificationSuite(checks=checks, fail_fast=fail_fast)


def list_available_suites() -> List[str]:
    """List all available verification suite names.

    Returns:
        List of suite names
    """
    return list(AGENT_SUITE_MAP.keys())
