# src/verifiers/missing_evidence.py
"""
Detector for missing requested evidence types.

Catches the fifth violation class:
  - User explicitly requests evidence (آية / حديث / دليل)
  - But generated answer contains no such evidence
  - Distinct from other violations — this is an incompleteness issue,
    not a grounding/attribution issue.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ── Request Patterns ──────────────────────────────────────────────────────────

# Patterns indicating user wants a Quranic verse
_QURAN_REQUEST_PATTERNS = [
    r"استشهد\s+بآية",
    r"اذكر\s+آية",
    r"دليل\s+من\s+القرآن",
    r"آية\s+قرآنية",
    r"من\s+القرآن",
    r"بآية\s+كريمة",
    r"اقتبس\s+آية",
    r"استدل\s+بآية",
    r"أذكر\s+آية",
]

# Patterns indicating user wants a Hadith
_HADITH_REQUEST_PATTERNS = [
    r"استشهد\s+بحديث",
    r"اذكر\s+حديث",
    r"دليل\s+من\s+السنة",
    r"حديث\s+نبوي",
    r"من\s+السنة",
    r"بحديث\s+شريف",
    r"اقتبس\s+حديث",
    r"استدل\s+بحديث",
]

# Patterns indicating user wants any evidence/proof
_GENERAL_EVIDENCE_PATTERNS = [
    r"استشهد\s+بدليل",
    r"أذكر\s+دليلاً",
    r"دليل\s+شرعي",
    r"أحتاج\s+دليل",
    r"ما\s+الدليل",
    r"بدليل",
]

# ── Answer Presence Patterns ─────────────────────────────────────────────────

# Detects a Quranic verse in the answer:
#   ﴿...﴾  or  [سورة X: Y]  or  (الآية رقم Y من سورة X)
_QURAN_IN_ANSWER_RE = re.compile(
    r"[﴿﴾]"                           # Quran brackets
    r"|[\u0600-\u06FF]+\s*:\s*\d+"    # سورة: رقم pattern
    r"|سورة\s+[\u0600-\u06FF]+"       # سورة + name
    r"|الآية\s+\d+",
    re.UNICODE,
)

# Detects a Hadith in the answer:
#   «...»  or  صحيح البخاري / مسلم / رواه / أخرجه
_HADITH_IN_ANSWER_RE = re.compile(
    r"«.{10,200}»"                         # quoted hadith text
    r"|صحيح\s+(البخاري|مسلم)"             # major collections
    r"|رواه\s+[\u0600-\u06FF]+"           # رواه X
    r"|أخرجه\s+[\u0600-\u06FF]+"          # أخرجه X
    r"|حديث\s+رقم\s+\d+"                  # حديث رقم N
    r"|\(ص\)|ﷺ.*قال",                    # attribution pattern
    re.UNICODE,
)

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
    Detect when user explicitly requested evidence that is absent in answer.

    Checks independently:
      - Quran verse requested but no Quranic text found in answer
      - Hadith requested but no Hadith text found in answer
      - General evidence requested but neither found

    Args:
        query:  Original (normalized) user query
        answer: Generated answer text

    Returns:
        List of violation dicts, empty if all requests are satisfied.

    Examples:
        query="استشهد بآية", answer="...النبي فعل كذا..."
        → [{"type": "missing_quran_evidence", ...}]

        query="اذكر حديثاً", answer="...روى البخاري عن..."
        → []  (satisfied)
    """
    violations: list[dict] = []

    wants_quran = bool(_QURAN_REQUEST_RE.search(query))
    wants_hadith = bool(_HADITH_REQUEST_RE.search(query))
    wants_evidence = bool(_GENERAL_EVIDENCE_RE.search(query))

    has_quran = bool(_QURAN_IN_ANSWER_RE.search(answer))
    has_hadith = bool(_HADITH_IN_ANSWER_RE.search(answer))

    if wants_quran and not has_quran:
        violations.append(
            {
                "type": "missing_quran_evidence",
                "message": (
                    "User requested a Quranic verse but none was found "
                    "in the generated answer."
                ),
                "details": {
                    "trigger_pattern": _QURAN_REQUEST_RE.search(query).group(0),
                    "has_quran_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_quran_evidence: query requested verse but answer has none"
        )

    if wants_hadith and not has_hadith:
        violations.append(
            {
                "type": "missing_hadith_evidence",
                "message": (
                    "User requested a Hadith but none was found "
                    "in the generated answer."
                ),
                "details": {
                    "trigger_pattern": _HADITH_REQUEST_RE.search(query).group(0),
                    "has_hadith_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_hadith_evidence: query requested hadith but answer has none"
        )

    if wants_evidence and not has_quran and not has_hadith:
        violations.append(
            {
                "type": "missing_general_evidence",
                "message": (
                    "User requested religious evidence but neither a "
                    "Quranic verse nor a Hadith was found in the answer."
                ),
                "details": {
                    "trigger_pattern": _GENERAL_EVIDENCE_RE.search(query).group(0),
                    "has_quran_in_answer": False,
                    "has_hadith_in_answer": False,
                },
            }
        )
        logger.warning(
            "missing_general_evidence: query requested proof but answer has none"
        )

    return violations


__all__ = ["detect_missing_requested_evidence"]