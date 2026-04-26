"""
Golden Set Schema for Burhan Evaluation Framework.

Defines the structure of test items used for evaluating agent performance
on Islamic scholarly questions, particularly in Fiqh domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class GoldenSetItem:
    """
    A test item representing a question with expected outputs for evaluation.

    Attributes:
        id: Unique identifier for the test item.
        question: The test question in Arabic or English.
        domains: List of relevant Islamic domains (e.g., ['fiqh', 'usul_al_fiqh']).
        ikhtilaf_required: Whether the answer should include differences of opinion
            (Ikhtilaf) among madhhabs.
        abstention_expected: Whether the agent should abstain from answering
            due to insufficient knowledge or ambiguity.
        gold_evidence_ids: List of expected evidence IDs that should be retrieved.
        gold_answer_outline: Expected answer structure/outline (not exact text).
        metrics_flags: Additional flags for specific metric calculations.
    """

    id: str
    question: str
    domains: list[str] = field(default_factory=list)
    ikhtilaf_required: bool = False
    abstention_expected: bool = False
    gold_evidence_ids: list[str] = field(default_factory=list)
    gold_answer_outline: str = ""
    metrics_flags: dict = field(default_factory=dict)


# =============================================================================
# Sample Golden Set for Fiqh Domain
# =============================================================================

FIQH_GOLDEN_SET: list[GoldenSetItem] = [
    GoldenSetItem(
        id="fiqh_001",
        question="ما حكم صلاة التراويح في رمضان؟",
        domains=["fiqh", "ibadah"],
        ikhtilaf_required=True,
        abstention_expected=False,
        gold_evidence_ids=["sahih_bukhari_tafsir", "muslim_salah", "ibn_qudamah_fiqh"],
        gold_answer_outline=(
            "صلاة التراويح مستحبة بإجماع العلماء. "
            "تكون القيام ليلاً في رمضان. "
            "اختلفوا في数量的ها: "
            "الحنفية: 20 ركعة بدون وتر. "
            "المالكية: 36 ركعة. "
            "الشافعية والحنابلة: 20 ركعة مع وتر."
        ),
        metrics_flags={"requires_citation": True, "requires_hadith_grade": False},
    ),
    GoldenSetItem(
        id="fiqh_002",
        question="هل يجوز للمسلم أكل لحم الخنزير؟",
        domains=["fiqh", "food"],
        ikhtilaf_required=False,
        abstention_expected=False,
        gold_evidence_ids=["quran_bakarah_173", "sahih_bukhari_food", "mawardi_ahkam"],
        gold_answer_outline=(
            "حرام بإجماع. قال تعالى: {إِنَّمَا حَرَّمَ عَلَيْكُمُ الْمَيْتَةَ وَالدَّمَ وَلَحْمَ الْخَنزِيرِ} الآية 173 من سورة البقرة."
        ),
        metrics_flags={"requires_citation": True, "requires_quran_verse": True},
    ),
    GoldenSetItem(
        id="fiqh_003",
        question="ما شروط صحة الصيام؟",
        domains=["fiqh", "sawm"],
        ikhtilaf_required=True,
        abstention_expected=False,
        gold_evidence_ids=["ibn_qudamah_sawm", "sahnun_mudawwana", "kasani_badai"],
        gold_answer_outline=(
            "شروط صحة الصيام: "
            "1. Islam (الإسلام) "
            "2. Niyyah (النية) قبل الفجر "
            "3. العلم بالحلول "
            "4. الاستطاعة "
            "5. عدم الحيض "
            "اختلفوا في بعض التفاصيل."
        ),
        metrics_flags={"requires_citation": True, "requires_hadith_grade": False},
    ),
    GoldenSetItem(
        id="fiqh_004",
        question="ما حكم ترك صلاة الجمعة عمداً؟",
        domains=["fiqh", "jumuah"],
        ikhtilaf_required=False,
        abstention_expected=False,
        gold_evidence_ids=["sahih_bukhari_jumuah", "muslim_jumuah", "ibn_rujwayh_fiqh"],
        gold_answer_outline=(
            "صلاة الجمعة فرض عين على كل ذكر حر مميز. تركها من غير عذر إثم كبير. من تركها ثلاث جمع متواليات فقد كفر."
        ),
        metrics_flags={"requires_citation": True, "requires_hadith_grade": True},
    ),
    GoldenSetItem(
        id="fiqh_005",
        question="كيف يتم حساب زكاة الذهب؟",
        domains=["fiqh", "zakat"],
        ikhtilaf_required=True,
        abstention_expected=False,
        gold_evidence_ids=["ibn_qudamah_zakat", "kasani_badai_zakat", "mawardi_ahkam_zakat"],
        gold_answer_outline=(
            "زكاة الذهب فرض إذا بلغ النصاب (85 جرام ذهب). "
            "النصاب = 20 مثقالاً = 85 جراماً تقريباً. "
            "القدر = ربع العشر (2.5%). "
            "اختلفوا في وقت الوجوب."
        ),
        metrics_flags={"requires_calculation": True, "requires_citation": True},
    ),
    GoldenSetItem(
        id="fiqh_006",
        question="ما حكم الأذان في أذن المولود؟",
        domains=["fiqh", "tazkiyah"],
        ikhtilaf_required=True,
        abstention_expected=False,
        gold_evidence_ids=["sahih_bukhari_adhan", "ibn_majah_adhan", "nisai_adhan"],
        gold_answer_outline=("الأذان في أذن المولود سنة. يؤذن في الأذن اليمنى عند الولادة. يؤذن في اليسرى عند الفطام."),
        metrics_flags={"requires_hadith_grade": True, "requires_citation": True},
    ),
    GoldenSetItem(
        id="fiqh_007",
        question="هل تجوز الصلاة خلف إمام فاسق؟",
        domains=["fiqh", "imamah"],
        ikhtilaf_required=True,
        abstention_expected=False,
        gold_evidence_ids=["sahih_bukhari_imam", "mawardi_ahkam_imam", "ibn_qudamah_imam"],
        gold_answer_outline=(
            "اختلفوا في جواز الصلاة خلف الفاسق: "
            "الحنابلة: لا تجوز. "
            "الشافعية: تجوز مع الكراهة. "
            "الحنفية: تجوز إن كان فسقه ليس كبيراً."
        ),
        metrics_flags={"requires_ikhtilaf": True, "requires_citation": True},
    ),
    GoldenSetItem(
        id="fiqh_008",
        question="ما شروط الوضوء الصحيح؟",
        domains=["fiqh", "taharah"],
        ikhtilaf_required=False,
        abstention_expected=False,
        gold_evidence_ids=["sahih_bukhari_wudu", "muslim_wudu", "ibn_abd_al_bar_fiqh"],
        gold_answer_outline=(
            "شروط الوضوء: النية، الماء الطهور، إزالة النجاسة، "
            "النية في الأعضاء الثلاثة: الوجه واليدين والرأس. "
            "المسح على الخفين."
        ),
        metrics_flags={"requires_citation": True},
    ),
]


def get_fiqh_golden_set() -> list[GoldenSetItem]:
    """Return the Fiqh golden set for evaluation."""
    return FIQH_GOLDEN_SET


def load_golden_set(path: str) -> list[GoldenSetItem]:
    """
    Load golden set from a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        List of GoldenSetItem objects.
    """
    import json

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [GoldenSetItem(**item) for item in data]
