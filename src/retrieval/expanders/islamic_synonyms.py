# Islamic Synonyms Module
"""Islamic terminology synonyms for query expansion."""

from typing import List, Dict


# Comprehensive Islamic terminology synonyms
ISLAMIC_SYNONYMS: Dict[str, List[str]] = {
    # Fiqh (Islamic jurisprudence) terms
    "صلاة": ["الصلاة", "الصلوات", "صلوات", "العبادة"],
    "صوم": ["الصيام", "الصوم", "صيام", "رمضان"],
    "زكاة": ["الزكاة", "زكاة المال", "الصدقة"],
    "حج": ["الحج", "الزيارة", "البيت"],
    "وضوء": ["الوضوء", "الطهارة", "الاغتسال"],
    # Hadith terms
    "حديث": ["الأحاديث", "الحديث", "السنّة", "السنة", "روايات"],
    "صحيح": ["الصحيح", "الصحيحة", "الحسن"],
    "ضعيف": ["الضعيف", "الضعيفة", "الواهية"],
    # Quran terms
    "آية": ["الآيات", "آية", "آي"],
    "سورة": ["السور", "سورة", "سور"],
    "قرآن": ["القرآن", "القرءان", "الكتاب"],
    # Aqeedah terms
    "توحيد": ["التوحيد", "وحدانية الله"],
    "شرك": ["الشرك", "الوثنية"],
    "إيمان": ["الإيمان", "التصديق", "الاعتقاد"],
    "كفر": ["الكفر", "الإنكار", "الجحود"],
}


def get_synonyms(term: str) -> List[str]:
    """Get synonyms for a term."""
    return ISLAMIC_SYNONYMS.get(term, [])


def expand_with_synonyms(query: str) -> List[str]:
    """Expand a query with synonyms."""
    terms = query.split()
    expanded = [query]
    for term in terms:
        if term in ISLAMIC_SYNONYMS:
            expanded.extend(ISLAMIC_SYNONYMS[term])
    return list(dict.fromkeys(expanded))
