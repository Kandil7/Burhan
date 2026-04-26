"""
SeerahAgenticChunker
====================
A production-grade agentic semantic chunking engine for Seerah (Prophetic
Biography) corpora stored as JSONL.

Design goals
------------
* Semantic coherence — chunks map to meaningful knowledge units a Seerah
  scholar would read together.
* Rich knowledge-graph metadata — every chunk carries typed entities,
  temporal context, narrative role, Quranic/Hadith references, and
  inferred inter-chunk relations.
* RAG optimisation — chunk sizes and overlaps are tuned for dense retrieval
  without context bleed.
* Provenance tracking — every chunk references its exact source passage IDs
  so the original text is always recoverable.

Usage
-----
    chunker = SeerahAgenticChunker(
        input_path="seerah_passages.jsonl",
        output_path="seerah_chunks.jsonl",
        small_section_max=5,
        medium_section_max=20,
        window_size=4,
        window_step=3,
    )
    report = chunker.run()
    print(report)

Output JSONL schema (one chunk per line)
-----------------------------------------
{
    "chunk_id": str,                    # "book_{id}_chunk_{n:05d}"
    "source_passage_ids": List[int],    # original _idx values from input
    "book_id": int,
    "book_title": str,
    "author": str,
    "author_death_year": int,           # 99999 = contemporary/unknown
    "category": str,
    "collection": str,
    "section_hierarchy": List[str],     # breadcrumb from root -> leaf
    "section_leaf": str,                # most specific named section
    "page_range": [int, int],           # inclusive [first_page, last_page]
    "page_count": int,
    "text": str,                        # joined passage content (HTML-stripped)
    "chunk_type": str,                  # "atomic" | "section" | "multi_page"
    "metadata": {
        "topics": List[str],            # up to 6 Seerah domain topics
        "entities": {
            "persons":  List[str],
            "places":   List[str],
            "events":   List[str],
            "concepts": List[str],
        },
        "quranic_refs":      List[str], # Surah:Ayah references found in text
        "hadith_collections":List[str], # hadith books cited
        "temporal_context":  str,       # human-readable period with CE/AH
        "temporal_order":    int,       # sortable epoch index (0-15)
        "narrative_role":    str,       # functional classification
        "relations":         List[dict],# inferred cross-chunk relations
    }
}
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# HTML stripping helper
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def _strip_html(text: str) -> str:
    """Remove all HTML/XML tags and normalise whitespace."""
    text = _HTML_TAG_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Passage:
    """One raw input record from the JSONL file."""
    idx: int                # zero-based line index in source file
    content: str
    content_type: str
    book_id: int
    book_title: str
    category: str
    author: str
    author_death: int
    collection: str
    page_number: int
    section_title: str
    hierarchy: List[str]


@dataclass
class Chunk:
    """One semantic chunk with rich metadata."""
    chunk_id: str
    source_passage_ids: List[int]
    book_id: int
    book_title: str
    author: str
    author_death_year: int
    category: str
    collection: str
    section_hierarchy: List[str]
    section_leaf: str
    page_range: Tuple[int, int]
    page_count: int
    text: str
    chunk_type: str                 # atomic | section | multi_page
    topics: List[str]
    persons: List[str]
    places: List[str]
    events: List[str]
    concepts: List[str]
    quranic_refs: List[str]
    hadith_collections: List[str]
    temporal_context: str
    temporal_order: int
    narrative_role: str
    relations: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source_passage_ids": self.source_passage_ids,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "author": self.author,
            "author_death_year": self.author_death_year,
            "category": self.category,
            "collection": self.collection,
            "section_hierarchy": self.section_hierarchy,
            "section_leaf": self.section_leaf,
            "page_range": list(self.page_range),
            "page_count": self.page_count,
            "text": self.text,
            "chunk_type": self.chunk_type,
            "metadata": {
                "topics": self.topics,
                "entities": {
                    "persons":  self.persons,
                    "places":   self.places,
                    "events":   self.events,
                    "concepts": self.concepts,
                },
                "quranic_refs":       self.quranic_refs,
                "hadith_collections": self.hadith_collections,
                "temporal_context":   self.temporal_context,
                "temporal_order":     self.temporal_order,   # FIX: was missing
                "narrative_role":     self.narrative_role,
                "relations":          self.relations,         # FIX: was missing
            },
        }


# ---------------------------------------------------------------------------
# Temporal epoch registry (sortable, human-readable)
# ---------------------------------------------------------------------------
# Each entry: (order_index, pattern, label)
# NOTE: More-specific epochs are listed FIRST so first-match wins correctly.
# Generic period patterns (Meccan / Medinan) are placed LAST (indices 14-15).
TEMPORAL_EPOCHS: List[Tuple[int, str, str]] = [
    (0,  r"قبل البعثة|قبل الإسلام|الجاهلية",
         "Pre-Islamic Era (before 610 CE)"),
    (1,  r"أول وحي|بدء الوحي|نزل عليه القرآن|اقرأ|بعثة النبي|بعث محمد",
         "Beginning of Revelation (610 CE / 13 BH)"),
    (2,  r"إسراء|معراج|ليلة المعراج",
         "Isra' wal-Mi'raj (~621 CE / 1 BH)"),
    (3,  r"هجرة النبي|هاجر إلى المدينة|دخل المدينة|الهجرة النبوية",
         "Prophetic Hijra to Medina (622 CE / 1 AH)"),
    (4,  r"غزوة بدر|بدر الكبرى|يوم بدر",
         "Battle of Badr (624 CE / 2 AH)"),
    (5,  r"غزوة أحد|يوم أحد|جبل أحد",
         "Battle of Uhud (625 CE / 3 AH)"),
    (6,  r"الخندق|غزوة الأحزاب",
         "Battle of the Trench / Ahzab (627 CE / 5 AH)"),
    (7,  r"صلح الحديبية|الحديبية",
         "Treaty of Hudaybiyya (628 CE / 6 AH)"),
    (8,  r"فتح خيبر|غزوة خيبر|خيبر",
         "Conquest of Khaybar (628 CE / 7 AH)"),
    (9,  r"فتح مكة|يوم الفتح|دخل مكة",
         "Conquest of Mecca (630 CE / 8 AH)"),
    (10, r"غزوة حنين|يوم حنين|حنين",
         "Battle of Hunayn (630 CE / 8 AH)"),
    (11, r"غزوة تبوك|تبوك",
         "Expedition of Tabuk (631 CE / 9 AH)"),
    (12, r"حجة الوداع|حج النبي|خطبة الوداع",
         "Farewell Pilgrimage (632 CE / 10 AH)"),
    (13, r"وفاة النبي|مرضه الأخير|قبره|بعد وفاته",
         "Death of the Prophet (632 CE / 11 AH)"),
    # Generic period patterns — kept LAST to avoid swallowing specific events
    (14, r"قبل الهجرة|مكية|مكي|السنة المكية",
         "Meccan Period (610-622 CE)"),
    (15, r"بعد الهجرة|مدنية|مدني|المرحلة المدنية",
         "Medinan Period (622-632 CE)"),
]

_DEFAULT_EPOCH = (99, "Prophetic Era (610-632 CE)")


# ---------------------------------------------------------------------------
# Entity / concept extraction tables
# ---------------------------------------------------------------------------

PERSON_TABLE: List[Tuple[str, str]] = [
    (r"النبي|رسول الله|محمد ﷺ|محمد صلى الله|صلى الله عليه وسلم",
     "Prophet Muhammad ﷺ"),
    (r"أبو بكر الصديق|أبو بكر رضي|الصديق",
     "Abu Bakr al-Siddiq"),
    (r"عمر بن الخطاب|عمر رضي الله|الفاروق",
     "Umar ibn al-Khattab"),
    (r"عثمان بن عفان|عثمان رضي|ذو النورين",
     "Uthman ibn Affan"),
    (r"علي بن أبي طالب|علي رضي الله|أبو الحسن",
     "Ali ibn Abi Talib"),
    (r"عائشة رضي|أم المؤمنين عائشة|عائشة أم",
     "Aisha bint Abi Bakr"),
    (r"خديجة بنت|خديجة رضي",
     "Khadija bint Khuwaylid"),
    (r"فاطمة الزهراء|فاطمة رضي",
     "Fatima al-Zahra"),
    (r"أبو هريرة",
     "Abu Hurayra"),
    (r"عبد الله بن عباس|ابن عباس",
     "Abdullah ibn Abbas"),
    (r"عبد الله بن مسعود|ابن مسعود",
     "Abdullah ibn Masud"),
    (r"أنس بن مالك",
     "Anas ibn Malik"),
    (r"أبو سفيان بن حرب|أبو سفيان",
     "Abu Sufyan ibn Harb"),
    (r"زيد بن حارثة",
     "Zayd ibn Haritha"),
    (r"جبريل|جبرائيل|الروح الأمين",
     "Angel Jibreel (Gabriel)"),
    (r"إبراهيم عليه السلام|نبي الله إبراهيم|إبراهيم الخليل",
     "Prophet Ibrahim (Abraham) ﷺ"),
    (r"موسى عليه السلام|نبي الله موسى|كليم الله",
     "Prophet Musa (Moses) ﷺ"),
    (r"عيسى عليه السلام|نبي الله عيسى|روح الله",
     "Prophet Isa (Jesus) ﷺ"),
    (r"ابن القيم الجوزية|ابن قيم|ابن القيم",
     "Ibn al-Qayyim al-Jawziyya (d. 751 AH)"),
    (r"ابن تيمية|شيخ الإسلام ابن تيمية",
     "Ibn Taymiyya (d. 728 AH)"),
    (r"حمزة بن عبد المطلب|سيد الشهداء",
     "Hamza ibn Abd al-Muttalib"),
    (r"أبو طالب بن عبد المطلب|أبو طالب",
     "Abu Talib ibn Abd al-Muttalib"),
    (r"المسور بن مخرمة",
     "Al-Miswar ibn Makhrama"),
    (r"الحسن بن علي|الحسن رضي",
     "Al-Hasan ibn Ali"),
    (r"الحسين بن علي|الحسين رضي",
     "Al-Husayn ibn Ali"),
    (r"معاوية بن أبي سفيان|معاوية رضي",
     "Muawiyah ibn Abi Sufyan"),
    (r"عبد الرحمن بن عوف",
     "Abd al-Rahman ibn Awf"),
    (r"سعد بن أبي وقاص",
     "Sad ibn Abi Waqqas"),
    (r"بلال بن رباح|بلال الحبشي",
     "Bilal ibn Rabah"),
    (r"أبو ذر الغفاري|أبو ذر",
     "Abu Dharr al-Ghifari"),
    (r"الألباني|الشيخ الألباني",
     "al-Albani (contemporary scholar)"),
    (r"سلمان الفارسي|سلمان رضي",
     "Salman al-Farisi"),
    (r"عمار بن ياسر",
     "Ammar ibn Yasir"),
    (r"أبو عبيدة بن الجراح|أبو عبيدة",
     "Abu Ubayda ibn al-Jarrah"),
    (r"طلحة بن عبيد الله|طلحة رضي",
     "Talha ibn Ubaydullah"),
    (r"الزبير بن العوام|الزبير رضي",
     "al-Zubayr ibn al-Awwam"),
    (r"سعد بن معاذ",
     "Sad ibn Muadh"),
    (r"عبد الله بن أبيّ|ابن سلول",
     "Abdullah ibn Ubayy (chief hypocrite)"),
    (r"أبو لهب|عبد العزى",
     "Abu Lahab"),
    (r"أبو جهل|عمرو بن هشام",
     "Abu Jahl"),
    (r"هند بنت عتبة|هند",
     "Hind bint Utba"),
]

PLACE_TABLE: List[Tuple[str, str]] = [
    (r"مكة المكرمة|مكة|مكه|البلد الحرام|أم القرى|بكة",
     "Mecca (Umm al-Qura)"),
    (r"المدينة المنورة|المدينة|طيبة|يثرب|مدينة النبي",
     "Medina (Madinat al-Nabi)"),
    (r"الكعبة المشرفة|الكعبة|البيت الحرام|الحرم المكي|بيت الله",
     "Kaaba / Masjid al-Haram"),
    (r"المسجد النبوي|مسجد النبي|المسجد الشريف",
     "Masjid al-Nabawi (Prophet's Mosque)"),
    (r"القدس|بيت المقدس|المسجد الأقصى|إيلياء|الصخرة المشرفة",
     "Jerusalem / Masjid al-Aqsa"),
    (r"السماء الأولى|السماء الثانية|السموات|السموات العلا",
     "The Seven Heavens"),
    (r"الجنة|الفردوس|جنة المأوى",
     "Paradise (Janna)"),
    (r"النار|جهنم|السعير",
     "Hellfire (Jahannam)"),
    (r"وادي بدر|يوم بدر|بدر الكبرى",
     "Badr (battlefield)"),
    (r"جبل أحد|يوم أحد|وادي أحد",
     "Uhud (mountain/battlefield)"),
    (r"الخندق|غزوة الأحزاب|المدينة الخندق",
     "Khandaq / Trench"),
    (r"خيبر|غزوة خيبر|حصون خيبر",
     "Khaybar"),
    (r"الحديبية|صلح الحديبية",
     "Al-Hudaybiyya"),
    (r"وادي حنين|غزوة حنين",
     "Hunayn (valley/battlefield)"),
    (r"تبوك|غزوة تبوك|منطقة تبوك",
     "Tabuk"),
    (r"الطائف",
     "Ta'if"),
    (r"الحجاز|منطقة الحجاز",
     "Hijaz (region)"),
    (r"بلاد الشام|الشام|سوريا",
     "Al-Sham (Syria/Levant)"),
    (r"غار حراء|جبل النور|حراء",
     "Cave of Hira' / Jabal al-Nur"),
    (r"غار ثور|جبل ثور",
     "Cave of Thawr"),
    (r"العقبة|منى|مشعر",
     "Aqaba / Mina / Masha'ir"),
    (r"نخلة|وادي نخلة",
     "Nakhlah (valley)"),
    (r"بئر معونة|رجيع",
     "Bi'r Ma'una / Raji'"),
    (r"بدر الصغرى|بدر الموعد",
     "Badr al-Maw'id (small Badr)"),
    (r"مؤتة|غزوة مؤتة",
     "Mu'ta (battlefield)"),
]

CONCEPT_TABLE: List[Tuple[str, str]] = [
    (r"توحيد|الإيمان بالله|لا إله إلا الله|العقيدة",
     "Tawhid (Divine Oneness)"),
    (r"الوحي|إنزال القرآن|تنزيل|الوحي الإلهي",
     "Revelation (Wahy)"),
    (r"النبوة|نبي|رسول|المرسلين|الرسالة",
     "Prophethood (Nubuwwa)"),
    (r"الإيمان|أركان الإيمان|الإيمان بالله",
     "Faith (Iman)"),
    (r"الإسلام|أركان الإسلام|الشهادتان",
     "Islam (Submission)"),
    (r"الجهاد|في سبيل الله|المجاهدين",
     "Jihad (Striving in Allah's path)"),
    (r"الهجرة|هجرة في سبيل الله",
     "Hijra (Migration for Allah's sake)"),
    (r"الصبر|الصابرين|التوكل",
     "Sabr (Patience) & Tawakkul"),
    (r"العدل|القسط|الميزان",
     "Adl (Justice)"),
    (r"الشورى|مشاورة|أهل الرأي",
     "Shura (Consultation)"),
    (r"المنافقون|النفاق|الازدواجية",
     "Nifaq (Hypocrisy)"),
    (r"الردة|المرتد",
     "Ridda (Apostasy)"),
    (r"الحلف|الميثاق|العهد|المعاهدة",
     "Treaty / Covenant"),
    (r"الأخوة|مؤاخاة|التضامن",
     "Brotherhood / Muakhaa"),
    (r"الزهد|التقشف|الدنيا",
     "Zuhd (Asceticism)"),
    (r"الشفاعة|شفاعة النبي",
     "Shafa'a (Intercession)"),
    (r"المعجزة|الآيات البينات|كرامة",
     "Miracles / Signs"),
    (r"الأخلاق|حسن الخلق|مكارم الأخلاق",
     "Prophetic Ethics (Akhlaq)"),
    (r"الفقر|المساكين|الزكاة|الصدقة",
     "Poverty / Zakat / Charity"),
    (r"السنة|الحديث النبوي|الأحاديث",
     "Sunnah / Prophetic Hadith"),
]

EVENT_TABLE: List[Tuple[str, str]] = [
    (r"أول وحي|نزل جبريل|اقرأ|بدء الوحي",
     "First Revelation in Cave Hira'"),
    (r"الإسراء والمعراج|ليلة المعراج|أسري به",
     "Isra' wal-Mi'raj (Night Journey & Ascension)"),
    (r"الهجرة إلى الحبشة|هجرة الحبشة",
     "Hijra to Abyssinia"),
    (r"بيعة العقبة الأولى|بيعة العقبة الثانية|بيعة العقبة",
     "Bay'at al-Aqaba"),
    (r"الهجرة إلى المدينة|هجرة النبي|الهجرة النبوية",
     "Prophetic Hijra to Medina"),
    (r"المؤاخاة بين المهاجرين والأنصار|مؤاخاة المدينة",
     "Brotherhood of Muhajirin and Ansar"),
    (r"بناء المسجد النبوي|أسس المسجد",
     "Construction of the Prophet's Mosque"),
    (r"صحيفة المدينة|وثيقة المدينة|ميثاق المدينة",
     "Charter of Medina"),
    (r"غزوة بدر الكبرى|يوم بدر",
     "Battle of Badr"),
    (r"غزوة أحد|يوم أحد|كسر رباعيته",
     "Battle of Uhud"),
    (r"غزوة الخندق|غزوة الأحزاب",
     "Battle of Khandaq (Confederates)"),
    (r"بني قريظة|غزوة بني قريظة",
     "Banu Qurayza Expedition"),
    (r"الحديبية|صلح الحديبية",
     "Treaty of Hudaybiyya"),
    (r"رسائل النبي|كتب النبي إلى الملوك",
     "Letters to Kings and Rulers"),
    (r"فتح خيبر|يوم خيبر",
     "Conquest of Khaybar"),
    (r"عمرة القضاء|عمرة الوفاء",
     "Umrat al-Qada'"),
    (r"فتح مكة|يوم الفتح الأعظم",
     "Conquest of Mecca"),
    (r"غزوة حنين|وادي حنين",
     "Battle of Hunayn"),
    (r"غزوة تبوك|جيش العسرة",
     "Expedition of Tabuk"),
    (r"حجة الوداع|خطبة الوداع|حج النبي",
     "Farewell Pilgrimage"),
    (r"وفاة النبي|انتقال النبي|المرض الأخير",
     "Death of Prophet Muhammad ﷺ"),
]

TOPIC_TABLE: List[Tuple[List[str], str]] = [
    (["هجرة", "هجرته", "الهجرة النبوية"],              "Hijra"),
    (["غزوة", "غزوات", "سرية", "معركة", "قتال", "جيش"], "Military Expedition/Battle"),
    (["صلاة", "صلاته", "الصلاة", "يصلي", "الركوع", "السجود"], "Salat (Prayer)"),
    (["صوم", "رمضان", "الصيام", "يصوم"],               "Sawm (Fasting)"),
    (["حج", "حجة", "عمرة", "الكعبة", "الطواف", "السعي", "الإحرام"], "Hajj/Umra (Pilgrimage)"),
    (["زكاة", "الصدقة", "الإنفاق"],                    "Zakat/Charity"),
    (["وفد", "وفود", "سفارة", "بعث"],                  "Delegation / Diplomatic"),
    (["فقه", "حكم", "أحكام", "الفوائد", "العبر", "الدروس", "استنبط"], "Fiqh / Legal Lessons"),
    (["شمائل", "خلق", "هدي", "طريقته", "كان يفعل", "عادته"], "Prophetic Character (Shama'il)"),
    (["معجزة", "معجزات", "كرامة", "آية من آيات"],       "Miracles / Prophetic Signs"),
    (["نكاح", "زواج", "طلاق", "أزواجه", "الزوجات", "النساء"], "Marriage / Family"),
    (["دعاء", "ذكر", "تسبيح", "استغفار", "الورد"],     "Du'a / Dhikr"),
    (["قرآن", "وحي", "نزول", "تنزيل", "آية", "سورة"],  "Revelation / Quran"),
    (["صحابة", "صحابي", "أصحاب", "الصحب"],             "Companions (Sahaba)"),
    (["طب", "دواء", "علاج", "الحجامة", "الطب النبوي"],  "Prophetic Medicine"),
    (["أنصار", "الأنصار"],                              "Ansar"),
    (["مهاجرون", "مهاجر", "المهاجرين"],                "Muhajirin"),
    (["يهود", "اليهود", "بني إسرائيل"],                "Jewish tribes / Banu Isra'il"),
    (["نصارى", "أهل الكتاب", "المسيحيون"],              "Christians / People of the Book"),
    (["منافق", "النفاق", "المنافقون"],                  "Hypocrisy / Munafiqeen"),
    (["تحقيق", "مقدمة", "منهج", "المحقق"],              "Scholarly Editorial"),
    (["طعام", "أكل", "شرب", "الغذاء"],                  "Food and Drink"),
    (["لباس", "ثوب", "كسوة", "الملبس"],                 "Dress / Clothing"),
    (["حديث", "رواية", "إسناد", "سند", "رجال"],         "Hadith Transmission"),
    (["تفسير", "تأويل"],                                "Quranic Exegesis (Tafsir)"),
    (["إسراء", "معراج", "ليلة المعراج"],                "Isra'/Mi'raj"),
]

HADITH_COLLECTION_TABLE: List[Tuple[str, str]] = [
    (r"البخاري|صحيح البخاري",                  "Sahih al-Bukhari"),
    (r"مسلم|صحيح مسلم",                        "Sahih Muslim"),
    (r"أبو داود|سنن أبي داود",                  "Sunan Abi Dawud"),
    (r"الترمذي|سنن الترمذي|جامع الترمذي",       "Jami' al-Tirmidhi"),
    (r"النسائي|سنن النسائي",                    "Sunan al-Nasa'i"),
    (r"ابن ماجه|سنن ابن ماجه",                  "Sunan Ibn Majah"),
    (r"أحمد|مسند أحمد",                         "Musnad Ahmad"),
    (r"الطبراني|المعجم الكبير|الأوسط",          "al-Tabarani (al-Mu'jam)"),
    (r"ابن حبان|صحيح ابن حبان",                 "Sahih Ibn Hibban"),
    (r"الحاكم|مستدرك الحاكم",                   "Mustadrak al-Hakim"),
    (r"البيهقي|سنن البيهقي|شعب الإيمان",        "Sunan al-Bayhaqi"),
    (r"الدارقطني|سنن الدارقطني",                "Sunan al-Daraqutni"),
    (r"ابن خزيمة|صحيح ابن خزيمة",               "Sahih Ibn Khuzayma"),
    (r"ابن أبي شيبة|مصنف ابن أبي شيبة",         "Musannaf Ibn Abi Shayba"),
    (r"الطيالسي|مسند الطيالسي",                 "Musnad al-Tayalisi"),
]

NARRATIVE_ROLE_TABLE: List[Tuple[str, str]] = [
    (r"فقه|أحكام|الفوائد|العبر|الدروس|استنبط|استدل",
     "Fiqh / Legal Derivation & Lessons"),
    (r"شمائل|خُلُق|خلقه|هدي|طريقته|كان يفعل|كان يقول|عادته",
     "Prophetic Shama'il / Character"),
    (r"غزوة|سرية|معركة|قتال|الجيش|الكتيبة|البطل",
     "Military Expedition Narrative"),
    (r"وفد|بعث رسالة|كاتب|سفير|الوفود",
     "Diplomatic / Delegation Account"),
    (r"تحقيق|مقدمة|منهج|المحقق|الناشر|طبعة|النسخ الخطية",
     "Scholarly / Editorial Introduction"),
    (r"حدثنا|أخبرنا|أخرجه|روي|رواه|أسند|الإسناد|باب .{1,30} حديث",
     "Hadith Narration / Isnad Chain"),
    (r"هجرة النبي|لما هاجر|أثناء الهجرة|رحلة الهجرة",
     "Hijra Narrative"),
    (r"حج النبي|أدى النبي العمرة|مناسك|الطواف",
     "Pilgrimage / Hajj Account"),
    (r"صلى النبي|صلاة النبي|هدي النبي في الصلاة",
     "Worship / Ibadah Description"),
    (r"خطب النبي|قال رسول الله في خطبة|الخطبة",
     "Prophetic Speech / Sermon"),
    (r"تفسير|في قوله تعالى|المراد بالآية|فسّر",
     "Quranic Exegesis (Tafsir)"),
    (r"الأنساب|نسب النبي|السلالة|جد النبي",
     "Genealogy / Nasab"),
]

# FIX: Extended Quran ref pattern to also catch bare ﴿...﴾ without a bracket ref
_QURAN_REF_PATTERN = re.compile(
    r"\[([^:\u003a\]]+)[:\u003a]\s*(\d+)\]"   # [Surah: ayah]
    r"|﴿([^﴾]{1,120})﴾\s*(?:\[([^\]]+)\])?"       # ﴿text﴾ optionally followed by [ref]
)


# ---------------------------------------------------------------------------
# SeerahAgenticChunker — main class
# ---------------------------------------------------------------------------

class SeerahAgenticChunker:
    """
    Agentic semantic chunker for Seerah JSONL corpora.

    Parameters
    ----------
    input_path : str | Path
        Path to the raw input JSONL file.
    output_path : str | Path
        Where to write the chunked JSONL output.
    small_section_max : int
        Sections with <= this many (unique) pages are emitted as a single chunk.
    medium_section_max : int
        Sections between small_section_max+1 and this value are split into
        windows of `window_size` pages with no overlap.
    window_size : int
        Number of pages per window for medium / large sections.
    window_step : int
        Step size for sliding window in large sections (window_step < window_size
        creates overlap, which helps RAG retrieval at boundary regions).
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        small_section_max: int = 5,
        medium_section_max: int = 20,
        window_size: int = 4,
        window_step: int = 3,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.small_section_max = small_section_max
        self.medium_section_max = medium_section_max
        self.window_size = window_size
        self.window_step = window_step

        self._passages: List[Passage] = []
        self._deduped: List[Passage] = []
        self._sections: Dict[Tuple, List[Passage]] = {}
        self._chunks: List[Chunk] = []
        self._chunk_counter: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> str:
        """Execute the full pipeline and return a human-readable report."""
        self._load_passages()
        self._deduplicate()
        self._group_into_sections()
        self._chunk_all_sections()
        self._infer_cross_chunk_relations()
        self._write_output()
        return self._build_report()

    # ------------------------------------------------------------------
    # Stage 1 — Load
    # ------------------------------------------------------------------

    def _load_passages(self) -> None:
        """Read every line of the JSONL into a Passage dataclass."""
        with self.input_path.open(encoding="utf-8") as fh:
            for idx, raw_line in enumerate(fh):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    rec = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    print(f"[WARN] Line {idx}: JSON parse error — {exc}",
                          file=sys.stderr)
                    continue

                # FIX: Strip HTML from content at load time
                raw_content = rec.get("content", "")
                clean_content = _strip_html(raw_content)

                self._passages.append(Passage(
                    idx=idx,
                    content=clean_content,
                    content_type=rec.get("content_type", "page"),
                    book_id=int(rec.get("book_id", 0)),
                    book_title=rec.get("book_title", ""),
                    category=rec.get("category", ""),
                    author=rec.get("author", ""),
                    author_death=int(rec.get("author_death", 99999)),
                    collection=rec.get("collection", ""),
                    page_number=int(rec.get("page_number", 0)),
                    section_title=rec.get("section_title", ""),
                    hierarchy=rec.get("hierarchy", []),
                ))

    # ------------------------------------------------------------------
    # Stage 2 — Deduplicate
    # ------------------------------------------------------------------

    def _deduplicate(self) -> None:
        """
        Remove exact duplicates using a content hash combining:
        book_id + page_number + hierarchy + content.
        Keeps the first occurrence (lowest idx) of each unique hash.
        """
        seen: set[str] = set()
        for p in self._passages:
            # FIX: Removed spurious extra opening parenthesis that caused TypeError
            fingerprint = hashlib.md5(
                (str(p.book_id) + str(p.page_number) + str(p.hierarchy) + p.content)
                .encode("utf-8")
            ).hexdigest()
            if fingerprint not in seen:
                seen.add(fingerprint)
                self._deduped.append(p)

    # ------------------------------------------------------------------
    # Stage 3 — Group into sections
    # ------------------------------------------------------------------

    def _group_into_sections(self) -> None:
        """
        Group deduplicated passages by (book_id, hierarchy_tuple).
        Passages within each group are sorted by page_number ascending.
        """
        raw_groups: Dict[Tuple, List[Passage]] = defaultdict(list)
        for p in self._deduped:
            key = (p.book_id, tuple(p.hierarchy))
            raw_groups[key].append(p)

        for key, pages in raw_groups.items():
            self._sections[key] = sorted(pages, key=lambda x: x.page_number)

    # ------------------------------------------------------------------
    # Stage 4 — Chunk every section
    # ------------------------------------------------------------------

    def _chunk_all_sections(self) -> None:
        """
        Apply the three-tier chunking strategy to every section group.

        Tier 1 — Small (<= small_section_max pages):
            Entire section -> one chunk.
        Tier 2 — Medium (small_section_max < n <= medium_section_max):
            Non-overlapping windows of `window_size` pages.
        Tier 3 — Large (> medium_section_max pages):
            Overlapping sliding windows (step < window_size).
        """
        for (book_id, hier_tuple), pages in self._sections.items():
            n = len(pages)

            if n <= self.small_section_max:
                groups = [pages]
            elif n <= self.medium_section_max:
                groups = self._non_overlapping_windows(pages, self.window_size)
            else:
                groups = self._sliding_windows(pages, self.window_size, self.window_step)

            for grp in groups:
                if grp:
                    chunk = self._build_chunk(grp, book_id, list(hier_tuple), n)
                    self._chunks.append(chunk)

    # ------------------------------------------------------------------
    # Stage 5 — Cross-chunk relation inference
    # ------------------------------------------------------------------

    def _infer_cross_chunk_relations(self) -> None:
        """
        Build a lightweight knowledge graph by detecting relations between chunks.

        Relation types:
          CONTINUES_FROM  — consecutive chunks within the same section
          SHARES_PERSON   — two chunks mention the same named person  [FIX: added]
          SHARES_EVENT    — two chunks reference the same historical event
          SHARES_PLACE    — two chunks mention the same place          [FIX: added]
          FIQH_OF         — a Fiqh chunk that derives rulings from a narrative chunk
        """
        # ── CONTINUES_FROM ──────────────────────────────────────────────
        section_index: Dict[Tuple, List[int]] = defaultdict(list)
        for i, chunk in enumerate(self._chunks):
            key = tuple(chunk.section_hierarchy)
            section_index[key].append(i)

        for indices in section_index.values():
            for prev_i, next_i in zip(indices, indices[1:]):
                self._chunks[prev_i].relations.append({
                    "type": "CONTINUES_FROM",
                    "target_chunk_id": self._chunks[next_i].chunk_id,
                    "direction": "precedes",
                })
                self._chunks[next_i].relations.append({
                    "type": "CONTINUES_FROM",
                    "target_chunk_id": self._chunks[prev_i].chunk_id,
                    "direction": "follows",
                })

        # ── SHARES_EVENT ────────────────────────────────────────────────
        event_index: Dict[str, List[int]] = defaultdict(list)
        for i, chunk in enumerate(self._chunks):
            for ev in chunk.events:
                event_index[ev].append(i)

        for ev, indices in event_index.items():
            if len(indices) < 2:
                continue
            for i in indices:
                others = [self._chunks[j].chunk_id for j in indices if j != i][:3]
                if others:
                    self._chunks[i].relations.append({
                        "type": "SHARES_EVENT",
                        "event": ev,
                        "related_chunk_ids": others,
                    })

        # ── SHARES_PERSON (FIX: implemented — was documented but missing) ──
        person_index: Dict[str, List[int]] = defaultdict(list)
        for i, chunk in enumerate(self._chunks):
            for person in chunk.persons:
                person_index[person].append(i)

        for person, indices in person_index.items():
            if len(indices) < 2:
                continue
            for i in indices:
                others = [self._chunks[j].chunk_id for j in indices if j != i][:3]
                if others:
                    self._chunks[i].relations.append({
                        "type": "SHARES_PERSON",
                        "person": person,
                        "related_chunk_ids": others,
                    })

        # ── SHARES_PLACE (FIX: implemented — was documented but missing) ──
        place_index: Dict[str, List[int]] = defaultdict(list)
        for i, chunk in enumerate(self._chunks):
            for place in chunk.places:
                place_index[place].append(i)

        for place, indices in place_index.items():
            if len(indices) < 2:
                continue
            for i in indices:
                others = [self._chunks[j].chunk_id for j in indices if j != i][:3]
                if others:
                    self._chunks[i].relations.append({
                        "type": "SHARES_PLACE",
                        "place": place,
                        "related_chunk_ids": others,
                    })

        # ── FIQH_OF ─────────────────────────────────────────────────────
        fiqh_chunks = [
            i for i, c in enumerate(self._chunks)
            if "Fiqh" in c.narrative_role
        ]
        narrative_chunks = [
            i for i, c in enumerate(self._chunks)
            if "Narrative" in c.narrative_role or "Battle" in c.narrative_role
        ]

        ev_narrative: Dict[str, List[int]] = defaultdict(list)
        for i in narrative_chunks:
            for ev in self._chunks[i].events:
                ev_narrative[ev].append(i)

        for fi in fiqh_chunks:
            fc = self._chunks[fi]
            for ev in fc.events:
                for ni in ev_narrative.get(ev, [])[:2]:
                    fc.relations.append({
                        "type": "FIQH_OF",
                        "target_chunk_id": self._chunks[ni].chunk_id,
                        "note": f"Derives rulings from: {ev}",
                    })

    # ------------------------------------------------------------------
    # Stage 6 — Write output
    # ------------------------------------------------------------------

    def _write_output(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as fh:
            for chunk in self._chunks:
                fh.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Chunk construction
    # ------------------------------------------------------------------

    def _build_chunk(
        self,
        pages: List[Passage],
        book_id: int,
        hier: List[str],
        section_total_pages: int,
    ) -> Chunk:
        rep = pages[0]
        combined_text = "\n\n".join(p.content for p in pages)

        if len(pages) == 1:
            chunk_type = "atomic"
        elif section_total_pages <= self.small_section_max:
            chunk_type = "section"
        else:
            chunk_type = "multi_page"

        section_leaf = self._resolve_section_leaf(hier, rep)
        temporal_ctx, temporal_order = self._infer_temporal_context(combined_text, hier)

        chunk = Chunk(
            chunk_id=f"book_{book_id}_chunk_{self._chunk_counter:05d}",
            source_passage_ids=[p.idx for p in pages],
            book_id=book_id,
            book_title=rep.book_title,
            author=rep.author,
            author_death_year=rep.author_death,
            category=rep.category,
            collection=rep.collection,
            section_hierarchy=hier,
            section_leaf=section_leaf,
            page_range=(pages[0].page_number, pages[-1].page_number),
            page_count=len(pages),
            text=combined_text,
            chunk_type=chunk_type,
            topics=self._extract_topics(combined_text, hier),
            persons=self._extract_persons(combined_text),
            places=self._extract_places(combined_text),
            events=self._extract_events(combined_text, hier),
            concepts=self._extract_concepts(combined_text),
            quranic_refs=self._extract_quranic_refs(combined_text),
            hadith_collections=self._extract_hadith_collections(combined_text),
            temporal_context=temporal_ctx,
            temporal_order=temporal_order,
            narrative_role=self._infer_narrative_role(combined_text, hier),
            relations=[],
        )
        self._chunk_counter += 1
        return chunk

    # ------------------------------------------------------------------
    # Windowing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _non_overlapping_windows(
        pages: List[Passage], size: int
    ) -> List[List[Passage]]:
        """Split `pages` into consecutive, non-overlapping groups of `size`."""
        return [pages[i : i + size] for i in range(0, len(pages), size)]

    @staticmethod
    def _sliding_windows(
        pages: List[Passage], size: int, step: int
    ) -> List[List[Passage]]:
        """
        Produce overlapping windows. `step` < `size` creates context overlap.

        FIX: Trailing windows smaller than size//2 are merged into the preceding
        window to avoid tiny stub chunks that hurt retrieval quality.
        """
        windows = [pages[i : i + size] for i in range(0, len(pages), step)]
        # Merge last stub window into the second-to-last if it is too small
        if len(windows) >= 2 and len(windows[-1]) < size // 2:
            windows[-2] = windows[-2] + [
                p for p in windows[-1] if p not in windows[-2]
            ]
            windows.pop()
        return windows

    # ------------------------------------------------------------------
    # Metadata extraction — Topics
    # ------------------------------------------------------------------

    def _extract_topics(self, text: str, hier: List[str]) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 700
        combined = " ".join(hier) + " " + text[:4000]
        topics: List[str] = []
        for keywords, label in TOPIC_TABLE:
            if any(kw in combined for kw in keywords):
                topics.append(label)
            if len(topics) >= 6:
                break
        return list(dict.fromkeys(topics))

    # ------------------------------------------------------------------
    # Metadata extraction — Persons
    # ------------------------------------------------------------------

    def _extract_persons(self, text: str) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 1000
        sample = text[:4000]
        persons: List[str] = []
        for pattern, canonical in PERSON_TABLE:
            if re.search(pattern, sample):
                persons.append(canonical)
        return list(dict.fromkeys(persons))[:8]

    # ------------------------------------------------------------------
    # Metadata extraction — Places
    # ------------------------------------------------------------------

    def _extract_places(self, text: str) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 900
        sample = text[:4000]
        places: List[str] = []
        for pattern, canonical in PLACE_TABLE:
            if re.search(pattern, sample):
                places.append(canonical)
        return list(dict.fromkeys(places))[:6]

    # ------------------------------------------------------------------
    # Metadata extraction — Events
    # ------------------------------------------------------------------

    def _extract_events(self, text: str, hier: List[str]) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 900
        combined = " ".join(hier) + " " + text[:4000]
        events: List[str] = []
        for pattern, canonical in EVENT_TABLE:
            if re.search(pattern, combined):
                events.append(canonical)
        return list(dict.fromkeys(events))[:5]

    # ------------------------------------------------------------------
    # Metadata extraction — Concepts
    # ------------------------------------------------------------------

    def _extract_concepts(self, text: str) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 800
        sample = text[:4000]
        concepts: List[str] = []
        for pattern, canonical in CONCEPT_TABLE:
            if re.search(pattern, sample):
                concepts.append(canonical)
        return list(dict.fromkeys(concepts))[:5]

    # ------------------------------------------------------------------
    # Metadata extraction — Quranic references
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_quranic_refs(text: str) -> List[str]:
        """
        Find Quran citations in the format [Surah: ayah] or ﴿...﴾ [ref].
        FIX: Also captures bare ﴿...﴾ blocks without a trailing bracket reference,
        returning the quoted text as the reference identifier.
        """
        refs: List[str] = []
        for m in _QURAN_REF_PATTERN.finditer(text):
            if m.group(1) and m.group(2):
                # [Surah: ayah]
                refs.append(f"{m.group(1).strip()} : {m.group(2).strip()}")
            elif m.group(4):
                # ﴿...﴾ [ref]
                refs.append(m.group(4).strip())
            elif m.group(3):
                # bare ﴿...﴾ — use quoted text snippet as ref
                snippet = m.group(3).strip()[:60]
                refs.append(f"﴿{snippet}﴾")
        return list(dict.fromkeys(refs))[:8]

    # ------------------------------------------------------------------
    # Metadata extraction — Hadith collections
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_hadith_collections(text: str) -> List[str]:
        # FIX: Scan full text (up to 4000 chars) instead of 1200
        sample = text[:4000]
        cited: List[str] = []
        for pattern, canonical in HADITH_COLLECTION_TABLE:
            if re.search(pattern, sample):
                cited.append(canonical)
        return list(dict.fromkeys(cited))[:6]

    # ------------------------------------------------------------------
    # Temporal context inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_temporal_context(
        text: str, hier: List[str]
    ) -> Tuple[str, int]:
        """
        Return (human-readable period string, sortable epoch index).
        FIX: Scans full text (up to 4000 chars) instead of 700.
        Iterates TEMPORAL_EPOCHS in definition order (specific events first,
        generic Meccan/Medinan periods last) and returns the first match.
        """
        combined = " ".join(hier) + " " + text[:4000]
        for order, pattern, label in TEMPORAL_EPOCHS:
            if re.search(pattern, combined):
                return label, order
        return _DEFAULT_EPOCH[1], _DEFAULT_EPOCH[0]

    # ------------------------------------------------------------------
    # Narrative role inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_narrative_role(text: str, hier: List[str]) -> str:
        # FIX: Scan full text (up to 4000 chars) instead of 600
        combined = " ".join(hier) + " " + text[:4000]
        for pattern, role in NARRATIVE_ROLE_TABLE:
            if re.search(pattern, combined):
                return role
        return "General Seerah Narrative"

    # ------------------------------------------------------------------
    # Section leaf resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_section_leaf(hier: List[str], rep: Passage) -> str:
        if not hier:
            return rep.section_title or ""
        leaf = hier[-1]
        if leaf == rep.book_title and rep.section_title:
            return rep.section_title
        return leaf

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _build_report(self) -> str:
        total_in       = len(self._passages)
        total_deduped  = len(self._deduped)
        total_sections = len(self._sections)
        total_chunks   = len(self._chunks)

        book_counts    = Counter(c.book_id          for c in self._chunks)
        role_counts    = Counter(c.narrative_role   for c in self._chunks)
        temporal_counts= Counter(c.temporal_context for c in self._chunks)
        chunk_types    = Counter(c.chunk_type        for c in self._chunks)
        topic_counts: Counter = Counter()
        for c in self._chunks:
            topic_counts.update(c.topics)

        rel_counts = Counter()
        for c in self._chunks:
            for r in c.relations:
                rel_counts[r["type"]] += 1

        lines = [
            "=" * 68,
            "  SeerahAgenticChunker — Run Report",
            "=" * 68,
            f"  Input file  : {self.input_path}",
            f"  Output file : {self.output_path}",
            "",
            "  ── Passage statistics ──────────────────────────────────",
            f"  Raw passages loaded  : {total_in:,}",
            f"  After deduplication  : {total_deduped:,} "
            f"({total_in - total_deduped:,} duplicates removed)",
            f"  Unique section groups: {total_sections:,}",
            "",
            "  ── Chunking parameters ─────────────────────────────────",
            f"  small_section_max  : <= {self.small_section_max} pages -> 1 chunk",
            f"  medium_section_max : <= {self.medium_section_max} pages -> "
            f"non-overlapping windows of {self.window_size}",
            f"  large section      : > {self.medium_section_max} pages -> "
            f"sliding window ({self.window_size}/{self.window_step})",
            "",
            "  ── Output chunks ───────────────────────────────────────",
            f"  Total chunks : {total_chunks:,}",
        ]
        for ct, cnt in sorted(chunk_types.items()):
            lines.append(f"    {ct:<14}: {cnt:,}")

        lines += ["", "  ── Chunks per book ─────────────────────────────────────"]
        for bid, cnt in book_counts.most_common():
            lines.append(f"    Book {bid:>4} : {cnt:,} chunks")

        lines += ["", "  ── Top narrative roles ──────────────────────────────────"]
        for role, cnt in role_counts.most_common(8):
            lines.append(f"    {cnt:>5}x  {role}")

        lines += ["", "  ── Top topics ───────────────────────────────────────────"]
        for topic, cnt in topic_counts.most_common(10):
            lines.append(f"    {cnt:>5}x  {topic}")

        lines += ["", "  ── Top temporal contexts ────────────────────────────────"]
        for ctx, cnt in temporal_counts.most_common(8):
            lines.append(f"    {cnt:>5}x  {ctx}")

        lines += ["", "  ── Knowledge-graph relations ────────────────────────────"]
        for rel_type, cnt in rel_counts.most_common():
            lines.append(f"    {cnt:>6}x  {rel_type}")

        lines += ["", "=" * 68]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Agentic semantic chunker for Seerah JSONL corpora."
    )
    parser.add_argument("input",  help="Path to input JSONL file")
    parser.add_argument("output", help="Path to output JSONL file")
    parser.add_argument("--small-max",  type=int, default=5,
                        help="Max pages for a single-chunk section (default 5)")
    parser.add_argument("--medium-max", type=int, default=20,
                        help="Max pages before sliding-window mode (default 20)")
    parser.add_argument("--window",     type=int, default=4,
                        help="Window size in pages (default 4)")
    parser.add_argument("--step",       type=int, default=3,
                        help="Step size for large-section sliding window "
                             "(default 3; set equal to --window for no overlap)")
    args = parser.parse_args()

    chunker = SeerahAgenticChunker(
        input_path=args.input,
        output_path=args.output,
        small_section_max=args.small_max,
        medium_section_max=args.medium_max,
        window_size=args.window,
        window_step=args.step,
    )
    report = chunker.run()
    print(report)


if __name__ == "__main__":
    main()
