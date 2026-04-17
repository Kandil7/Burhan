# Category Mapping Module
"""Category mapping for Islamic text classification."""

from typing import Dict, List, Set
from enum import Enum


class CategoryHierarchy(str, Enum):
    """Category hierarchy levels."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


# Primary to secondary category mappings
PRIMARY_TO_SECONDARY: Dict[str, List[str]] = {
    "quran": ["tafsir", "quranic_sciences", "recitation"],
    "hadith": ["fiqh", "aqeedah", "ethics", "history"],
    "fiqh": ["ibadat", "muamalat", "family", "penal", "constitutional"],
    "tafsir": ["classical_tafsir", "contemporary_tafsir", "thematic_tafsir"],
    "aqeedah": ["tawhid", "attributes_of_allah", "prophethood", "eschatology"],
    "seerah": ["biography", "military", "diplomatic", "economic"],
    "history": ["pre_islamic", "early_islam", "caliphate", "modern"],
    "language": ["arabic_grammar", "morphology", "rhetoric", "lexicography"],
    "ethics": ["akhlaq", "tasawwuf", "spiritual_development"],
}

# Category keywords for classification
CATEGORY_KEYWORDS: Dict[str, Set[str]] = {
    "quran": {"قرآن", "آية", "سورة", "تنزيل", "كتاب الله"},
    "hadith": {"حديث", "رسول", "صحيح", "ضعيف", "سنّة"},
    "fiqh": {"حكم", "فقيه", "مذهب", "فتوى", " صلاة", "صوم", "زكاة", "حج"},
    "tafsir": {"تفسير", "بيان", "معنى", "آية", "فسير"},
    "aqeedah": {"توحيد", "إيمان", "كفر", "شرك", "عقيدة"},
    "seerah": {"سيرة", "نبوية", "صحابة", "غزوة", "فتح"},
    "history": {"تاريخ", "حضارة", "عصر", "دولة", "خلافة"},
    "language": {"لغة", "عربي", "نحو", "صرف", "بلاغة"},
    "ethics": {"أخلاق", "تخلق", "تزكية", "تصوف", "رياضة"},
}


def map_category(text: str) -> List[str]:
    """Map text to categories based on keywords."""
    if not text:
        return []

    found_categories = []

    # Normalize text: remove diacritics and normalize whitespace
    # Note: For Arabic text, we check for keyword presence directly
    text_normalized = text.strip()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # Strip keyword for matching (keywords may have leading/trailing spaces)
            keyword_stripped = keyword.strip()
            if keyword_stripped and keyword_stripped in text_normalized:
                if category not in found_categories:
                    found_categories.append(category)
                break

    return found_categories


def get_subcategories(category: str) -> List[str]:
    """Get subcategories for a primary category."""
    return PRIMARY_TO_SECONDARY.get(category, [])


def get_all_categories() -> List[str]:
    """Get all category names."""
    return list(CATEGORY_KEYWORDS.keys())
