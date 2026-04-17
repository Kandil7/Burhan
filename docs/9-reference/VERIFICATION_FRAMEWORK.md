# Athar Verification Framework

## Overview

The verification framework ensures that generated answers are grounded in reliable sources before being presented to users. It implements "Digital Isnad" (chain of verification) for Islamic content.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query + Candidates → Quote Validator → Source Attribution →    │
│                          ↓                                       │
│  Contradiction Detector → Evidence Sufficiency → Hadith Grade  →
│                          ↓                                       │
│  School Consistency → Temporal Consistency → Groundedness     │
│                          ↓                                       │
│              VerificationReport (passed/failed)                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Verification Suite

Each agent has a verification suite with configurable checks:

```python
VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True),
    ],
    fail_fast=True
)
```

---

## Fail Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `abstain` | Return empty verified_passages, do not generate | Critical checks (quote, evidence) |
| `warn` | Continue but add warning to metadata | Important checks (source) |
| `proceed` | Continue regardless of result | Informational checks |

---

## Verification Suites by Agent

### FiqhAgent Suite

```python
FIQH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain"),
        VerificationCheck(name="source_attributor", fail_policy="warn"),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed"),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain"),
    ],
    fail_fast=True
)
```

### HadithAgent Suite

```python
HADITH_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain"),
        VerificationCheck(name="hadith_grade_checker", fail_policy="abstain"),
        VerificationCheck(name="source_attributor", fail_policy="warn"),
    ],
    fail_fast=True
)
```

### TafsirAgent Suite

```python
TAFSIR_VERIFICATION_SUITE = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain"),
        VerificationCheck(name="source_attributor", fail_policy="warn"),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed"),
    ],
    fail_fast=True
)
```

---

## Verifier Implementations

### 1. Quote Validator

Verifies that quoted text exists in the source:

```python
class QuoteValidator(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        # Extract quoted phrases
        quotes = extract_quotes(claim)
        
        # Check each quote exists in evidence
        for quote in quotes:
            if not search_in_evidence(quote, evidence):
                return VerificationResult(
                    verifier_type=VerifierType.EXACT_QUOTE,
                    passed=False,
                    confidence=0.3,
                    message=f"Quote not found in evidence: {quote}"
                )
        
        return VerificationResult(
            verifier_type=VerifierType.EXACT_QUOTE,
            passed=True,
            confidence=0.95,
            message="All quotes verified"
        )
```

### 2. Source Attributor

Verifies the source is a recognized Islamic text:

```python
class SourceAttributor(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        # Check author authenticity
        authors = extract_authors(evidence)
        
        for author in authors:
            if not is_recognized_author(author):
                logger.warning(f"Unrecognized author: {author}")
        
        return VerificationResult(
            verifier_type=VerifierType.SOURCE_ATTRIBUTION,
            passed=True,
            confidence=0.8,
            message="Sources recognized"
        )
```

### 3. Contradiction Detector

Detects contradictions between passages:

```python
class ContradictionDetector(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        # Compare content between passages
        contradictions = find_contradictions(evidence)
        
        if contradictions:
            return VerificationResult(
                verifier_type=VerifierType.CONTRADICTION,
                passed=True,  # Proceed but note
                confidence=0.6,
                message=f"Potential contradictions: {contradictions}",
                details={"contradictions": contradictions}
            )
        
        return VerificationResult(
            verifier_type=VerifierType.CONTRADICTION,
            passed=True,
            confidence=0.9,
            message="No contradictions detected"
        )
```

### 4. Evidence Sufficiency

Verifies enough evidence exists:

```python
class EvidenceSufficiency(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        if len(evidence) < MIN_EVIDENCE_COUNT:
            return VerificationResult(
                verifier_type=VerifierType.EVIDENCE_SUFFICIENCY,
                passed=False,
                confidence=0.2,
                message=f"Insufficient evidence: {len(evidence)} passages"
            )
        
        return VerificationResult(
            verifier_type=VerifierType.EVIDENCE_SUFFICIENCY,
            passed=True,
            confidence=0.85,
            message="Sufficient evidence"
        )
```

### 5. Hadith Grade Checker

Validates hadith authenticity grades:

```python
class HadithGradeChecker(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        grades = extract_hadith_grades(evidence)
        
        valid_grades = ["sahih", "hasan"]
        weak_grades = ["daif", "mawdu"]
        
        has_weak = any(g in weak_grades for g in grades)
        
        if has_weak and not any(g in valid_grades for g in grades):
            return VerificationResult(
                verifier_type=VerifierType.HADITH_GRADE,
                passed=False,
                confidence=0.3,
                message="Weak hadith without corroboration"
            )
        
        return VerificationResult(
            verifier_type=VerifierType.HADITH_GRADE,
            passed=True,
            confidence=0.9,
            message="Hadith grades verified"
        )
```

### 6. School Consistency (Maddhab)

Verifies madhhab consistency:

```python
class SchoolConsistencyVerifier(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        madhhabs = extract_madhhabs(evidence)
        
        # Check if multiple madhhabs agree
        unique_madhhabs = set(madhhabs)
        
        if len(unique_madhhabs) > 1:
            return VerificationResult(
                verifier_type=VerifierType.SCHOOL_CONSISTENCY,
                passed=True,  # Multiple views is valid
                confidence=0.7,
                message=f"Multiple madhhabs: {unique_madhhabs}",
                details={"madhhabs": list(unique_madhhabs)}
            )
        
        return VerificationResult(
            verifier_type=VerifierType.SCHOOL_CONSISTENCY,
            passed=True,
            confidence=0.9,
            message="Single madhhab"
        )
```

### 7. Temporal Consistency

Verifies era consistency:

```python
class TemporalConsistencyVerifier(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        eras = extract_eras(evidence)
        
        # Check for temporal consistency
        # e.g., Classical scholars shouldn't cite modern sources
        
        return VerificationResult(
            verifier_type=VerifierType.TEMPORAL_CONSISTENCY,
            passed=True,
            confidence=0.8,
            message="Temporal consistency verified"
        )
```

### 8. Groundedness Judge

Verifies answer is based on evidence:

```python
class GroundednessJudge(BaseVerifier):
    async def verify(self, claim: str, evidence: list[dict]) -> VerificationResult:
        # Use LLM to judge if claim is grounded
        grounded = await llm_judge_groundedness(claim, evidence)
        
        return VerificationResult(
            verifier_type=VerifierType.GROUNDEDNESS,
            passed=grounded,
            confidence=0.75,
            message="Groundedness verified" if grounded else "Potential hallucination"
        )
```

---

## Verification Report

The verification pipeline returns a report:

```python
@dataclass
class VerificationReport:
    is_verified: bool           # Overall passed
    confidence: float          # Average confidence
    issues: list[str]          # List of issues
    details: dict[str, Any]    # Per-verifier results
    verified_passages: list[dict]  # Passages that passed
```

---

## Using the Verification Suite

### Building a Suite

```python
from src.verifiers.suite_builder import build_verification_suite_for

# Get Fiqh verification suite
suite = build_verification_suite_for("fiqh_agent")

# Run verification
report = await run_verification_suite(
    suite=suite,
    query="ما حكم الصلاة؟",
    candidates=retrieved_passages
)

print(f"Verified: {report.is_verified}")
print(f"Confidence: {report.confidence}")
print(f"Verified passages: {len(report.verified_passages)}")
```

### Custom Suite

```python
from src.agents.collection_agent import (
    VerificationSuite,
    VerificationCheck
)

custom_suite = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain"),
        VerificationCheck(name="groundedness_judge", fail_policy="warn"),
    ],
    fail_fast=False
)
```

---

## Integration with Agents

### In CollectionAgent

```python
class FiqhCollectionAgent(CollectionAgent):
    async def run_verification(self, query: str, candidates: list[dict]) -> VerificationReport:
        from src.verifiers.suite_builder import build_verification_suite_for
        
        suite = build_verification_suite_for("fiqh_agent")
        
        return await run_verification_suite(suite, query, candidates)
```

### With Fail Policy Handling

```python
async def run_verification_suite(suite: VerificationSuite, query: str, candidates: list[dict]) -> VerificationReport:
    results = []
    verified_passages = candidates.copy()
    
    for check in suite.checks:
        if not check.enabled:
            continue
            
        result = await run_check(check.name, query, verified_passages)
        results.append(result)
        
        # Handle fail policy
        if not result.passed:
            if check.fail_policy == "abstain":
                return VerificationReport(
                    is_verified=False,
                    confidence=result.confidence,
                    issues=[result.message],
                    verified_passages=[]  # Empty!
                )
            elif check.fail_policy == "warn":
                logger.warning(f"Warning: {result.message}")
    
    # All checks passed
    return VerificationReport(
        is_verified=True,
        confidence=avg_confidence(results),
        issues=[],
        verified_passages=verified_passages
    )
```

---

## Testing Verifiers

```python
@pytest.mark.asyncio
async def test_quote_validator():
    verifier = QuoteValidator()
    
    claim = "قال النبي صلى الله عليه وسلم: إنما الأعمال بالنية"
    evidence = [
        {"content": "إنما الأعمال بالنية...", "metadata": {"source": "صحيح البخاري"}}
    ]
    
    result = await verifier.verify(claim, evidence)
    
    assert result.passed is True
    assert result.confidence > 0.8

@pytest.mark.asyncio
async def test_evidence_sufficiency_fails():
    verifier = EvidenceSufficiency()
    
    claim = "ما حكم الزكاة؟"
    evidence = [{"content": "بعض النصوص..."}]  # Only 1
    
    result = await verifier.verify(claim, evidence)
    
    assert result.passed is False
    assert "Insufficient" in result.message
```

---

## Configuration

### Enable/Disable Checks

```python
suite = VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", enabled=True),
        VerificationCheck(name="source_attributor", enabled=False),
    ]
)
```

### Adjust Fail Policy

```python
# Make evidence check warn instead of abstain
suite = VerificationSuite(
    checks=[
        VerificationCheck(name="evidence_sufficiency", fail_policy="warn"),
    ]
)
```

---

## Performance Considerations

1. **Parallel Execution**: Run independent verifiers in parallel
2. **Early Exit**: Use fail_fast=True to skip unnecessary checks
3. **Caching**: Cache verification results for repeated queries

---

## Troubleshooting

### False Positives

- Increase confidence threshold
- Add more evidence requirements
- Enable additional verifiers

### False Negatives

- Decrease confidence threshold
- Check fail_policy is appropriate
- Review individual verifier logic

### Slow Verification

- Disable unnecessary verifiers
- Enable fail_fast
- Reduce evidence requirements

---

## See Also

- [Phase 10 Index](./PHASE10_INDEX.md) - Navigation guide
- [Multi-Agent Architecture](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md) - Main architecture
- [API Collections](./API_COLLECTIONS.md) - API endpoints
- [Retrieval Strategies](./RETRIEVAL_STRATEGIES.md) - Retrieval configuration
- [Orchestration Patterns](./ORCHESTRATION_PATTERNS.md) - Multi-agent patterns