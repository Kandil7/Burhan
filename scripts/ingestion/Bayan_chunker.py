#!/usr/bin/env python3
"""
BayanAgenticChunker - SOTA Islamic Corpus Chunker
===================================================
Production-grade agentic hierarchical chunker for Burhan/Bayan.
Integrates EHRAG hypergraph pre-computation, semantic diffusion readiness,
and master_catalog.json enrichment.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from openai import (
    APIConnectionError, APITimeoutError, AsyncOpenAI,
    InternalServerError, RateLimitError,
)
from sentence_transformers import SentenceTransformer
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm.asyncio import tqdm as atqdm
from scipy.sparse import lil_matrix, csr_matrix
from sklearn.cluster import Birch  # ← NEW: for EHRAG semantic hyperedges

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("BayanChunker")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ChunkingStrategy(Enum):
    FIXED = "fixed"
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    DISCOURSE = "discourse"

class EntityType(Enum):
    PERSON = "person"
    PLACE = "place"
    EVENT = "event"
    CONCEPT = "concept"
    FIQH_RULING = "fiqh_ruling"
    HADITH_NARRATOR = "hadith_narrator"
    TAFSIR_METHOD = "tafsir_method"
    MADHHAB = "madhhab"
    BOOK = "book"
    QURAN_SURA = "quran_sura"
    ANGEL = "angel"
    PROPHET = "prophet"
    SAHABA = "sahaba"
    TABI = "tabi"

class RelationType(Enum):
    CONTINUES_INTO = "CONTINUES_INTO"
    CONTINUES_FROM = "CONTINUES_FROM"
    SHARES_PERSON = "SHARES_PERSON"
    SHARES_PLACE = "SHARES_PLACE"
    SHARES_EVENT = "SHARES_EVENT"
    CITES_HADITH = "CITES_HADITH"
    CITES_QURAN = "CITES_QURAN"
    DERIVES_FROM = "DERIVES_FROM"
    SUPPORTS = "SUPPORTS"
    OPPOSES = "OPPOSES"
    FIQH_OF = "FIQH_OF"
    NARRATED_BY = "NARRATED_BY"
    MENTIONS = "MENTIONS"
    SAME_CONCEPT = "SAME_CONCEPT"   # ← NEW: for EHRAG semantic bridging


# ---------------------------------------------------------------------------
# Text Cleaning
# ---------------------------------------------------------------------------
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NL_RE = re.compile(r"\n{3,}")
_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]", re.UNICODE)

def strip_html(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()

def remove_diacritics(text: str) -> str:
    return _DIACRITICS_RE.sub("", text)

# ← NEW: Arabic sentence splitter respecting Islamic text patterns
_SENT_END_RE = re.compile(r"(?<=[.!?؟।])\s+|(?<=\n)")
def split_sentences_arabic(text: str) -> List[str]:
    sents = _SENT_END_RE.split(text)
    return [s.strip() for s in sents if s.strip()]


# ---------------------------------------------------------------------------
# Entity Tables (unchanged from original — kept complete)
# ---------------------------------------------------------------------------
PERSON_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"محمد ﷺ|رسول الله|النبي|صلى الله عليه وسلم|المصطفى|خاتم الأنبياء", "Prophet Muhammad ﷺ", EntityType.PROPHET),  # ← Added aliases
    (r"إبراهيم عليه السلام|إبراهيم الخليل", "Prophet Ibrahim (Abraham)", EntityType.PROPHET),
    (r"موسى عليه السلام|كليم الله", "Prophet Musa (Moses)", EntityType.PROPHET),
    (r"عيسى عليه السلام|المسيح|روح الله", "Prophet Isa (Jesus)", EntityType.PROPHET),
    (r"نوح عليه السلام", "Prophet Nuh (Noah)", EntityType.PROPHET),
    (r"أبو بكر الصديق|الصديق|خليفة رسول الله", "Abu Bakr al-Siddiq", EntityType.SAHABA),  # ← Added alias
    (r"عمر بن الخطاب|الفاروق", "Umar ibn al-Khattab", EntityType.SAHABA),
    (r"عثمان بن عفان|ذو النورين", "Uthman ibn Affan", EntityType.SAHABA),
    (r"علي بن أبي طالب|أبو الحسن|الإمام علي", "Ali ibn Abi Talib", EntityType.SAHABA),
    (r"أبو هريرة", "Abu Hurayra", EntityType.SAHABA),
    (r"عبد الله بن عباس|ابن عباس|حبر الأمة", "Abdullah ibn Abbas", EntityType.SAHABA),  # ← Added alias
    (r"عائشة رضي|أم المؤمنين عائشة", "Aisha bint Abi Bakr", EntityType.SAHABA),
    (r"خديجة بنت خويلد", "Khadija bint Khuwaylid", EntityType.SAHABA),
    (r"فاطمة الزهراء|فاطمة بنت محمد", "Fatima al-Zahra", EntityType.SAHABA),
    (r"حمزة بن عبد المطلب|سيد الشهداء", "Hamza ibn Abd al-Muttalib", EntityType.SAHABA),
    (r"زيد بن حارثة", "Zayd ibn Haritha", EntityType.SAHABA),
    (r"بلال بن رباح", "Bilal ibn Rabah", EntityType.SAHABA),
    (r"سلمان الفارسي", "Salman al-Farisi", EntityType.SAHABA),
    (r"أبو ذر الغفاري", "Abu Dharr al-Ghifari", EntityType.SAHABA),
    (r"عمار بن ياسر", "Ammar ibn Yasir", EntityType.SAHABA),
    (r"أبو عبيدة بن الجراح", "Abu Ubayda ibn al-Jarrah", EntityType.SAHABA),
    (r"طلحة بن عبيد الله", "Talha ibn Ubaydullah", EntityType.SAHABA),
    (r"الزبير بن العوام", "al-Zubayr ibn al-Awwam", EntityType.SAHABA),
    (r"سعد بن أبي وقاص", "Sad ibn Abi Waqqas", EntityType.SAHABA),
    (r"عبد الرحمن بن عوف", "Abd al-Rahman ibn Awf", EntityType.SAHABA),
    (r"أبو حنيفة|النعمان بن ثابت", "Abu Hanifa", EntityType.PERSON),
    (r"مالك بن أنس|الإمام مالك", "Malik ibn Anas", EntityType.PERSON),
    (r"محمد بن إدريس الشافعي|الشافعي|الإمام الشافعي", "Muhammad ibn Idris al-Shafi'i", EntityType.PERSON),
    (r"أحمد بن حنبل|الإمام أحمد|ابن حنبل", "Ahmad ibn Hanbal", EntityType.PERSON),  # ← Added alias
    (r"ابن تيمية|شيخ الإسلام", "Ibn Taymiyya", EntityType.PERSON),
    (r"ابن القيم الجوزية|ابن القيم", "Ibn al-Qayyim", EntityType.PERSON),
    (r"الذهبي|شمس الدين الذهبي", "Al-Dhahabi", EntityType.PERSON),
    (r"ابن كثير|إسماعيل بن كثير", "Ibn Kathir", EntityType.PERSON),
    (r"الطبري|ابن جرير الطبري", "Al-Tabari", EntityType.PERSON),
    (r"القرطبي", "Al-Qurtubi", EntityType.PERSON),
    (r"النووي|محيي الدين النووي", "Al-Nawawi", EntityType.PERSON),
    (r"ابن حجر العسقلاني|ابن حجر", "Ibn Hajar al-Asqalani", EntityType.PERSON),
    (r"جبريل|جبرائيل|الروح الأمين", "Angel Jibreel (Gabriel)", EntityType.ANGEL),
    (r"ميكائيل|ميكال", "Angel Mika'il (Michael)", EntityType.ANGEL),
    (r"إسرافيل", "Angel Israfil", EntityType.ANGEL),
    (r"عزرائيل|ملك الموت", "Angel Azra'il (Angel of Death)", EntityType.ANGEL),
]

PLACE_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"مكة|البلد الحرام|أم القرى", "Mecca", EntityType.PLACE),
    (r"المدينة|طيبة|يثرب", "Medina", EntityType.PLACE),
    (r"الكعبة|البيت الحرام|البيت العتيق", "Kaaba", EntityType.PLACE),
    (r"المسجد النبوي", "Masjid al-Nabawi", EntityType.PLACE),
    (r"المسجد الأقصى|القدس|بيت المقدس", "Masjid al-Aqsa", EntityType.PLACE),
    (r"غار حراء|جبل النور", "Cave of Hira", EntityType.PLACE),
    (r"غار ثور", "Cave of Thawr", EntityType.PLACE),
    (r"بدر|وادي بدر", "Badr", EntityType.PLACE),
    (r"أحد|جبل أحد", "Uhud", EntityType.PLACE),
    (r"الخندق|غزوة الأحزاب", "Trench of Khandaq", EntityType.PLACE),
    (r"خيبر", "Khaybar", EntityType.PLACE),
    (r"الحديبية", "Hudaybiyya", EntityType.PLACE),
    (r"حنين|وادي حنين", "Hunayn", EntityType.PLACE),
    (r"تبوك", "Tabuk", EntityType.PLACE),
    (r"الطائف", "Ta'if", EntityType.PLACE),
    (r"الحجاز", "Hijaz", EntityType.PLACE),
    (r"بلاد الشام|الشام|سوريا", "Al-Sham", EntityType.PLACE),
    (r"مصر|القاهرة", "Egypt", EntityType.PLACE),
    (r"بغداد", "Baghdad", EntityType.PLACE),
    (r"الأندلس", "Andalus", EntityType.PLACE),
    (r"الجنة|الفردوس|دار السلام", "Paradise", EntityType.PLACE),
    (r"جهنم|النار|دار العذاب", "Hellfire", EntityType.PLACE),
]

EVENT_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"أول وحي|بدء الوحي|نزل جبريل", "First Revelation", EntityType.EVENT),
    (r"الإسراء والمعراج|ليلة المعراج", "Isra' wal-Mi'raj", EntityType.EVENT),
    (r"الهجرة إلى المدينة|الهجرة النبوية", "Hijra to Medina", EntityType.EVENT),
    (r"بيعة العقبة الأولى|بيعة العقبة الثانية", "Bay'at al-Aqaba", EntityType.EVENT),
    (r"غزوة بدر|بدر الكبرى", "Battle of Badr", EntityType.EVENT),
    (r"غزوة أحد", "Battle of Uhud", EntityType.EVENT),
    (r"غزوة الخندق|الأحزاب", "Battle of the Trench", EntityType.EVENT),
    (r"صلح الحديبية", "Treaty of Hudaybiyya", EntityType.EVENT),
    (r"فتح خيبر", "Conquest of Khaybar", EntityType.EVENT),
    (r"فتح مكة|يوم الفتح", "Conquest of Mecca", EntityType.EVENT),
    (r"غزوة حنين", "Battle of Hunayn", EntityType.EVENT),
    (r"غزوة تبوك", "Expedition of Tabuk", EntityType.EVENT),
    (r"حجة الوداع", "Farewell Pilgrimage", EntityType.EVENT),
    (r"وفاة النبي", "Death of Prophet Muhammad", EntityType.EVENT),
    (r"جمع القرآن|تجميع المصحف", "Compilation of Quran", EntityType.EVENT),
    (r"فتنة مقتل عثمان", "Fitna of Uthman's assassination", EntityType.EVENT),
    (r"موقعة الجمل", "Battle of the Camel", EntityType.EVENT),
    (r"صفين", "Battle of Siffin", EntityType.EVENT),
    (r"النهروان", "Battle of Nahrawan", EntityType.EVENT),
]

CONCEPT_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"توحيد|الإيمان بالله|لا إله إلا الله", "Tawhid", EntityType.CONCEPT),
    (r"الوحي|إنزال القرآن", "Wahy (Revelation)", EntityType.CONCEPT),
    (r"النبوة|الرسالة", "Prophethood", EntityType.CONCEPT),
    (r"الإيمان|أركان الإيمان", "Iman (Faith)", EntityType.CONCEPT),
    (r"القضاء والقدر", "Qadr (Predestination)", EntityType.CONCEPT),
    (r"اليوم الآخر|الساعة|القيامة", "Last Day", EntityType.CONCEPT),
    (r"الشفاعة", "Intercession", EntityType.CONCEPT),
    (r"المعجزات|الآيات", "Miracles", EntityType.CONCEPT),
    (r"الكرامات", "Karamat (Saints' miracles)", EntityType.CONCEPT),
    (r"الزكاة|الصدقة الواجبة", "Zakat", EntityType.FIQH_RULING),
    (r"الصلاة|الركوع|السجود|الركعة", "Salah", EntityType.FIQH_RULING),
    (r"الصيام|رمضان|الإفطار", "Sawm", EntityType.FIQH_RULING),
    (r"الحج|العمرة|الطواف|السعي", "Hajj", EntityType.FIQH_RULING),
    (r"الطهارة|الوضوء|الغسل|التيمم", "Tahara", EntityType.FIQH_RULING),
    (r"النجاسة", "Najasah", EntityType.FIQH_RULING),
    (r"الربا|الفوائد البنكية", "Riba", EntityType.FIQH_RULING),
    (r"النكاح|الزواج|عقد الزواج", "Marriage", EntityType.FIQH_RULING),
    (r"الطلاق|الخلع", "Divorce", EntityType.FIQH_RULING),
    (r"البيع|التجارة|المعاملات", "Trade", EntityType.FIQH_RULING),
    (r"الإجارة|الكراء", "Leasing", EntityType.FIQH_RULING),
    (r"الوقف|الحبس", "Waqf", EntityType.FIQH_RULING),
    (r"الجهاد|القتال في سبيل الله", "Jihad", EntityType.FIQH_RULING),
    (r"الحدود|القطع|الرجم", "Hudud", EntityType.FIQH_RULING),
    (r"الديات|القصاص", "Diyat", EntityType.FIQH_RULING),
    (r"التفسير|تأويل|معنى الآية", "Tafsir", EntityType.TAFSIR_METHOD),
    (r"أسباب النزول", "Asbab al-Nuzul", EntityType.TAFSIR_METHOD),
    (r"الناسخ والمنسوخ", "Naskh", EntityType.TAFSIR_METHOD),
    (r"المكي والمدني", "Makki/Madani", EntityType.TAFSIR_METHOD),
    (r"القراءات|القراءات السبع", "Qira'at", EntityType.TAFSIR_METHOD),
    (r"السنة|الحديث النبوي", "Sunnah", EntityType.CONCEPT),
    (r"الإجماع", "Ijma'", EntityType.CONCEPT),
    (r"القياس", "Qiyas", EntityType.CONCEPT),
    (r"الاستحسان", "Istihsan", EntityType.CONCEPT),
    (r"المصلحة المرسلة", "Maslaha", EntityType.CONCEPT),
    (r"الذريعة|سد الذرائع", "Sadd al-Dhara'i", EntityType.CONCEPT),
    (r"العرف|العادة", "Urf", EntityType.CONCEPT),
    (r"التقليد", "Taqlid", EntityType.CONCEPT),
    (r"الاجتهاد", "Ijtihad", EntityType.CONCEPT),
    (r"الفتوى", "Fatwa", EntityType.CONCEPT),
    (r"الحلال", "Halal", EntityType.CONCEPT),
    (r"الحرام", "Haram", EntityType.CONCEPT),
    (r"المكروه", "Makruh", EntityType.CONCEPT),
    (r"المباح", "Mubah", EntityType.CONCEPT),
    (r"الفرض|الواجب", "Fard", EntityType.CONCEPT),
    (r"السنة المؤكدة", "Sunnah Mu'akkadah", EntityType.CONCEPT),
    (r"النفل|التطوع", "Nafl", EntityType.CONCEPT),
]

MADHHAB_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"حنفي|أبو حنيفة|المذهب الحنفي", "Hanafi", EntityType.MADHHAB),
    (r"مالكي|الإمام مالك|المذهب المالكي", "Maliki", EntityType.MADHHAB),
    (r"شافعي|الشافعي|المذهب الشافعي", "Shafi'i", EntityType.MADHHAB),
    (r"حنبل|ابن حنبل|المذهب الحنبلي", "Hanbali", EntityType.MADHHAB),
    (r"ظاهري|ابن حزم", "Zahiri", EntityType.MADHHAB),
    (r"جعفري|الإمامية|المذهب الجعفري", "Ja'fari", EntityType.MADHHAB),
    (r"إباضي|الإباضية", "Ibadi", EntityType.MADHHAB),
]

BOOK_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"صحيح البخاري|البخاري", "Sahih al-Bukhari", EntityType.BOOK),
    (r"صحيح مسلم|مسلم", "Sahih Muslim", EntityType.BOOK),
    (r"سنن أبي داود|أبو داود", "Sunan Abi Dawud", EntityType.BOOK),
    (r"جامع الترمذي|الترمذي", "Jami' al-Tirmidhi", EntityType.BOOK),
    (r"سنن النسائي|النسائي", "Sunan al-Nasa'i", EntityType.BOOK),
    (r"سنن ابن ماجه|ابن ماجه", "Sunan Ibn Majah", EntityType.BOOK),
    (r"موطأ مالك|الموطأ", "Muwatta Malik", EntityType.BOOK),
    (r"مسند أحمد", "Musnad Ahmad", EntityType.BOOK),
    (r"الهداية", "Al-Hidayah", EntityType.BOOK),
    (r"المغني", "Al-Mughni", EntityType.BOOK),
    (r"الروض المربع", "Al-Rawd al-Murbi", EntityType.BOOK),
    (r"القدوري|مختصر القدوري", "Mukhtasar al-Quduri", EntityType.BOOK),
    (r"تفسير ابن كثير", "Tafsir Ibn Kathir", EntityType.BOOK),
    (r"تفسير الطبري|جامع البيان", "Tafsir al-Tabari", EntityType.BOOK),
    (r"تفسير القرطبي", "Tafsir al-Qurtubi", EntityType.BOOK),
    (r"تفسير السعدي", "Tafsir al-Sa'di", EntityType.BOOK),
    (r"تفسير الجلالين", "Tafsir al-Jalalayn", EntityType.BOOK),
    (r"سيرة ابن هشام", "Sirat Ibn Hisham", EntityType.BOOK),
    (r"الرحيق المختوم", "Al-Rahiq al-Makhtum", EntityType.BOOK),
    (r"البداية والنهاية", "Al-Bidaya wa al-Nihaya", EntityType.BOOK),
    (r"الشفا بتعريف حقوق المصطفى", "Al-Shifa", EntityType.BOOK),
    (r"سنن الدارقطني", "Sunan al-Daraqutni", EntityType.BOOK),
    (r"المستدرك على الصحيحين", "Al-Mustadrak", EntityType.BOOK),
    (r"صحيح ابن خزيمة", "Sahih Ibn Khuzayma", EntityType.BOOK),
    (r"صحيح ابن حبان", "Sahih Ibn Hibban", EntityType.BOOK),
]

TEMPORAL_EPOCHS: List[Tuple[int, str, str]] = [
    (0, r"قبل البعثة|الجاهلية|عصر الجاهلية", "Pre-Islamic Era (before 610 CE)"),
    (1, r"أول وحي|بدء الوحي|نزل عليه القرآن", "First Revelation (610 CE)"),
    (2, r"الإسراء|المعراج", "Isra' wal-Mi'raj (~621 CE)"),
    (3, r"هجرة إلى المدينة|الهجرة النبوية", "Hijra to Medina (622 CE)"),
    (4, r"غزوة بدر", "Battle of Badr (624 CE)"),
    (5, r"غزوة أحد", "Battle of Uhud (625 CE)"),
    (6, r"الخندق|الأحزاب", "Battle of the Trench (627 CE)"),
    (7, r"الحديبية", "Treaty of Hudaybiyya (628 CE)"),
    (8, r"خيبر", "Conquest of Khaybar (628 CE)"),
    (9, r"فتح مكة", "Conquest of Mecca (630 CE)"),
    (10, r"حنين", "Battle of Hunayn (630 CE)"),
    (11, r"تبوك", "Expedition of Tabuk (631 CE)"),
    (12, r"حجة الوداع", "Farewell Pilgrimage (632 CE)"),
    (13, r"وفاة النبي", "Death of Prophet (632 CE)"),
    (14, r"مكية|قبل الهجرة", "Meccan Period (610-622 CE)"),
    (15, r"مدنية|بعد الهجرة", "Medinan Period (622-632 CE)"),
    (20, r"الخلافة الراشدة|أبو بكر|عمر|عثمان|علي", "Rashidun Caliphate (632-661 CE)"),
    (21, r"الأموي|بني أمية", "Umayyad Caliphate (661-750 CE)"),
    (22, r"العباسي|بني العباس", "Abbasid Caliphate (750-1258 CE)"),
    (30, r"فقه|أحكام|فتوى|استنباط", "Fiqh / Legal Rulings (non-temporal)"),
    (99, r".*", "General / Unspecified"),
]

# ← NEW: Pre-compile ALL regex patterns at module load for 10x speed
_COMPILED_PATTERNS: Dict[str, List[Tuple[re.Pattern, str, EntityType]]] = {
    "person":  [(re.compile(p, re.UNICODE), c, e) for p, c, e in PERSON_TABLE],
    "place":   [(re.compile(p, re.UNICODE), c, e) for p, c, e in PLACE_TABLE],
    "event":   [(re.compile(p, re.UNICODE), c, e) for p, c, e in EVENT_TABLE],
    "concept": [(re.compile(p, re.UNICODE), c, e) for p, c, e in CONCEPT_TABLE],
    "madhhab": [(re.compile(p, re.UNICODE), c, e) for p, c, e in MADHHAB_TABLE],
    "book":    [(re.compile(p, re.UNICODE), c, e) for p, c, e in BOOK_TABLE],
}
_COMPILED_TEMPORAL = [(order, re.compile(p, re.UNICODE), label) for order, p, label in TEMPORAL_EPOCHS]


# ---------------------------------------------------------------------------
# ← NEW: Master Catalog Loader
# ---------------------------------------------------------------------------
class MasterCatalog:
    """Loads master_catalog.json and provides O(1) book lookups."""
    def __init__(self, path: Optional[Path] = None):
        self._books: Dict[int, Dict] = {}
        self._collection_to_domain: Dict[str, str] = {
            "aqeedah_passages": "aqeedah",
            "fiqh_passages": "fiqh",
            "hadith_passages": "hadith",
            "quran_tafsir": "tafsir",
            "seerah_passages": "seerah",
            "islamic_history_passages": "seerah",
            "general_islamic": "general",
            "arabic_language_passages": "general",
            "spirituality_passages": "aqeedah",
        }
        if path and path.exists():
            self._load(path)

    def _load(self, path: Path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for book in data.get("books", []):
            self._books[book["book_id"]] = book
        log.info("MasterCatalog: loaded %d books", len(self._books))

    def get_book(self, book_id: int) -> Dict:
        return self._books.get(book_id, {})

    def get_domain(self, book_id: int) -> str:
        book = self.get_book(book_id)
        collection = book.get("collection", "general_islamic")
        return self._collection_to_domain.get(collection, "general")

    def get_category(self, book_id: int) -> str:
        return self.get_book(book_id).get("category_name", "")

    def get_author_death(self, book_id: int) -> int:
        return int(self.get_book(book_id).get("author_death", 99999))


# ---------------------------------------------------------------------------
# LLM Prompt (enhanced with catalog context)
# ---------------------------------------------------------------------------
LLM_METADATA_PROMPT = """أنت نظام استخراج بيانات متخصص في التراث الإسلامي (سيرة، فقه، حديث، تفسير، عقيدة).
مهمتك: تحليل النص التالي وإرجاع JSON منظَّم بدون أي نص إضافي.

النص:
\"\"\"
{text}
\"\"\"

معلومات إضافية:
- الكتاب: {book_title}
- المؤلف: {author} (توفي: {author_death} هـ)
- تصنيف الكتاب: {category}
- المجموعة: {collection}
- القسم: {section_leaf}
- المجال: {domain}

أرجع JSON بهذا الشكل بالضبط:
{{
  "temporal_context": "<وصف الفترة الزمنية بالعربي مع السنة>",
  "temporal_order": <رقم من 0-99>,
  "narrative_role": "<دور النص>",
  "summary": "<ملخص جملة واحدة>",
  "topics": ["<موضوع1>", "<موضوع2>", "<موضوع3>"],
  "entities": {{
    "persons": ["<اسم>"],
    "places": ["<مكان>"],
    "events": ["<حدث>"],
    "concepts": ["<مفهوم>"],
    "fiqh_rulings": ["<حكم>"],
    "madhhab": ["<مذهب>"],
    "books": ["<كتاب>"]
  }},
  "quranic_refs": ["سورة:آية"],
  "hadith_collections": ["<كتاب>"],
  "isnad_chain": ["راوٍ1", "راوٍ2"],
  "hadith_grade": "<صحيح|حسن|ضعيف|موضوع|null>",
  "key_lessons": ["<درس>"],
  "relations": [
    {{"type": "CITES_HADITH", "target": "البخاري:12"}},
    {{"type": "DERIVES_FROM", "target": "الآية 2:255"}}
  ]
}}

قواعد:
- hadith_grade: أضف درجة الحديث إذا كان النص حديثاً (صحيح/حسن/ضعيف).
- entities: أسماء موحدة كلما أمكن.
- إذا لم تجد المعلومة، أرجع [] أو null.
- relations: أقصى 3 علاقات.
"""


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class ExtractedEntity:
    name: str
    entity_type: EntityType
    canonical_name: str
    confidence: float = 1.0
    source_text: str = ""

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
    parent_chunk_id: Optional[str]
    level: str
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
    chunk_type: str
    enriched_by_llm: bool = False
    domain: str = "general"
    topics: List[str] = field(default_factory=list)
    entities: List[ExtractedEntity] = field(default_factory=list)
    persons: List[str] = field(default_factory=list)
    places: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    fiqh_rulings: List[str] = field(default_factory=list)
    madhahib: List[str] = field(default_factory=list)
    books: List[str] = field(default_factory=list)
    quranic_refs: List[str] = field(default_factory=list)
    hadith_collections: List[str] = field(default_factory=list)
    isnad_chain: List[str] = field(default_factory=list)
    hadith_grade: Optional[str] = None   # ← NEW
    temporal_context: str = ""
    temporal_order: int = 99
    narrative_role: str = "General"
    summary: str = ""
    key_lessons: List[str] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    child_chunk_ids: List[str] = field(default_factory=list)
    sibling_chunk_ids: List[str] = field(default_factory=list)
    # EHRAG fields
    entity_ids: List[int] = field(default_factory=list)
    structural_hyperedge: List[int] = field(default_factory=list)
    entity_embeddings_computed: bool = False  # ← NEW

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "parent_chunk_id": self.parent_chunk_id,
            "level": self.level,
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
            "domain": self.domain,
            "enriched_by_llm": self.enriched_by_llm,
            "metadata": {
                "topics": self.topics,
                "entities": {
                    "persons": self.persons,
                    "places": self.places,
                    "events": self.events,
                    "concepts": self.concepts,
                    "fiqh_rulings": self.fiqh_rulings,
                    "madhahib": self.madhahib,
                    "books": self.books,
                },
                "quranic_refs": self.quranic_refs,
                "hadith_collections": self.hadith_collections,
                "isnad_chain": self.isnad_chain,
                "hadith_grade": self.hadith_grade,  # ← NEW
                "temporal_context": self.temporal_context,
                "temporal_order": self.temporal_order,
                "narrative_role": self.narrative_role,
                "summary": self.summary,
                "key_lessons": self.key_lessons,
                "relations": self.relations,
                "child_chunk_ids": self.child_chunk_ids,
                "sibling_chunk_ids": self.sibling_chunk_ids,
            },
            "ehrag": {
                "entity_ids": self.entity_ids,
                "structural_hyperedge": self.structural_hyperedge,
            }
        }


# ---------------------------------------------------------------------------
# ← IMPROVED: Regex Extractors (using pre-compiled patterns, full text)
# ---------------------------------------------------------------------------
def regex_extract_entities(text: str, hierarchy: List[str]) -> List[ExtractedEntity]:
    """
    FIX: Was cutting text at 8000 chars — now uses full text.
    Uses pre-compiled patterns for 10x speed.
    """
    combined = " ".join(hierarchy) + " " + text  # ← FIX: removed [:8000] limit
    entities = []
    seen: Set[str] = set()

    for table_key in ("person", "place", "event", "concept", "madhhab", "book"):
        for compiled_pat, canonical, etype in _COMPILED_PATTERNS[table_key]:
            if compiled_pat.search(combined):
                if canonical not in seen:
                    entities.append(ExtractedEntity(
                        name=canonical, entity_type=etype,
                        canonical_name=canonical, confidence=0.85
                    ))
                    seen.add(canonical)
    return entities

def regex_extract_quran_refs(text: str) -> List[str]:
    pattern = re.compile(r"\[([^\:\]]+):(\d+)\]|﴿([^﴾]+)﴾")
    refs = []
    for m in pattern.finditer(text):
        if m.group(1) and m.group(2):
            refs.append(f"{m.group(1).strip()}:{m.group(2)}")
        elif m.group(3):
            refs.append(f"﴿{m.group(3).strip()[:80]}﴾")
    return list(dict.fromkeys(refs))[:8]

def regex_extract_hadith_collections(text: str) -> List[str]:
    """FIX: Now uses compiled regex instead of string `in` match."""
    found = []
    seen: Set[str] = set()
    for compiled_pat, canonical, etype in _COMPILED_PATTERNS["book"]:
        if etype == EntityType.BOOK and compiled_pat.search(text):
            book_name = canonical
            if any(kw in book_name for kw in ("Sahih", "Sunan", "Musnad", "Muwatta", "Jami'")):
                if book_name not in seen:
                    found.append(book_name)
                    seen.add(book_name)
    return found[:6]

def regex_extract_isnad(text: str) -> List[str]:
    # ← IMPROVED: broader isnad pattern
    narrators = re.findall(
        r"(?:حدثنا|أخبرنا|حدثني|روى|رواه|قال)\s+([\u0600-\u06FF]{3,20}(?:\s+[\u0600-\u06FF]{3,20}){0,2})",
        text
    )
    return list(dict.fromkeys(narrators))[:5]

def regex_temporal(text: str, hier: List[str]) -> Tuple[str, int]:
    combined = " ".join(hier) + " " + text[:4000]
    for order, compiled_pat, label in _COMPILED_TEMPORAL:
        if compiled_pat.search(combined):
            return label, order
    return "General / Unspecified", 99

def regex_narrative_role(text: str, hier: List[str], domain: str = "general") -> str:
    combined = " ".join(hier) + " " + text[:4000]
    if domain == "fiqh":
        if re.search(r"حكم|فتوى|استنباط|الأحكام", combined):
            return "Fiqh / Legal Derivation"
        return "Fiqh / General"
    elif domain == "hadith":
        if re.search(r"حدثنا|أخبرنا|روى|الإسناد", combined):
            return "Hadith Narration / Isnad"
        return "Hadith / Text"
    elif domain == "tafsir":
        if re.search(r"تفسير|معنى|الآية|أسباب النزول", combined):
            return "Tafsir / Exegesis"
        return "Tafsir / General"
    elif domain == "aqeedah":
        return "Aqeedah / Theology"
    else:
        if re.search(r"غزوة|سرية|معركة", combined):
            return "Military Expedition"
        elif re.search(r"وفد|دبلوماسية|سفير", combined):
            return "Diplomatic / Delegation"
        elif re.search(r"شمائل|خلقه|هدي", combined):
            return "Prophetic Character (Shama'il)"
        return "General Seerah Narrative"


# ---------------------------------------------------------------------------
# LLM Extractor
# ---------------------------------------------------------------------------
_TRANSIENT_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)

from openai import AsyncOpenAI

class LLMMetadataExtractor:
    def __init__(
        self,
        api_key: str = "ollama",
        model: str = "qwen2.5:1.5b",
        base_url: Optional[str] = "http://localhost:11434/v1/",
        batch_size: int = 4,  # خليه صغير عشان 1.5B
    ):
        self.model = model
        self.batch_size = batch_size
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self._semaphore = asyncio.Semaphore(batch_size)
        self._stats = Counter()
    @retry(
        retry=retry_if_exception_type(_TRANSIENT_ERRORS),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _call_llm(self, prompt: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1500,
            timeout=60,
        )
        return json.loads(response.choices[0].message.content)

    async def _enrich_one(self, chunk: HierarchicalChunk, catalog: MasterCatalog) -> None:
        async with self._semaphore:
            book_info = catalog.get_book(chunk.book_id)
            prompt = LLM_METADATA_PROMPT.format(
                text=chunk.text[:10000],
                book_title=chunk.book_title,
                author=chunk.author,
                author_death=chunk.author_death_year,  # ← NEW
                category=book_info.get("category_name", chunk.category),  # ← NEW: from catalog
                collection=chunk.collection,  # ← NEW
                section_leaf=chunk.section_leaf,
                domain=chunk.domain,
            )
            try:
                data = await self._call_llm(prompt)
                self._apply_llm_fields(chunk, data)
                chunk.enriched_by_llm = True
                self._stats["llm_success"] += 1
            except Exception as e:
                log.warning("LLM failed for %s: %s", chunk.chunk_id, e)
                self._stats["llm_fallback"] += 1

    def _apply_llm_fields(self, chunk: HierarchicalChunk, data: dict) -> None:
        def safe_str(v, default): return str(v).strip() if v else default
        def safe_list(v, n): return [str(x).strip() for x in (v or []) if str(x).strip()][:n]

        chunk.temporal_context = safe_str(data.get("temporal_context"), chunk.temporal_context)
        chunk.temporal_order = int(data.get("temporal_order", chunk.temporal_order))
        chunk.narrative_role = safe_str(data.get("narrative_role"), chunk.narrative_role)
        chunk.summary = safe_str(data.get("summary"), chunk.summary)
        chunk.topics = safe_list(data.get("topics"), 6)
        ents = data.get("entities", {})
        chunk.persons = safe_list(ents.get("persons"), 12)
        chunk.places = safe_list(ents.get("places"), 8)
        chunk.events = safe_list(ents.get("events"), 6)
        chunk.concepts = safe_list(ents.get("concepts"), 8)
        chunk.fiqh_rulings = safe_list(ents.get("fiqh_rulings"), 6)
        chunk.madhahib = safe_list(ents.get("madhhab"), 3)
        chunk.books = safe_list(ents.get("books"), 6)
        chunk.quranic_refs = safe_list(data.get("quranic_refs"), 8)
        chunk.hadith_collections = safe_list(data.get("hadith_collections"), 6)
        chunk.isnad_chain = safe_list(data.get("isnad_chain"), 5)
        chunk.hadith_grade = safe_str(data.get("hadith_grade"), None)  # ← NEW
        chunk.key_lessons = safe_list(data.get("key_lessons"), 4)
        for rel in data.get("relations", []):
            if isinstance(rel, dict) and "type" in rel and "target" in rel:
                chunk.relations.append(rel)

    async def enrich_all(self, chunks: List[HierarchicalChunk],
                         catalog: MasterCatalog) -> Counter:
        children = [c for c in chunks if c.level == "child"]
        log.info("LLM enriching %d child chunks", len(children))
        tasks = [self._enrich_one(c, catalog) for c in children]
        for coro in atqdm.as_completed(tasks, total=len(tasks), desc="LLM enrichment"):
            await coro
        log.info("LLM done: success=%d, fallback=%d",
                 self._stats["llm_success"], self._stats["llm_fallback"])
        return self._stats


# ---------------------------------------------------------------------------
# Main Chunker
# ---------------------------------------------------------------------------
class BayanAgenticChunker:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        catalog_path: Optional[Path] = None,  # ← NEW
        domain: str = "auto",  # ← NEW: "auto" infers from catalog
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        batch_size: int = 20,
        parent_max_pages: int = 12,
        child_pages: int = 2,
        child_overlap: int = 1,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE,
        skip_llm: bool = False,
        embedder_model: str = "BAAI/bge-m3",
        resume_path: Optional[Path] = None,
        compute_entity_embeddings: bool = True,  # ← NEW: EHRAG semantic hyperedges
        birch_threshold: float = 0.5,            # ← NEW: EHRAG clustering param
        birch_top_d: int = 100,                  # ← NEW: top-D entities per cluster
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.domain = domain
        self.parent_max_pages = parent_max_pages
        self.child_pages = child_pages
        self.child_overlap = child_overlap
        self.chunking_strategy = chunking_strategy
        self.skip_llm = skip_llm
        self.compute_entity_embeddings = compute_entity_embeddings
        self.birch_threshold = birch_threshold
        self.birch_top_d = birch_top_d

        # ← NEW: Load master catalog
        self._catalog = MasterCatalog(catalog_path)

        # ← FIX: Only load embedder if actually needed
        self._embedder: Optional[SentenceTransformer] = None
        if compute_entity_embeddings:
            log.info("Loading embedder: %s", embedder_model)
            self._embedder = SentenceTransformer(embedder_model)

        self._extractor = (
            LLMMetadataExtractor(api_key or os.getenv("OPENAI_API_KEY", ""), model, base_url, batch_size)
            if not skip_llm else None
        )

        self._done_ids: Set[str] = set()
        if resume_path and resume_path.exists():
            with open(resume_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        self._done_ids.add(json.loads(line)["chunk_id"])
                    except Exception:
                        pass
            log.info("Resume: loaded %d existing chunk IDs", len(self._done_ids))

        self._passages: List[Passage] = []
        self._deduped: List[Passage] = []
        self._sections: Dict[Tuple, List[Passage]] = {}
        self._chunks: List[HierarchicalChunk] = []
        self._parent_ctr = 0
        self._child_ctr = 0

        # ← NEW: EHRAG global state
        self._global_entity_index: Dict[str, int] = {}
        self._semantic_hyperedges: List[List[int]] = []  # cluster_id → [entity_ids]

    async def run(self) -> str:
        t0 = time.time()
        log.info("Stage 1/10: Loading passages")
        self._load_passages()
        log.info("Stage 2/10: Deduplicating")
        self._deduplicate()
        log.info("Stage 3/10: Grouping sections")
        self._group_sections()
        log.info("Stage 4/10: Building hierarchy")
        self._build_hierarchy()
        log.info("Stage 5/10: Extracting baseline entities (regex)")
        self._extract_baseline_entities()
        log.info("Stage 6/10: LLM enrichment")
        if not self.skip_llm and self._extractor:
            await self._extractor.enrich_all(self._chunks, self._catalog)
        log.info("Stage 7/10: Bubbling metadata to parents")
        self._bubble_up_to_parents()
        log.info("Stage 8/10: Linking siblings & cross-chunk relations")
        self._link_siblings()
        self._infer_cross_chunk_relations()
        log.info("Stage 9/10: Pre-computing EHRAG hyperedge structures")
        self._precompute_ehrag_structures()
        log.info("Stage 10/10: Writing output")
        self._write_output()
        return self._report(time.time() - t0)

    def _load_passages(self):
        with open(self.input_path, encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                book_id = int(rec.get("book_id", 0))
                # ← NEW: Enrich from catalog
                cat_book = self._catalog.get_book(book_id)
                self._passages.append(Passage(
                    idx=idx,
                    content=strip_html(rec.get("content", "")),
                    content_type=rec.get("content_type", "page"),
                    book_id=book_id,
                    book_title=rec.get("book_title", "") or cat_book.get("title", ""),
                    category=rec.get("category", "") or cat_book.get("category_name", ""),
                    author=rec.get("author", "") or cat_book.get("author_name", ""),
                    author_death=int(rec.get("author_death", 0)) or self._catalog.get_author_death(book_id),
                    collection=rec.get("collection", "") or cat_book.get("collection", ""),
                    page_number=int(rec.get("page_number", 0)),
                    section_title=rec.get("section_title", ""),
                    hierarchy=rec.get("hierarchy", []),
                ))
        log.info("Loaded %d passages", len(self._passages))

    def _deduplicate(self):
        seen: Set[str] = set()
        for p in self._passages:
            fp = hashlib.md5(
                f"{p.book_id}|{p.page_number}|{'|'.join(p.hierarchy)}|{p.content[:200]}".encode()
            ).hexdigest()
            if fp not in seen:
                seen.add(fp)
                self._deduped.append(p)
        log.info("Kept %d after dedup (removed %d)", len(self._deduped),
                 len(self._passages) - len(self._deduped))

    def _group_sections(self):
        raw: Dict[Tuple, List[Passage]] = defaultdict(list)
        for p in self._deduped:
            raw[(p.book_id, tuple(p.hierarchy))].append(p)
        for key, pages in raw.items():
            self._sections[key] = sorted(pages, key=lambda x: x.page_number)
        log.info("Grouped into %d sections", len(self._sections))

    def _make_windows(self, pages: List[Passage], size: int, step: int) -> List[List[Passage]]:
        """FIX: Corrected window merging logic."""
        if not pages:
            return []
        windows = []
        for start in range(0, len(pages), step):
            win = pages[start:start + size]
            if win:
                windows.append(win)
        # ← FIX: Only merge last window if it's a small orphan AND we have > 1 window
        if len(windows) >= 2:
            last = windows[-1]
            second_last = windows[-2]
            # Merge only if last window is less than 1/3 of target size
            if len(last) < max(1, size // 3):
                extra = [p for p in last if p.idx not in {x.idx for x in second_last}]
                windows[-2] = second_last + extra[:size - len(second_last)]
                windows.pop()
        return windows

    def _infer_domain(self, book_id: int, category: str, collection: str) -> str:
        """← NEW: Auto-infer domain from catalog."""
        if self.domain != "auto":
            return self.domain
        cat_domain = self._catalog.get_domain(book_id)
        if cat_domain != "general":
            return cat_domain
        cat_lower = category.lower()
        if "فقه" in cat_lower or "حنبل" in cat_lower or "حنفي" in cat_lower:
            return "fiqh"
        if "حديث" in cat_lower or "سنة" in cat_lower or "شرح" in cat_lower:
            return "hadith"
        if "تفسير" in cat_lower or "قرآن" in cat_lower:
            return "tafsir"
        if "عقيدة" in cat_lower or "توحيد" in cat_lower:
            return "aqeedah"
        if "سيرة" in cat_lower or "تاريخ" in cat_lower:
            return "seerah"
        return "general"

    def _make_chunk(self, pages: List[Passage], chunk_id: str,
                    parent_id: Optional[str], level: str, chunk_type: str,
                    book_id: int, hier: List[str]) -> HierarchicalChunk:
        text = "\n\n".join(p.content for p in pages if p.content.strip())
        first = pages[0]
        page_nums = [p.page_number for p in pages]
        domain = self._infer_domain(book_id, first.category, first.collection)  # ← NEW
        temporal_ctx, temporal_ord = regex_temporal(text, hier)
        return HierarchicalChunk(
            chunk_id=chunk_id,
            parent_chunk_id=parent_id,
            level=level,
            source_passage_ids=[p.idx for p in pages],
            book_id=book_id,
            book_title=first.book_title,
            author=first.author,
            author_death_year=first.author_death,
            category=first.category,
            collection=first.collection,
            section_hierarchy=hier,
            section_leaf=hier[-1] if hier else "",
            page_range=(min(page_nums), max(page_nums)),
            page_count=len(set(page_nums)),
            text=text,
            chunk_type=chunk_type,
            domain=domain,
            temporal_context=temporal_ctx,
            temporal_order=temporal_ord,
            narrative_role=regex_narrative_role(text, hier, domain),
        )

    def _build_hierarchy(self):
        for (book_id, hier_tuple), pages in self._sections.items():
            hier = list(hier_tuple)
            parent_windows = self._make_windows(pages, self.parent_max_pages, self.parent_max_pages)
            for parent_pages in parent_windows:
                parent_id = f"b{book_id}_p{self._parent_ctr:05d}"
                self._parent_ctr += 1
                parent = self._make_chunk(parent_pages, parent_id, None, "parent", "parent", book_id, hier)
                child_step = max(1, self.child_pages - self.child_overlap)
                child_windows = self._make_windows(parent_pages, self.child_pages, child_step)
                child_ids = []
                for child_pages in child_windows:
                    child_id = f"b{book_id}_c{self._child_ctr:05d}"
                    self._child_ctr += 1
                    child = self._make_chunk(child_pages, child_id, parent_id, "child", "child", book_id, hier)
                    self._chunks.append(child)
                    child_ids.append(child_id)
                parent.child_chunk_ids = child_ids
                self._chunks.append(parent)
        log.info("Built %d parents + %d children", self._parent_ctr, self._child_ctr)

    def _extract_baseline_entities(self):
        for chunk in self._chunks:
            entities = regex_extract_entities(chunk.text, chunk.section_hierarchy)
            chunk.entities = entities
            chunk.persons = [e.canonical_name for e in entities
                             if e.entity_type in (EntityType.PERSON, EntityType.PROPHET,
                                                  EntityType.SAHABA, EntityType.TABI)]
            chunk.places = [e.canonical_name for e in entities if e.entity_type == EntityType.PLACE]
            chunk.events = [e.canonical_name for e in entities if e.entity_type == EntityType.EVENT]
            chunk.concepts = [e.canonical_name for e in entities if e.entity_type == EntityType.CONCEPT]
            chunk.fiqh_rulings = [e.canonical_name for e in entities if e.entity_type == EntityType.FIQH_RULING]
            chunk.madhahib = [e.canonical_name for e in entities if e.entity_type == EntityType.MADHHAB]
            chunk.books = [e.canonical_name for e in entities if e.entity_type == EntityType.BOOK]
            chunk.topics = chunk.concepts[:6]
            chunk.quranic_refs = regex_extract_quran_refs(chunk.text)
            chunk.hadith_collections = regex_extract_hadith_collections(chunk.text)
            chunk.isnad_chain = regex_extract_isnad(chunk.text)

    def _bubble_up_to_parents(self):
        chunk_map = {c.chunk_id: c for c in self._chunks}
        for parent in (c for c in self._chunks if c.level == "parent"):
            for cid in parent.child_chunk_ids:
                child = chunk_map.get(cid)
                if not child:
                    continue
                for attr, limit in [
                    ("persons", 15), ("places", 10), ("events", 8),
                    ("concepts", 10), ("fiqh_rulings", 8), ("madhahib", 4),
                    ("books", 8), ("topics", 8), ("quranic_refs", 10),
                    ("hadith_collections", 8),
                ]:
                    merged = list(dict.fromkeys(getattr(parent, attr) + getattr(child, attr)))[:limit]
                    setattr(parent, attr, merged)

    def _link_siblings(self):
        parent_children: Dict[str, List[HierarchicalChunk]] = defaultdict(list)
        for c in self._chunks:
            if c.level == "child" and c.parent_chunk_id:
                parent_children[c.parent_chunk_id].append(c)
        for children in parent_children.values():
            for i, child in enumerate(children):
                sibs = []
                if i > 0:
                    sibs.append(children[i - 1].chunk_id)
                if i < len(children) - 1:
                    sibs.append(children[i + 1].chunk_id)
                child.sibling_chunk_ids = sibs

    def _infer_cross_chunk_relations(self):
        """
        FIX: Was O(N²) per entity — now uses inverted index O(N·E).
        """
        children = [c for c in self._chunks if c.level == "child"]
        MAX_SHARE = 3

        # CONTINUES_INTO / FROM
        parent_children: Dict[str, List[HierarchicalChunk]] = defaultdict(list)
        for c in children:
            if c.parent_chunk_id:
                parent_children[c.parent_chunk_id].append(c)
        for siblings in parent_children.values():
            for i in range(len(siblings) - 1):
                prev, nxt = siblings[i], siblings[i + 1]
                prev.relations.append({"type": "CONTINUES_INTO", "target_chunk_id": nxt.chunk_id})
                nxt.relations.append({"type": "CONTINUES_FROM", "target_chunk_id": prev.chunk_id})

        # ← FIX: Build inverted index first, then connect — O(N·E) not O(N²)
        for attr, rel_type in [("persons", "SHARES_PERSON"), ("places", "SHARES_PLACE"), ("events", "SHARES_EVENT")]:
            entity_map: Dict[str, List[HierarchicalChunk]] = defaultdict(list)
            for c in children:
                for ent in getattr(c, attr):
                    entity_map[ent].append(c)
            for ent, clist in entity_map.items():
                if len(clist) < 2:
                    continue
                # Sort by temporal_order for locality
                sorted_c = sorted(clist, key=lambda x: x.temporal_order)
                for i, chunk in enumerate(sorted_c):
                    # Only connect to MAX_SHARE nearest temporal neighbors
                    neighbours = sorted_c[max(0, i - MAX_SHARE):i] + sorted_c[i + 1:i + 1 + MAX_SHARE]
                    for nb in neighbours:
                        if len(chunk.relations) < 20:  # ← NEW: cap relations per chunk
                            chunk.relations.append({
                                "type": rel_type,
                                "target_chunk_id": nb.chunk_id,
                                "shared_entity": ent,
                            })

        # FIQH_OF
        fiqh_chunks = [c for c in children if "Fiqh" in c.narrative_role]
        narrative_chunks = [c for c in children if "Fiqh" not in c.narrative_role]
        for fiqh in fiqh_chunks:
            candidates = sorted(narrative_chunks, key=lambda x: abs(x.temporal_order - fiqh.temporal_order))
            for cand in candidates[:2]:
                fiqh.relations.append({"type": "FIQH_OF", "target_chunk_id": cand.chunk_id})

    def _precompute_ehrag_structures(self):
        """
        ← NEW: Full EHRAG implementation:
        1. Build global entity index
        2. Assign structural hyperedges per chunk
        3. Compute entity embeddings (batch)
        4. Run BIRCH clustering → semantic hyperedges
        5. Save semantic hyperedges to output
        """
        # 1. Global entity index
        for chunk in self._chunks:
            for ent in chunk.entities:
                key = f"{ent.entity_type.value}:{ent.canonical_name}"
                if key not in self._global_entity_index:
                    self._global_entity_index[key] = len(self._global_entity_index)

        # 2. Assign entity IDs and structural hyperedges
        for chunk in self._chunks:
            ids = []
            for ent in chunk.entities:
                key = f"{ent.entity_type.value}:{ent.canonical_name}"
                ids.append(self._global_entity_index[key])
            chunk.entity_ids = ids
            chunk.structural_hyperedge = ids

        log.info("EHRAG: %d unique entities in global index", len(self._global_entity_index))

        # 3. Compute batch embeddings if embedder available
        if self._embedder and self.compute_entity_embeddings and self._global_entity_index:
            entity_names = [k.split(":", 1)[1] for k in sorted(
                self._global_entity_index, key=self._global_entity_index.get
            )]
            log.info("EHRAG: computing embeddings for %d entities", len(entity_names))
            embeddings = self._embedder.encode(
                entity_names, batch_size=512, show_progress_bar=True,
                normalize_embeddings=True
            )

            # 4. BIRCH clustering → semantic hyperedges
            log.info("EHRAG: running BIRCH clustering (threshold=%.2f)", self.birch_threshold)
            birch = Birch(threshold=self.birch_threshold, n_clusters=None)
            cluster_labels = birch.fit_predict(embeddings)

            # Group entity indices by cluster
            cluster_map: Dict[int, List[int]] = defaultdict(list)
            for ent_idx, cluster_id in enumerate(cluster_labels):
                cluster_map[int(cluster_id)].append(ent_idx)

            self._semantic_hyperedges = list(cluster_map.values())
            log.info("EHRAG: %d semantic hyperedges (clusters)", len(self._semantic_hyperedges))

            # Save entity embeddings and semantic hyperedges to separate file
            ehrag_output = self.output_path.with_suffix(".ehrag.json")
            ehrag_data = {
                "entity_index": self._global_entity_index,
                "entity_embeddings_shape": list(embeddings.shape),
                "semantic_hyperedges": self._semantic_hyperedges,
                "birch_threshold": self.birch_threshold,
                "birch_top_d": self.birch_top_d,
                "n_entities": len(entity_names),
                "n_clusters": len(self._semantic_hyperedges),
            }
            np.save(str(self.output_path.with_suffix(".embeddings.npy")), embeddings)
            with open(ehrag_output, "w", encoding="utf-8") as f:
                json.dump(ehrag_data, f, ensure_ascii=False, indent=2)
            log.info("EHRAG: saved embeddings → %s", ehrag_output)

    def _write_output(self):
        """← FIX: Buffered write for speed."""
        mode = "a" if self._done_ids else "w"
        written = 0
        BUFFER_SIZE = 1000
        buffer = []
        with open(self.output_path, mode, encoding="utf-8") as f:
            for chunk in self._chunks:
                if chunk.chunk_id in self._done_ids:
                    continue
                buffer.append(json.dumps(chunk.to_dict(), ensure_ascii=False))
                written += 1
                if len(buffer) >= BUFFER_SIZE:
                    f.write("\n".join(buffer) + "\n")
                    buffer.clear()
            if buffer:
                f.write("\n".join(buffer) + "\n")
        log.info("Wrote %d chunks → %s", written, self.output_path)

    def _report(self, elapsed: float) -> str:
        parents = sum(1 for c in self._chunks if c.level == "parent")
        children = sum(1 for c in self._chunks if c.level == "child")
        llm_enriched = sum(1 for c in self._chunks if c.enriched_by_llm)
        return f"""
{'='*60}
  BayanAgenticChunker Report
{'='*60}
  Input passages   : {len(self._passages)}
  After dedup      : {len(self._deduped)}
  Sections         : {len(self._sections)}
  Parent chunks    : {parents}
  Child chunks     : {children}
  LLM enriched     : {llm_enriched}
  Global entities  : {len(self._global_entity_index)}
  Semantic hyperedges: {len(self._semantic_hyperedges)}
  Output file      : {self.output_path}
  Elapsed          : {elapsed:.1f}s
{'='*60}
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BayanAgenticChunker - SOTA Islamic Corpus Chunker")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--catalog", default=None, help="Path to master_catalog.json")  # ← NEW
    parser.add_argument("--domain", default="auto",
                        choices=["auto", "seerah", "fiqh", "hadith", "tafsir", "aqeedah", "general"])
    parser.add_argument("--api-key")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--base-url")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--parent-pages", type=int, default=12)
    parser.add_argument("--child-pages", type=int, default=2)
    parser.add_argument("--child-overlap", type=int, default=1)
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("--no-embeddings", action="store_true",
                        help="Skip EHRAG entity embedding computation")  # ← NEW
    parser.add_argument("--birch-threshold", type=float, default=0.5)  # ← NEW
    parser.add_argument("--resume")
    args = parser.parse_args()

    chunker = BayanAgenticChunker(
        input_path=Path(args.input),
        output_path=Path(args.output),
        catalog_path=Path(args.catalog) if args.catalog else None,  # ← NEW
        domain=args.domain,
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
        batch_size=args.batch_size,
        parent_max_pages=args.parent_pages,
        child_pages=args.child_pages,
        child_overlap=args.child_overlap,
        skip_llm=args.skip_llm,
        compute_entity_embeddings=not args.no_embeddings,  # ← NEW
        birch_threshold=args.birch_threshold,  # ← NEW
        resume_path=Path(args.resume) if args.resume else None,
    )
    print(asyncio.run(chunker.run()))