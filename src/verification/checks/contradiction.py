# Contradiction Verifier Module
"""Verifier for detecting contradictions between a generated answer and evidence.

The check is deliberately conservative. It looks for two narrow, mechanical
conflicts between one answer statement and one retrieved passage:

1. **Polarity conflict** query: the statement and the passage are about the
   same subject (they share content words) but one is negated and the other is
   not.
2. **Numeric conflict**: both mention the same unit (verse count, year, hadith
   number) but disagree on the number.

Both heuristics used to run against the evidence **flattened into one blob**.
Any negation anywhere in the passage set then turned every non-negated answer
sentence into a "contradiction", because the blob always contained a "لا".
Fiqh answers routinely cite one passage that negates an obligation for one
group and another that affirms it for another group, so the check failed on
almost every answer and forced ``is_verified=False``. Comparing statement
against passage, one at a time, is what makes the polarity test meaningful.

Negation detection is token based, not substring based. The old substring test
matched ``"لا "`` inside ``"إلا "``, ``"بلا "`` and ``"ألا "``, which are not
negations. A short list of idiomatic phrases (``لا شك``, ``لا بد``, ...) is
removed before tokenizing for the same reason.

A semantic contradiction ("the prayer is obligatory" against "the prayer is
not obligatory" with different wording) needs understanding, not string
matching, and is left to the groundedness judge.
"""

import re
from typing import Any

from ..base import BaseVerifier
from ..schemas import CheckResult, VerificationStatus, VerifierType

# Arabic diacritics, superscript alef, and tatweel carry no meaning for matching.
_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")
_TOKEN_RE = re.compile(r"[0-9]+|[^\W\d_]+", re.UNICODE)
_NUMBER_RE = re.compile(r"\d+")

# Whole-token negations only. Substring matching is explicitly avoided.
_NEGATION_TOKENS = frozenset(
    {
        "not",
        "no",
        "never",
        "neither",
        "nor",
        "لا",
        "لم",
        "لن",
        "ليس",
        "ليست",
        "غير",
    }
)

# Phrases that contain "لا" but do not negate the predicate.
_NON_NEGATING_PHRASES = (
    "لا شك",
    "لا ريب",
    "لا بد",
    "لا سيما",
    "لا يخفي",
    "لا يخفى",
    "لا جرم",
    "لا محاله",
)

_STOPWORDS = frozenset(
    {
        # Arabic function words, written in their normalized form
        "في",
        "من",
        "علي",
        "الي",
        "عن",
        "ان",
        "انه",
        "انها",
        "التي",
        "الذي",
        "الذين",
        "هو",
        "هي",
        "هم",
        "هن",
        "كان",
        "كانت",
        "يكون",
        "تكون",
        "ما",
        "ماذا",
        "هل",
        "ثم",
        "قد",
        "كل",
        "بعض",
        "بين",
        "حتي",
        "اذا",
        "كما",
        "لكن",
        "ولكن",
        "او",
        "و",
        "ب",
        "ل",
        "ك",
        "هذا",
        "هذه",
        "ذلك",
        "تلك",
        "عند",
        "لدي",
        "مع",
        "بعد",
        "قبل",
        "حيث",
        "كيف",
        "لماذا",
        "متي",
        "اين",
        "هناك",
        "هنا",
        "ايضا",
        "جدا",
        "فيه",
        "فيها",
        "منه",
        "منها",
        "عليه",
        "عليها",
        "له",
        "لها",
        "به",
        "بها",
        # English function words
        "the",
        "an",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "with",
        "as",
        "by",
        "from",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "which",
        "who",
        "whom",
        "there",
        "their",
        "they",
        "he",
        "she",
        "we",
        "you",
        "i",
        "also",
        "such",
        "than",
        "then",
        "into",
        "about",
        "over",
        "under",
    }
)

# Units that make two numbers comparable, in normalized form.
_UNIT_TOKENS = frozenset(
    {
        "ayah",
        "ayahs",
        "ayat",
        "verse",
        "verses",
        "surah",
        "surahs",
        "sura",
        "year",
        "years",
        "hadith",
        "hadiths",
        "ايه",
        "ايات",
        "سوره",
        "سور",
        "سنه",
        "سنوات",
        "عام",
        "عاما",
        "حديث",
        "حديثا",
        "احاديث",
    }
)

_MIN_OVERLAP_TOKENS = 3
_MIN_OVERLAP_COVERAGE = 0.6


class ContradictionVerifier(BaseVerifier):
    """Detects mechanical contradictions between an answer and its evidence."""

    def __init__(self) -> None:
        self.verifier_type = VerifierType.CONTRADICTION

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        """Check each claim statement against each passage separately."""
        statements = self._extract_statements(claim)
        passages = self._passage_texts(evidence)

        if not statements or not passages:
            return CheckResult(
                check_name=self.verifier_type.value,
                status=VerificationStatus.SKIPPED,
                passed=True,
                confidence=1.0,
                message="No claim or no evidence to compare",
            )

        contradictions: list[dict[str, str]] = []
        for statement in statements:
            for passage in passages:
                reason = self._contradiction_reason(statement, passage)
                if reason:
                    contradictions.append(
                        {
                            "statement": statement,
                            "passage": passage[:200],
                            "reason": reason,
                        }
                    )
                    break

        if contradictions:
            return CheckResult(
                check_name=self.verifier_type.value,
                status=VerificationStatus.FAILED,
                passed=False,
                confidence=0.8,
                message=f"Found {len(contradictions)} contradictions",
                details={"contradictions": contradictions},
            )

        return CheckResult(
            check_name=self.verifier_type.value,
            status=VerificationStatus.PASSED,
            passed=True,
            confidence=0.9,
            message="No contradictions found",
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return bool(evidence)

    # ------------------------------------------------------------------
    # Text preparation
    # ------------------------------------------------------------------

    def _extract_statements(self, claim: str) -> list[str]:
        """Split the answer into sentences worth checking."""
        parts = [p.strip() for p in re.split(r"[.!?؟\n؛]+", claim or "") if p.strip()]
        return parts

    def _normalize(self, text: str) -> str:
        """Fold case, diacritics, and Arabic letter variants."""
        folded = _DIACRITICS.sub("", text)
        folded = folded.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
        for phrase in _NON_NEGATING_PHRASES:
            folded = folded.replace(phrase, " ")
        return folded.lower()

    def _tokens(self, text: str) -> set[str]:
        return set(_TOKEN_RE.findall(self._normalize(text)))

    def _content_tokens(self, text: str) -> set[str]:
        return {t for t in self._tokens(text) if t not in _STOPWORDS and t not in _NEGATION_TOKENS}

    def _numbers(self, text: str) -> set[str]:
        return set(_NUMBER_RE.findall(text))

    def _passage_texts(self, evidence: Any) -> list[str]:
        """Return one text per passage so contradictions stay attributable."""
        if evidence is None:
            return []
        if isinstance(evidence, str):
            return [evidence] if evidence.strip() else []
        if isinstance(evidence, dict):
            texts = [str(v) for v in evidence.values() if isinstance(v, str)]
            return [t for t in texts if t.strip()]
        if isinstance(evidence, (list, tuple)):
            texts = []
            for item in evidence:
                if isinstance(item, str):
                    if item.strip():
                        texts.append(item)
                elif isinstance(item, dict):
                    for key in ("content", "text", "excerpt"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            texts.append(value)
                            break
            return texts
        return []

    # ------------------------------------------------------------------
    # Heuristics
    # ------------------------------------------------------------------

    def _contradiction_reason(self, statement: str, passage: str) -> str | None:
        """Return a short reason when the statement conflicts with the passage."""
        statement_tokens = self._tokens(statement)
        statement_content = self._content_tokens(statement)
        if len(statement_content) < _MIN_OVERLAP_TOKENS:
            return None

        passage_tokens = self._tokens(passage)
        passage_content = self._content_tokens(passage)
        overlap = statement_content & passage_content
        if len(overlap) < _MIN_OVERLAP_TOKENS:
            return None

        coverage = len(overlap) / len(statement_content)
        if coverage < _MIN_OVERLAP_COVERAGE:
            return None

        statement_numbers = self._numbers(statement)
        passage_numbers = self._numbers(passage)
        if statement_numbers and passage_numbers and statement_numbers.isdisjoint(passage_numbers):
            if (statement_content & _UNIT_TOKENS) and (passage_content & _UNIT_TOKENS):
                return "numeric_conflict"

        statement_negated = self._is_negated(statement_tokens)
        passage_negated = self._is_negated(passage_tokens)
        if statement_negated != passage_negated:
            return "polarity_conflict"

        return None

    def _is_negated(self, tokens: set[str]) -> bool:
        """Return True when the sentence denies its predicate.

        "لا ... إلا" and "not ... except" restrict a negation to an exception.
        The sentence still affirms the general rule ("لا يجوز إعادة صلاة
        الكسوف إلا إن صلاها منفردا"), so it is not read as a denial.
        """
        if not tokens & _NEGATION_TOKENS:
            return False
        if "لا" in tokens and "الا" in tokens:
            return False
        if tokens & {"not", "no"} and tokens & {"except", "unless"}:
            return False
        return True


# Default verifier instance
contradiction_verifier = ContradictionVerifier()
