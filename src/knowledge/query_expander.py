"""
Query expansion with Islamic synonyms for better retrieval.

Expands queries with Arabic/Islamic terminology synonyms
to improve recall in RAG retrieval.

Phase 9: Added query expander with comprehensive Islamic terminology.

Usage:
    expander = QueryExpandor()
    expanded = expander.expand("صلاة الفجر")
    # Returns: ["صلاة الفجر", "صلاة", "الفجر", "الصبح", "فجر"]
"""

from __future__ import annotations

import re
from typing import Any

from src.config.logging_config import get_logger

logger = get_logger()


# Comprehensive Islamic terminology synonyms
ISLAMIC_SYNONYMS: dict[str, list[str]] = {
    # ==========================================
    # Fiqh (Islamic jurisprudence) terms
    # ==========================================
    "صلاة": ["الصلاة", "الصلوات", "صلوات", "العبادة"],
    "صوم": ["الصيام", "الصوم", "صيام", "رمضان"],
    "زكاة": ["الزكاة", "زكاة المال", "الصدقة"],
    "حج": ["الحج", "الزيارة", "البيت"],
    "وضوء": ["الوضوء", "الطهارة", "الاغتسال"],
    "غسل": ["الغسل", "الاغتسال", "الطهارة"],
    "طهارة": ["الطهارة", "النظافة", "الپاکی"],
    "أذان": ["الاذان", "الاقامة", "النداء"],
    "اقامة": ["الاقامة", "الأذان"],
    "جمعة": ["الجمعة", "الجمعه", "يوم الجمعة"],
    "عيد": ["العيد", "الأعياد", "الاحتفال"],
    "رمضان": ["رمضان", "الصيام", "شهر رمضان"],
    # ==========================================
    # Hadith terms
    # ==========================================
    "حديث": ["الأحاديث", "الحديث", "السنّة", "السنة", "روايات"],
    "رواية": ["الرواية", "الروايات", "السند"],
    "صحابي": ["الصحابة", "الصحابي", "التابعين"],
    "تابعين": ["التابعين", "تابعون"],
    "صحيح": ["الصحيح", "الصحيحة", "الحسن"],
    "ضعيف": ["الضعيف", "الضعيفة", "الواهية"],
    "موضوع": ["الموضوع", " الموضوع", " المكذوب"],
    "متصلة": ["المتصلة", "المتتابع"],
    "مرفوع": ["المرفوع", "مرفوع إلى النبي"],
    # ==========================================
    # Quran terms
    # ==========================================
    "آية": ["الآيات", "آية", "آي"],
    "سورة": ["السور", "سورة", "سور"],
    "قرآن": ["القرآن", "القرءان", "الكتاب"],
    "تلاوة": ["التلاوة", "القراءة", "تلاوت"],
    "حفظ": ["الحفظ", "التلقين", "الالتزام"],
    "تفسير": ["التفسير", "التأويل", "بيان"],
    "معنى": ["المعنى", "الznaczenie", "الدلالة"],
    # ==========================================
    # Islamic creed (Aqeedah) terms
    # ==========================================
    "إسلام": ["الإسلام", "الاسلام", "الدين"],
    "مسلم": ["المسلم", "المسلمون", "المؤمن"],
    "مؤمن": ["المؤمن", "المؤمنون", "المسلم"],
    "كافر": ["الكافر", "الكافرون", "الجاحدين", "المشركين"],
    "مشرك": ["المشرك", "المشركون", "الشرك"],
    "منافق": ["المنافق", "المنافقون", "نفاق"],
    "توحيد": ["التوحيد", "وحدانية الله"],
    "شرك": ["الشرك", "الوثنية", "العبادة لغير الله"],
    "إيمان": ["الإيمان", "التصديق", "الاعتقاد"],
    "كفر": ["الكفر", "الإنكار", "الجحود"],
    # ==========================================
    # Islamic history terms
    # ==========================================
    "النبي": ["النبي", "رسول الله", "نبينا"],
    "رسول": ["رسول الله", "الرسول", "النبي"],
    "صحابة": ["الصحابة", "الصحابة رضي الله عنهم"],
    "خلفاء": ["الخلفاء", "الخلافة", "الخلف"],
    "عمر": ["عمر", "عمر بن الخطاب", "الفاروق"],
    "علي": ["علي", "علي بن أبي طالب", "أمير المؤمنين"],
    "فاطمة": ["فاطمة", "فاطمة الزهراء"],
    "مكة": ["مكة", "مكة المكرمة", "بكة"],
    " Medina": ["المدينة", "المدينة المنورة", "يثرب"],
    # ==========================================
    # Islamic theology terms
    # ==========================================
    "الله": ["الله", "ال Tuhan", "الألوهية"],
    "الرحمن": ["الرحمن", "الرحيم", "الأكثر رحمة"],
    "الملائكة": ["الملائكة", "الملائكة", "ملك"],
    "الجن": ["الجن", "الجان", "الشياطين"],
    "الشيطان": ["الشيطان", "الشياطين", "إبليس"],
    "الجنة": ["الجنة", "الجنان", "النعيم"],
    "النار": ["النار", "جحيم", "السعير"],
    "البرزخ": ["البرزخ", "القبر", "بين الحياة والموت"],
    "الساعة": ["الساعة", "القيامة", "ال قيام"],
    "عذاب": ["العذاب", "التعذيب", "ال العقاب"],
    # ==========================================
    # Islamic law schools terms
    # ==========================================
    "مذهب": ["المذهب", "المذاهب", "الملة"],
    "حنفي": ["حنفي", "الحنفية", "أبي حنيفة"],
    "مالكي": ["مالكي", "المالكية", "مالك"],
    "شافعي": ["شافعي", "الشافعية", "الشافعي"],
    "حنبلي": ["حنبلي", "الحنابلة", "ابن حنبل"],
    "جعفر": ["جعفر", "الجعفرية", "الشيعة"],
    # ==========================================
    # Islamic ethics terms
    # ==========================================
    "تقوى": ["التقوى", "الورع", "الزهد"],
    "صبر": ["الصبر", "الملازمة", "التحمل"],
    "شكر": ["الشكر", "الامتنان", "العرفان"],
    "خوف": ["الخوف", "الهيبة", "الرق"],
    "رجاء": ["الرجاء", "الأمل", "التوقع"],
    "محبة": ["المحبة", "الحب", "الود"],
    # ==========================================
    # Dua and adhkar terms
    # ==========================================
    "دعاء": ["الدعاء", "ال supplication", "الطلب"],
    "ذكر": ["الذكر", "الأذكار", "التسبيح"],
    "تسبيح": ["التسبيح", "سبحان الله", "تنزيه"],
    "تحميد": ["التحميد", "الحمد لله", "الشكر"],
    "تكبير": ["التكبير", "الله أكبر", "التعظيم"],
    "تهليل": ["التهليل", "لا إله إلا الله", "التوحيد"],
    # ==========================================
    # Common Arabic words
    # ==========================================
    "هل": ["هل", "أ"],
    "ما": ["ما", "ليس"],
    "لا": ["لا", "ليس"],
    "نعم": ["نعم", "أيوه"],
}


class QueryExpander:
    """
    Expand queries with synonyms for better retrieval.

    Phase 9: Added comprehensive Islamic terminology synonyms.

    Usage:
        expander = QueryExpander()
        expanded = expander.expand("صلاة الفجر")
        # Returns: ["صلاة الفجر", "صلاة", "الفجر", ...]
    """

    def __init__(self):
        self.synonyms = ISLAMIC_SYNONYMS

    def expand(self, query: str) -> list[str]:
        """
        Expand query with all synonyms.

        Args:
            query: Original query text

        Returns:
            List of expanded query variations
        """
        # Keep original
        expanded = [query]

        # Extract terms from query
        terms = self._extract_terms(query)

        for term in terms:
            # Check term directly
            if term in self.synonyms:
                expanded.extend(self.synonyms[term])

            # Also check normalized
            for key, vals in self.synonyms.items():
                if term in vals or term == key:
                    expanded.append(key)
                    expanded.extend(vals)

        # Remove duplicates while preserving order
        result = list(dict.fromkeys(expanded))

        logger.debug(
            "query.expanded",
            original=query[:30],
            terms=len(terms),
            expanded=len(result),
        )

        return result

    def expand_for_retrieval(
        self,
        query: str,
        max_expansions: int = 5,
    ) -> list[str]:
        """
        Get limited expansions for actual retrieval.

        Args:
            query: Original query text
            max_expansions: Maximum number of expansions

        Returns:
            Limited list of query variations
        """
        all_expanded = self.expand(query)

        # Keep original + top expansions
        result = [query]
        for exp in all_expanded[1:max_expansions]:
            if exp not in result:
                result.append(exp)

        return result

    def _extract_terms(self, text: str) -> list[str]:
        """
        Extract Arabic terms from text.

        Args:
            text: Input text

        Returns:
            List of terms
        """
        # Remove diacritics
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

        # Unify alef variants
        text = re.sub(r"[\u0622\u0623\u0625\u0671]", "\u0627", text)

        # Extract Arabic words
        words = re.findall(r"[\u0600-\u06FF]+", text)

        # Filter stop words and short words
        stop_words = {
            "في",
            "من",
            "على",
            "إلى",
            "عن",
            "هذا",
            "هذه",
            "الذي",
            "التي",
            "هو",
            "هي",
            "هم",
            "نحن",
            "أنا",
            "أنت",
            "ما",
            "لا",
            "قد",
            "و",
            "أو",
            "ثم",
            "لكن",
            "إذا",
            "إن",
            "أن",
            "هل",
        }

        filtered = [w for w in words if w not in stop_words and len(w) > 2]

        return filtered

    def normalize(self, text: str) -> str:
        """
        Normalize Arabic text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Remove diacritics
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

        # Unify alef variants
        text = re.sub(r"[\u0622\u0623\u0625\u0671]", "\u0627", text)

        # Normalize ya
        text = text.replace("\u0649", "\u064a")  # ي → ي

        # Normalize ta marbuta
        text = text.replace("\u0629", "\u0647")  # ة → ه

        return text


# ==========================================
# Query Expansion for Retrieval
# ==========================================


class RetrievalQueryExpander(QueryExpander):
    """
    Query expander optimized for retrieval.

    Returns multiple query variations for parallel retrieval.
    """

    def __init__(self):
        super().__init__()

    def get_retrieval_queries(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """
        Get multiple query variations for retrieval.

        Args:
            query: Original query

        Returns:
            List of dicts with query text and weight
        """
        expanded = self.expand(query)

        queries = []

        # Original gets highest weight
        queries.append(
            {
                "query": query,
                "weight": 1.0,
                "type": "original",
            }
        )

        # Add variations with decreasing weight
        for i, exp in enumerate(expanded[1:], 1):
            if exp != query:
                weight = 1.0 / (i + 1)  # Decreasing weight
                queries.append(
                    {
                        "query": exp,
                        "weight": weight,
                        "type": "synonym",
                    }
                )

        return queries
