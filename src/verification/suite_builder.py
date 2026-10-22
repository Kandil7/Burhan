# Verification Suite Builder Module
"""Builds and runs verification suites for different agents."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from src.verification.schemas import (
    CheckResult,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
    VerificationSuite,
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
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True, stage="evidence"),
    ],
    fail_fast=True,
)


# =============================================================================
# Hadith Agent Verification Suite
# =============================================================================

HADITH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="hadith_grade_checker", fail_policy="abstain", enabled=True, stage="both"),
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
        VerificationCheck(name="evidence_sufficiency", fail_policy="warn", enabled=True, stage="evidence"),
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
        VerificationCheck(name="evidence_sufficiency", fail_policy="warn", enabled=True, stage="evidence"),
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
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True, stage="evidence"),
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

AGENT_SUITE_MAP: dict[str, VerificationSuite] = {
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
# The check registry lives in src.verification.base so the check modules can
# register without importing this builder (import cycle). Re-exported here for
# the existing importers.
from src.verification.base import (  # noqa: E402
    CHECK_IMPLEMENTATIONS,
    get_check_implementation,
    register_check,
)

_CHECKS_REGISTERED = False


def register_all_checks() -> None:
    """Register all available verification checks."""
    # 1. High-Integrity Domain Checks (Quote Verification)
    try:
        from src.verification.checks.fiqh_checks import EvidenceSufficiency, QuoteValidator

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


def _stage_applies(check_stage: str, stage: str | None) -> bool:
    """Return True when a check belongs to the requested pipeline stage."""
    if stage is None:
        return True
    return check_stage == "both" or check_stage == stage


def _abstain_without_evidence(query: str, reason: str) -> VerificationReport:
    """Empty evidence can never be verified, regardless of the suite."""
    return VerificationReport(
        query=query,
        is_verified=False,
        confidence=0.0,
        status=VerificationStatus.ABSTAINED,
        issues=[{"type": "no_evidence", "message": reason}],
        check_results={},
        verified_passages=[],
    )


def _ensure_checks_registered() -> None:
    """Register built-in checks the first time a suite runs.

    Registration used to depend on the FastAPI lifespan, so direct callers
    such as scripts and tests silently ran with an empty registry.
    """
    global _CHECKS_REGISTERED
    if not _CHECKS_REGISTERED:
        register_all_checks()
        _CHECKS_REGISTERED = True


def run_verification_suite(
    suite: VerificationSuite,
    query: str,
    candidates: list[dict],
    answer: str = "",
    stage: str | None = None,
) -> VerificationReport:
    """Run a verification suite against the evidence and, optionally, the answer.

    Args:
        suite: Verification suite to run.
        query: Original user question.
        candidates: Retrieved passages.
        answer: Generated answer. Required for checks whose stage is
            ``answer`` or ``both``.
        stage: Pipeline stage being verified, ``evidence`` or ``answer``.
            Checks are filtered by their own ``stage`` before running.
            ``None`` runs every enabled check.
    """
    if not candidates:
        return _abstain_without_evidence(query, "Verification received no evidence passages.")

    _ensure_checks_registered()

    verified_passages: list[dict] = list(candidates)
    issues: list[dict] = []
    check_results: dict[str, CheckResult] = {}
    details: dict[str, Any] = {}
    confidence = 1.0
    verified = True
    checks_run: list[str] = []

    for check in suite.checks:
        if not check.enabled:
            continue
        if not _stage_applies(check.stage, stage):
            continue

        check_class = get_check_implementation(check.name)
        if check_class is None:
            # A missing implementation is a configuration bug. Never fake a pass.
            logger.error("verification.check_not_registered", extra={"check": check.name})
            result = CheckResult(
                check_name=check.name,
                status=VerificationStatus.SKIPPED,
                passed=False,
                confidence=0.0,
                message=f"No implementation registered for check '{check.name}'",
            )
        else:
            claim_text = answer if check.stage in ("answer", "both") and answer else query
            result = _run_check(check_class, check.name, claim_text, verified_passages, stage)

        checks_run.append(check.name)
        check_results[check.name] = result
        details[check.name] = result.model_dump(mode="json")

        if result.status in (VerificationStatus.SKIPPED,) or result.passed:
            continue

        message = result.message or "Unknown error"
        if check.fail_policy == "abstain":
            issues.append(
                {
                    "type": "check_failed",
                    "check": check.name,
                    "policy": "abstain",
                    "message": f"Check '{check.name}' failed: {message}",
                }
            )
            return VerificationReport(
                query=query,
                is_verified=False,
                confidence=0.0,
                status=VerificationStatus.ABSTAINED,
                issues=issues,
                check_results=check_results,
                verified_passages=[],
                details=details,
            )

        if check.fail_policy == "warn":
            issues.append(
                {
                    "type": "warning",
                    "check": check.name,
                    "policy": "warn",
                    "message": f"Check '{check.name}' warned: {message}",
                }
            )
            confidence -= 0.10
        else:  # proceed
            issues.append(
                {
                    "type": "check_failed",
                    "check": check.name,
                    "policy": "proceed",
                    "message": f"Check '{check.name}' failed: {message}",
                }
            )
            verified = False
            confidence -= 0.20

        if suite.fail_fast:
            break

    confidence = max(0.0, min(1.0, round(confidence, 3)))
    status = VerificationStatus.PASSED if verified else VerificationStatus.FAILED
    if verified and issues:
        status = VerificationStatus.WARNING

    return VerificationReport(
        query=query,
        is_verified=verified,
        confidence=confidence,
        status=status,
        issues=issues,
        check_results=check_results,
        verified_passages=verified_passages,
        details=details,
    )


def _run_check(
    check_class: type,
    check_name: str,
    claim_text: str,
    passages: list[dict],
    stage: str | None = None,
) -> CheckResult:
    """Run an actual check implementation."""
    try:
        checker = check_class()
        result: CheckResult = _run_coroutine_sync(
            checker.verify(
                claim=claim_text,
                evidence=passages,
                context={"query": claim_text, "passages": passages, "stage": stage},
            )
        )
        return result
    except Exception as e:
        logger.exception("verification.check_error", extra={"check": check_name})
        return CheckResult(
            check_name=check_name,
            status=VerificationStatus.FAILED,
            passed=False,
            confidence=0.0,
            message=f"Check '{check_name}' error: {str(e)}",
        )


def _run_coroutine_sync(coro: Any) -> Any:
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
    checks: list[VerificationCheck],
    fail_fast: bool = True,
) -> VerificationSuite:
    """Create a custom verification suite for an agent."""
    return VerificationSuite(checks=checks, fail_fast=fail_fast)


def list_available_suites() -> list[str]:
    """List all available verification suite names."""
    return list(AGENT_SUITE_MAP.keys())
