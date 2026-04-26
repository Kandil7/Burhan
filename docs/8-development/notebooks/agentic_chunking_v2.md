## الكود الكامل — كل الـ Cells

***

### Cell 1 — Dependencies

```python
!pip install -q \
  transformers accelerate bitsandbytes \
  sentence-transformers \
  huggingface_hub datasets \
  scikit-learn scipy tqdm tenacity \
  numpy

print("✅ Dependencies installed")
```

***

### Cell 2 — Config

```python
from huggingface_hub import login, HfApi
from google.colab import userdata
import os

HF_TOKEN = userdata.get("HF_TOKEN")
login(token=HF_TOKEN)

HF_USERNAME        = "Kandil7"
HF_DATASET_REPO    = f"{HF_USERNAME}/Athar-RAG-Hub"
INPUT_JSON         = "/content/seerah_passages.json"
CATALOG_JSON       = "/content/master_catalog.json"
LLM_MODEL_ID       = "Qwen/Qwen3-4B-Instruct-2507"
EMBEDDER_MODEL_ID  = "BAAI/bge-m3"
PARENT_MAX_PAGES   = 12
CHILD_PAGES        = 2
CHILD_OVERLAP      = 1
PUSH_EVERY_N       = 500
SKIP_LLM           = False
COMPUTE_EMBEDDINGS = True

api = HfApi()
try:
    api.create_repo(repo_id=HF_DATASET_REPO, repo_type="dataset", private=True, exist_ok=True)
    print(f"✅ Dataset repo ready: {HF_DATASET_REPO}")
except Exception as e:
    print(f"⚠️ Repo: {e}")
```

***

### Cell 3 — Imports

```python
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
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm.auto import tqdm
from scipy.sparse import lil_matrix, csr_matrix
from sklearn.cluster import Birch
from huggingface_hub import HfApi, hf_hub_download
from datasets import Dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("BayanChunker")
print("✅ Imports done")
```

***

### Cell 4 — Enums + Entity Tables + Text Cleaning

```python
# ── Enums ──────────────────────────────────────────────────
class ChunkingStrategy(Enum):
    FIXED = "fixed"; SENTENCE = "sentence"
    SEMANTIC = "semantic"; DISCOURSE = "discourse"

class EntityType(Enum):
    PERSON = "person"; PLACE = "place"; EVENT = "event"
    CONCEPT = "concept"; FIQH_RULING = "fiqh_ruling"
    HADITH_NARRATOR = "hadith_narrator"; TAFSIR_METHOD = "tafsir_method"
    MADHHAB = "madhhab"; BOOK = "book"; QURAN_SURA = "quran_sura"
    ANGEL = "angel"; PROPHET = "prophet"; SAHABA = "sahaba"; TABI = "tabi"

class RelationType(Enum):
    CONTINUES_INTO = "CONTINUES_INTO"; CONTINUES_FROM = "CONTINUES_FROM"
    SHARES_PERSON = "SHARES_PERSON"; SHARES_PLACE = "SHARES_PLACE"
    SHARES_EVENT = "SHARES_EVENT"; CITES_HADITH = "CITES_HADITH"
    CITES_QURAN = "CITES_QURAN"; DERIVES_FROM = "DERIVES_FROM"
    SUPPORTS = "SUPPORTS"; OPPOSES = "OPPOSES"; FIQH_OF = "FIQH_OF"
    NARRATED_BY = "NARRATED_BY"; MENTIONS = "MENTIONS"
    SAME_CONCEPT = "SAME_CONCEPT"

# ── Text Cleaning ───────────────────────────────────────────
_HTML_TAG_RE  = re.compile(r"<[^>]+>", re.UNICODE)
_MULTI_SPACE  = re.compile(r"[ \t]{2,}")
_MULTI_NL     = re.compile(r"\n{3,}")
_DIACRITICS   = re.compile(r"[\u064B-\u065F\u0670]", re.UNICODE)
_SENT_END_RE  = re.compile(r"(?<=[.!?؟।])\s+|(?<=\n)")

def strip_html(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()

def remove_diacritics(text: str) -> str:
    return _DIACRITICS.sub("", text)

def split_sentences_arabic(text: str) -> List[str]:
    return [s.strip() for s in _SENT_END_RE.split(text) if s.strip()]

# ── Entity Tables ───────────────────────────────────────────
PERSON_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"محمد ﷺ|رسول الله|النبي|صلى الله عليه وسلم|المصطفى|خاتم الأنبياء", "Prophet Muhammad ﷺ", EntityType.PROPHET),
    (r"إبراهيم عليه السلام|إبراهيم الخليل", "Prophet Ibrahim", EntityType.PROPHET),
    (r"موسى عليه السلام|كليم الله", "Prophet Musa", EntityType.PROPHET),
    (r"عيسى عليه السلام|المسيح|روح الله", "Prophet Isa", EntityType.PROPHET),
    (r"نوح عليه السلام", "Prophet Nuh", EntityType.PROPHET),
    (r"أبو بكر الصديق|الصديق|خليفة رسول الله", "Abu Bakr al-Siddiq", EntityType.SAHABA),
    (r"عمر بن الخطاب|الفاروق", "Umar ibn al-Khattab", EntityType.SAHABA),
    (r"عثمان بن عفان|ذو النورين", "Uthman ibn Affan", EntityType.SAHABA),
    (r"علي بن أبي طالب|أبو الحسن|الإمام علي", "Ali ibn Abi Talib", EntityType.SAHABA),
    (r"أبو هريرة", "Abu Hurayra", EntityType.SAHABA),
    (r"عبد الله بن عباس|ابن عباس|حبر الأمة", "Abdullah ibn Abbas", EntityType.SAHABA),
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
    (r"محمد بن إدريس الشافعي|الشافعي|الإمام الشافعي", "Al-Shafi'i", EntityType.PERSON),
    (r"أحمد بن حنبل|الإمام أحمد|ابن حنبل", "Ahmad ibn Hanbal", EntityType.PERSON),
    (r"ابن تيمية|شيخ الإسلام", "Ibn Taymiyya", EntityType.PERSON),
    (r"ابن القيم الجوزية|ابن القيم", "Ibn al-Qayyim", EntityType.PERSON),
    (r"الذهبي|شمس الدين الذهبي", "Al-Dhahabi", EntityType.PERSON),
    (r"ابن كثير|إسماعيل بن كثير", "Ibn Kathir", EntityType.PERSON),
    (r"الطبري|ابن جرير الطبري", "Al-Tabari", EntityType.PERSON),
    (r"القرطبي", "Al-Qurtubi", EntityType.PERSON),
    (r"النووي|محيي الدين النووي", "Al-Nawawi", EntityType.PERSON),
    (r"ابن حجر العسقلاني|ابن حجر", "Ibn Hajar al-Asqalani", EntityType.PERSON),
    (r"البخاري|محمد بن إسماعيل البخاري", "Al-Bukhari", EntityType.PERSON),
    (r"مسلم بن الحجاج|الإمام مسلم", "Muslim ibn al-Hajjaj", EntityType.PERSON),
]

PLACE_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"مكة المكرمة|مكة|البلد الحرام|أم القرى", "Mecca", EntityType.PLACE),
    (r"المدينة المنورة|المدينة|يثرب|طيبة", "Medina", EntityType.PLACE),
    (r"القدس|بيت المقدس|المسجد الأقصى", "Jerusalem", EntityType.PLACE),
    (r"الكعبة المشرفة|البيت الحرام|الكعبة", "Kaaba", EntityType.PLACE),
    (r"المسجد النبوي|المسجد الشريف", "Prophet's Mosque", EntityType.PLACE),
    (r"المسجد الحرام", "Masjid al-Haram", EntityType.PLACE),
    (r"غار حراء|جبل النور", "Cave of Hira", EntityType.PLACE),
    (r"غار ثور", "Cave of Thawr", EntityType.PLACE),
    (r"بدر|غزوة بدر", "Badr", EntityType.PLACE),
    (r"أُحُد|جبل أحد|غزوة أحد", "Uhud", EntityType.PLACE),
    (r"الخندق|غزوة الخندق|غزوة الأحزاب", "al-Khandaq", EntityType.PLACE),
    (r"خيبر|غزوة خيبر", "Khaybar", EntityType.PLACE),
    (r"الطائف", "al-Taif", EntityType.PLACE),
    (r"الشام|بلاد الشام|سوريا", "al-Sham", EntityType.PLACE),
    (r"مصر|أرض مصر", "Egypt", EntityType.PLACE),
    (r"الحبشة|أرض الحبشة", "Abyssinia", EntityType.PLACE),
    (r"العراق|أرض العراق", "Iraq", EntityType.PLACE),
    (r"اليمن|أرض اليمن", "Yemen", EntityType.PLACE),
    (r"فارس|الفرس", "Persia", EntityType.PLACE),
    (r"الجنة|الفردوس|دار النعيم", "Paradise", EntityType.PLACE),
    (r"النار|جهنم|العذاب", "Hellfire", EntityType.PLACE),
]

EVENT_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"الهجرة النبوية|هجرة الرسول|هجرة المسلمين إلى المدينة", "Hijra to Medina", EntityType.EVENT),
    (r"غزوة بدر|يوم بدر|معركة بدر", "Battle of Badr", EntityType.EVENT),
    (r"غزوة أحد|يوم أحد|معركة أحد", "Battle of Uhud", EntityType.EVENT),
    (r"غزوة الخندق|غزوة الأحزاب|يوم الخندق", "Battle of al-Khandaq", EntityType.EVENT),
    (r"فتح مكة|يوم الفتح", "Conquest of Mecca", EntityType.EVENT),
    (r"غزوة تبوك|جيش العسرة", "Battle of Tabuk", EntityType.EVENT),
    (r"حجة الوداع|الحج الأخير", "Farewell Pilgrimage", EntityType.EVENT),
    (r"الإسراء والمعراج|ليلة المعراج", "Isra wal-Miraj", EntityType.EVENT),
    (r"بدء الوحي|نزول الوحي الأول|أول نزول القرآن", "First Revelation", EntityType.EVENT),
    (r"بيعة العقبة الأولى|بيعة العقبة الثانية", "Bay'a of Aqaba", EntityType.EVENT),
    (r"صلح الحديبية|عمرة الحديبية", "Treaty of Hudaybiyya", EntityType.EVENT),
    (r"وفاة النبي|وفاة رسول الله", "Death of the Prophet ﷺ", EntityType.EVENT),
    (r"الهجرة إلى الحبشة|هجرة الحبشة", "Hijra to Abyssinia", EntityType.EVENT),
]

CONCEPT_TABLE: List[Tuple[str, str, EntityType]] = [
    (r"التوحيد|لا إله إلا الله|توحيد الله", "Tawhid", EntityType.CONCEPT),
    (r"الإيمان بالله|أركان الإيمان", "Iman (Faith)", EntityType.CONCEPT),
    (r"الصلاة|إقامة الصلاة|الصلوات الخمس", "Salah (Prayer)", EntityType.CONCEPT),
    (r"الزكاة|أداء الزكاة", "Zakat", EntityType.CONCEPT),
    (r"الصوم|صيام رمضان|شهر الصوم", "Sawm (Fasting)", EntityType.CONCEPT),
    (r"الحج|أداء الحج|مناسك الحج", "Hajj", EntityType.CONCEPT),
    (r"الجهاد في سبيل الله|القتال في سبيل الله", "Jihad", EntityType.CONCEPT),
    (r"الإخلاص|إخلاص النية", "Ikhlas (Sincerity)", EntityType.CONCEPT),
    (r"التوكل على الله|التوكل", "Tawakkul", EntityType.CONCEPT),
    (r"الصبر|الصبر على البلاء", "Sabr (Patience)", EntityType.CONCEPT),
    (r"الشكر|شكر النعمة", "Shukr (Gratitude)", EntityType.CONCEPT),
    (r"الحرام|المحرمات", "Haram", EntityType.CONCEPT),
    (r"الحلال|المباحات", "Halal", EntityType.CONCEPT),
    (r"الفرض|الواجب|الفرائض", "Fard", EntityType.CONCEPT),
    (r"السنة النبوية|السنة المطهرة", "Sunnah", EntityType.CONCEPT),
    (r"القيامة|يوم القيامة|الساعة", "Last Day", EntityType.CONCEPT),
    (r"الجنة|نعيم الجنة", "Paradise", EntityType.CONCEPT),
    (r"النار|عذاب النار|عذاب جهنم", "Hellfire", EntityType.CONCEPT),
    (r"الشفاعة|شفاعة النبي", "Intercession", EntityType.CONCEPT),
    (r"الأخلاق|مكارم الأخلاق|حسن الخلق", "Islamic Ethics", EntityType.CONCEPT),
]

HADITH_BOOK_TABLE: List[Tuple[str, str]] = [
    (r"صحيح البخاري|رواه البخاري|أخرجه البخاري", "Sahih al-Bukhari"),
    (r"صحيح مسلم|رواه مسلم|أخرجه مسلم", "Sahih Muslim"),
    (r"سنن أبي داود|رواه أبو داود|أخرجه أبو داود", "Sunan Abi Dawud"),
    (r"جامع الترمذي|رواه الترمذي|أخرجه الترمذي", "Jami' al-Tirmidhi"),
    (r"سنن النسائي|رواه النسائي|أخرجه النسائي", "Sunan al-Nasa'i"),
    (r"سنن ابن ماجة|رواه ابن ماجة|أخرجه ابن ماجة", "Sunan Ibn Majah"),
    (r"مسند أحمد|رواه أحمد|أخرجه أحمد", "Musnad Ahmad"),
    (r"موطأ مالك|رواه مالك", "Muwatta Malik"),
    (r"مستدرك الحاكم|رواه الحاكم", "Mustadrak al-Hakim"),
    (r"سنن الدارمي|رواه الدارمي", "Sunan al-Darimi"),
]

QURAN_REF_RE = re.compile(
    r"﴿([^﴾]{3,200})﴾\s*\[([^]]+)\]|سورة\s+(\w+)",
    re.UNICODE,
)
HADITH_GRADE_RE = re.compile(
    r"(صحيح|حسن|ضعيف|موضوع|منكر|متفق عليه|حسن صحيح)",
    re.UNICODE,
)
ISNAD_RE = re.compile(
    r"عن\s+(\S+\s+\S+)|حدثنا\s+(\S+\s+\S+)|أخبرنا\s+(\S+\s+\S+)|روى\s+(\S+\s+\S+)",
    re.UNICODE,
)

print("✅ Enums + Entity Tables ready")
```

***

### Cell 5 — Dataclasses

```python
@dataclass
class Passage:
    idx:           int
    content:       str
    content_type:  str
    book_id:       int
    book_title:    str
    category:      str
    author:        str
    author_death:  int
    collection:    str
    page_number:   int
    section_title: str
    hierarchy:     List[str]

@dataclass
class Chunk:
    chunk_id:         str
    parent_chunk_id:  Optional[str]
    level:            str
    source_passage_ids: List[int]
    book_id:          int
    book_title:       str
    author:           str
    author_death_year: int
    category:         str
    collection:       str
    section_hierarchy: List[str]
    section_leaf:     str
    page_range:       Tuple[int, int]
    page_count:       int
    text:             str
    chunk_type:       str
    domain:           str
    enriched_by_llm:  bool = False
    summary:          str = ""
    narrative_role:   str = ""
    key_lessons:      List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "topics": [], "entities": {
            "persons": [], "places": [], "events": [],
            "concepts": [], "fiqh_rulings": [], "madhahib": [], "books": []
        },
        "quranic_refs": [], "hadith_collections": [], "isnad_chain": [],
        "hadith_grade": None, "temporal_context": "General / Unspecified",
        "temporal_order": 99, "narrative_role": "", "summary": "",
        "key_lessons": [], "relations": [],
        "child_chunk_ids": [], "sibling_chunk_ids": [],
    })
    ehrag: Dict[str, Any] = field(default_factory=lambda: {
        "entity_ids": [], "structural_hyperedge": []
    })

    def to_dict(self) -> dict:
        d = {
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
            "domain":             self.domain,
            "enriched_by_llm":    self.enriched_by_llm,
            "metadata":           self.metadata,
            "ehrag":              self.ehrag,
        }
        d["metadata"]["summary"]        = self.summary
        d["metadata"]["narrative_role"] = self.narrative_role
        d["metadata"]["key_lessons"]    = self.key_lessons
        return d

print("✅ Dataclasses ready")
```

***

### Cell 6 — HFLocalLLM

```python
class HFLocalLLM:
    def __init__(
        self,
        model_id: str = "Qwen/Qwen3-4B-Instruct-2507",
        use_4bit: bool = True,
        max_new_tokens: int = 150,
        inference_batch_size: int = 8,
    ):
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.inference_batch_size = inference_batch_size
        self._inference_lock = asyncio.Lock()

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, trust_remote_code=True, padding_side="left"
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=use_4bit,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        ) if use_4bit else None

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="auto",
            quantization_config=bnb_config,
            trust_remote_code=True,
        )
        self.model.eval()
        print(f"✅ Model loaded: {model_id}")

    def _build_prompt(self, text: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise JSON extractor for Islamic Arabic texts.\n"
                    "RULES:\n"
                    "1. Return ONLY valid JSON starting with { and ending with }.\n"
                    "2. ALL values must be in Arabic or English ONLY.\n"
                    "3. Use null for missing strings, [] for missing arrays.\n"
                    "4. NO thinking, NO explanation, NO markdown."
                ),
            },
            {"role": "user", "content": text},
        ]
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def generate_batch(self, prompts: List[str], chunk_ids: List[str]) -> List[str]:
        formatted = [self._build_prompt(p) for p in prompts]
        encoded = [
            self.tokenizer.encode(p, truncation=True, max_length=1024)
            for p in formatted
        ]
        max_len = max(len(e) for e in encoded)
        input_ids = torch.tensor([
            [self.tokenizer.pad_token_id] * (max_len - len(e)) + e
            for e in encoded
        ]).to(self.model.device)
        attention_mask = (input_ids != self.tokenizer.pad_token_id).long()

        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        results = []
        input_len = input_ids.shape[1]
        for i, ids in enumerate(output_ids):
            raw = self.tokenizer.decode(ids[input_len:], skip_special_tokens=True)
            print(f"  🧩 [{chunk_ids[i]}] → {raw[:80].replace(chr(10), ' ')}...")
            results.append(raw)
        return results

    def extract_json(self, raw: str) -> dict:
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        raw = re.sub(r"```(?:json)?\s*", "", raw)
        raw = re.sub(r"```\s*$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            try:
                return json.loads(raw[s:e+1])
            except json.JSONDecodeError:
                cleaned = re.sub(r",\s*([}\]])", r"\1", raw[s:e+1])
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass
        result = {}
        for key in ["summary", "narrative_role", "key_lessons"]:
            m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
            if m:
                result[key] = m.group(1)
        return result

    async def call_async_batch(self, prompts: List[str], chunk_ids: List[str]) -> List[dict]:
        async with self._inference_lock:
            loop = asyncio.get_event_loop()
            raws = await loop.run_in_executor(None, self.generate_batch, prompts, chunk_ids)
        return [self.extract_json(r) for r in raws]

print("✅ HFLocalLLM ready")
```

***

### Cell 7 — HFLLMMetadataExtractor (3 fields)

```python
MINIMAL_LLM_PROMPT = """النص:
\"\"\"{text}\"\"\"

الكتاب: {book_title} | المجال: {domain}

أرجع JSON بـ 3 حقول فقط:
{{
  "summary": "<جملة عربية واحدة تلخص النص>",
  "narrative_role": "<سرد|فقه|حديث|تفسير|عقيدة|شمائل|مقدمة|باب|وصف>",
  "key_lessons": ["<درس1>", "<درس2>"]
}}"""


class HFLLMMetadataExtractor:
    def __init__(self, hf_llm: HFLocalLLM, batch_size: int = 8):
        self._llm = hf_llm
        self.batch_size = batch_size
        self._stats = Counter()

    def _build_prompt_text(self, chunk: Chunk, catalog: dict) -> str:
        return MINIMAL_LLM_PROMPT.format(
            text=chunk.text[:800],
            book_title=chunk.book_title,
            domain=chunk.domain,
        )

    def _apply_llm_fields(self, chunk: Chunk, data: dict) -> None:
        def safe_str(v, default):
            if not v or v == "null":
                return default
            s = str(v).strip()
            if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", s):
                return default
            return s if s else default

        def safe_list(v, n):
            return [
                str(x).strip() for x in (v or [])
                if str(x).strip()
                and not re.search(r"[\u4e00-\u9fff]", str(x))
                and len(str(x)) < 200
            ][:n]

        chunk.summary        = safe_str(data.get("summary"), chunk.summary)
        chunk.narrative_role = safe_str(data.get("narrative_role"), chunk.narrative_role)
        chunk.key_lessons    = safe_list(data.get("key_lessons"), 3)

    async def enrich_all(self, chunks: List[Chunk], catalog: dict,
                         ckpt_mgr=None) -> Counter:
        children = [c for c in chunks if c.level == "child"]
        done_ids = ckpt_mgr.load_done_ids() if ckpt_mgr else set()
        children = [c for c in children if c.chunk_id not in done_ids]

        total = len(children)
        print(f"\n🚀 Enriching {total} chunks | batch={self.batch_size} | fields=3 | tokens=150")

        for batch_start in tqdm(
            range(0, total, self.batch_size),
            desc="🔬 Enriching",
            total=(total + self.batch_size - 1) // self.batch_size,
        ):
            batch     = children[batch_start:batch_start + self.batch_size]
            prompts   = [self._build_prompt_text(c, catalog) for c in batch]
            chunk_ids = [c.chunk_id for c in batch]

            try:
                results = await self._llm.call_async_batch(prompts, chunk_ids)
                for chunk, data in zip(batch, results):
                    if data:
                        self._apply_llm_fields(chunk, data)
                        chunk.enriched_by_llm = True
                        self._stats["llm_success"] += 1
                    else:
                        self._stats["llm_fallback"] += 1
            except Exception as ex:
                print(f"  ❌ Batch failed: {ex}")
                self._stats["llm_fallback"] += len(batch)

        print(f"\n🎉 Enrichment done: ✅ {self._stats['llm_success']} | ❌ {self._stats['llm_fallback']}")
        return self._stats

print("✅ HFLLMMetadataExtractor ready")
```

***

### Cell 8 — BayanAgenticChunker

```python
class BayanAgenticChunker:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        catalog_path: Path,
        domain: str = "seerah",
        parent_max_pages: int = 12,
        child_pages: int = 2,
        child_overlap: int = 1,
        skip_llm: bool = False,
        compute_entity_embeddings: bool = True,
        embedder_model: str = "BAAI/bge-m3",
        birch_threshold: float = 0.5,
    ):
        self.input_path    = input_path
        self.output_path   = output_path
        self.catalog_path  = catalog_path
        self.domain        = domain
        self.parent_max_pages = parent_max_pages
        self.child_pages   = child_pages
        self.child_overlap = child_overlap
        self.skip_llm      = skip_llm
        self.birch_threshold = birch_threshold
        self.compute_entity_embeddings = compute_entity_embeddings
        self.embedder_model = embedder_model

        self._passages:   List[Passage] = []
        self._deduped:    List[Passage] = []
        self._sections:   Dict         = {}
        self._chunks:     List[Chunk]  = []
        self._catalog:    Dict         = {}
        self._done_ids:   Set[str]     = set()
        self._parent_ctr  = 0
        self._child_ctr   = 0

        self._embedder = None
        if compute_entity_embeddings:
            print(f"📦 Loading embedder: {embedder_model}")
            self._embedder = SentenceTransformer(embedder_model)
            print("✅ Embedder ready")

        self._compiled_persons  = [(re.compile(p, re.UNICODE), n, t) for p, n, t in PERSON_TABLE]
        self._compiled_places   = [(re.compile(p, re.UNICODE), n, t) for p, n, t in PLACE_TABLE]
        self._compiled_events   = [(re.compile(p, re.UNICODE), n, t) for p, n, t in EVENT_TABLE]
        self._compiled_concepts = [(re.compile(p, re.UNICODE), n, t) for p, n, t in CONCEPT_TABLE]
        self._compiled_hadith   = [(re.compile(p, re.UNICODE), n) for p, n in HADITH_BOOK_TABLE]

    # ── Stage 1: Load ───────────────────────────────────────
    def _load_passages(self):
        with open(self.input_path, encoding="utf-8") as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                raw_data = [json.loads(l) for l in f if l.strip()]

        skipped = 0
        for idx, item in enumerate(raw_data):
            content = item.get("content", "").strip()
            if len(content.split()) < 10:
                skipped += 1
                continue
            self._passages.append(Passage(
                idx=len(self._passages),
                content=content,
                content_type=item.get("content_type", "page"),
                book_id=item.get("book_id", 0),
                book_title=item.get("book_title", ""),
                category=item.get("category", ""),
                author=item.get("author", ""),
                author_death=item.get("author_death", 99999),
                collection=item.get("collection", ""),
                page_number=item.get("page_number", 0),
                section_title=item.get("section_title", ""),
                hierarchy=item.get("hierarchy", []),
            ))

        if self.catalog_path.exists():
            with open(self.catalog_path, encoding="utf-8") as f:
                self._catalog = json.load(f)

        print(f"   📥 Raw: {len(raw_data)} | ✅ Kept: {len(self._passages)} | 🗑️ Noise: {skipped}")

    # ── Stage 2: Dedup ──────────────────────────────────────
    def _deduplicate(self):
        seen = set()
        for p in self._passages:
            h = hashlib.md5(p.content.encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                self._deduped.append(p)

    # ── Stage 3: Group Sections ─────────────────────────────
    def _group_sections(self):
        self._sections = defaultdict(list)
        skipped = 0
        for passage in self._deduped:
            if len(passage.content.split()) < 50:
                skipped += 1
                continue
            hier_key = tuple(passage.hierarchy) if passage.hierarchy else (passage.book_title,)
            self._sections[(passage.book_id, hier_key)].append(passage)
        self._sections = {k: v for k, v in self._sections.items() if v}
        print(f"   🗑️ Noise skipped: {skipped}")

    # ── Stage 4: Build Hierarchy ────────────────────────────
    def _make_windows(self, pages: List[Passage], size: int, step: int) -> List[List[Passage]]:
        if not pages:
            return []
        windows = []
        for i in range(0, len(pages), step):
            w = pages[i:i+size]
            if w:
                windows.append(w)
        return windows

    def _make_chunk(self, pages: List[Passage], chunk_id: str,
                    parent_id: Optional[str], level: str,
                    chunk_type: str, book_id: int,
                    hier: List[str]) -> Chunk:
        p0 = pages[0]
        text = "\n\n".join(p.content for p in pages)
        domain = self.domain if self.domain != "auto" else p0.category.lower()
        return Chunk(
            chunk_id=chunk_id,
            parent_chunk_id=parent_id,
            level=level,
            source_passage_ids=[p.idx for p in pages],
            book_id=book_id,
            book_title=p0.book_title,
            author=p0.author,
            author_death_year=p0.author_death,
            category=p0.category,
            collection=p0.collection,
            section_hierarchy=hier,
            section_leaf=hier[-1] if hier else "",
            page_range=(pages[0].page_number, pages[-1].page_number),
            page_count=len(pages),
            text=text,
            chunk_type=chunk_type,
            domain=domain,
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

    # ── Stage 5: Regex Entity Extraction ───────────────────
    def _extract_entities_from_text(self, text: str) -> dict:
        nd = remove_diacritics(text)
        persons  = list({n for p, n, _ in self._compiled_persons  if p.search(nd)})
        places   = list({n for p, n, _ in self._compiled_places   if p.search(nd)})
        events   = list({n for p, n, _ in self._compiled_events   if p.search(nd)})
        concepts = list({n for p, n, _ in self._compiled_concepts if p.search(nd)})
        books    = list({n for p, n   in self._compiled_hadith    if p.search(nd)})
        quran    = [m.group(0) for m in QURAN_REF_RE.finditer(text)]
        isnad    = [next(g for g in m.groups() if g) for m in ISNAD_RE.finditer(nd)]
        grade_m  = HADITH_GRADE_RE.search(nd)
        grade    = grade_m.group(1) if grade_m else None
        return {
            "entities": {
                "persons": persons, "places": places, "events": events,
                "concepts": concepts, "fiqh_rulings": [], "madhahib": [], "books": books,
            },
            "quranic_refs": quran[:5],
            "hadith_collections": books,
            "isnad_chain": isnad[:6],
            "hadith_grade": grade,
        }

    def _extract_baseline_entities(self):
        for chunk in tqdm(self._chunks, desc="🔎 Regex entities"):
            ext = self._extract_entities_from_text(chunk.text)
            chunk.metadata.update(ext)
            # Populate EHRAG entity_ids
            ids = set()
            for etype, names in ext["entities"].items():
                for name in names:
                    ids.add(f"{etype}:{name.replace(' ', '_')}")
            chunk.ehrag["entity_ids"] = list(ids)

    # ── Stage 7: Bubble Up ──────────────────────────────────
    def _bubble_up_to_parents(self):
        child_map: Dict[str, List[Chunk]] = defaultdict(list)
        for c in self._chunks:
            if c.level == "child" and c.parent_chunk_id:
                child_map[c.parent_chunk_id].append(c)

        for chunk in self._chunks:
            if chunk.level != "parent":
                continue
            children = child_map.get(chunk.chunk_id, [])
            all_persons = set(); all_places = set(); all_events = set()
            all_concepts = set(); all_books = set()
            for ch in children:
                all_persons.update(ch.metadata["entities"]["persons"])
                all_places.update(ch.metadata["entities"]["places"])
                all_events.update(ch.metadata["entities"]["events"])
                all_concepts.update(ch.metadata["entities"]["concepts"])
                all_books.update(ch.metadata["entities"]["books"])
            chunk.metadata["entities"] = {
                "persons": list(all_persons), "places": list(all_places),
                "events": list(all_events), "concepts": list(all_concepts),
                "fiqh_rulings": [], "madhahib": [], "books": list(all_books),
            }
            ids = set()
            for etype, names in chunk.metadata["entities"].items():
                for name in names:
                    ids.add(f"{etype}:{name.replace(' ', '_')}")
            chunk.ehrag["entity_ids"] = list(ids)

    # ── Stage 8: Link Siblings ──────────────────────────────
    def _link_siblings(self):
        parent_map: Dict[str, List[str]] = defaultdict(list)
        for c in self._chunks:
            if c.level == "child" and c.parent_chunk_id:
                parent_map[c.parent_chunk_id].append(c.chunk_id)

        id_to_chunk = {c.chunk_id: c for c in self._chunks}
        for siblings in parent_map.values():
            for i, cid in enumerate(siblings):
                ch = id_to_chunk[cid]
                ch.metadata["sibling_chunk_ids"] = [
                    s for s in siblings if s != cid
                ]
                if i > 0:
                    ch.metadata.setdefault("relations", []).append({
                        "type": RelationType.CONTINUES_FROM.value,
                        "target": siblings[i-1],
                    })
                if i < len(siblings) - 1:
                    ch.metadata.setdefault("relations", []).append({
                        "type": RelationType.CONTINUES_INTO.value,
                        "target": siblings[i+1],
                    })

    def _infer_cross_chunk_relations(self):
        id_to_chunk = {c.chunk_id: c for c in self._chunks if c.level == "child"}
        chunks_list = list(id_to_chunk.values())
        for i, c in enumerate(chunks_list):
            cp = set(c.metadata["entities"]["persons"])
            for j in range(max(0, i-5), min(len(chunks_list), i+5)):
                if i == j:
                    continue
                other = chunks_list[j]
                shared = cp & set(other.metadata["entities"]["persons"])
                if shared:
                    c.metadata.setdefault("relations", []).append({
                        "type": RelationType.SHARES_PERSON.value,
                        "target": other.chunk_id,
                        "shared": list(shared)[:3],
                    })

    # ── Stage 9: EHRAG ──────────────────────────────────────
    def _precompute_ehrag_structures(self):
        if not self._embedder:
            return
        children = [c for c in self._chunks if c.level == "child"]
        if not children:
            return
        texts = [c.text[:512] for c in children]
        embs  = self._embedder.encode(texts, batch_size=64,
                                       show_progress_bar=True,
                                       normalize_embeddings=True)
        birch = Birch(n_clusters=None, threshold=self.birch_threshold)
        labels = birch.fit_predict(embs)
        cluster_map: Dict[int, List[str]] = defaultdict(list)
        for chunk, label in zip(children, labels):
            cluster_map[int(label)].append(chunk.chunk_id)
        for label, ids in cluster_map.items():
            hedge_id = f"semantic_cluster_{label}"
            for cid in ids:
                id_to_chunk = {c.chunk_id: c for c in self._chunks}
                if cid in id_to_chunk:
                    id_to_chunk[cid].ehrag["structural_hyperedge"].append(hedge_id)
        log.info("EHRAG: %d semantic clusters", len(cluster_map))

    def _report(self, elapsed: float) -> str:
        parents  = sum(1 for c in self._chunks if c.level == "parent")
        children = sum(1 for c in self._chunks if c.level == "child")
        enriched = sum(1 for c in self._chunks if c.enriched_by_llm)
        return (
            f"\n{'='*50}\n"
            f"✅ BayanChunker Report\n"
            f"   Parents:  {parents}\n"
            f"   Children: {children}\n"
            f"   Enriched: {enriched}\n"
            f"   Time:     {elapsed/60:.1f} min\n"
            f"{'='*50}"
        )

print("✅ BayanAgenticChunker ready")
```

***

### Cell 9 — HFDatasetPusher + HFCheckpointManager

```python
class HFDatasetPusher:
    def __init__(self, repo_id: str, hf_token: str, push_every: int = 500):
        self._repo_id    = repo_id
        self._hf_token   = hf_token
        self._push_every = push_every
        self._buffer:    List[dict] = []
        self._shard      = 0
        self._api        = HfApi(token=hf_token)

    def add(self, record: dict):
        self._buffer.append(record)
        if len(self._buffer) >= self._push_every:
            self._push()

    def _push(self):
        if not self._buffer:
            return
        ds = Dataset.from_list(self._buffer)
        ds.push_to_hub(
            self._repo_id, split=f"train_shard_{self._shard:04d}",
            token=self._hf_token, private=True,
        )
        print(f"\n  ⬆️ Pushed shard {self._shard:04d} ({len(self._buffer)} records)")
        self._shard += 1
        self._buffer.clear()

    def finalize(self):
        if self._buffer:
            self._push()
        print(f"✅ All shards pushed — total: {self._shard}")


class HFCheckpointManager:
    def __init__(self, repo_id: str, hf_token: str,
                 local_path: str = "/content/chunks_done.jsonl",
                 save_every: int = 100):
        self.repo_id    = repo_id
        self.hf_token   = hf_token
        self.local_path = Path(local_path)
        self.save_every = save_every
        self._api       = HfApi(token=hf_token)
        self._total     = 0
        self._file_handle = None

    def load_done_ids(self) -> set:
        try:
            path = hf_hub_download(
                repo_id=self.repo_id, filename="chunks_done.jsonl",
                repo_type="dataset", token=self.hf_token,
                local_dir="/content/ckpt",
            )
            done = set()
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        done.add(json.loads(line)["chunk_id"])
            print(f"✅ Resumed: {len(done)} chunks already done")
            return done
        except Exception:
            print("📋 No checkpoint — starting fresh")
            return set()

    def load_progress(self) -> dict:
        try:
            path = hf_hub_download(
                repo_id=self.repo_id, filename="progress.json",
                repo_type="dataset", token=self.hf_token,
                local_dir="/content/ckpt",
            )
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {"last_batch": 0, "success": 0, "fallback": 0}

    def open(self):
        self._file_handle = open(self.local_path, "a", encoding="utf-8")

    def write_chunk(self, chunk_dict: dict):
        if self._file_handle:
            self._file_handle.write(
                json.dumps(chunk_dict, ensure_ascii=False) + "\n"
            )
            self._file_handle.flush()
        self._total += 1
        if self._total % self.save_every == 0:
            self._push_to_hf()

    def _push_to_hf(self):
        if self._file_handle:
            self._file_handle.flush()
        try:
            self._api.upload_file(
                path_or_fileobj=str(self.local_path),
                path_in_repo="chunks_done.jsonl",
                repo_id=self.repo_id, repo_type="dataset",
                commit_message=f"Checkpoint: {self._total} chunks",
            )
            print(f"\n  💾 HF checkpoint → {self._total} chunks")
        except Exception as ex:
            print(f"\n  ⚠️ Checkpoint push failed: {ex}")

    def save_progress(self, batch_idx: int, stats: dict):
        p = {"last_batch": batch_idx,
             "success": stats.get("llm_success", 0),
             "fallback": stats.get("llm_fallback", 0),
             "total_chunks": self._total}
        prog = Path("/content/progress.json")
        prog.write_text(json.dumps(p, ensure_ascii=False, indent=2))
        try:
            self._api.upload_file(
                path_or_fileobj=str(prog), path_in_repo="progress.json",
                repo_id=self.repo_id, repo_type="dataset",
                commit_message=f"Progress: batch {batch_idx}",
            )
        except Exception as ex:
            print(f"  ⚠️ Progress push failed: {ex}")

    def close(self):
        if self._file_handle:
            self._file_handle.close()
        self._push_to_hf()
        print(f"\n🎉 Final checkpoint: {self._total} chunks on HF")

print("✅ HFDatasetPusher + HFCheckpointManager ready")
```

***

### Cell 10 — BayanColabChunker

```python
class BayanColabChunker(BayanAgenticChunker):
    def __init__(self, hf_llm, hf_pusher, **kwargs):
        super().__init__(skip_llm=True, **kwargs)
        self._hf_llm    = hf_llm
        self._hf_pusher = hf_pusher
        self._extractor = HFLLMMetadataExtractor(
            hf_llm, batch_size=hf_llm.inference_batch_size
        )

    async def run(self, ckpt_mgr=None) -> str:
        t0 = time.time()

        print("📂 Stage 1/9: Loading passages")
        self._load_passages()
        print(f"   ✅ Loaded {len(self._passages)} passages")

        print("🔍 Stage 2/9: Deduplicating")
        self._deduplicate()
        print(f"   ✅ Kept {len(self._deduped)}")

        print("📁 Stage 3/9: Grouping sections")
        self._group_sections()
        print(f"   ✅ {len(self._sections)} sections")

        print("🏗️ Stage 4/9: Building hierarchy")
        self._build_hierarchy()
        print(f"   ✅ {self._parent_ctr} parents, {self._child_ctr} children")

        print("🔎 Stage 5/9: Regex entity extraction")
        self._extract_baseline_entities()

        print("🤖 Stage 6/9: LLM enrichment (3 fields)")
        await self._extractor.enrich_all(
            self._chunks, self._catalog, ckpt_mgr=None  # checkpoint بعد الـ linking
        )

        print("⬆️ Stage 7/9: Bubble metadata to parents")
        self._bubble_up_to_parents()

        print("🔗 Stage 8/9: Linking siblings + cross-chunk relations")
        self._link_siblings()
        self._infer_cross_chunk_relations()

        print("💾 Stage 9/9: Checkpoint + Push to HF")
        if ckpt_mgr:
            ckpt_mgr.open()
        written = 0
        for chunk in tqdm(self._chunks, desc="💾 Writing"):
            d = chunk.to_dict()
            if ckpt_mgr:
                ckpt_mgr.write_chunk(d)
            self._hf_pusher.add(d)
            written += 1
        if ckpt_mgr:
            ckpt_mgr.close()
        self._hf_pusher.finalize()
        print(f"   ✅ {written} chunks written")

        return self._report(time.time() - t0)

print("✅ BayanColabChunker ready")
```

***

### Cell 11 — Load Model

```python
hf_llm = HFLocalLLM(
    model_id="Qwen/Qwen3-4B-Instruct-2507",
    use_4bit=True,
    max_new_tokens=150,
    inference_batch_size=8,
)

# Quick sanity test
test = hf_llm.generate_batch(
    ['أرجع JSON: {"summary": "اختبار", "narrative_role": "حديث", "key_lessons": []}'],
    ["test_0"]
)
print("✅ Test:", hf_llm.extract_json(test[0]))
```

***

### Cell 12 — Initialize

```python
hf_pusher = HFDatasetPusher(
    repo_id=HF_DATASET_REPO,
    hf_token=HF_TOKEN,
    push_every=PUSH_EVERY_N,
)

ckpt_mgr = HFCheckpointManager(
    repo_id=HF_DATASET_REPO,
    hf_token=HF_TOKEN,
    local_path="/content/chunks_done.jsonl",
    save_every=100,
)

chunker = BayanColabChunker(
    hf_llm=hf_llm,
    hf_pusher=hf_pusher,
    input_path=Path(INPUT_JSON),
    output_path=Path("/content/chunks_output.jsonl"),
    catalog_path=Path(CATALOG_JSON),
    domain="seerah",
    parent_max_pages=PARENT_MAX_PAGES,
    child_pages=CHILD_PAGES,
    child_overlap=CHILD_OVERLAP,
    compute_entity_embeddings=COMPUTE_EMBEDDINGS,
    embedder_model=EMBEDDER_MODEL_ID,
    birch_threshold=0.5,
)

print("✅ All components ready")
```

***

### Cell 13 — RUN 🚀

```python
report = await chunker.run(ckpt_mgr=ckpt_mgr)
print(report)
```