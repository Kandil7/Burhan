"""
Detector for missing requested evidence types.

Catches the fifth violation class:
  - User explicitly requests evidence (آية / حديث / دليل)
  - But generated answer contains no such evidence
  - Distinct from other violations — this is an incompleteness issue,
    not a grounding/attribution issue.

False-positive guards:
  - Minimum query length: 4 words (single-word queries excluded)
  - Patterns require explicit request verb + evidence noun
  - Ambiguous short patterns (من القرآن, بدليل) replaced with
    longer, intent-clear variants
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

# Minimum query word count to run detection at all.
# Queries shorter than this are unlikely to be structured evidence requests.
_MIN_QUERY_WORDS = 4

# ── Request Patterns ──────────────────────────────────────────────────────────

# Patterns indicating user wants a Quranic verse.
# Each pattern requires an explicit request verb (استشهد / اذكر / اقتبس /
# استدل / أذكر / هات / أريد) + evidence noun (آية / دليل من القرآن).
# Removed: r"من\s+القرآن"  — too ambiguous, matches descriptive context
# Removed: r"آية\s+قرآنية" — matches answer content, not just requests
_QURAN_REQUEST_PATTERNS = [
    r"استشهد\s+بآية",
    r"اذكر\s+(?:لي\s+)?آية",
    r"دليل(?:\s+قرآني|\s+من\s+القرآن\s+الكريم)",
    r"بآية\s+(?:كريمة|قرآنية)",
    r"اقتبس\s+(?:لي\s+)?آية",
    r"استدل\s+بآية",
    r"أذكر\s+(?:لي\s+)?آية",
    r"هات\s+(?:لي\s+)?آية",
    r"أريد\s+آية",
    r"أحتاج\s+(?:إلى\s+)?آية",
]

# Patterns indicating user wants a Hadith.
# Removed: r"من\s+السنة" — too ambiguous
# Removed: r"حديث\s+نبوي" — may appear in answer body
_HADITH_REQUEST_PATTERNS = [
    r"استشهد\s+بحديث",
    r"اذكر\s+(?:لي\s+)?حديث",
    r"دليل\s+من\s+السنة\s+النبوية",
    r"بحديث\s+(?:شريف|نبوي)",
    r"اقتبس\s+(?:لي\s+)?حديث",
    r"استدل\s+بحديث",
    r"هات\s+(?:لي\s+)?حديث",
    r"أريد\s+حديث",
    r"أحتاج\s+(?:إلى\s+)?حديث",
]

# Patterns indicating user wants any religious evidence.
# Removed: r"بدليل" — far too short and ambiguous
_GENERAL_EVIDENCE_PATTERNS = [
    r"استشهد\s+بدليل",
    r"أذكر\s+دليلاً\s+شرعياً?",
    r"دليل\s+شرعي",
    r"أحتاج\s+(?:إلى\s+)?دليل\s+شرعي",
    r"ما\s+الدليل\s+(?:الشرعي|على\s+ذلك|من\s+القرآن|من\s+السنة)",
    r"اذكر\s+(?:لي\s+)?دليلاً",
]

# ── Answer Presence Patterns ─────────────────────────────────────────────────

# Detects a Quranic verse in the answer:
#   ﴿...﴾  or  سورة X: Y  or  الآية رقم Y
_QURAN_IN_ANSWER_RE = re.compile(
    r"[﴿﴾]"                         # Quran brackets
    r"|سورة\s+[\u0600-\u06FF]+\s*:\s*\d+"   # سورة المائدة: 82
    r"|سورة\s+[\u0600-\u06FF]+"     # سورة + name (looser)
    r"|الآية\s+(?:رقم\s+)?\d+",
    re.UNICODE,
)

# Detects a Hadith in the answer:
#   «...»  or  صحيح البخاري / مسلم / رواه / أخرجه
_HADITH_IN_ANSWER_RE = re.compile(
    r"«.{10,200}»"                      # quoted hadith text
    r"|صحيح\s+(?:البخاري|مسلم)"        # major collections
    r"|رواه\s+[\u0600-\u06FF]+"        # رواه X
    r"|أخرجه\s+[\u0600-\u06FF]+"       # أخرجه X
    r"|حديث\s+رقم\s+\d+"               # حديث رقم N
    r"|ﷺ[^.]{5,100}قال",              # النبي ﷺ ... قال (attribution)
    re.UNICODE | re.DOTALL,
)

# ── Compiled request regexes ─────────────────────────────────────────────────

_QURAN_REQUEST_RE = re.compile(
    "|".join(_QURAN_REQUEST_PATTERNS), re.UNICODE
)
_HADITH_REQUEST_RE = re.compile(
    "|".join(_HADITH_REQUEST_PATTERNS), re.UNICODE
)
_GENERAL_EVIDENCE_RE = re.compile(
    "|".join(_GENERAL_EVIDENCE_PATTERNS), re.UNICODE
)

# ── Public API ────────────────────────────────────────────────────────────────


def detect_missing_requested_evidence(
    query: str,
    answer: str,
) -> list[dict]:
    """
    Detect when user explicitly requested evidence absent in answer.

    Checks independently:
      - Quran verse requested but no Quranic text found in answer
      - Hadith requested but no Hadith text found in answer
      - General evidence requested but neither found

    Args:
        query:  Original (raw, pre-normalization) user query
        answer: Generated answer text

    Returns:
        List of violation dicts, empty if all requests are satisfied
        or if query is too short to contain a structured request.

    Examples:
        query="استشهد بآية على فضل الصدقة", answer="...النبي فعل كذا..."
        → [{"type": "missing_quran_evidence", ...}]

        query="اذكر حديثاً", answer="...روى البخاري عن..."
        → []  (satisfied)

        query="ما حكم الصلاة؟", answer="..."
        → []  (no evidence request detected)
    """
    if not query or not answer:
        return []

    # Guard: skip short queries — unlikely to be structured evidence requests
    if len(query.split()) < _MIN_QUERY_WORDS:
        return []

    violations: list[dict] = []

    wants_quran = bool(_QURAN_REQUEST_RE.search(query))
    wants_hadith = bool(_HADITH_REQUEST_RE.search(query))
    wants_evidence = bool(_GENERAL_EVIDENCE_RE.search(query))

    has_quran = bool(_QURAN_IN_ANSWER_RE.search(answer))
    has_hadith = bool(_HADITH_IN_ANSWER_RE.search(answer))

    if wants_quran and not has_quran:
        match = _QURAN_REQUEST_RE.search(query)
        violations.append(
            {
                "type": "missing_quran_evidence",
                "message": (
                    "User requested a Quranic verse but none was found "
                    "in the generated answer."
                ),
                "details": {
                    "trigger_pattern": match.group(0) if match else "",
                    "has_quran_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_quran_evidence: query='%s…' has no Quran in answer",
            query[:60],
        )

    if wants_hadith and not has_hadith:
        match = _HADITH_REQUEST_RE.search(query)
        violations.append(
            {
                "type": "missing_hadith_evidence",
                "message": (
                    "User requested a Hadith but none was found "
                    "in the generated answer."
                ),
                "details": {
                    "trigger_pattern": match.group(0) if match else "",
                    "has_hadith_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_hadith_evidence: query='%s…' has no Hadith in answer",
            query[:60],
        )

    if wants_evidence and not has_quran and not has_hadith:
        match = _GENERAL_EVIDENCE_RE.search(query)
        violations.append(
            {
                "type": "missing_general_evidence",
                "message": (
                    "User requested religious evidence but neither a "
                    "Quranic verse nor a Hadith was found in the answer."
                ),
                "details": {
                    "trigger_pattern": match.group(0) if match else "",
                    "has_quran_in_answer": False,
                    "has_hadith_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_general_evidence: query='%s…' has no evidence in answer",
            query[:60],
        )

    return violations


__all__ = ["detect_missing_requested_evidence"]