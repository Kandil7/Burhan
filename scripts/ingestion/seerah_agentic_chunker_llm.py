"""
SeerahAgenticChunkerLLM
=======================
Production-grade agentic hierarchical chunker for Seerah JSONL corpora.
Uses an LLM (OpenAI-compatible API) for deep semantic metadata extraction
on every child chunk, with regex-based fallback for resilience.

Architecture
------------
Stage 1 — Load & clean raw JSONL passages (HTML strip, UTF-8 normalise)
Stage 2 — Deduplicate by content fingerprint (MD5)
Stage 3 — Group passages into section trees by (book_id, hierarchy)
Stage 4 — Build 2-level hierarchy (parent windows + child windows)
Stage 5 — Async LLM metadata enrichment on all child chunks
           • Batched API calls (BATCH_SIZE concurrent requests)
           • Structured JSON output via response_format
           • Per-field regex fallback if LLM field is empty/invalid
           • Full retry with exponential back-off (tenacity)
Stage 6 — Sibling linking (prev/next child pointers)
Stage 7 — Cross-chunk knowledge-graph relations
           (CONTINUES_FROM, SHARES_PERSON, SHARES_PLACE, SHARES_EVENT, FIQH_OF)
Stage 8 — Write enriched JSONL output

Output JSONL schema
-------------------
{
  "chunk_id":           str,         # "book_{id}_parent/child_{n:05d}"
  "parent_chunk_id":    str | null,
  "level":              "parent" | "child",
  "source_passage_ids": List[int],
  "book_id":            int,
  "book_title":         str,
  "author":             str,
  "author_death_year":  int,
  "category":           str,
  "collection":         str,
  "section_hierarchy":  List[str],
  "section_leaf":       str,
  "page_range":         [int, int],
  "page_count":         int,
  "text":               str,
  "chunk_type":         "parent" | "child",
  "enriched_by_llm":    bool,        # True if LLM enrichment succeeded
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
    "summary":            str,       # LLM-generated 1-sentence Arabic summary
    "key_lessons":        List[str], # LLM-generated Fiqh/moral lessons
    "relations":          List[dict],
    "child_chunk_ids":    List[str], # parent only
    "sibling_chunk_ids":  List[str], # child only
  }
}

Usage
-----
    import asyncio
    chunker = SeerahAgenticChunkerLLM(
        input_path="seerah_passages.jsonl",
        output_path="seerah_agentic_chunks.jsonl",
        api_key="sk-...",            # or set OPENAI_API_KEY env var
        model="gpt-4o-mini",         # any OpenAI-compatible model
        base_url=None,               # set for Groq/Ollama/vLLM
        batch_size=20,               # concurrent LLM requests
        parent_max_pages=12,
        child_pages=2,
        child_overlap=1,
    )
    asyncio.run(chunker.run())
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party — install with:
#   pip install openai tenacity tqdm
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm.asyncio import tqdm as atqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("SeerahAgenticChunkerLLM")


# ---------------------------------------------------------------------------
# HTML / text cleaning
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
# Temporal epochs
# ---------------------------------------------------------------------------

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
    (14, r"قبل الهجرة|مكية|مكي|السنة المكية",
         "Meccan Period (610-622 CE)"),
    (15, r"بعد الهجرة|مدنية|مدني|المرحلة المدنية",
         "Medinan Period (622-632 CE)"),
]
_DEFAULT_EPOCH = (99, "Prophetic Era (610-632 CE)")

# ---------------------------------------------------------------------------
# Lookup tables (regex fallback)
# ---------------------------------------------------------------------------

PERSON_TABLE: List[Tuple[str, str]] = [
    (r"النبي|رسول الله|محمد ﷺ|محمد صلى الله|صلى الله عليه وسلم", "Prophet Muhammad ﷺ"),
    (r"أبو بكر الصديق|أبو بكر رضي|الصديق",     "Abu Bakr al-Siddiq"),
    (r"عمر بن الخطاب|عمر رضي الله|الفاروق",     "Umar ibn al-Khattab"),
    (r"عثمان بن عفان|عثمان رضي|ذو النورين",      "Uthman ibn Affan"),
    (r"علي بن أبي طالب|علي رضي الله|أبو الحسن", "Ali ibn Abi Talib"),
    (r"عائشة رضي|أم المؤمنين عائشة",            "Aisha bint Abi Bakr"),
    (r"خديجة بنت|خديجة رضي",                    "Khadija bint Khuwaylid"),
    (r"فاطمة الزهراء|فاطمة رضي",                "Fatima al-Zahra"),
    (r"أبو هريرة",                               "Abu Hurayra"),
    (r"عبد الله بن عباس|ابن عباس",              "Abdullah ibn Abbas"),
    (r"عبد الله بن مسعود|ابن مسعود",            "Abdullah ibn Masud"),
    (r"أنس بن مالك",                             "Anas ibn Malik"),
    (r"أبو سفيان بن حرب|أبو سفيان",             "Abu Sufyan ibn Harb"),
    (r"زيد بن حارثة",                            "Zayd ibn Haritha"),
    (r"جبريل|جبرائيل|الروح الأمين",             "Angel Jibreel (Gabriel)"),
    (r"إبراهيم عليه السلام|إبراهيم الخليل",      "Prophet Ibrahim (Abraham) ﷺ"),
    (r"موسى عليه السلام|كليم الله",              "Prophet Musa (Moses) ﷺ"),
    (r"عيسى عليه السلام|روح الله",               "Prophet Isa (Jesus) ﷺ"),
    (r"ابن القيم الجوزية|ابن القيم",             "Ibn al-Qayyim al-Jawziyya (d. 751 AH)"),
    (r"ابن تيمية|شيخ الإسلام ابن تيمية",         "Ibn Taymiyya (d. 728 AH)"),
    (r"حمزة بن عبد المطلب|سيد الشهداء",          "Hamza ibn Abd al-Muttalib"),
    (r"أبو طالب بن عبد المطلب|أبو طالب",         "Abu Talib ibn Abd al-Muttalib"),
    (r"الحسن بن علي|الحسن رضي",                 "Al-Hasan ibn Ali"),
    (r"الحسين بن علي|الحسين رضي",               "Al-Husayn ibn Ali"),
    (r"معاوية بن أبي سفيان|معاوية رضي",          "Muawiyah ibn Abi Sufyan"),
    (r"بلال بن رباح|بلال الحبشي",               "Bilal ibn Rabah"),
    (r"سعد بن معاذ",                             "Sad ibn Muadh"),
    (r"عبد الله بن أبيّ|ابن سلول",              "Abdullah ibn Ubayy (chief hypocrite)"),
    (r"أبو لهب|عبد العزى",                       "Abu Lahab"),
    (r"أبو جهل|عمرو بن هشام",                   "Abu Jahl"),
    (r"هند بنت عتبة|هند",                        "Hind bint Utba"),
    (r"سلمان الفارسي|سلمان رضي",                 "Salman al-Farisi"),
    (r"عمار بن ياسر",                            "Ammar ibn Yasir"),
    (r"أبو عبيدة بن الجراح|أبو عبيدة",          "Abu Ubayda ibn al-Jarrah"),
    (r"طلحة بن عبيد الله|طلحة رضي",             "Talha ibn Ubaydullah"),
    (r"الزبير بن العوام|الزبير رضي",             "al-Zubayr ibn al-Awwam"),
    (r"بلال بن رباح|بلال الحبشي",               "Bilal ibn Rabah"),
    (r"سعد بن أبي وقاص",                         "Sad ibn Abi Waqqas"),
    (r"عبد الرحمن بن عوف",                       "Abd al-Rahman ibn Awf"),
    (r"أبو ذر الغفاري|أبو ذر",                  "Abu Dharr al-Ghifari"),
]

PLACE_TABLE: List[Tuple[str, str]] = [
    (r"مكة المكرمة|مكة|البلد الحرام|أم القرى|بكة", "Mecca (Umm al-Qura)"),
    (r"المدينة المنورة|المدينة|طيبة|يثرب",          "Medina (Madinat al-Nabi)"),
    (r"الكعبة|البيت الحرام|الحرم المكي|بيت الله",   "Kaaba / Masjid al-Haram"),
    (r"المسجد النبوي|مسجد النبي",                   "Masjid al-Nabawi"),
    (r"القدس|بيت المقدس|المسجد الأقصى",             "Jerusalem / Masjid al-Aqsa"),
    (r"الجنة|الفردوس|جنة المأوى",                   "Paradise (Janna)"),
    (r"النار|جهنم|السعير",                          "Hellfire (Jahannam)"),
    (r"وادي بدر|بدر الكبرى",                        "Badr (battlefield)"),
    (r"جبل أحد|يوم أحد|وادي أحد",                   "Uhud (mountain/battlefield)"),
    (r"الخندق|غزوة الأحزاب",                        "Khandaq / Trench"),
    (r"خيبر|حصون خيبر",                             "Khaybar"),
    (r"الحديبية|صلح الحديبية",                      "Al-Hudaybiyya"),
    (r"وادي حنين|غزوة حنين",                        "Hunayn (valley/battlefield)"),
    (r"تبوك|منطقة تبوك",                            "Tabuk"),
    (r"الطائف",                                     "Ta'if"),
    (r"الحجاز|منطقة الحجاز",                        "Hijaz (region)"),
    (r"بلاد الشام|الشام",                           "Al-Sham (Syria/Levant)"),
    (r"غار حراء|جبل النور|حراء",                    "Cave of Hira' / Jabal al-Nur"),
    (r"غار ثور|جبل ثور",                            "Cave of Thawr"),
    (r"العقبة|منى|مشعر",                            "Aqaba / Mina / Masha'ir"),
]

CONCEPT_TABLE: List[Tuple[str, str]] = [
    (r"توحيد|الإيمان بالله|لا إله إلا الله|العقيدة", "Tawhid (Divine Oneness)"),
    (r"الوحي|إنزال القرآن|تنزيل",                    "Revelation (Wahy)"),
    (r"النبوة|نبي|رسول|المرسلين",                    "Prophethood (Nubuwwa)"),
    (r"الإيمان|أركان الإيمان",                       "Faith (Iman)"),
    (r"الجهاد|في سبيل الله",                         "Jihad"),
    (r"الهجرة|هجرة في سبيل الله",                   "Hijra"),
    (r"الصبر|الصابرين|التوكل",                       "Sabr & Tawakkul"),
    (r"المنافقون|النفاق",                            "Nifaq (Hypocrisy)"),
    (r"الأخوة|مؤاخاة",                              "Brotherhood / Muakhaa"),
    (r"المعجزة|الآيات البينات|كرامة",               "Miracles / Signs"),
    (r"الأخلاق|حسن الخلق|مكارم الأخلاق",           "Prophetic Ethics (Akhlaq)"),
    (r"السنة|الحديث النبوي|الأحاديث",               "Sunnah / Prophetic Hadith"),
]

EVENT_TABLE: List[Tuple[str, str]] = [
    (r"أول وحي|نزل جبريل|اقرأ|بدء الوحي",              "First Revelation in Cave Hira'"),
    (r"الإسراء والمعراج|ليلة المعراج|أسري به",          "Isra' wal-Mi'raj"),
    (r"الهجرة إلى الحبشة|هجرة الحبشة",                 "Hijra to Abyssinia"),
    (r"بيعة العقبة الأولى|بيعة العقبة الثانية",         "Bay'at al-Aqaba"),
    (r"الهجرة إلى المدينة|هجرة النبي|الهجرة النبوية",   "Prophetic Hijra to Medina"),
    (r"المؤاخاة بين المهاجرين والأنصار",               "Brotherhood of Muhajirin and Ansar"),
    (r"بناء المسجد النبوي|أسس المسجد",                  "Construction of the Prophet's Mosque"),
    (r"صحيفة المدينة|وثيقة المدينة|ميثاق المدينة",      "Charter of Medina"),
    (r"غزوة بدر الكبرى|يوم بدر",                       "Battle of Badr"),
    (r"غزوة أحد|يوم أحد|كسر رباعيته",                  "Battle of Uhud"),
    (r"غزوة الخندق|غزوة الأحزاب",                      "Battle of Khandaq (Confederates)"),
    (r"بني قريظة|غزوة بني قريظة",                      "Banu Qurayza Expedition"),
    (r"الحديبية|صلح الحديبية",                         "Treaty of Hudaybiyya"),
    (r"فتح خيبر|يوم خيبر",                             "Conquest of Khaybar"),
    (r"فتح مكة|يوم الفتح الأعظم",                       "Conquest of Mecca"),
    (r"غزوة حنين|وادي حنين",                           "Battle of Hunayn"),
    (r"غزوة تبوك|جيش العسرة",                          "Expedition of Tabuk"),
    (r"حجة الوداع|خطبة الوداع|حج النبي",               "Farewell Pilgrimage"),
    (r"وفاة النبي|انتقال النبي|المرض الأخير",           "Death of Prophet Muhammad ﷺ"),
]

TOPIC_TABLE: List[Tuple[List[str], str]] = [
    (["هجرة", "هجرته", "الهجرة النبوية"],               "Hijra"),
    (["غزوة", "غزوات", "سرية", "معركة", "قتال", "جيش"], "Military Expedition/Battle"),
    (["صلاة", "صلاته", "الصلاة", "يصلي", "الركوع"],     "Salat (Prayer)"),
    (["صوم", "رمضان", "الصيام", "يصوم"],                "Sawm (Fasting)"),
    (["حج", "حجة", "عمرة", "الكعبة", "الطواف", "الإحرام"], "Hajj/Umra (Pilgrimage)"),
    (["زكاة", "الصدقة", "الإنفاق"],                     "Zakat/Charity"),
    (["وفد", "وفود", "سفارة", "بعث"],                   "Delegation / Diplomatic"),
    (["فقه", "حكم", "أحكام", "الفوائد", "العبر", "الدروس", "استنبط"], "Fiqh / Legal Lessons"),
    (["شمائل", "خلق", "هدي", "طريقته", "كان يفعل"],     "Prophetic Character (Shama'il)"),
    (["معجزة", "معجزات", "كرامة"],                      "Miracles / Prophetic Signs"),
    (["نكاح", "زواج", "طلاق", "أزواجه", "الزوجات"],     "Marriage / Family"),
    (["دعاء", "ذكر", "تسبيح", "استغفار", "الورد"],      "Du'a / Dhikr"),
    (["قرآن", "وحي", "نزول", "تنزيل", "آية", "سورة"],   "Revelation / Quran"),
    (["صحابة", "صحابي", "أصحاب", "الصحب"],              "Companions (Sahaba)"),
    (["طب", "دواء", "علاج", "الحجامة"],                 "Prophetic Medicine"),
    (["أنصار", "الأنصار"],                               "Ansar"),
    (["مهاجرون", "مهاجر", "المهاجرين"],                 "Muhajirin"),
    (["يهود", "اليهود", "بني إسرائيل"],                 "Jewish tribes / Banu Isra'il"),
    (["منافق", "النفاق", "المنافقون"],                   "Hypocrisy / Munafiqeen"),
    (["حديث", "رواية", "إسناد", "سند", "رجال"],          "Hadith Transmission"),
    (["تفسير", "تأويل"],                                 "Quranic Exegesis (Tafsir)"),
    (["إسراء", "معراج", "ليلة المعراج"],                 "Isra'/Mi'raj"),
]

HADITH_COLLECTION_TABLE: List[Tuple[str, str]] = [
    (r"البخاري|صحيح البخاري",             "Sahih al-Bukhari"),
    (r"مسلم|صحيح مسلم",                   "Sahih Muslim"),
    (r"أبو داود|سنن أبي داود",             "Sunan Abi Dawud"),
    (r"الترمذي|سنن الترمذي|جامع الترمذي",  "Jami' al-Tirmidhi"),
    (r"النسائي|سنن النسائي",               "Sunan al-Nasa'i"),
    (r"ابن ماجه|سنن ابن ماجه",             "Sunan Ibn Majah"),
    (r"أحمد|مسند أحمد",                    "Musnad Ahmad"),
    (r"الطبراني|المعجم الكبير|الأوسط",    "al-Tabarani (al-Mu'jam)"),
    (r"ابن حبان|صحيح ابن حبان",            "Sahih Ibn Hibban"),
    (r"الحاكم|مستدرك الحاكم",              "Mustadrak al-Hakim"),
    (r"البيهقي|سنن البيهقي|شعب الإيمان",   "Sunan al-Bayhaqi"),
    (r"الدارقطني|سنن الدارقطني",           "Sunan al-Daraqutni"),
    (r"ابن خزيمة|صحيح ابن خزيمة",          "Sahih Ibn Khuzayma"),
    (r"ابن أبي شيبة|مصنف ابن أبي شيبة",    "Musannaf Ibn Abi Shayba"),
]

NARRATIVE_ROLE_TABLE: List[Tuple[str, str]] = [
    (r"فقه|أحكام|الفوائد|العبر|الدروس|استنبط|استدل",          "Fiqh / Legal Derivation & Lessons"),
    (r"شمائل|خُلُق|خلقه|هدي|طريقته|كان يفعل|كان يقول|عادته",  "Prophetic Shama'il / Character"),
    (r"غزوة|سرية|معركة|قتال|الجيش|الكتيبة",                   "Military Expedition Narrative"),
    (r"وفد|بعث رسالة|كاتب|سفير|الوفود",                       "Diplomatic / Delegation Account"),
    (r"تحقيق|مقدمة|منهج|المحقق|الناشر|طبعة",                  "Scholarly / Editorial Introduction"),
    (r"حدثنا|أخبرنا|أخرجه|روي|رواه|أسند|الإسناد",             "Hadith Narration / Isnad Chain"),
    (r"هجرة النبي|لما هاجر|أثناء الهجرة",                     "Hijra Narrative"),
    (r"حج النبي|أدى النبي العمرة|مناسك|الطواف",                "Pilgrimage / Hajj Account"),
    (r"صلى النبي|صلاة النبي|هدي النبي في الصلاة",              "Worship / Ibadah Description"),
    (r"خطب النبي|قال رسول الله في خطبة|الخطبة",                "Prophetic Speech / Sermon"),
    (r"تفسير|في قوله تعالى|المراد بالآية|فسّر",                "Quranic Exegesis (Tafsir)"),
    (r"الأنساب|نسب النبي|السلالة|جد النبي",                    "Genealogy / Nasab"),
]

_QURAN_REF_PATTERN = re.compile(
    r"\[([^:\u003a\]]+)[:\u003a]\s*(\d+)\]"
    r"|﴿([^﴾]{1,120})﴾\s*(?:\[([^\]]+)\])?"
)


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

LLM_METADATA_PROMPT = """أنت نظام استخراج بيانات متخصص في السيرة النبوية والتراث الإسلامي.
مهمتك: تحليل النص التالي من كتب السيرة وإرجاع JSON منظَّم بدون أي نص إضافي.

النص:
"""
{text}
"""

معلومات إضافية:
- الكتاب: {book_title}
- المؤلف: {author}
- الفصل/الباب: {section_leaf}

أرجع JSON بهذا الشكل بالضبط (لا تضف حقولاً أخرى):
{{
  "temporal_context": "<وصف الفترة الزمنية بالعربي مع السنة الهجرية والميلادية، مثال: غزوة بدر (624م / 2هـ)>",
  "temporal_order": <رقم صحيح من 0 إلى 15 يمثل الترتيب الزمني في السيرة — 0=ما قبل الإسلام، 15=الفترة المدنية>,
  "narrative_role": "<دور النص: سرد غزوة / فقه واستنباط / شمائل وأخلاق / حديث وإسناد / دبلوماسية / تفسير قرآني / نسب / تحقيق علمي / غير ذلك>",
  "summary": "<ملخص جملة واحدة بالعربي لأهم ما في النص>",
  "topics": ["<موضوع1>", "<موضوع2>"],
  "entities": {{
    "persons": ["<الاسم الكامل للشخص>", ...],
    "places": ["<المكان>", ...],
    "events": ["<الحدث التاريخي>", ...],
    "concepts": ["<المفهوم الديني>", ...]
  }},
  "quranic_refs": ["<سورة:آية>", ...],
  "hadith_collections": ["<اسم الكتاب>", ...],
  "key_lessons": ["<درس أو فائدة مستنبطة>", ...]
}}

قواعد مهمة:
- temporal_order: 0=جاهلية، 1=بدء الوحي، 2=معراج، 3=هجرة، 4=بدر، 5=أحد، 6=خندق، 7=حديبية، 8=خيبر، 9=فتح مكة، 10=حنين، 11=تبوك، 12=حجة الوداع، 13=وفاة النبي، 14=الفترة المكية عامة، 15=الفترة المدنية عامة، 99=غير محدد
- topics: 2-5 موضوعات فقط
- entities: الأسماء كما وردت في النص
- key_lessons: 0-3 دروس فقط، فاضيها [] لو مش فيه فوائد صريحة
- quranic_refs: بصيغة "اسم السورة:رقم الآية" مثل "البقرة:142"
- لو المعلومة مش موجودة في النص أرجع قائمة فاضية []
"""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Passage:
    idx:          int
    content:      str
    content_type: str
    book_id:      int
    book_title:   str
    category:     str
    author:       str
    author_death: int
    collection:   str
    page_number:  int
    section_title: str
    hierarchy:    List[str]


@dataclass
class HierarchicalChunk:
    chunk_id:            str
    parent_chunk_id:     Optional[str]
    level:               str
    source_passage_ids:  List[int]
    book_id:             int
    book_title:          str
    author:              str
    author_death_year:   int
    category:            str
    collection:          str
    section_hierarchy:   List[str]
    section_leaf:        str
    page_range:          Tuple[int, int]
    page_count:          int
    text:                str
    chunk_type:          str
    enriched_by_llm:     bool = False
    topics:              List[str] = field(default_factory=list)
    persons:             List[str] = field(default_factory=list)
    places:              List[str] = field(default_factory=list)
    events:              List[str] = field(default_factory=list)
    concepts:            List[str] = field(default_factory=list)
    quranic_refs:        List[str] = field(default_factory=list)
    hadith_collections:  List[str] = field(default_factory=list)
    temporal_context:    str = ""
    temporal_order:      int = 99
    narrative_role:      str = "General Seerah Narrative"
    summary:             str = ""
    key_lessons:         List[str] = field(default_factory=list)
    relations:           List[dict] = field(default_factory=list)
    child_chunk_ids:     List[str] = field(default_factory=list)
    sibling_chunk_ids:   List[str] = field(default_factory=list)

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
            "enriched_by_llm":    self.enriched_by_llm,
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
                "summary":            self.summary,
                "key_lessons":        self.key_lessons,
                "relations":          self.relations,
                "child_chunk_ids":    self.child_chunk_ids,
                "sibling_chunk_ids":  self.sibling_chunk_ids,
            },
        }


# ---------------------------------------------------------------------------
# LLM metadata extractor (async + retry)
# ---------------------------------------------------------------------------

class LLMMetadataExtractor:
    """
    Async LLM-based metadata extractor with:
    - Batched concurrent calls (semaphore-controlled)
    - Exponential backoff retry on rate-limit / transient errors
    - Field-level validation with regex fallback
    - Progress tracking via tqdm
    """

    def __init__(
        self,
        api_key:    str,
        model:      str = "gpt-4o-mini",
        base_url:   Optional[str] = None,
        batch_size: int = 20,
    ) -> None:
        self.model      = model
        self.batch_size = batch_size
        self._client    = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self._semaphore = asyncio.Semaphore(batch_size)
        self._stats     = Counter()

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=False,
    )
    async def _call_llm(self, prompt: str) -> dict:
        """Single LLM call with retry."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=900,
            timeout=30,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)

    async def _enrich_one(self, chunk: HierarchicalChunk) -> None:
        """Enrich a single chunk with LLM metadata (in-place)."""
        async with self._semaphore:
            prompt = LLM_METADATA_PROMPT.format(
                text=chunk.text[:3500],
                book_title=chunk.book_title,
                author=chunk.author,
                section_leaf=chunk.section_leaf,
            )
            try:
                data = await self._call_llm(prompt)
                self._apply_llm_fields(chunk, data)
                chunk.enriched_by_llm = True
                self._stats["llm_success"] += 1
            except Exception as exc:
                log.warning("LLM failed for %s — using regex fallback. Error: %s",
                            chunk.chunk_id, exc)
                self._stats["llm_fallback"] += 1
                # regex fallback is already set before this call

    def _apply_llm_fields(self, chunk: HierarchicalChunk, data: dict) -> None:
        """
        Merge LLM output into chunk fields.
        Each field is validated; invalid/empty values keep the regex default.
        """
        def _safe_str(val: Any, default: str) -> str:
            return str(val).strip() if val and str(val).strip() else default

        def _safe_list(val: Any, default: list) -> list:
            if isinstance(val, list) and val:
                return [str(x).strip() for x in val if str(x).strip()]
            return default

        def _safe_int(val: Any, lo: int, hi: int, default: int) -> int:
            try:
                v = int(val)
                return v if lo <= v <= hi else default
            except (TypeError, ValueError):
                return default

        entities = data.get("entities", {})

        chunk.temporal_context   = _safe_str(data.get("temporal_context"), chunk.temporal_context)
        chunk.temporal_order     = _safe_int(data.get("temporal_order"), 0, 99, chunk.temporal_order)
        chunk.narrative_role     = _safe_str(data.get("narrative_role"), chunk.narrative_role)
        chunk.summary            = _safe_str(data.get("summary"), chunk.summary)
        chunk.topics             = _safe_list(data.get("topics"), chunk.topics)[:6]
        chunk.persons            = _safe_list(entities.get("persons"), chunk.persons)[:10]
        chunk.places             = _safe_list(entities.get("places"), chunk.places)[:8]
        chunk.events             = _safe_list(entities.get("events"), chunk.events)[:6]
        chunk.concepts           = _safe_list(entities.get("concepts"), chunk.concepts)[:6]
        chunk.quranic_refs       = _safe_list(data.get("quranic_refs"), chunk.quranic_refs)[:8]
        chunk.hadith_collections = _safe_list(data.get("hadith_collections"), chunk.hadith_collections)[:6]
        chunk.key_lessons        = _safe_list(data.get("key_lessons"), chunk.key_lessons)[:4]

    async def enrich_all(self, chunks: List[HierarchicalChunk]) -> Counter:
        """Enrich all CHILD chunks concurrently with progress bar."""
        children = [c for c in chunks if c.level == "child"]
        log.info("Starting LLM enrichment for %d child chunks (batch=%d)",
                 len(children), self.batch_size)
        tasks = [self._enrich_one(c) for c in children]
        for coro in atqdm.as_completed(tasks, total=len(tasks),
                                       desc="LLM enrichment"):
            await coro
        log.info("LLM enrichment done — success: %d | fallback: %d",
                 self._stats["llm_success"], self._stats["llm_fallback"])
        return self._stats


# ---------------------------------------------------------------------------
# Regex-based fallback extractors (standalone functions)
# ---------------------------------------------------------------------------

def _regex_temporal(text: str, hier: List[str]) -> Tuple[str, int]:
    combined = " ".join(hier) + " " + text[:4000]
    for order, pattern, label in TEMPORAL_EPOCHS:
        if re.search(pattern, combined):
            return label, order
    return _DEFAULT_EPOCH[1], _DEFAULT_EPOCH[0]

def _regex_persons(text: str) -> List[str]:
    s = text[:4000]
    return list(dict.fromkeys(c for p, c in PERSON_TABLE if re.search(p, s)))[:8]

def _regex_places(text: str) -> List[str]:
    s = text[:4000]
    return list(dict.fromkeys(c for p, c in PLACE_TABLE if re.search(p, s)))[:6]

def _regex_events(text: str, hier: List[str]) -> List[str]:
    combined = " ".join(hier) + " " + text[:4000]
    return list(dict.fromkeys(c for p, c in EVENT_TABLE if re.search(p, combined)))[:5]

def _regex_concepts(text: str) -> List[str]:
    s = text[:4000]
    return list(dict.fromkeys(c for p, c in CONCEPT_TABLE if re.search(p, s)))[:5]

def _regex_topics(text: str, hier: List[str]) -> List[str]:
    combined = " ".join(hier) + " " + text[:4000]
    out = [lbl for kws, lbl in TOPIC_TABLE if any(k in combined for k in kws)]
    return list(dict.fromkeys(out))[:6]

def _regex_hadith_cols(text: str) -> List[str]:
    s = text[:4000]
    return list(dict.fromkeys(c for p, c in HADITH_COLLECTION_TABLE if re.search(p, s)))[:6]

def _regex_quran_refs(text: str) -> List[str]:
    refs = []
    for m in _QURAN_REF_PATTERN.finditer(text):
        if m.group(1) and m.group(2):
            refs.append(f"{m.group(1).strip()} : {m.group(2).strip()}")
        elif m.group(4):
            refs.append(m.group(4).strip())
        elif m.group(3):
            refs.append(f"﴿{m.group(3).strip()[:60]}﴾")
    return list(dict.fromkeys(refs))[:8]

def _regex_narrative_role(text: str, hier: List[str]) -> str:
    combined = " ".join(hier) + " " + text[:4000]
    for pattern, role in NARRATIVE_ROLE_TABLE:
        if re.search(pattern, combined):
            return role
    return "General Seerah Narrative"


# ---------------------------------------------------------------------------
# Main chunker class
# ---------------------------------------------------------------------------

class SeerahAgenticChunkerLLM:
    """
    Full agentic hierarchical chunker with async LLM enrichment.

    Parameters
    ----------
    input_path       : Raw JSONL passages
    output_path      : Enriched hierarchical JSONL chunks
    api_key          : OpenAI-compatible API key (or set OPENAI_API_KEY)
    model            : LLM model name (default: gpt-4o-mini)
    base_url         : Custom API endpoint (Groq / Ollama / vLLM / etc.)
    batch_size       : Concurrent LLM requests (default: 20)
    parent_max_pages : Pages per parent window (default: 12)
    child_pages      : Pages per child chunk (default: 2)
    child_overlap    : Overlap pages between children (default: 1)
    llm_only_children: If True, run LLM only on children (faster, cheaper)
    skip_llm         : If True, use only regex (offline/debug mode)
    resume_path      : Path to existing partial output to resume from
    """

    def __init__(
        self,
        input_path:         str | Path,
        output_path:        str | Path,
        api_key:            Optional[str] = None,
        model:              str = "gpt-4o-mini",
        base_url:           Optional[str] = None,
        batch_size:         int = 20,
        parent_max_pages:   int = 12,
        child_pages:        int = 2,
        child_overlap:      int = 1,
        llm_only_children:  bool = True,
        skip_llm:           bool = False,
        resume_path:        Optional[str | Path] = None,
    ) -> None:
        self.input_path        = Path(input_path)
        self.output_path       = Path(output_path)
        self.model             = model
        self.batch_size        = batch_size
        self.parent_max_pages  = parent_max_pages
        self.child_pages       = child_pages
        self.child_overlap     = child_overlap
        self.llm_only_children = llm_only_children
        self.skip_llm          = skip_llm

        _api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not _api_key and not skip_llm:
            raise ValueError(
                "API key required. Pass api_key='...' or set OPENAI_API_KEY env var. "
                "Use skip_llm=True for offline/regex-only mode."
            )

        self._extractor = LLMMetadataExtractor(
            api_key=_api_key or "dummy",
            model=model,
            base_url=base_url,
            batch_size=batch_size,
        ) if not skip_llm else None

        # Already-processed chunk IDs (for resume support)
        self._done_ids: set[str] = set()
        if resume_path:
            rp = Path(resume_path)
            if rp.exists():
                with rp.open(encoding="utf-8") as f:
                    for line in f:
                        try:
                            self._done_ids.add(json.loads(line)["chunk_id"])
                        except Exception:
                            pass
                log.info("Resume: loaded %d already-processed chunks", len(self._done_ids))

        self._passages:   List[Passage]           = []
        self._deduped:    List[Passage]           = []
        self._sections:   Dict[Tuple, List[Passage]] = {}
        self._chunks:     List[HierarchicalChunk] = []
        self._parent_ctr: int = 0
        self._child_ctr:  int = 0

    # ── Public ──────────────────────────────────────────────────────────────

    async def run(self) -> str:
        """Full async pipeline. Returns a human-readable report."""
        t0 = time.time()

        log.info("Stage 1/8 — Loading passages")
        self._load_passages()

        log.info("Stage 2/8 — Deduplicating")
        self._deduplicate()

        log.info("Stage 3/8 — Grouping into sections")
        self._group_into_sections()

        log.info("Stage 4/8 — Building hierarchy (parent + child windows)")
        self._build_hierarchy()

        log.info("Stage 5/8 — LLM enrichment")
        llm_stats = Counter()
        if self.skip_llm:
            log.info("skip_llm=True — using regex only")
        else:
            llm_stats = await self._extractor.enrich_all(self._chunks)

        log.info("Stage 6/8 — Linking siblings")
        self._link_siblings()

        log.info("Stage 7/8 — Inferring cross-chunk relations")
        self._infer_cross_chunk_relations()

        log.info("Stage 8/8 — Writing output")
        self._write_output()

        elapsed = time.time() - t0
        return self._build_report(llm_stats, elapsed)

    # ── Stage 1: Load ───────────────────────────────────────────────────────

    def _load_passages(self) -> None:
        with self.input_path.open(encoding="utf-8") as fh:
            for idx, raw in enumerate(fh):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except json.JSONDecodeError as exc:
                    log.warning("Line %d: JSON parse error — %s", idx, exc)
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
        log.info("Loaded %d passages", len(self._passages))

    # ── Stage 2: Deduplicate ────────────────────────────────────────────────

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
        removed = len(self._passages) - len(self._deduped)
        log.info("Deduplication: %d removed, %d kept", removed, len(self._deduped))

    # ── Stage 3: Group ──────────────────────────────────────────────────────

    def _group_into_sections(self) -> None:
        raw: Dict[Tuple, List[Passage]] = defaultdict(list)
        for p in self._deduped:
            raw[(p.book_id, tuple(p.hierarchy))].append(p)
        for key, pages in raw.items():
            self._sections[key] = sorted(pages, key=lambda x: x.page_number)
        log.info("Grouped into %d sections", len(self._sections))

    # ── Stage 4: Build hierarchy ────────────────────────────────────────────

    def _build_hierarchy(self) -> None:
        for (book_id, hier_tuple), pages in self._sections.items():
            hier = list(hier_tuple)
            parent_windows = self._make_windows(
                pages, self.parent_max_pages, self.parent_max_pages
            )
            for parent_pages in parent_windows:
                parent_id = f"book_{book_id}_parent_{self._parent_ctr:05d}"
                self._parent_ctr += 1

                parent_chunk = self._make_chunk(
                    pages=parent_pages, chunk_id=parent_id,
                    parent_chunk_id=None, level="parent",
                    chunk_type="parent", book_id=book_id, hier=hier,
                )

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
                        pages=child_pages, chunk_id=child_id,
                        parent_chunk_id=parent_id, level="child",
                        chunk_type="child", book_id=book_id, hier=hier,
                    )
                    child_ids.append(child_id)
                    child_chunks.append(child_chunk)

                parent_chunk.child_chunk_ids = child_ids
                self._chunks.append(parent_chunk)
                self._chunks.extend(child_chunks)

        log.info("Built %d parents + %d children = %d total",
                 self._parent_ctr, self._child_ctr,
                 len(self._chunks))

    # ── Stage 6: Sibling linking ────────────────────────────────────────────

    def _link_siblings(self) -> None:
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

    # ── Stage 7: Cross-chunk relations ──────────────────────────────────────

    def _infer_cross_chunk_relations(self) -> None:
        children = [(i, c) for i, c in enumerate(self._chunks) if c.level == "child"]

        # CONTINUES_FROM
        sec_idx: Dict[Tuple, List[int]] = defaultdict(list)
        for i, c in children:
            sec_idx[tuple(c.section_hierarchy)].append(i)
        for idxs in sec_idx.values():
            for prev, nxt in zip(idxs, idxs[1:]):
                self._chunks[prev].relations.append(
                    {"type": "CONTINUES_FROM",
                     "target_chunk_id": self._chunks[nxt].chunk_id,
                     "direction": "precedes"})
                self._chunks[nxt].relations.append(
                    {"type": "CONTINUES_FROM",
                     "target_chunk_id": self._chunks[prev].chunk_id,
                     "direction": "follows"})

        # SHARES_EVENT / SHARES_PERSON / SHARES_PLACE
        for field_name, rel_type in [
            ("events",  "SHARES_EVENT"),
            ("persons", "SHARES_PERSON"),
            ("places",  "SHARES_PLACE"),
        ]:
            idx_map: Dict[str, List[int]] = defaultdict(list)
            for i, c in children:
                for val in getattr(c, field_name):
                    idx_map[val].append(i)
            for val, idxs in idx_map.items():
                if len(idxs) < 2:
                    continue
                for i in idxs:
                    others = [self._chunks[j].chunk_id for j in idxs if j != i][:3]
                    if others:
                        self._chunks[i].relations.append(
                            {"type": rel_type, field_name[:-1]: val,
                             "related_chunk_ids": others})

        # FIQH_OF
        fiqh = [i for i, c in children if "Fiqh" in c.narrative_role]
        narr = [i for i, c in children
                if "Narrative" in c.narrative_role or "Battle" in c.narrative_role]
        ev_narr: Dict[str, List[int]] = defaultdict(list)
        for i in narr:
            for ev in self._chunks[i].events:
                ev_narr[ev].append(i)
        for fi in fiqh:
            for ev in self._chunks[fi].events:
                for ni in ev_narr.get(ev, [])[:2]:
                    self._chunks[fi].relations.append(
                        {"type": "FIQH_OF",
                         "target_chunk_id": self._chunks[ni].chunk_id,
                         "note": f"Derives rulings from: {ev}"})

    # ── Stage 8: Write ───────────────────────────────────────────────────────

    def _write_output(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with self.output_path.open("w", encoding="utf-8") as fh:
            for c in self._chunks:
                if c.chunk_id in self._done_ids:
                    continue
                fh.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
                written += 1
        log.info("Wrote %d chunks to %s", written, self.output_path)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_windows(pages: List[Passage], size: int, step: int) -> List[List[Passage]]:
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

        # Pre-fill with regex defaults (LLM will override later for children)
        temporal_ctx, temporal_order = _regex_temporal(text, hier)

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
            enriched_by_llm=False,
            topics=_regex_topics(text, hier),
            persons=_regex_persons(text),
            places=_regex_places(text),
            events=_regex_events(text, hier),
            concepts=_regex_concepts(text),
            quranic_refs=_regex_quran_refs(text),
            hadith_collections=_regex_hadith_cols(text),
            temporal_context=temporal_ctx,
            temporal_order=temporal_order,
            narrative_role=_regex_narrative_role(text, hier),
            summary="",
            key_lessons=[],
        )

    # ── Report ───────────────────────────────────────────────────────────────

    def _build_report(self, llm_stats: Counter, elapsed: float) -> str:
        parents  = [c for c in self._chunks if c.level == "parent"]
        children = [c for c in self._chunks if c.level == "child"]
        enriched = sum(1 for c in children if c.enriched_by_llm)

        rel_counts:     Counter = Counter()
        topic_counts:   Counter = Counter()
        temporal_counts: Counter = Counter()
        role_counts:    Counter = Counter()

        for c in children:
            for r in c.relations:
                rel_counts[r["type"]] += 1
            topic_counts.update(c.topics)
            temporal_counts[c.temporal_context] += 1
            role_counts[c.narrative_role] += 1

        book_counts = Counter(c.book_id for c in parents)
        avg_children = len(children) / len(parents) if parents else 0

        def _pct(n, total):
            return f"{100 * n / total:.1f}%" if total else "0%"

        lines = [
            "=" * 70,
            "  SeerahAgenticChunkerLLM — Run Report",
            "=" * 70,
            f"  Input  : {self.input_path}",
            f"  Output : {self.output_path}",
            f"  Model  : {self.model}",
            f"  Elapsed: {elapsed:.1f}s",
            "",
            "  ── Chunking parameters ──────────────────────────────────────",
            f"  parent_max_pages : {self.parent_max_pages}",
            f"  child_pages      : {self.child_pages}",
            f"  child_overlap    : {self.child_overlap}",
            "",
            "  ── Chunk counts ─────────────────────────────────────────────",
            f"  Parent chunks      : {len(parents):,}",
            f"  Child chunks       : {len(children):,}",
            f"  Total records      : {len(self._chunks):,}",
            f"  Avg children/parent: {avg_children:.1f}",
            "",
            "  ── LLM enrichment ───────────────────────────────────────────",
            f"  Enriched by LLM  : {enriched:,} / {len(children):,} ({_pct(enriched, len(children))})",
            f"  LLM success      : {llm_stats.get('llm_success', 0):,}",
            f"  Regex fallback   : {llm_stats.get('llm_fallback', 0):,}",
            "",
            "  ── Books ────────────────────────────────────────────────────",
        ]
        for bid, cnt in book_counts.most_common():
            lines.append(f"    Book {bid:>4}: {cnt:,} parents")

        lines += ["", "  ── Top narrative roles (children) ───────────────────────────"]
        for role, cnt in role_counts.most_common(8):
            lines.append(f"    {cnt:>5}x  {role}")

        lines += ["", "  ── Top temporal contexts (children) ─────────────────────────"]
        for ctx, cnt in temporal_counts.most_common(8):
            lines.append(f"    {cnt:>5}x  {ctx}")

        lines += ["", "  ── Top topics (children) ────────────────────────────────────"]
        for t, cnt in topic_counts.most_common(10):
            lines.append(f"    {cnt:>5}x  {t}")

        lines += ["", "  ── Knowledge-graph relations (children) ─────────────────────"]
        for rt, cnt in rel_counts.most_common():
            lines.append(f"    {cnt:>6}x  {rt}")

        lines += ["", "=" * 70]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Agentic hierarchical chunker for Seerah JSONL corpora (LLM-powered)."
    )
    parser.add_argument("input",  help="Input JSONL path")
    parser.add_argument("output", help="Output JSONL path")
    parser.add_argument("--api-key",      default=None,
                        help="OpenAI-compatible API key (or set OPENAI_API_KEY)")
    parser.add_argument("--model",        default="gpt-4o-mini",
                        help="LLM model name (default: gpt-4o-mini)")
    parser.add_argument("--base-url",     default=None,
                        help="Custom API base URL (Groq / Ollama / vLLM)")
    parser.add_argument("--batch-size",   type=int, default=20,
                        help="Concurrent LLM requests (default: 20)")
    parser.add_argument("--parent-max",   type=int, default=12,
                        help="Max pages per parent chunk (default: 12)")
    parser.add_argument("--child-pages",  type=int, default=2,
                        help="Pages per child chunk (default: 2)")
    parser.add_argument("--child-overlap",type=int, default=1,
                        help="Overlap pages between children (default: 1)")
    parser.add_argument("--skip-llm",     action="store_true",
                        help="Use regex only — no LLM calls (offline mode)")
    parser.add_argument("--resume",       default=None,
                        help="Path to partial output to resume from")
    args = parser.parse_args()

    chunker = SeerahAgenticChunkerLLM(
        input_path=args.input,
        output_path=args.output,
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
        batch_size=args.batch_size,
        parent_max_pages=args.parent_max,
        child_pages=args.child_pages,
        child_overlap=args.child_overlap,
        skip_llm=args.skip_llm,
        resume_path=args.resume,
    )

    report = asyncio.run(chunker.run())
    print(report)


if __name__ == "__main__":
    main()
