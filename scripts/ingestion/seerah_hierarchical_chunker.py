"""
SeerahHierarchicalChunker
=========================
Hierarchical chunking strategy for Seerah (and general Athar) corpora.

Core idea
---------
Each "knowledge unit" is stored at TWO levels simultaneously:

    PARENT chunk  (large, ~full section)
        └── CHILD chunks  (small, ~1-2 pages, used for dense retrieval)

During RAG:
  1. Search is done on CHILD chunks (high precision).
  2. The matched child's parent_chunk_id is used to fetch the full PARENT
     for LLM context (high recall / richer context window).

This avoids the classic tradeoff between retrieval precision and LLM context.

Output JSONL schema
-------------------
{
  "chunk_id":          str,    # e.g. "book_197_parent_00001"
  "parent_chunk_id":   str,    # null for parent chunks
  "level":             str,    # "parent" | "child"
  "source_passage_ids":List[int],
  "book_id":           int,
  "book_title":        str,
  "author":            str,
  "author_death_year": int,
  "category":          str,
  "collection":        str,
  "section_hierarchy": List[str],
  "section_leaf":      str,
  "page_range":        [int, int],
  "page_count":        int,
  "text":              str,
  "chunk_type":        str,    # "parent" | "child"
  "metadata": {
    "topics":              List[str],
    "entities": {
      "persons":  List[str],
      "places":   List[str],
      "events":   List[str],
      "concepts": List[str],
    },
    "quranic_refs":       List[str],
    "hadith_collections": List[str],
    "temporal_context":   str,
    "temporal_order":     int,
    "narrative_role":     str,
    "relations":          List[dict],
    "child_chunk_ids":    List[str],  # only on parent chunks
    "sibling_chunk_ids":  List[str],  # only on child chunks (prev/next)
  }
}

Usage
-----
    chunker = SeerahHierarchicalChunker(
        input_path="seerah_passages.jsonl",
        output_path="seerah_hierarchical_chunks.jsonl",
        parent_max_pages=12,
        child_pages=2,
        child_overlap=1,
    )
    report = chunker.run()
    print(report)
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

_HTML_TAG_RE    = re.compile(r"<[^>]+>", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NL_RE    = re.compile(r"\n{3,}")


def _strip_html(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Lookup tables (persons, places, events, concepts, topics, epochs, roles)
# — identical to fixed chunker, imported here for completeness —
# ---------------------------------------------------------------------------

TEMPORAL_EPOCHS: List[Tuple[int, str, str]] = [
    (0,  r"قبل البعثة|قبل الإسلام|الجاهلية",                          "Pre-Islamic Era (before 610 CE)"),
    (1,  r"أول وحي|بدء الوحي|نزل عليه القرآن|اقرأ|بعثة النبي|بعث محمد", "Beginning of Revelation (610 CE / 13 BH)"),
    (2,  r"إسراء|معراج|ليلة المعراج",                                   "Isra' wal-Mi'raj (~621 CE / 1 BH)"),
    (3,  r"هجرة النبي|هاجر إلى المدينة|دخل المدينة|الهجرة النبوية",     "Prophetic Hijra to Medina (622 CE / 1 AH)"),
    (4,  r"غزوة بدر|بدر الكبرى|يوم بدر",                               "Battle of Badr (624 CE / 2 AH)"),
    (5,  r"غزوة أحد|يوم أحد|جبل أحد",                                  "Battle of Uhud (625 CE / 3 AH)"),
    (6,  r"الخندق|غزوة الأحزاب",                                        "Battle of the Trench / Ahzab (627 CE / 5 AH)"),
    (7,  r"صلح الحديبية|الحديبية",                                      "Treaty of Hudaybiyya (628 CE / 6 AH)"),
    (8,  r"فتح خيبر|غزوة خيبر|خيبر",                                   "Conquest of Khaybar (628 CE / 7 AH)"),
    (9,  r"فتح مكة|يوم الفتح|دخل مكة",                                  "Conquest of Mecca (630 CE / 8 AH)"),
    (10, r"غزوة حنين|يوم حنين|حنين",                                    "Battle of Hunayn (630 CE / 8 AH)"),
    (11, r"غزوة تبوك|تبوك",                                             "Expedition of Tabuk (631 CE / 9 AH)"),
    (12, r"حجة الوداع|حج النبي|خطبة الوداع",                            "Farewell Pilgrimage (632 CE / 10 AH)"),
    (13, r"وفاة النبي|مرضه الأخير|قبره|بعد وفاته",                      "Death of the Prophet (632 CE / 11 AH)"),
    (14, r"قبل الهجرة|مكية|مكي|السنة المكية",                           "Meccan Period (610-622 CE)"),
    (15, r"بعد الهجرة|مدنية|مدني|المرحلة المدنية",                      "Medinan Period (622-632 CE)"),
]
_DEFAULT_EPOCH = (99, "Prophetic Era (610-632 CE)")

PERSON_TABLE: List[Tuple[str, str]] = [
    (r"النبي|رسول الله|محمد ﷺ|محمد صلى الله|صلى الله عليه وسلم", "Prophet Muhammad ﷺ"),
    (r"أبو بكر الصديق|أبو بكر رضي|الصديق",                       "Abu Bakr al-Siddiq"),
    (r"عمر بن الخطاب|عمر رضي الله|الفاروق",                       "Umar ibn al-Khattab"),
    (r"عثمان بن عفان|عثمان رضي|ذو النورين",                        "Uthman ibn Affan"),
    (r"علي بن أبي طالب|علي رضي الله|أبو الحسن",                   "Ali ibn Abi Talib"),
    (r"عائشة رضي|أم المؤمنين عائشة|عائشة أم",                     "Aisha bint Abi Bakr"),
    (r"خديجة بنت|خديجة رضي",                                       "Khadija bint Khuwaylid"),
    (r"فاطمة الزهراء|فاطمة رضي",                                   "Fatima al-Zahra"),
    (r"أبو هريرة",                                                  "Abu Hurayra"),
    (r"عبد الله بن عباس|ابن عباس",                                  "Abdullah ibn Abbas"),
    (r"عبد الله بن مسعود|ابن مسعود",                                "Abdullah ibn Masud"),
    (r"أنس بن مالك",                                                "Anas ibn Malik"),
    (r"أبو سفيان بن حرب|أبو سفيان",                                 "Abu Sufyan ibn Harb"),
    (r"زيد بن حارثة",                                               "Zayd ibn Haritha"),
    (r"جبريل|جبرائيل|الروح الأمين",                                 "Angel Jibreel (Gabriel)"),
    (r"إبراهيم عليه السلام|نبي الله إبراهيم|إبراهيم الخليل",        "Prophet Ibrahim (Abraham) ﷺ"),
    (r"موسى عليه السلام|نبي الله موسى|كليم الله",                   "Prophet Musa (Moses) ﷺ"),
    (r"عيسى عليه السلام|نبي الله عيسى|روح الله",                    "Prophet Isa (Jesus) ﷺ"),
    (r"ابن القيم الجوزية|ابن قيم|ابن القيم",                        "Ibn al-Qayyim al-Jawziyya (d. 751 AH)"),
    (r"ابن تيمية|شيخ الإسلام ابن تيمية",                            "Ibn Taymiyya (d. 728 AH)"),
    (r"حمزة بن عبد المطلب|سيد الشهداء",                             "Hamza ibn Abd al-Muttalib"),
    (r"أبو طالب بن عبد المطلب|أبو طالب",                            "Abu Talib ibn Abd al-Muttalib"),
    (r"الحسن بن علي|الحسن رضي",                                     "Al-Hasan ibn Ali"),
    (r"الحسين بن علي|الحسين رضي",                                   "Al-Husayn ibn Ali"),
    (r"معاوية بن أبي سفيان|معاوية رضي",                             "Muawiyah ibn Abi Sufyan"),
    (r"بلال بن رباح|بلال الحبشي",                                   "Bilal ibn Rabah"),
    (r"سعد بن معاذ",                                                "Sad ibn Muadh"),
    (r"عبد الله بن أبيّ|ابن سلول",                                  "Abdullah ibn Ubayy (chief hypocrite)"),
    (r"أبو لهب|عبد العزى",                                          "Abu Lahab"),
    (r"أبو جهل|عمرو بن هشام",                                       "Abu Jahl"),
    (r"هند بنت عتبة|هند",                                           "Hind bint Utba"),
]

PLACE_TABLE: List[Tuple[str, str]] = [
    (r"مكة المكرمة|مكة|مكه|البلد الحرام|أم القرى|بكة",              "Mecca (Umm al-Qura)"),
    (r"المدينة المنورة|المدينة|طيبة|يثرب|مدينة النبي",              "Medina (Madinat al-Nabi)"),
    (r"الكعبة المشرفة|الكعبة|البيت الحرام|الحرم المكي|بيت الله",    "Kaaba / Masjid al-Haram"),
    (r"المسجد النبوي|مسجد النبي|المسجد الشريف",                     "Masjid al-Nabawi (Prophet's Mosque)"),
    (r"القدس|بيت المقدس|المسجد الأقصى|إيلياء",                      "Jerusalem / Masjid al-Aqsa"),
    (r"الجنة|الفردوس|جنة المأوى",                                   "Paradise (Janna)"),
    (r"النار|جهنم|السعير",                                          "Hellfire (Jahannam)"),
    (r"وادي بدر|يوم بدر|بدر الكبرى",                                "Badr (battlefield)"),
    (r"جبل أحد|يوم أحد|وادي أحد",                                   "Uhud (mountain/battlefield)"),
    (r"الخندق|غزوة الأحزاب",                                        "Khandaq / Trench"),
    (r"خيبر|غزوة خيبر|حصون خيبر",                                  "Khaybar"),
    (r"الحديبية|صلح الحديبية",                                      "Al-Hudaybiyya"),
    (r"وادي حنين|غزوة حنين",                                        "Hunayn (valley/battlefield)"),
    (r"تبوك|غزوة تبوك|منطقة تبوك",                                  "Tabuk"),
    (r"الطائف",                                                      "Ta'if"),
    (r"الحجاز|منطقة الحجاز",                                        "Hijaz (region)"),
    (r"بلاد الشام|الشام|سوريا",                                     "Al-Sham (Syria/Levant)"),
    (r"غار حراء|جبل النور|حراء",                                     "Cave of Hira' / Jabal al-Nur"),
    (r"غار ثور|جبل ثور",                                            "Cave of Thawr"),
    (r"العقبة|منى|مشعر",                                            "Aqaba / Mina / Masha'ir"),
]

CONCEPT_TABLE: List[Tuple[str, str]] = [
    (r"توحيد|الإيمان بالله|لا إله إلا الله|العقيدة",   "Tawhid (Divine Oneness)"),
    (r"الوحي|إنزال القرآن|تنزيل|الوحي الإلهي",         "Revelation (Wahy)"),
    (r"النبوة|نبي|رسول|المرسلين|الرسالة",              "Prophethood (Nubuwwa)"),
    (r"الإيمان|أركان الإيمان",                         "Faith (Iman)"),
    (r"الجهاد|في سبيل الله|المجاهدين",                 "Jihad"),
    (r"الهجرة|هجرة في سبيل الله",                      "Hijra"),
    (r"الصبر|الصابرين|التوكل",                         "Sabr & Tawakkul"),
    (r"المنافقون|النفاق",                              "Nifaq (Hypocrisy)"),
    (r"الأخوة|مؤاخاة|التضامن",                         "Brotherhood / Muakhaa"),
    (r"المعجزة|الآيات البينات|كرامة",                  "Miracles / Signs"),
    (r"الأخلاق|حسن الخلق|مكارم الأخلاق",              "Prophetic Ethics (Akhlaq)"),
    (r"السنة|الحديث النبوي|الأحاديث",                  "Sunnah / Prophetic Hadith"),
]

EVENT_TABLE: List[Tuple[str, str]] = [
    (r"أول وحي|نزل جبريل|اقرأ|بدء الوحي",                        "First Revelation in Cave Hira'"),
    (r"الإسراء والمعراج|ليلة المعراج|أسري به",                    "Isra' wal-Mi'raj"),
    (r"الهجرة إلى الحبشة|هجرة الحبشة",                            "Hijra to Abyssinia"),
    (r"بيعة العقبة الأولى|بيعة العقبة الثانية|بيعة العقبة",       "Bay'at al-Aqaba"),
    (r"الهجرة إلى المدينة|هجرة النبي|الهجرة النبوية",             "Prophetic Hijra to Medina"),
    (r"المؤاخاة بين المهاجرين والأنصار|مؤاخاة المدينة",           "Brotherhood of Muhajirin and Ansar"),
    (r"بناء المسجد النبوي|أسس المسجد",                             "Construction of the Prophet's Mosque"),
    (r"صحيفة المدينة|وثيقة المدينة|ميثاق المدينة",                "Charter of Medina"),
    (r"غزوة بدر الكبرى|يوم بدر",                                  "Battle of Badr"),
    (r"غزوة أحد|يوم أحد|كسر رباعيته",                             "Battle of Uhud"),
    (r"غزوة الخندق|غزوة الأحزاب",                                 "Battle of Khandaq (Confederates)"),
    (r"بني قريظة|غزوة بني قريظة",                                 "Banu Qurayza Expedition"),
    (r"الحديبية|صلح الحديبية",                                    "Treaty of Hudaybiyya"),
    (r"فتح خيبر|يوم خيبر",                                        "Conquest of Khaybar"),
    (r"فتح مكة|يوم الفتح الأعظم",                                  "Conquest of Mecca"),
    (r"غزوة حنين|وادي حنين",                                      "Battle of Hunayn"),
    (r"غزوة تبوك|جيش العسرة",                                     "Expedition of Tabuk"),
    (r"حجة الوداع|خطبة الوداع|حج النبي",                           "Farewell Pilgrimage"),
    (r"وفاة النبي|انتقال النبي|المرض الأخير",                      "Death of Prophet Muhammad ﷺ"),
]

TOPIC_TABLE: List[Tuple[List[str], str]] = [
    (["هجرة", "هجرته", "الهجرة النبوية"],              "Hijra"),
    (["غزوة", "غزوات", "سرية", "معركة", "قتال", "جيش"], "Military Expedition/Battle"),
    (["صلاة", "صلاته", "الصلاة", "يصلي", "الركوع"],    "Salat (Prayer)"),
    (["صوم", "رمضان", "الصيام", "يصوم"],               "Sawm (Fasting)"),
    (["حج", "حجة", "عمرة", "الكعبة", "الطواف", "الإحرام"], "Hajj/Umra (Pilgrimage)"),
    (["زكاة", "الصدقة", "الإنفاق"],                    "Zakat/Charity"),
    (["وفد", "وفود", "سفارة", "بعث"],                  "Delegation / Diplomatic"),
    (["فقه", "حكم", "أحكام", "الفوائد", "العبر", "الدروس", "استنبط"], "Fiqh / Legal Lessons"),
    (["شمائل", "خلق", "هدي", "طريقته", "كان يفعل"],    "Prophetic Character (Shama'il)"),
    (["معجزة", "معجزات", "كرامة"],                     "Miracles / Prophetic Signs"),
    (["نكاح", "زواج", "طلاق", "أزواجه", "الزوجات"],    "Marriage / Family"),
    (["دعاء", "ذكر", "تسبيح", "استغفار", "الورد"],     "Du'a / Dhikr"),
    (["قرآن", "وحي", "نزول", "تنزيل", "آية", "سورة"],  "Revelation / Quran"),
    (["صحابة", "صحابي", "أصحاب", "الصحب"],             "Companions (Sahaba)"),
    (["طب", "دواء", "علاج", "الحجامة"],                "Prophetic Medicine"),
    (["أنصار", "الأنصار"],                              "Ansar"),
    (["مهاجرون", "مهاجر", "المهاجرين"],                "Muhajirin"),
    (["يهود", "اليهود", "بني إسرائيل"],                "Jewish tribes / Banu Isra'il"),
    (["منافق", "النفاق", "المنافقون"],                  "Hypocrisy / Munafiqeen"),
    (["حديث", "رواية", "إسناد", "سند", "رجال"],         "Hadith Transmission"),
    (["تفسير", "تأويل"],                                "Quranic Exegesis (Tafsir)"),
    (["إسراء", "معراج", "ليلة المعراج"],                "Isra'/Mi'raj"),
]

HADITH_COLLECTION_TABLE: List[Tuple[str, str]] = [
    (r"البخاري|صحيح البخاري",            "Sahih al-Bukhari"),
    (r"مسلم|صحيح مسلم",                  "Sahih Muslim"),
    (r"أبو داود|سنن أبي داود",            "Sunan Abi Dawud"),
    (r"الترمذي|سنن الترمذي|جامع الترمذي", "Jami' al-Tirmidhi"),
    (r"النسائي|سنن النسائي",              "Sunan al-Nasa'i"),
    (r"ابن ماجه|سنن ابن ماجه",            "Sunan Ibn Majah"),
    (r"أحمد|مسند أحمد",                   "Musnad Ahmad"),
    (r"الطبراني|المعجم الكبير|الأوسط",   "al-Tabarani (al-Mu'jam)"),
    (r"ابن حبان|صحيح ابن حبان",           "Sahih Ibn Hibban"),
    (r"الحاكم|مستدرك الحاكم",             "Mustadrak al-Hakim"),
    (r"البيهقي|سنن البيهقي|شعب الإيمان",  "Sunan al-Bayhaqi"),
    (r"الدارقطني|سنن الدارقطني",          "Sunan al-Daraqutni"),
    (r"ابن خزيمة|صحيح ابن خزيمة",         "Sahih Ibn Khuzayma"),
    (r"ابن أبي شيبة|مصنف ابن أبي شيبة",   "Musannaf Ibn Abi Shayba"),
]

NARRATIVE_ROLE_TABLE: List[Tuple[str, str]] = [
    (r"فقه|أحكام|الفوائد|العبر|الدروس|استنبط|استدل",         "Fiqh / Legal Derivation & Lessons"),
    (r"شمائل|خُلُق|خلقه|هدي|طريقته|كان يفعل|كان يقول|عادته", "Prophetic Shama'il / Character"),
    (r"غزوة|سرية|معركة|قتال|الجيش|الكتيبة",                  "Military Expedition Narrative"),
    (r"وفد|بعث رسالة|كاتب|سفير|الوفود",                      "Diplomatic / Delegation Account"),
    (r"تحقيق|مقدمة|منهج|المحقق|الناشر|طبعة",                 "Scholarly / Editorial Introduction"),
    (r"حدثنا|أخبرنا|أخرجه|روي|رواه|أسند|الإسناد",            "Hadith Narration / Isnad Chain"),
    (r"هجرة النبي|لما هاجر|أثناء الهجرة",                    "Hijra Narrative"),
    (r"حج النبي|أدى النبي العمرة|مناسك|الطواف",               "Pilgrimage / Hajj Account"),
    (r"صلى النبي|صلاة النبي|هدي النبي في الصلاة",             "Worship / Ibadah Description"),
    (r"خطب النبي|قال رسول الله في خطبة|الخطبة",               "Prophetic Speech / Sermon"),
    (r"تفسير|في قوله تعالى|المراد بالآية|فسّر",               "Quranic Exegesis (Tafsir)"),
    (r"الأنساب|نسب النبي|السلالة|جد النبي",                   "Genealogy / Nasab"),
]

_QURAN_REF_PATTERN = re.compile(
    r"\[([^:\u003a\]]+)[:\u003a]\s*(\d+)\]"
    r"|﴿([^﴾]{1,120})﴾\s*(?:\[([^\]]+)\])?"
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Passage:
    idx: int
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
class HierarchicalChunk:
    chunk_id: str
    parent_chunk_id: Optional[str]          # None for parent chunks
    level: str                               # "parent" | "child"
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
    chunk_type: str                          # "parent" | "child"
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
    child_chunk_ids: List[str] = field(default_factory=list)   # parent only
    sibling_chunk_ids: List[str] = field(default_factory=list) # child only

    def to_dict(self) -> dict:
        return {
            "chunk_id":           self.chunk_id,
            "parent_chunk_id":    self.parent_chunk_id,
            "level":              self.level,
            "source_passage_ids": self.source_passage_ids,
            "book_id":            self.book_id,
            "book_title":         self.book_title,
            "author":             self.author,
            "author_death_year":  self.author_death_year,
            "category":           self.category,
            "collection":         self.collection,
            "section_hierarchy":  self.section_hierarchy,
            "section_leaf":       self.section_leaf,
            "page_range":         list(self.page_range),
            "page_count":         self.page_count,
            "text":               self.text,
            "chunk_type":         self.chunk_type,
            "metadata": {
                "topics":              self.topics,
                "entities": {
                    "persons":  self.persons,
                    "places":   self.places,
                    "events":   self.events,
                    "concepts": self.concepts,
                },
                "quranic_refs":       self.quranic_refs,
                "hadith_collections": self.hadith_collections,
                "temporal_context":   self.temporal_context,
                "temporal_order":     self.temporal_order,
                "narrative_role":     self.narrative_role,
                "relations":          self.relations,
                "child_chunk_ids":    self.child_chunk_ids,
                "sibling_chunk_ids":  self.sibling_chunk_ids,
            },
        }


# ---------------------------------------------------------------------------
# SeerahHierarchicalChunker
# ---------------------------------------------------------------------------

class SeerahHierarchicalChunker:
    """
    Two-level hierarchical chunker for Seerah corpora.

    Parameters
    ----------
    input_path       : path to raw JSONL
    output_path      : path to write hierarchical JSONL
    parent_max_pages : max pages in one parent chunk (default 12)
    child_pages      : pages per child chunk (default 2)
    child_overlap    : overlap pages between consecutive children (default 1)
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        parent_max_pages: int = 12,
        child_pages: int = 2,
        child_overlap: int = 1,
    ) -> None:
        self.input_path      = Path(input_path)
        self.output_path     = Path(output_path)
        self.parent_max_pages = parent_max_pages
        self.child_pages     = child_pages
        self.child_overlap   = child_overlap

        self._passages:  List[Passage]           = []
        self._deduped:   List[Passage]           = []
        self._sections:  Dict[Tuple, List[Passage]] = {}
        self._chunks:    List[HierarchicalChunk] = []
        self._parent_ctr: int = 0
        self._child_ctr:  int = 0

    # ── Public ─────────────────────────────────────────────────────────

    def run(self) -> str:
        self._load_passages()
        self._deduplicate()
        self._group_into_sections()
        self._build_hierarchy()
        self._link_siblings()
        self._infer_cross_chunk_relations()
        self._write_output()
        return self._build_report()

    # ── Stage 1: Load ──────────────────────────────────────────────────

    def _load_passages(self) -> None:
        with self.input_path.open(encoding="utf-8") as fh:
            for idx, raw in enumerate(fh):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except json.JSONDecodeError as exc:
                    print(f"[WARN] Line {idx}: {exc}", file=sys.stderr)
                    continue
                self._passages.append(Passage(
                    idx=idx,
                    content=_strip_html(rec.get("content", "")),
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

    # ── Stage 2: Deduplicate ───────────────────────────────────────────

    def _deduplicate(self) -> None:
        seen: set[str] = set()
        for p in self._passages:
            fp = hashlib.md5(
                (str(p.book_id) + str(p.page_number) + str(p.hierarchy) + p.content)
                .encode("utf-8")
            ).hexdigest()
            if fp not in seen:
                seen.add(fp)
                self._deduped.append(p)

    # ── Stage 3: Group ────────────────────────────────────────────────

    def _group_into_sections(self) -> None:
        raw: Dict[Tuple, List[Passage]] = defaultdict(list)
        for p in self._deduped:
            raw[(p.book_id, tuple(p.hierarchy))].append(p)
        for key, pages in raw.items():
            self._sections[key] = sorted(pages, key=lambda x: x.page_number)

    # ── Stage 4: Build hierarchy ──────────────────────────────────────

    def _build_hierarchy(self) -> None:
        """
        For each section:
          1. Split into parent windows (parent_max_pages each).
          2. For each parent window, split into child windows
             (child_pages with child_overlap-1 step → actual overlap of 1 page).
          3. Link children to their parent via parent_chunk_id.
          4. Store child_chunk_ids on the parent.
        """
        for (book_id, hier_tuple), pages in self._sections.items():
            hier = list(hier_tuple)

            # ── Parent windows ───────────────────────────────────────
            parent_windows = self._make_windows(
                pages, self.parent_max_pages, self.parent_max_pages  # no overlap between parents
            )

            for parent_pages in parent_windows:
                parent_id = f"book_{book_id}_parent_{self._parent_ctr:05d}"
                self._parent_ctr += 1

                parent_chunk = self._make_chunk(
                    pages=parent_pages,
                    chunk_id=parent_id,
                    parent_chunk_id=None,
                    level="parent",
                    chunk_type="parent",
                    book_id=book_id,
                    hier=hier,
                )

                # ── Child windows inside this parent ─────────────────
                child_step = max(1, self.child_pages - self.child_overlap)
                child_windows = self._make_windows(
                    parent_pages, self.child_pages, child_step
                )

                child_ids: List[str] = []
                child_chunks: List[HierarchicalChunk] = []

                for child_pages in child_windows:
                    child_id = f"book_{book_id}_child_{self._child_ctr:05d}"
                    self._child_ctr += 1

                    child_chunk = self._make_chunk(
                        pages=child_pages,
                        chunk_id=child_id,
                        parent_chunk_id=parent_id,
                        level="child",
                        chunk_type="child",
                        book_id=book_id,
                        hier=hier,
                    )
                    child_ids.append(child_id)
                    child_chunks.append(child_chunk)

                # Store child IDs on the parent
                parent_chunk.child_chunk_ids = child_ids

                # Emit parent first, then its children
                self._chunks.append(parent_chunk)
                self._chunks.extend(child_chunks)

    # ── Stage 5: Link siblings ────────────────────────────────────────

    def _link_siblings(self) -> None:
        """
        For each child chunk, record its immediate previous and next
        sibling IDs. This enables the retriever to walk the sequence.
        """
        # Group children by parent
        parent_children: Dict[str, List[int]] = defaultdict(list)
        for i, c in enumerate(self._chunks):
            if c.level == "child" and c.parent_chunk_id:
                parent_children[c.parent_chunk_id].append(i)

        for indices in parent_children.values():
            for pos, i in enumerate(indices):
                siblings: List[str] = []
                if pos > 0:
                    siblings.append(self._chunks[indices[pos - 1]].chunk_id)
                if pos < len(indices) - 1:
                    siblings.append(self._chunks[indices[pos + 1]].chunk_id)
                self._chunks[i].sibling_chunk_ids = siblings

    # ── Stage 6: Cross-chunk relations ───────────────────────────────

    def _infer_cross_chunk_relations(self) -> None:
        """CONTINUES_FROM, SHARES_PERSON, SHARES_EVENT, SHARES_PLACE, FIQH_OF."""

        # Index only child chunks for relations (avoids duplicating with parents)
        children = [(i, c) for i, c in enumerate(self._chunks) if c.level == "child"]

        # CONTINUES_FROM
        section_index: Dict[Tuple, List[int]] = defaultdict(list)
        for i, c in children:
            section_index[tuple(c.section_hierarchy)].append(i)
        for idxs in section_index.values():
            for prev, nxt in zip(idxs, idxs[1:]):
                self._chunks[prev].relations.append(
                    {"type": "CONTINUES_FROM", "target_chunk_id": self._chunks[nxt].chunk_id, "direction": "precedes"})
                self._chunks[nxt].relations.append(
                    {"type": "CONTINUES_FROM", "target_chunk_id": self._chunks[prev].chunk_id, "direction": "follows"})

        # SHARES_EVENT
        ev_idx: Dict[str, List[int]] = defaultdict(list)
        for i, c in children:
            for ev in c.events:
                ev_idx[ev].append(i)
        for ev, idxs in ev_idx.items():
            if len(idxs) < 2:
                continue
            for i in idxs:
                others = [self._chunks[j].chunk_id for j in idxs if j != i][:3]
                if others:
                    self._chunks[i].relations.append({"type": "SHARES_EVENT", "event": ev, "related_chunk_ids": others})

        # SHARES_PERSON
        per_idx: Dict[str, List[int]] = defaultdict(list)
        for i, c in children:
            for p in c.persons:
                per_idx[p].append(i)
        for person, idxs in per_idx.items():
            if len(idxs) < 2:
                continue
            for i in idxs:
                others = [self._chunks[j].chunk_id for j in idxs if j != i][:3]
                if others:
                    self._chunks[i].relations.append({"type": "SHARES_PERSON", "person": person, "related_chunk_ids": others})

        # SHARES_PLACE
        pl_idx: Dict[str, List[int]] = defaultdict(list)
        for i, c in children:
            for pl in c.places:
                pl_idx[pl].append(i)
        for place, idxs in pl_idx.items():
            if len(idxs) < 2:
                continue
            for i in idxs:
                others = [self._chunks[j].chunk_id for j in idxs if j != i][:3]
                if others:
                    self._chunks[i].relations.append({"type": "SHARES_PLACE", "place": place, "related_chunk_ids": others})

        # FIQH_OF
        fiqh = [i for i, c in children if "Fiqh" in c.narrative_role]
        narr = [i for i, c in children if "Narrative" in c.narrative_role or "Battle" in c.narrative_role]
        ev_narr: Dict[str, List[int]] = defaultdict(list)
        for i in narr:
            for ev in self._chunks[i].events:
                ev_narr[ev].append(i)
        for fi in fiqh:
            for ev in self._chunks[fi].events:
                for ni in ev_narr.get(ev, [])[:2]:
                    self._chunks[fi].relations.append(
                        {"type": "FIQH_OF", "target_chunk_id": self._chunks[ni].chunk_id, "note": f"Derives rulings from: {ev}"})

    # ── Stage 7: Write ────────────────────────────────────────────────

    def _write_output(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as fh:
            for c in self._chunks:
                fh.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _make_windows(pages: List[Passage], size: int, step: int) -> List[List[Passage]]:
        """Sliding windows; merges tiny trailing stub into previous window."""
        windows = [pages[i: i + size] for i in range(0, len(pages), step)]
        if len(windows) >= 2 and len(windows[-1]) < size // 2:
            windows[-2] = windows[-2] + [p for p in windows[-1] if p not in windows[-2]]
            windows.pop()
        return windows

    def _make_chunk(
        self,
        pages: List[Passage],
        chunk_id: str,
        parent_chunk_id: Optional[str],
        level: str,
        chunk_type: str,
        book_id: int,
        hier: List[str],
    ) -> HierarchicalChunk:
        rep  = pages[0]
        text = "\n\n".join(p.content for p in pages)
        leaf = hier[-1] if hier else (rep.section_title or "")
        if hier and leaf == rep.book_title and rep.section_title:
            leaf = rep.section_title
        temporal_ctx, temporal_order = self._infer_temporal(text, hier)
        return HierarchicalChunk(
            chunk_id=chunk_id,
            parent_chunk_id=parent_chunk_id,
            level=level,
            source_passage_ids=[p.idx for p in pages],
            book_id=book_id,
            book_title=rep.book_title,
            author=rep.author,
            author_death_year=rep.author_death,
            category=rep.category,
            collection=rep.collection,
            section_hierarchy=hier,
            section_leaf=leaf,
            page_range=(pages[0].page_number, pages[-1].page_number),
            page_count=len(pages),
            text=text,
            chunk_type=chunk_type,
            topics=self._topics(text, hier),
            persons=self._persons(text),
            places=self._places(text),
            events=self._events(text, hier),
            concepts=self._concepts(text),
            quranic_refs=self._quran_refs(text),
            hadith_collections=self._hadith_cols(text),
            temporal_context=temporal_ctx,
            temporal_order=temporal_order,
            narrative_role=self._narrative_role(text, hier),
        )

    # ── Extraction helpers ─────────────────────────────────────────────

    @staticmethod
    def _infer_temporal(text: str, hier: List[str]) -> Tuple[str, int]:
        combined = " ".join(hier) + " " + text[:4000]
        for order, pattern, label in TEMPORAL_EPOCHS:
            if re.search(pattern, combined):
                return label, order
        return _DEFAULT_EPOCH[1], _DEFAULT_EPOCH[0]

    @staticmethod
    def _topics(text: str, hier: List[str]) -> List[str]:
        combined = " ".join(hier) + " " + text[:4000]
        out = [label for kws, label in TOPIC_TABLE if any(k in combined for k in kws)]
        return list(dict.fromkeys(out))[:6]

    @staticmethod
    def _persons(text: str) -> List[str]:
        sample = text[:4000]
        return list(dict.fromkeys(
            c for p, c in PERSON_TABLE if re.search(p, sample)
        ))[:8]

    @staticmethod
    def _places(text: str) -> List[str]:
        sample = text[:4000]
        return list(dict.fromkeys(
            c for p, c in PLACE_TABLE if re.search(p, sample)
        ))[:6]

    @staticmethod
    def _events(text: str, hier: List[str]) -> List[str]:
        combined = " ".join(hier) + " " + text[:4000]
        return list(dict.fromkeys(
            c for p, c in EVENT_TABLE if re.search(p, combined)
        ))[:5]

    @staticmethod
    def _concepts(text: str) -> List[str]:
        sample = text[:4000]
        return list(dict.fromkeys(
            c for p, c in CONCEPT_TABLE if re.search(p, sample)
        ))[:5]

    @staticmethod
    def _quran_refs(text: str) -> List[str]:
        refs = []
        for m in _QURAN_REF_PATTERN.finditer(text):
            if m.group(1) and m.group(2):
                refs.append(f"{m.group(1).strip()} : {m.group(2).strip()}")
            elif m.group(4):
                refs.append(m.group(4).strip())
            elif m.group(3):
                refs.append(f"﴿{m.group(3).strip()[:60]}﴾")
        return list(dict.fromkeys(refs))[:8]

    @staticmethod
    def _hadith_cols(text: str) -> List[str]:
        sample = text[:4000]
        return list(dict.fromkeys(
            c for p, c in HADITH_COLLECTION_TABLE if re.search(p, sample)
        ))[:6]

    @staticmethod
    def _narrative_role(text: str, hier: List[str]) -> str:
        combined = " ".join(hier) + " " + text[:4000]
        for pattern, role in NARRATIVE_ROLE_TABLE:
            if re.search(pattern, combined):
                return role
        return "General Seerah Narrative"

    # ── Report ────────────────────────────────────────────────────────

    def _build_report(self) -> str:
        parents  = [c for c in self._chunks if c.level == "parent"]
        children = [c for c in self._chunks if c.level == "child"]
        avg_children = len(children) / len(parents) if parents else 0

        rel_counts: Counter = Counter()
        for c in children:
            for r in c.relations:
                rel_counts[r["type"]] += 1

        topic_counts: Counter = Counter()
        for c in children:
            topic_counts.update(c.topics)

        temporal_counts = Counter(c.temporal_context for c in children)
        role_counts     = Counter(c.narrative_role   for c in children)
        book_counts     = Counter(c.book_id           for c in parents)

        lines = [
            "=" * 68,
            "  SeerahHierarchicalChunker — Run Report",
            "=" * 68,
            f"  Input  : {self.input_path}",
            f"  Output : {self.output_path}",
            "",
            "  ── Parameters ──────────────────────────────────────────",
            f"  parent_max_pages : {self.parent_max_pages}",
            f"  child_pages      : {self.child_pages}",
            f"  child_overlap    : {self.child_overlap}",
            "",
            "  ── Chunk counts ────────────────────────────────────────",
            f"  Parent chunks    : {len(parents):,}",
            f"  Child chunks     : {len(children):,}",
            f"  Total records    : {len(self._chunks):,}",
            f"  Avg children/parent: {avg_children:.1f}",
            "",
            "  ── Books ───────────────────────────────────────────────",
        ]
        for bid, cnt in book_counts.most_common():
            lines.append(f"    Book {bid:>4}: {cnt:,} parents")
        lines += ["", "  ── Top narrative roles (children) ──────────────────────"]
        for role, cnt in role_counts.most_common(6):
            lines.append(f"    {cnt:>5}x  {role}")
        lines += ["", "  ── Top temporal contexts (children) ────────────────────"]
        for ctx, cnt in temporal_counts.most_common(6):
            lines.append(f"    {cnt:>5}x  {ctx}")
        lines += ["", "  ── Top topics (children) ───────────────────────────────"]
        for t, cnt in topic_counts.most_common(8):
            lines.append(f"    {cnt:>5}x  {t}")
        lines += ["", "  ── Knowledge-graph relations (children) ────────────────"]
        for rt, cnt in rel_counts.most_common():
            lines.append(f"    {cnt:>6}x  {rt}")
        lines += ["", "=" * 68]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Hierarchical semantic chunker for Seerah JSONL corpora."
    )
    parser.add_argument("input",  help="Input JSONL path")
    parser.add_argument("output", help="Output JSONL path")
    parser.add_argument("--parent-max",     type=int, default=12,
                        help="Max pages per parent chunk (default 12)")
    parser.add_argument("--child-pages",    type=int, default=2,
                        help="Pages per child chunk (default 2)")
    parser.add_argument("--child-overlap",  type=int, default=1,
                        help="Overlap pages between children (default 1)")
    args = parser.parse_args()

    chunker = SeerahHierarchicalChunker(
        input_path=args.input,
        output_path=args.output,
        parent_max_pages=args.parent_max,
        child_pages=args.child_pages,
        child_overlap=args.child_overlap,
    )
    print(chunker.run())


if __name__ == "__main__":
    main()
