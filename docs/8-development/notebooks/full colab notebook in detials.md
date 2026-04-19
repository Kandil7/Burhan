<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# full colab notebook in detials

هكتب لك الـ Notebook الكامل من أول وجديد — كل خلية مرقّمة، مرتّبة، وجاهزة للـ copy-paste في Colab.

***

# 📓 Athar RAG — Full Colab Notebook


***

## 🔷 SECTION 0 — Setup \& Storage

### Cell 00 — Install Libraries

```python
# Cell 00 – Install all dependencies
!pip install -q datasets sentence-transformers huggingface_hub \
              qdrant-client transformers accelerate tqdm

# Optional: better Arabic sentence tokenization
!pip install -q camel-tools 2>/dev/null || echo "camel-tools not available — using regex fallback"
```


***

### Cell 01 — Imports

```python
# Cell 01 – All imports
import re, json, os, time, hashlib
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from tqdm.auto import tqdm

from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import HfApi, InferenceClient, hf_hub_download, login
from huggingface_hub.utils import EntryNotFoundError
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter,
    MatchValue, PointStruct, VectorParams,
)
from sentence_transformers import SentenceTransformer

print("✅ All imports OK")
```


***

### Cell 02 — Login + Constants

```python
# Cell 02 – HF login + global constants
login()   # paste your HF token when prompted

# ── Repos ──────────────────────────────────────────────
HF_BASE  = "Kandil7/Athar-Datasets"
HF_MINI  = "Kandil7/Athar-Mini-Dataset-v2"
HF_HUB   = "Kandil7/Athar-RAG-Hub"

# ── Models ─────────────────────────────────────────────
EMBED_MODEL = "BAAI/bge-m3"
LLM_MODEL   = "Qwen/Qwen2.5-7B-Instruct"

# ── Chunking ───────────────────────────────────────────
CHUNK_VER   = "agentic_v1"
MAX_CHARS   = 1800
BATCH_SIZE  = 3        # pre-chunks per LLM call
LLM_SLEEP   = 1.5      # seconds between LLM calls
FLUSH_EVERY = 25       # passages before HF upload
TOP_K       = 10       # retrieval candidates
TEST_MODE   = False    # set True to run only 10 passages per collection

# ── Collections ────────────────────────────────────────
COLLECTIONS = [
    "aqeedah_passages",
    "arabic_language_passages",
    "fiqh_passages",
    "general_islamic",
    "hadith_passages",
    "islamic_history_passages",
    "quran_tafsir",
    "seerah_passages",
    "spirituality_passages",
    "usul_fiqh",
]

DOMAIN_CHUNK_TYPES = {
    "seerah_passages":          "seerah_event",
    "fiqh_passages":            "fiqh_issue",
    "quran_tafsir":             "tafsir_segment",
    "hadith_passages":          "hadith",
    "aqeedah_passages":         "aqeedah_point",
    "islamic_history_passages": "history_event",
    "usul_fiqh":                "usul_rule",
    "spirituality_passages":    "spiritual_point",
    "arabic_language_passages": "arabic_language_rule",
    "general_islamic":          "general_islamic_point",
}

print("✅ Constants set")
```


***

### Cell 03 — HF Storage Manager (Streaming-Safe, Resume)

```python
# Cell 03 – HF-only persistent storage (no Drive needed)
HF_TOKEN = os.environ.get("HF_TOKEN") or None
api      = HfApi(token=HF_TOKEN)
TMP_DIR  = Path("/tmp/athar"); TMP_DIR.mkdir(exist_ok=True)
_buffers: dict[str, list] = {}

def _hf_path(fn): return f"streaming/{fn}"

def load_checkpoint() -> dict:
    try:
        local = hf_hub_download(HF_HUB, _hf_path("checkpoint.json"),
                                repo_type="dataset", token=HF_TOKEN,
                                force_download=True)
        with open(local) as f: cp = json.load(f)
        print(f"♻️  Checkpoint: {cp}"); return cp
    except EntryNotFoundError: return {}
    except Exception as e: print(f"⚠ checkpoint: {e}"); return {}

def save_checkpoint(col: str, idx: int):
    cp = load_checkpoint()
    cp[col] = idx; cp["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    api.upload_file(
        path_or_fileobj=json.dumps(cp, ensure_ascii=False).encode(),
        path_in_repo=_hf_path("checkpoint.json"),
        repo_id=HF_HUB, repo_type="dataset",
        commit_message=f"ckpt: {col}@{idx}",
    )

def is_done(col, total): return load_checkpoint().get(col,-1) >= total-1

def get_tmp(col, kind): return TMP_DIR / f"{kind}_{col}.jsonl"

def buffer_chunks(chunks, col, kind="agentic"):
    k = f"{kind}_{col}"
    _buffers.setdefault(k, []).extend(chunks)

def flush_buffer(col, kind="agentic", force=False):
    k = f"{kind}_{col}"; buf = _buffers.get(k, [])
    if not buf or (len(buf) < FLUSH_EVERY and not force): return
    tmp = get_tmp(col, kind)
    with open(tmp, "a", encoding="utf-8") as f:
        for ch in buf: f.write(json.dumps(ch, ensure_ascii=False)+"\n")
    api.upload_file(
        path_or_fileobj=str(tmp),
        path_in_repo=_hf_path(f"{k}.jsonl"),
        repo_id=HF_HUB, repo_type="dataset",
        commit_message=f"stream: {kind} {col} +{len(buf)}",
    )
    _buffers[k] = []
    print(f"  📤 flushed {len(buf)} {kind} → {col}")

def load_existing(col, kind="agentic") -> list:
    try:
        local = hf_hub_download(
            HF_HUB, _hf_path(f"{kind}_{col}.jsonl"),
            repo_type="dataset", token=HF_TOKEN,
            force_download=True, local_dir=str(TMP_DIR),
            local_dir_use_symlinks=False,
        )
        rows = []
        with open(local, encoding="utf-8") as f:
            for line in f:
                if line.strip(): rows.append(json.loads(line))
        print(f"  ♻️  restored {len(rows)} {kind} ← {col}")
        return rows
    except EntryNotFoundError: return []
    except Exception as e: print(f"  ⚠ restore {kind}/{col}: {e}"); return []

print("✅ HF Storage Manager ready")
```


***

## 🔷 SECTION 1 — Data Loading

### Cell 04 — Load Datasets + Inspect Fields

```python
# Cell 04 – Load datasets and print schema
base_ds = load_dataset(HF_BASE, split="train")
mini_ds = load_dataset(HF_MINI, split="train")

print("=== base_ds ==="); print(base_ds); print(base_ds[^0])
print("\n=== mini_ds ==="); print(mini_ds); print(mini_ds[^0])
```

```python
# Cell 04b – Set field names AFTER inspecting output above
CONTENT_FIELD       = "content"        # ← edit if different
COLLECTION_FIELD    = "collection"
BOOK_ID_FIELD       = "book_id"
SECTION_TITLE_FIELD = "section_title"
PAGE_FIELD          = "page_number"
print("✅ Fields set")
```


***

### Cell 05 — Split per Collection

```python
# Cell 05 – Split passages per collection
passages_splits = {}
for col in COLLECTIONS:
    sub = base_ds.filter(lambda x, c=col: x[COLLECTION_FIELD] == c)
    if TEST_MODE:
        sub = sub.select(range(min(10, len(sub))))
    passages_splits[col] = sub
    print(f"  {col}: {len(sub)}")
```


***

## 🔷 SECTION 2 — Pre-Chunking

### Cell 06 — Pre-Chunking Functions

```python
# Cell 06 – Section-aware pre-chunking with CAMeL fallback

try:
    from camel_tools.tokenizers.sent_tokenizer import SentTokenizer
    _camel = SentTokenizer()
    def split_sentences(text: str) -> list[str]:
        text = re.sub(r'\s+', ' ', text).strip()
        return [s.strip() for s in _camel.tokenize(text) if s.strip()]
    print("✅ CAMeL SentTokenizer active")
except Exception:
    def split_sentences(text: str) -> list[str]:
        return [s.strip() for s in
                re.split(r"(?<=[.!؟\n])\s+", text) if s.strip()]
    print("⚠️  regex sentence split active")

INDEX_KW = ["فهرس","فهارس","محتويات","index"]

def choose_maxchars(section_title: str) -> int:
    t = section_title or ""
    if any(k in t for k in INDEX_KW): return 1200
    if any(k in t for k in ["غزوة","سيرة","قصة","حياة"]): return 2200
    if any(k in t for k in ["دروس","فوائد","أحكام","مسألة"]): return 1600
    return MAX_CHARS

def has_unbalanced_quran(text: str) -> bool:
    return "﴿" in text and "﴾" not in text

def repair_spans(chunks: list[str]) -> list[str]:
    out, skip = [], False
    for i, cur in enumerate(chunks):
        if skip: skip = False; continue
        nxt = chunks[i+1] if i+1 < len(chunks) else None
        if nxt and has_unbalanced_quran(cur) and "﴾" in nxt:
            out.append((cur+" "+nxt).strip()); skip = True
        else: out.append(cur)
    return out

def window_chunk(sentences: list[str], max_chars: int,
                 overlap: int = 1) -> list[str]:
    chunks, i = [], 0
    while i < len(sentences):
        buf, length = [], 0; j = i
        while j < len(sentences) and length+len(sentences[j])+1 <= max_chars:
            buf.append(sentences[j]); length += len(sentences[j])+1; j += 1
        if not buf: buf = [sentences[j]]; j += 1
        text = " ".join(buf).strip()
        if len(text) >= 200: chunks.append(text)
        i = max(j - overlap, i+1)
    return repair_spans(chunks)

def pre_chunk_row(row: dict) -> list[dict]:
    content = row.get(CONTENT_FIELD, "")
    if not content.strip(): return []
    sec       = row.get(SECTION_TITLE_FIELD, "") or ""
    is_index  = any(k in sec for k in INDEX_KW)
    max_chars = choose_maxchars(sec) if not is_index else 1200
    sentences = split_sentences(content)
    chunks    = window_chunk(sentences, max_chars)
    return [{
        "text":           ch,
        "collection":     row[COLLECTION_FIELD],
        "chunk_type":     "pre",
        "chunk_version":  "pre_v1",
        "book_id":        row.get(BOOK_ID_FIELD),
        "section_title":  sec,
        "page_number":    row.get(PAGE_FIELD),
        "is_index_page":  is_index,
        "metadata":       {},
    } for ch in chunks]

print("✅ Pre-chunking functions ready")
```


***

## 🔷 SECTION 3 — LLM Client

### Cell 07 — LLM Client + Batching

```python
# Cell 07 – HF Inference API client (correct message structure)
hf_client = InferenceClient(model=LLM_MODEL)

def call_llm(system: str, user: str, max_tokens: int = 2048) -> str:
    for attempt in range(4):
        try:
            resp = hf_client.chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                max_tokens=max_tokens,
                temperature=0.0,
            )
            return resp.choices[^0].message.content
        except Exception as e:
            wait = 2 ** attempt
            print(f"  ⚠ LLM attempt {attempt+1}/4: {e} — wait {wait}s")
            time.sleep(wait)
    return "[]"

def parse_json_safe(text: str) -> Any:
    text = re.sub(r"```json\n?|```\n?", "", text).strip()
    try: return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except Exception: pass
    return []

def batch_pre_chunks(pre_chunks: list[dict],
                     batch_size: int = BATCH_SIZE) -> list[list[dict]]:
    batches, cur, cur_sec = [], [], None
    for ch in pre_chunks:
        sec = ch.get("section_title","")
        if cur_sec is None: cur_sec = sec
        if sec != cur_sec or len(cur) >= batch_size:
            if cur: batches.append(cur)
            cur, cur_sec = [ch], sec
        else: cur.append(ch)
    if cur: batches.append(cur)
    return batches

print("✅ LLM client ready")
```


***

## 🔷 SECTION 4 — Agentic Chunkers

### Cell 08 — Shared Fallback Helper

```python
# Cell 08 – Shared fallback + all chunker agents

def _fallback(batch: list[dict], chunk_type: str) -> list[dict]:
    out = []
    for ch in batch:
        fb = ch.copy()
        fb["chunk_type"]    = chunk_type
        fb["chunk_version"] = CHUNK_VER
        fb["metadata"]      = ch.get("metadata",{}) | {"fallback": True}
        out.append(fb)
    return out

def _base_chunk(item: dict, pre: dict, collection: str,
                chunk_type: str, extra_meta: dict) -> dict:
    return {
        "text":          item.get(list(item.keys())[-1], ""),  # last key = text field
        "collection":    collection,
        "chunk_type":    chunk_type,
        "chunk_version": CHUNK_VER,
        "book_id":       pre.get("book_id"),
        "section_title": pre.get("section_title"),
        "page_number":   pre.get("page_number"),
        "metadata":      extra_meta,
    }
```


***

### Cell 09 — SeerahChunkerAgent

```python
# Cell 09 – SeerahChunkerAgent (batched)
_SEE_SYS = """أنت وكيل متخصص في السيرة النبوية. قسّم النص إلى أحداث.
أخرج JSON فقط — لا تضف أي نص خارجه."""

_SEE_USR = """قسّم النص إلى أحداث سيرة. لكل حدث:
event_title, period(قبل البعثة|مكي|مدني),
year_after_hijrah(int|null), place(str|null),
participants(list≤5), summary(≤جملتان), event_text

[{{"event_title":"","period":"","year_after_hijrah":null,"place":"",
"participants":[],"summary":"","event_text":""}}]
النص:\n{text}"""

def seerah_chunker(batch: list[dict]) -> list[dict]:
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_SEE_SYS, _SEE_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items:
        return _fallback(batch, "seerah_event")
    out = [{
        "text":          i["event_text"],
        "collection":    "seerah_passages",
        "chunk_type":    "seerah_event",
        "chunk_version": CHUNK_VER,
        "book_id":       base.get("book_id"),
        "section_title": base.get("section_title"),
        "page_number":   base.get("page_number"),
        "metadata": {
            "event_title":       i.get("event_title",""),
            "period":            i.get("period"),
            "year_after_hijrah": i.get("year_after_hijrah"),
            "place":             i.get("place"),
            "participants":      i.get("participants",[]),
            "summary":           i.get("summary",""),
        },
    } for i in items if i.get("event_text","").strip()]
    return out or _fallback(batch, "seerah_event")
```


***

### Cell 10 — FiqhChunkerAgent

```python
# Cell 10 – FiqhChunkerAgent
_FQH_SYS = "أنت وكيل فقهي. قسّم النص إلى مسائل مستقلة. أخرج JSON فقط."
_FQH_USR = """قسّم النص إلى مسائل فقهية. لكل مسألة:
issue_name, topic(صلاة|زكاة|صوم|حج|نكاح|طلاق|بيع|جنايات|...),
hukm(واجب|مستحب|مباح|مكروه|حرام|null),
madhhab_views{{hanafi,maliki,shafi_i,hanbali}},
evidences[{{type,reference}}], issue_text

[{{"issue_name":"","topic":"","hukm":null,"madhhab_views":{{}},"evidences":[],"issue_text":""}}]
النص:\n{text}"""

def fiqh_chunker(batch: list[dict]) -> list[dict]:
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_FQH_SYS, _FQH_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items:
        return _fallback(batch, "fiqh_issue")
    out = [{
        "text":          i["issue_text"],
        "collection":    "fiqh_passages",
        "chunk_type":    "fiqh_issue",
        "chunk_version": CHUNK_VER,
        "book_id":       base.get("book_id"),
        "section_title": base.get("section_title"),
        "page_number":   base.get("page_number"),
        "metadata": {
            "issue_name":    i.get("issue_name",""),
            "topic":         i.get("topic"),
            "hukm":          i.get("hukm"),
            "madhhab_views": i.get("madhhab_views",{}),
            "evidences":     i.get("evidences",[]),
        },
    } for i in items if i.get("issue_text","").strip()]
    return out or _fallback(batch, "fiqh_issue")
```


***

### Cell 11 — TafsirChunkerAgent

```python
# Cell 11 – TafsirChunkerAgent
_TAF_SYS = "أنت وكيل تفسير قرآني. قسّم النص إلى مقاطع تفسيرية. أخرج JSON فقط."
_TAF_USR = """قسّم نص التفسير إلى مقاطع. لكل مقطع:
surah, ayah_range("1" أو "1-5"),
mufassir(str|null),
segment_type(asbab_al_nuzul|linguistic|aqeedah|fiqh|general),
opinion_summary(جملة واحدة), segment_text

[{{"surah":"","ayah_range":"","mufassir":null,"segment_type":"general","opinion_summary":"","segment_text":""}}]
النص:\n{text}"""

def tafsir_chunker(batch: list[dict]) -> list[dict]:
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_TAF_SYS, _TAF_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items:
        return _fallback(batch, "tafsir_segment")
    out = [{
        "text":          i["segment_text"],
        "collection":    "quran_tafsir",
        "chunk_type":    "tafsir_segment",
        "chunk_version": CHUNK_VER,
        "book_id":       base.get("book_id"),
        "section_title": base.get("section_title"),
        "page_number":   base.get("page_number"),
        "metadata": {
            "surah":           i.get("surah"),
            "ayah_range":      i.get("ayah_range"),
            "mufassir":        i.get("mufassir") or base.get("metadata",{}).get("mufassir"),
            "segment_type":    i.get("segment_type","general"),
            "opinion_summary": i.get("opinion_summary",""),
        },
    } for i in items if i.get("segment_text","").strip()]
    return out or _fallback(batch, "tafsir_segment")
```


***

### Cell 12 — HadithChunkerAgent

```python
# Cell 12 – HadithChunkerAgent
_HAD_SYS = "أنت وكيل حديث. استخرج الأحاديث وشروحها. أخرج JSON فقط."
_HAD_USR = """استخرج من النص:
ahadith: [{{collection_name,hadith_number,matn,isnad,grading,topics[]}}]
explanations: [{{hadith_ref,explainer,section,points[],explanation_text}}]

{{"ahadith":[...],"explanations":[...]}}
النص:\n{text}"""

def hadith_chunker(batch: list[dict]) -> list[dict]:
    text = "\n\n---\n\n".join(c["text"] for c in batch)
    data = parse_json_safe(call_llm(_HAD_SYS, _HAD_USR.format(text=text)))
    base = batch[^0]
    if not isinstance(data, dict): return _fallback(batch, "hadith")
    out = []
    for h in data.get("ahadith",[]):
        if not h.get("matn","").strip(): continue
        out.append({"text": h["matn"], "collection": "hadith_passages",
                    "chunk_type": "hadith", "chunk_version": CHUNK_VER,
                    "book_id": base.get("book_id"),
                    "section_title": base.get("section_title"),
                    "page_number": base.get("page_number"),
                    "metadata": {"collection_name": h.get("collection_name"),
                                 "hadith_number": h.get("hadith_number"),
                                 "isnad": h.get("isnad"),
                                 "grading": h.get("grading"),
                                 "topics": h.get("topics",[])}})
    for e in data.get("explanations",[]):
        if not e.get("explanation_text","").strip(): continue
        out.append({"text": e["explanation_text"], "collection": "hadith_passages",
                    "chunk_type": "hadith_explanation", "chunk_version": CHUNK_VER,
                    "book_id": base.get("book_id"),
                    "section_title": base.get("section_title"),
                    "page_number": base.get("page_number"),
                    "metadata": {"hadith_ref": e.get("hadith_ref"),
                                 "explainer": e.get("explainer"),
                                 "section": e.get("section"),
                                 "points": e.get("points",[])}})
    return out or _fallback(batch, "hadith")
```


***

### Cell 13 — Remaining 6 Chunkers

```python
# Cell 13 – AqeedahChunkerAgent
_AQD_SYS = "أنت وكيل عقيدة. قسّم النص إلى نقاط عقائدية مستقلة. أخرج JSON فقط."
_AQD_USR = """قسّم نص العقيدة. لكل نقطة:
theme(tawhid_rububiyyah|tawhid_uluhiyyah|asma_was_sifat|iman|qadr|akhirah|other),
statement_type(affirmation|negation|refutation),
proposition(النص المركزي), evidences[{{type,reference}}],
refuted_group(str|null), point_text

[{{"theme":"","statement_type":"affirmation","proposition":"","evidences":[],"refuted_group":null,"point_text":""}}]
النص:\n{text}"""

def aqeedah_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_AQD_SYS, _AQD_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"aqeedah_point")
    out = [{"text": i["point_text"], "collection": "aqeedah_passages",
            "chunk_type": "aqeedah_point", "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"theme": i.get("theme"), "statement_type": i.get("statement_type"),
                         "proposition": i.get("proposition",""),
                         "evidences": i.get("evidences",[]),
                         "refuted_group": i.get("refuted_group")}}
           for i in items if i.get("point_text","").strip()]
    return out or _fallback(batch,"aqeedah_point")


# Cell 13b – IslamicHistoryChunkerAgent
_HST_SYS = "أنت وكيل تاريخ إسلامي. قسّم النص إلى أحداث أو تراجم. أخرج JSON فقط."
_HST_USR = """قسّم النص. لكل وحدة:
content_type(history_event|scholar_bio), title, period, year_hijri(int|null),
place(str|null), persons[], unit_text

[{{"content_type":"history_event","title":"","period":"","year_hijri":null,"place":"","persons":[],"unit_text":""}}]
النص:\n{text}"""

def islamic_history_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_HST_SYS, _HST_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"history_event")
    out = [{"text": i["unit_text"], "collection": "islamic_history_passages",
            "chunk_type": i.get("content_type","history_event"),
            "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"title": i.get("title"), "period": i.get("period"),
                         "year_hijri": i.get("year_hijri"),
                         "place": i.get("place"), "persons": i.get("persons",[])}}
           for i in items if i.get("unit_text","").strip()]
    return out or _fallback(batch,"history_event")


# Cell 13c – UsulFiqhChunkerAgent
_USL_SYS = "أنت وكيل أصول الفقه. قسّم النص إلى قواعد مستقلة. أخرج JSON فقط."
_USL_USR = """قسّم النص. لكل قاعدة:
rule_name, category(amr_nahy|ijma|qiyas|khabar|maqasid|other),
definition, evidences[{{type,reference}}], exceptions[], applications[], rule_text

[{{"rule_name":"","category":"","definition":"","evidences":[],"exceptions":[],"applications":[],"rule_text":""}}]
النص:\n{text}"""

def usul_fiqh_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_USL_SYS, _USL_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"usul_rule")
    out = [{"text": i["rule_text"], "collection": "usul_fiqh",
            "chunk_type": "usul_rule", "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"rule_name": i.get("rule_name"), "category": i.get("category"),
                         "definition": i.get("definition"),
                         "evidences": i.get("evidences",[]),
                         "exceptions": i.get("exceptions",[]),
                         "applications": i.get("applications",[])}}
           for i in items if i.get("rule_text","").strip()]
    return out or _fallback(batch,"usul_rule")


# Cell 13d – SpiritualityChunkerAgent
_SPR_SYS = "أنت وكيل تزكية. قسّم النص إلى مقاطع موضوعية. أخرج JSON فقط."
_SPR_USR = """قسّم النص. لكل مقطع:
topic(tazkiyah|dhikr|dua|sabr|tawakkul|zuhd|tawbah|other),
content_type(admonition|dua_text|zikr_formula|teaching),
proposition, related_ayahs[], related_ahadith[], point_text

[{{"topic":"","content_type":"teaching","proposition":"","related_ayahs":[],"related_ahadith":[],"point_text":""}}]
النص:\n{text}"""

def spirituality_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_SPR_SYS, _SPR_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"spiritual_point")
    out = [{"text": i["point_text"], "collection": "spirituality_passages",
            "chunk_type": "spiritual_point", "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"topic": i.get("topic"), "content_type": i.get("content_type"),
                         "proposition": i.get("proposition",""),
                         "related_ayahs": i.get("related_ayahs",[]),
                         "related_ahadith": i.get("related_ahadith",[])}}
           for i in items if i.get("point_text","").strip()]
    return out or _fallback(batch,"spiritual_point")


# Cell 13e – ArabicLanguageChunkerAgent
_ARA_SYS = "أنت وكيل لغة عربية. قسّم النص إلى قواعد لغوية. أخرج JSON فقط."
_ARA_USR = """قسّم النص. لكل قاعدة:
topic(nahw|sarf|balaghah|i3rab|lughat|other),
rule_name, definition, examples[], rule_text

[{{"topic":"","rule_name":"","definition":"","examples":[],"rule_text":""}}]
النص:\n{text}"""

def arabic_language_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_ARA_SYS, _ARA_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"arabic_language_rule")
    out = [{"text": i["rule_text"], "collection": "arabic_language_passages",
            "chunk_type": "arabic_language_rule", "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"topic": i.get("topic"), "rule_name": i.get("rule_name"),
                         "definition": i.get("definition"),
                         "examples": i.get("examples",[])}}
           for i in items if i.get("rule_text","").strip()]
    return out or _fallback(batch,"arabic_language_rule")


# Cell 13f – GeneralIslamicChunkerAgent
_GEN_SYS = "أنت وكيل إسلامي عام. قسّم النص إلى نقاط مستقلة. أخرج JSON فقط."
_GEN_USR = """قسّم النص. لكل نقطة:
topic(adab|akhlaq|dawah|ibadah|muamalat|other),
summary(جملة واحدة), related_ayahs[], related_ahadith[], point_text

[{{"topic":"","summary":"","related_ayahs":[],"related_ahadith":[],"point_text":""}}]
النص:\n{text}"""

def general_islamic_chunker(batch):
    text  = "\n\n---\n\n".join(c["text"] for c in batch)
    items = parse_json_safe(call_llm(_GEN_SYS, _GEN_USR.format(text=text)))
    base  = batch[^0]
    if not isinstance(items, list) or not items: return _fallback(batch,"general_islamic_point")
    out = [{"text": i["point_text"], "collection": "general_islamic",
            "chunk_type": "general_islamic_point", "chunk_version": CHUNK_VER,
            "book_id": base.get("book_id"), "section_title": base.get("section_title"),
            "page_number": base.get("page_number"),
            "metadata": {"topic": i.get("topic"), "summary": i.get("summary",""),
                         "related_ayahs": i.get("related_ayahs",[]),
                         "related_ahadith": i.get("related_ahadith",[])}}
           for i in items if i.get("point_text","").strip()]
    return out or _fallback(batch,"general_islamic_point")

print("✅ All 10 chunker agents ready")
```


***

### Cell 14 — Router

```python
# Cell 14 – Chunker Router
CHUNKER_MAP = {
    "seerah_passages":          seerah_chunker,
    "fiqh_passages":            fiqh_chunker,
    "quran_tafsir":             tafsir_chunker,
    "hadith_passages":          hadith_chunker,
    "aqeedah_passages":         aqeedah_chunker,
    "islamic_history_passages": islamic_history_chunker,
    "usul_fiqh":                usul_fiqh_chunker,
    "spirituality_passages":    spirituality_chunker,
    "arabic_language_passages": arabic_language_chunker,
    "general_islamic":          general_islamic_chunker,
}

def route_batch(batch: list[dict]) -> list[dict]:
    col    = batch[^0].get("collection","general_islamic")
    domain = DOMAIN_CHUNK_TYPES.get(col,"general_islamic_point")
    fn     = CHUNKER_MAP.get(col, general_islamic_chunker)
    try:    return fn(batch)
    except Exception as e:
        print(f"  ✗ route_batch [{col}]: {e}")
        return _fallback(batch, domain)

print("✅ Router ready")
```


***

## 🔷 SECTION 5 — Streaming Pipeline

### Cell 15 — Full Streaming Pipeline

```python
# Cell 15 – Streaming pipeline: per-passage, checkpoint, HF flush

embed_model = SentenceTransformer(EMBED_MODEL)
VECTOR_DIM  = embed_model.get_sentence_embedding_dimension()

def embed_dataset(ds: Dataset) -> Dataset:
    def _batch(batch):
        embs = embed_model.encode(
            batch["text"], batch_size=64,
            normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False,
        )
        return {"embedding": [e.astype("float32") for e in embs]}
    return ds.map(_batch, batched=True, batch_size=64, desc="Embedding")

checkpoint = load_checkpoint()

for col in COLLECTIONS:
    total = len(passages_splits[col])
    if is_done(col, total):
        print(f"✅ {col} done ({total}) — skip"); continue

    start = checkpoint.get(col, -1) + 1
    print(f"\n{'='*55}\n  {col}  [{start}/{total}]\n{'='*55}")

    # Restore existing chunks if resuming
    if start > 0:
        for kind in ("agentic","pre"):
            rows = load_existing(col, kind)
            tmp  = get_tmp(col, kind)
            with open(tmp, "a", encoding="utf-8") as f:
                for r in rows: f.write(json.dumps(r, ensure_ascii=False)+"\n")

    pre_buf = []

    for idx in tqdm(range(start, total), desc=col):
        row        = passages_splits[col][idx]
        pre_chunks = pre_chunk_row(row)
        if not pre_chunks:
            save_checkpoint(col, idx); continue

        buffer_chunks(pre_chunks, col, "pre")
        pre_buf.extend(pre_chunks)

        batches          = batch_pre_chunks(pre_buf)
        complete_batches = batches[:-1] if len(batches) > 1 else batches
        pre_buf          = batches[-1]  if len(batches) > 1 else []

        for b in complete_batches:
            agentic = route_batch(b)
            buffer_chunks(agentic, col, "agentic")
            time.sleep(LLM_SLEEP)

        flush_buffer(col, "agentic")
        flush_buffer(col, "pre")
        save_checkpoint(col, idx)

    # Flush remaining
    if pre_buf:
        buffer_chunks(route_batch(pre_buf), col, "agentic")
    flush_buffer(col, "agentic", force=True)
    flush_buffer(col, "pre",     force=True)

    # Push final Dataset for this collection
    agentic_rows = load_existing(col, "agentic")
    pre_rows     = load_existing(col, "pre")
    if agentic_rows:
        emb_ds = embed_dataset(Dataset.from_list(agentic_rows))
        DatasetDict({
            "chunks":     emb_ds,
            "pre_chunks": Dataset.from_list(pre_rows) if pre_rows else Dataset.from_list([]),
        }).push_to_hub(HF_HUB, config_name=col,
                       commit_message=f"[{col}] chunks + embeddings")
        print(f"  ✅ pushed config '{col}'")

    save_checkpoint(col, total-1)
    checkpoint = load_checkpoint()

print("\n🎉 All collections done!")
```


***

## 🔷 SECTION 6 — Qdrant Indexing

### Cell 16 — Index All Collections in Qdrant

```python
# Cell 16 – Qdrant in-memory index (for Colab RAG)
qdrant = QdrantClient(":memory:")

for col in COLLECTIONS:
    rows = load_existing(col, "agentic")
    if not rows:
        print(f"⚠ No chunks for {col}"); continue

    # Create collection
    qdrant.recreate_collection(
        collection_name=col,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )

    # Embed + upsert in batches
    texts   = [r["text"] for r in rows]
    all_emb = embed_model.encode(texts, batch_size=64,
                                  normalize_embeddings=True,
                                  convert_to_numpy=True,
                                  show_progress_bar=True)

    points = [
        PointStruct(
            id=i,
            vector=all_emb[i].tolist(),
            payload={
                "text":          rows[i]["text"],
                "chunk_type":    rows[i]["chunk_type"],
                "book_id":       rows[i].get("book_id"),
                "section_title": rows[i].get("section_title",""),
                "page_number":   rows[i].get("page_number"),
                "metadata":      rows[i].get("metadata",{}),
            },
        )
        for i in range(len(rows))
    ]
    qdrant.upsert(collection_name=col, points=points)
    print(f"  ✅ {col}: {len(points)} points indexed")

print(f"\n✅ Qdrant ready — {VECTOR_DIM}d vectors")
```


***

## 🔷 SECTION 7 — Agents

### Cell 17 — Data Models + Base Verifiers

```python
# Cell 17 – Agent data models + shared verifiers
@dataclass
class Citation:
    text:          str
    book_id:       Any  = None
    section_title: str  = ""
    page_number:   Any  = None
    score:         float= 0.0
    metadata:      dict = field(default_factory=dict)

@dataclass
class AgentOutput:
    answer:               str
    citations:            list = field(default_factory=list)
    metadata:             dict = field(default_factory=dict)
    confidence:           float= 1.0
    requires_human_review: bool= False

class IntentLabel(str, Enum):
    FiqhHukm            = "fiqh_hukm"
    FiqhMasaail         = "fiqh_masaail"
    HadithMatn          = "hadith_matn"
    HadithSharh         = "hadith_sharh"
    TafsirAyah          = "tafsir_ayah"
    AqeedahTawhid       = "aqeedah_tawhid"
    SeerahEvent         = "seerah_event"
    IslamicHistoryEvent = "islamic_history_event"
    ArabicGrammar       = "arabic_grammar"
    TazkiyahSuluk       = "tazkiyah_suluk"
    UsulFiqhQiyas       = "usul_fiqh_qiyas"
    GeneralIslamic      = "general_islamic"

SERIOUS_VIOLATIONS = {
    "strict_grounding_violation", "source_attribution_violation",
    "misattributed_quran_text",   "missing_requested_evidence",
    "answer_truncated",
}
QURAN_RE = re.compile(r'﴿(.+?)﴾')

def verify_quotes(passages, answer=""):
    issues = []
    for m in QURAN_RE.finditer(answer):
        q = m.group(1).strip()
        if not any(q in p.get("text","") for p in passages):
            issues.append({"type":"misattributed_quran_text",
                           "message":f"اقتباس غير موثّق: ﴿{q[:40]}﴾"})
    return issues

def verify_sources(passages):
    un = [p for p in passages if not p.get("book_id")]
    return [{"type":"source_attribution_violation",
             "message":f"{len(un)} مقطع بدون مصدر"}] if un else []

def verify_sufficiency(passages, requires=True, minimum=1):
    if requires and len(passages) < minimum:
        return [{"type":"missing_requested_evidence",
                 "message":"لا يوجد دليل كافٍ"}]
    return []

def verify_temporal(passages, intent):
    if intent not in (IntentLabel.SeerahEvent,IntentLabel.IslamicHistoryEvent):
        return []
    years = {p["metadata"].get("year_after_hijrah") or
              p["metadata"].get("year_hijri")
              for p in passages if p.get("metadata")}
    years.discard(None)
    if len(years) > 3:
        return [{"type":"temporal_inconsistency",
                 "message":f"تضارب في التواريخ: {years}"}]
    return []

print("✅ Models + verifiers ready")
```


***

### Cell 18 — CollectionAgent Base Class

```python
# Cell 18 – Abstract CollectionAgent base
class CollectionAgent(ABC):
    name:       str   = "base"
    COLLECTION: str   = ""
    TOP_K:      int   = TOP_K
    THRESHOLD:  float = 0.60

    def __init__(self):
        pass  # uses global qdrant, embed_model, call_llm

    def query_intake(self, q: str) -> str:
        q = re.sub(r'\s+', ' ', q).strip()
        return re.sub(r'^(أخبرني عن|اشرح لي|ما هو|ما هي)\s*','', q)

    @abstractmethod
    def classify_intent(self, q: str) -> IntentLabel: ...

    def retrieve(self, q: str) -> list[dict]:
        emb = embed_model.encode(q, normalize_embeddings=True,
                                 convert_to_numpy=True)
        results = qdrant.search(
            collection_name=self.COLLECTION,
            query_vector=emb.tolist(),
            limit=self.TOP_K,
            score_threshold=self.THRESHOLD,
            with_payload=True,
        )
        return [{"text": r.payload.get("text",""),
                 "score": r.score,
                 "book_id": r.payload.get("book_id"),
                 "section_title": r.payload.get("section_title",""),
                 "page_number": r.payload.get("page_number"),
                 "chunk_type": r.payload.get("chunk_type",""),
                 "metadata": r.payload.get("metadata",{})}
                for r in results]

    def rerank(self, q: str, candidates: list[dict]) -> list[dict]:
        qw = set(q.split())
        def boost(c):
            overlap = len(qw & set(c["text"].split())) / max(len(qw),1)
            return c["score"] + 0.05 * overlap
        # dedup
        seen, deduped = set(), []
        for c in sorted(candidates, key=boost, reverse=True):
            h = hash(c["text"][:200])
            if h not in seen: seen.add(h); deduped.append(c)
        return deduped

    @abstractmethod
    def verify(self, q: str, candidates: list[dict]) \
        -> tuple[list[dict], list[dict]]: ...

    @abstractmethod
    def generate(self, q: str, passages: list[dict]) -> str: ...

    def cite(self, passages: list[dict]) -> list[Citation]:
        seen, out = set(), []
        for p in passages:
            k = (p.get("book_id"), p.get("section_title",""))
            if k not in seen:
                seen.add(k)
                out.append(Citation(text=p["text"][:300],
                                    book_id=p.get("book_id"),
                                    section_title=p.get("section_title",""),
                                    page_number=p.get("page_number"),
                                    score=p.get("score",0.0),
                                    metadata=p.get("metadata",{})))
        return out

    def run(self, query: str) -> AgentOutput:
        t0         = time.perf_counter()
        q          = self.query_intake(query)
        intent     = self.classify_intent(q)
        candidates = self.retrieve(q)
        candidates = self.rerank(q, candidates)
        verified, issues = self.verify(q, candidates)

        if not verified:
            return AgentOutput(
                answer="لم أجد معلومات كافية في المصادر للإجابة على سؤالك.",
                metadata={"agent": self.name, "collection": self.COLLECTION,
                          "intent": intent.value, "is_verified": False,
                          "verification_issues": issues, "retrieved": len(candidates),
                          "verified": 0,
                          "latency_ms": int((time.perf_counter()-t0)*1000)},
                confidence=0.0, requires_human_review=True)

        answer    = self.generate(q, verified)
        citations = self.cite(verified)

        issue_types = {i.get("type","") for i in issues}
        has_serious = bool(issue_types & SERIOUS_VIOLATIONS)

        return AgentOutput(
            answer=answer, citations=citations,
            metadata={"agent": self.name, "collection": self.COLLECTION,
                      "intent": intent.value,
                      "is_verified": not has_serious,
                      "verification_issues": issues,
                      "retrieved": len(candidates), "verified": len(verified),
                      "latency_ms": int((time.perf_counter()-t0)*1000)},
            confidence=0.85 if not has_serious else 0.4,
            requires_human_review=has_serious)
```


***

### Cell 19 — All 10 Agents

```python
# Cell 19 – All 10 Collection Agents

class SeerahAgent(CollectionAgent):
    name = "SeerahAgent"; COLLECTION = "seerah_passages"
    def classify_intent(self, q):  return IntentLabel.SeerahEvent
    def verify(self, q, c):
        issues = verify_sources(c) + verify_temporal(c, IntentLabel.SeerahEvent)
        issues += verify_sufficiency(c)
        return ([], issues) if any(i["type"]=="missing_requested_evidence" for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت وكيل سيرة. أجب من النصوص فقط. اذكر الأحداث والتواريخ والأماكن."
        return call_llm(sys, f"السؤال: {q}\n\nالنصوص:\n{ctx}\n\nالإجابة:")

class FiqhAgent(CollectionAgent):
    name = "FiqhAgent"; COLLECTION = "fiqh_passages"
    def classify_intent(self, q):
        return IntentLabel.FiqhHukm if any(k in q for k in ["حكم","يجوز","حلال","حرام"]) else IntentLabel.FiqhMasaail
    def verify(self, q, c):
        issues = verify_sources(c) + verify_quotes(c, "") + verify_sufficiency(c, "دليل" in q or "حكم" in q)
        return ([], issues) if any(i["type"] in SERIOUS_VIOLATIONS for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        mvs = "\n".join(f"- {x['metadata'].get('hukm','')}: {x['metadata'].get('madhhab_views',{})}" for x in p if x.get("metadata",{}).get("hukm"))
        sys = "أنت فقيه. اذكر الحكم ثم الدليل ثم أقوال المذاهب. التزم بالنصوص فقط."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}" + (f"\n\nأقوال المذاهب:\n{mvs}" if mvs else "") + "\n\nالإجابة الفقهية:")

class TafsirAgent(CollectionAgent):
    name = "TafsirAgent"; COLLECTION = "quran_tafsir"
    def classify_intent(self, q): return IntentLabel.TafsirAyah
    def verify(self, q, c):
        issues = verify_sources(c) + verify_quotes(c)
        return ([], issues) if any(i["type"]=="strict_grounding_violation" for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت مفسر. اعتمد على النصوص فقط. اذكر السورة والآية."
        return call_llm(sys, f"السؤال التفسيري: {q}\n\n{ctx}\n\nالتفسير المختصر:")

class HadithAgent(CollectionAgent):
    name = "HadithAgent"; COLLECTION = "hadith_passages"
    def classify_intent(self, q):
        return IntentLabel.HadithSharh if any(k in q for k in ["شرح","معنى"]) else IntentLabel.HadithMatn
    def verify(self, q, c):
        issues = verify_sources(c) + verify_quotes(c)
        for p in c:
            if "ضعيف" in (p.get("metadata",{}).get("grading") or ""):
                issues.append({"type":"weak_hadith_used","message":"حديث ضعيف"})
        return c, issues   # warn only
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']} — {x['metadata'].get('collection_name','')} {x['metadata'].get('hadith_number','')} — {x['metadata'].get('grading','')}" for i,x in enumerate(p[:5]))
        sys = "أنت محدّث. اذكر الحديث بنصه وشرحه من المصادر فقط."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة:")

class AqeedahAgent(CollectionAgent):
    name = "AqeedahAgent"; COLLECTION = "aqeedah_passages"
    def classify_intent(self, q): return IntentLabel.AqeedahTawhid
    def verify(self, q, c):
        issues = verify_sources(c) + verify_quotes(c) + verify_sufficiency(c, True)
        return ([], issues) if any(i["type"] in SERIOUS_VIOLATIONS for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت عالم عقيدة. اذكر الدليل. ردّ على الشبهة إن وُجدت."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة العقدية:")

class HistoryAgent(CollectionAgent):
    name = "HistoryAgent"; COLLECTION = "islamic_history_passages"
    def classify_intent(self, q): return IntentLabel.IslamicHistoryEvent
    def verify(self, q, c):
        return c, verify_sources(c) + verify_temporal(c, IntentLabel.IslamicHistoryEvent)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت مؤرخ إسلامي. اذكر التواريخ والأحداث بدقة."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة:")

class UsulFiqhAgent(CollectionAgent):
    name = "UsulFiqhAgent"; COLLECTION = "usul_fiqh"
    def classify_intent(self, q): return IntentLabel.UsulFiqhQiyas
    def verify(self, q, c):
        issues = verify_sources(c) + verify_sufficiency(c, True)
        return ([], issues) if any(i["type"] in SERIOUS_VIOLATIONS for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت أصولي. اذكر القاعدة وتطبيقاتها."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة الأصولية:")

class SpiritualityAgent(CollectionAgent):
    name = "SpiritualityAgent"; COLLECTION = "spirituality_passages"
    def classify_intent(self, q): return IntentLabel.TazkiyahSuluk
    def verify(self, q, c):
        issues    = verify_sources(c)
        flagged   = [p for p in c if any(w in p["text"] for w in ["تكفير","غلو","ضلال"])]
        if flagged: issues.append({"type":"tone_safety_flag","message":"محتوى يحتاج مراجعة"})
        return [p for p in c if p not in flagged], issues
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت مرشد روحي. أجب بأسلوب تزكوي هادئ من النصوص."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة:")

class ArabicLanguageAgent(CollectionAgent):
    name = "ArabicLanguageAgent"; COLLECTION = "arabic_language_passages"
    def classify_intent(self, q): return IntentLabel.ArabicGrammar
    def verify(self, q, c): return c, verify_sources(c)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        exs = "\n".join(f"- {e}" for x in p for e in x.get("metadata",{}).get("examples",[])[:2])
        sys = "أنت نحوي. اذكر القاعدة والأمثلة."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}" + (f"\n\nأمثلة:\n{exs}" if exs else "") + "\n\nالإجابة:")

class GeneralIslamicAgent(CollectionAgent):
    name = "GeneralIslamicAgent"; COLLECTION = "general_islamic"
    def classify_intent(self, q): return IntentLabel.GeneralIslamic
    def verify(self, q, c):
        issues = verify_sources(c) + verify_sufficiency(c, len(c) < 2)
        return ([], issues) if any(i["type"]=="missing_requested_evidence" for i in issues) else (c, issues)
    def generate(self, q, p):
        ctx = "\n\n".join(f"[{i+1}] {x['text']}" for i,x in enumerate(p[:5]))
        sys = "أنت مساعد إسلامي. أجب بوضوح ودقة من النصوص."
        return call_llm(sys, f"السؤال: {q}\n\n{ctx}\n\nالإجابة:")

print("✅ All 10 agents ready")
```


***

### Cell 20 — RouterAgent + Instantiate

```python
# Cell 20 – RouterAgent + instantiate all agents

_ROUTER_SYS = """حدد collection الأنسب للسؤال الإسلامي.
أخرج JSON فقط: {"primary":"collection","secondary":["col2","col3"]}
collections: seerah_passages|fiqh_passages|quran_tafsir|hadith_passages|
aqeedah_passages|islamic_history_passages|usul_fiqh|
spirituality_passages|arabic_language_passages|general_islamic"""

AGENTS = {
    "seerah_passages":          SeerahAgent(),
    "fiqh_passages":            FiqhAgent(),
    "quran_tafsir":             TafsirAgent(),
    "hadith_passages":          HadithAgent(),
    "aqeedah_passages":         AqeedahAgent(),
    "islamic_history_passages": HistoryAgent(),
    "usul_fiqh":                UsulFiqhAgent(),
    "spirituality_passages":    SpiritualityAgent(),
    "arabic_language_passages": ArabicLanguageAgent(),
    "general_islamic":          GeneralIslamicAgent(),
}

def route(query: str) -> tuple[str, list[str]]:
    raw    = call_llm(_ROUTER_SYS, f"السؤال: {query}")
    parsed = {}
    try:   parsed = json.loads(re.sub(r"```.*?```","",raw,flags=re.S).strip())
    except Exception: pass
    primary   = parsed.get("primary","general_islamic")
    secondary = parsed.get("secondary",[])
    valid     = set(AGENTS)
    primary   = primary if primary in valid else "general_islamic"
    secondary = [c for c in secondary if c in valid and c != primary][:2]
    return primary, secondary

def ask(question: str) -> AgentOutput:
    print(f"\n❓ {question}")
    primary, secondary = route(question)
    print(f"  🔀 → {primary}" + (f" + {secondary}" if secondary else ""))
    result = AGENTS[primary].run(question)
    if not result.citations and secondary:
        for col in secondary:
            fb = AGENTS[col].run(question)
            if fb.citations: result = fb; break
    print(f"  ✅ [{result.metadata.get('agent')}] "
          f"verified={result.metadata.get('is_verified')} | "
          f"citations={len(result.citations)} | "
          f"{result.metadata.get('latency_ms')}ms")
    print(f"  📝 {result.answer[:250]}...")
    return result

print("✅ Router + all agents instantiated")
```


***

## 🔷 SECTION 8 — Evaluation

### Cell 21 — QA Generator + Evaluation

```python
# Cell 21 – QA generation + evaluation pipeline

QA_SYS = """أنت خبير تقييم لأنظمة RAG الإسلامية.
ولّد أسئلة واقعية مع إجاباتها من النص. أخرج JSON فقط."""

QA_USR = """من النص التالي ولّد {n} أسئلة. لكل سؤال:
question, gold_answer, answer_type(factual|causal|ruling|explanatory),
requires_evidence(bool), difficulty(easy|medium|hard)

[{{"question":"","gold_answer":"","answer_type":"factual","requires_evidence":false,"difficulty":"medium"}}]
النص:\n{text}"""

def generate_qa(chunk: dict, n: int = 2) -> list[dict]:
    raw   = call_llm(QA_SYS, QA_USR.format(text=chunk["text"], n=n))
    items = parse_json_safe(raw)
    if not isinstance(items, list): return []
    out = []
    for item in items:
        if not item.get("question","").strip(): continue
        out.append({
            "id":               f"{chunk.get('collection','')[:4]}_{hash(item['question'])&0xFFFF:04x}",
            "question":         item["question"],
            "gold_answer":      item.get("gold_answer",""),
            "answer_type":      item.get("answer_type","factual"),
            "requires_evidence":item.get("requires_evidence",False),
            "difficulty":       item.get("difficulty","medium"),
            "collection":       chunk.get("collection",""),
            "gold_passages":    [{"book_id": chunk.get("book_id"),
                                  "section_title": chunk.get("section_title"),
                                  "text_snippet": chunk["text"][:200]}],
        })
    return out

# Build QA dataset
QA_TARGET = {"seerah_passages":50,"fiqh_passages":60,"quran_tafsir":40,
             "hadith_passages":40,"aqeedah_passages":30,"islamic_history_passages":30,
             "usul_fiqh":25,"spirituality_passages":20,
             "arabic_language_passages":20,"general_islamic":20}
import random; random.seed(42)
all_qa = []

for col in COLLECTIONS:
    rows    = load_existing(col, "agentic")
    target  = QA_TARGET.get(col, 20)
    pool    = [r for r in rows if not r.get("metadata",{}).get("fallback")]
    sampled = random.sample(pool, min(target//2+3, len(pool)))
    col_qa, seen = [], set()

    for chunk in tqdm(sampled, desc=f"QA {col}"):
        for p in generate_qa(chunk, n=2):
            q_key = p["question"].strip().lower()
            if q_key not in seen and len(col_qa) < target:
                seen.add(q_key); p["id"] = f"{col[:4]}_{len(col_qa):04d}"
                col_qa.append(p)
        time.sleep(1.0)

    all_qa.extend(col_qa)
    Dataset.from_list(col_qa).push_to_hub(
        HF_HUB, config_name=f"{col}_qa", split="eval",
        commit_message=f"[QA] {col} — {len(col_qa)} pairs")
    print(f"  ✅ {col}: {len(col_qa)} QA pairs")

print(f"\n📊 Total QA pairs: {len(all_qa)}")
```


***

### Cell 22 — Run Agents on QA + Compute Metrics

```python
# Cell 22 – Evaluate agents + compute 8 metrics

eval_results = []
for row in tqdm(all_qa, desc="Evaluating"):
    try:    resp = AGENTS.get(row["collection"], AGENTS["general_islamic"]).run(row["question"])
    except Exception as e:
        resp = AgentOutput(answer="", metadata={"error":str(e),"is_verified":False,"verification_issues":[]}, requires_human_review=True)
    eval_results.append({
        **{k: row[k] for k in ["id","collection","question","gold_answer","gold_passages","answer_type","difficulty","requires_evidence"]},
        "agent_name":  resp.metadata.get("agent",""),
        "answer":      resp.answer,
        "citations":   [{"book_id":c.book_id,"section_title":c.section_title,"score":c.score} for c in resp.citations],
        "metadata":    resp.metadata,
        "requires_human_review": resp.requires_human_review,
    })

# ── Metrics ──────────────────────────────────────────────────────────────
def compute_metrics(results):
    n = len(results)
    if not n: return {}

    recall_flags, faithful_flags, violations = [], [], Counter()
    for r in results:
        gold_set   = {(p.get("book_id"), p.get("section_title","")) for p in r.get("gold_passages",[])}
        ret_set    = {(c.get("book_id"), c.get("section_title","")) for c in r.get("citations",[])[:TOP_K]}
        recall_flags.append(1 if gold_set and gold_set & ret_set else 0)

        meta   = r.get("metadata",{}) or {}
        issues = meta.get("verification_issues",[])
        types  = {i.get("type","") if isinstance(i,dict) else i for i in issues}
        for t in types: violations[t] += 1
        faithful_flags.append(1 if meta.get("is_verified") and not (types & SERIOUS_VIOLATIONS) else 0)

    requires_ev = [r for r in results if r.get("requires_evidence")]
    return {
        "n": n,
        "context_recall_at_10":  round(sum(recall_flags)/len(recall_flags),4) if recall_flags else 0,
        "faithfulness_rate":     round(sum(faithful_flags)/n,4),
        "evidence_completeness": round(sum(1 for r in requires_ev if r.get("citations"))/len(requires_ev),4) if requires_ev else None,
        "human_review_rate":     round(sum(1 for r in results if r.get("requires_human_review"))/n,4),
        "answer_coverage":       round(sum(1 for r in results if r.get("answer","").strip())/n,4),
        "violation_rates":       {k:round(v/n,4) for k,v in violations.most_common()},
    }

by_col = defaultdict(list)
for r in eval_results: by_col[r["collection"]].append(r)

print(f"\n{'='*62}")
print(f"  {'Collection':<30} {'Recall@10':>9} {'Faithful':>9} {'Coverage':>9}")
print(f"{'='*62}")
all_metrics = {}
for col in COLLECTIONS:
    m = compute_metrics(by_col.get(col,[]))
    if not m: continue
    all_metrics[col] = m
    print(f"  {col:<30} {m['context_recall_at_10']:>9.3f} {m['faithfulness_rate']:>9.3f} {m['answer_coverage']:>9.3f}")
print(f"{'='*62}")
overall = compute_metrics(eval_results)
print(f"  {'OVERALL':<30} {overall['context_recall_at_10']:>9.3f} {overall['faithfulness_rate']:>9.3f} {overall['answer_coverage']:>9.3f}")
```


***

### Cell 23 — Push Eval + Final Stats

```python
# Cell 23 – Push eval results + metrics to HF

Dataset.from_list(eval_results).push_to_hub(
    HF_HUB, config_name="qa_eval", split="eval",
    commit_message="[eval] all collections — agents + metrics")

api.upload_file(
    path_or_fileobj=json.dumps({"per_collection":all_metrics,"overall":overall},
                                ensure_ascii=False,indent=2).encode(),
    path_in_repo="eval/metrics_summary.json",
    repo_id=HF_HUB, repo_type="dataset",
    commit_message="[eval] metrics summary",
)

# Stats
chunk_counts = Counter()
for col in COLLECTIONS:
    rows = load_existing(col,"agentic")
    chunk_counts[col] = len(rows)

print("\n📊 Final Stats:")
print(f"{'='*45}")
for col, cnt in chunk_counts.most_common():
    print(f"  {col:<35} {cnt:>6}")
print(f"{'='*45}")
print(f"  {'TOTAL':<35} {sum(chunk_counts.values()):>6}")
print(f"\n🔗 https://huggingface.co/datasets/{HF_HUB}")
```


***

### Cell 24 — Quick Test

```python
# Cell 24 – Quick end-to-end test
test_questions = [
    "ما حكم الصلاة في الثوب النجس؟",
    "متى كانت غزوة بدر الكبرى؟",
    "ما معنى قوله تعالى ﴿إن الله مع الصابرين﴾؟",
    "ما هو القياس في أصول الفقه؟",
    "ما الفرق بين الفاعل والمبتدأ في النحو؟",
]
for q in test_questions:
    ask(q)
    print()
```


***

## خريطة الـ Notebook الكاملة

| \# | الخلية | الوظيفة |
| :-- | :-- | :-- |
| 00–01 | Install + Imports | كل المكتبات |
| 02 | Constants | كل الثوابت في مكان واحد |
| 03 | HF Storage Manager | checkpoint + flush + resume |
| 04–05 | Load Data | base_ds + mini_ds + splits |
| 06 | Pre-Chunking | CAMeL + section-aware + span repair |
| 07 | LLM Client | correct API + batching |
| 08–14 | Chunkers + Router | 10 agents + router + fallback |
| 15 | Streaming Pipeline | checkpoint-safe, HF-only |
| 16 | Qdrant Indexing | in-memory, all collections |
| 17–20 | RAG Agents | base + 10 agents + RouterAgent |
| 21–23 | Evaluation | QA gen + 8 metrics + push |
| 24 | Quick Test | 5 اختبارات فورية |

الـ notebook كامل ومترابط — كل cell تعتمد على اللي قبلها بالترتيب الصحيح.[^1]

<div align="center">⁂</div>

[^1]: chat-Search-Athar-Dataset.txt.md

