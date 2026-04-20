# build_seerah_chunks_camel_v3.py

import json
import re
from pathlib import Path
from typing import List, Dict, Any

# from camel_tools.tokenizers.senttokenizer import SentTokenizer
from camel_tools.utils.normalize import (
    normalize_alef_maksura_ar,
    normalize_teh_marbuta_ar,
)
from camel_tools.utils.dediac import dediac_ar

# --------- إعدادات عامة ---------
INPUT_PATH = Path("data/mini_dataset_v2/seerah_passages.jsonl")            # raw JSONL input
OUTPUT_PATH = Path("data/mini_dataset_v2/seerah_chunks_v3.jsonl")

DEFAULT_MAX_CHARS = 1800                  # default char limit
OVERLAP_SENTENCES = 2                     # sentence overlap between chunks

# sent_tokenizer = SentTokenizer()

# ---------- Heuristics ----------

INDEX_KEYWORDS = [
    "الفهرس", "الفِهْرِسُ", "الفهرس العام", "الفهرس المفصل",
    "فهرس", "index",
]

DESCRIPTIVE_KEYWORDS = [
    "الشمائل", "صفة", "صفات", "أخلاق", "خلق", "خصائص",
]

BATTLE_KEYWORDS = [
    "غزوة", "سرية", "وقعة", "معركة", "بدر", "أحد", "الخندق",
]

LESSON_KEYWORDS = [
    "دروس", "فوائد", "لطائف", "العبرة", "عبرة", "مواقف", "موقف",
]

# ---------- Helpers ----------

def detect_index_page(section_title: str, content: str) -> bool:
    """Return True if this looks like an index/table-of-contents page."""
    title = (section_title or "").strip()
    text = content.strip()

    if any(kw in title for kw in INDEX_KEYWORDS):
        return True

    # محتوى قصير مليان أرقام صفحات وعناوين سطور قصيرة
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) >= 5:
        numbered_like = sum(
            1 for l in lines
            if re.search(r"\d{1,3}$", l) and len(l.split()) <= 8
        )
        if numbered_like >= 4:
            return True

    return False


def choose_max_chars(section_title: str) -> int:
    """Choose chunk size based on section type heuristics."""
    title = (section_title or "").strip()

    if any(kw in title for kw in INDEX_KEYWORDS):
        return 1200  # not critical, will likely be flagged as index

    if any(kw in title for kw in DESCRIPTIVE_KEYWORDS):
        return 2200

    if any(kw in title for kw in BATTLE_KEYWORDS):
        return 1800

    if any(kw in title for kw in LESSON_KEYWORDS):
        return 1600

    return DEFAULT_MAX_CHARS


def split_arabic_sentences(text: str) -> List[str]:
    """Sentence splitting using regex fallback."""
    if not text:
        return []
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n+", "\n", text)
    # sentences = sent_tokenizer.tokenize(text)
    # Using regex as a fallback if SentTokenizer is unavailable
    sentences = re.split(r'(?<=[.؟!؛])\s+|\n+', text)
    return [s.strip() for s in sentences if s.strip()]


def normalize_for_embedding(text: str) -> str:
    text = dediac_ar(text)
    text = normalize_alef_maksura_ar(text)
    text = normalize_teh_marbuta_ar(text)
    return text


def has_unbalanced_quran(text: str) -> bool:
    """﴿ exists without matching ﴾."""
    return ("﴿" in text) and ("﴾" not in text)


def has_unbalanced_arabic_quotes(text: str) -> bool:
    """« exists without » or vice versa."""
    left = "«" in text
    right = "»" in text
    return (left and not right) or (right and not left)


def chunk_sentences(
    sentences: List[str],
    max_chars: int,
    overlap_sents: int = OVERLAP_SENTENCES,
) -> List[str]:
    """
    Basic sentence-aware chunking with char limit and sentence overlap.
    """
    chunks: List[str] = []
    i = 0
    n = len(sentences)

    while i < n:
        current: List[str] = []
        length = 0
        j = i

        while j < n and (length + len(sentences[j]) + 1) <= max_chars:
            current.append(sentences[j])
            length += len(sentences[j]) + 1
            j += 1

        if not current:
            current = [sentences[j]]
            j += 1

        chunk_text = " ".join(current).strip()
        if chunk_text:
            chunks.append(chunk_text)

        if j >= n:
            break
        i = max(j - overlap_sents, i + 1)

    return chunks


def repair_broken_spans(chunks: List[str]) -> List[str]:
    """
    يحاول يصلح الحالات البسيطة للآيات/الأحاديث المقطوعة عبر
    دمج بعض الchunks المتجاورة.

    قواعد بسيطة:
      - لو chunk[i] فيه ﴿ بدون ﴾ و chunk[i+1] فيه ﴾ → دمج.
      - لو chunk[i] فيه « بدون » و chunk[i+1] فيه » → دمج.
    """
    if not chunks:
        return chunks

    repaired: List[str] = []
    skip_next = False
    n = len(chunks)

    for i in range(n):
        if skip_next:
            skip_next = False
            continue

        cur = chunks[i]
        if i < n - 1:
            nxt = chunks[i + 1]
        else:
            nxt = ""

        merged = None

        # حالة قرآن: بداية في cur، نهاية في nxt
        if has_unbalanced_quran(cur) and "﴾" in nxt:
            merged = (cur + " " + nxt).strip()
            skip_next = True

        # حالة حديث: بداية في cur، نهاية في nxt
        elif has_unbalanced_arabic_quotes(cur) and "»" in nxt:
            merged = (cur + " " + nxt).strip()
            skip_next = True

        if merged is not None:
            repaired.append(merged)
        else:
            repaired.append(cur)

    return repaired


def build_chunk_record(
    base: Dict[str, Any],
    chunk_text: str,
    chunk_index: int,
    is_index_page: bool,
    max_chars_used: int,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    for k, v in base.items():
        if k == "content":
            continue
        out[k] = v

    out["content"] = chunk_text
    out["chunk_index"] = chunk_index
    out["chunk_size_chars"] = len(chunk_text)
    out["content_normalized"] = normalize_for_embedding(chunk_text)

    if "collection" not in out:
        out["collection"] = "seerah_passages"

    out["is_index_page"] = is_index_page
    out["max_chars_used"] = max_chars_used

    # Flags for remaining issues (for debugging/evaluation)
    out["has_unbalanced_quran"] = has_unbalanced_quran(chunk_text)
    out["has_unbalanced_arabic_quotes"] = has_unbalanced_arabic_quotes(chunk_text)

    return out


# ---------- Main pipeline ----------

def process_file(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    total_raw = 0
    total_chunks = 0

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    with input_path.open("r", encoding="utf-8") as fin, \
         output_path.open("w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                base = json.loads(line)
            except json.JSONDecodeError:
                continue

            content = base.get("content", "")
            if not content or not content.strip():
                continue

            total_raw += 1

            section_title = base.get("section_title", "") or ""
            is_index = detect_index_page(section_title, content)
            max_chars = choose_max_chars(section_title)

            sentences = split_arabic_sentences(content)
            if not sentences:
                continue

            # 1) chunk on sentences and max_chars
            chunks = chunk_sentences(sentences, max_chars=max_chars)

            # 2) repair simple broken spans across adjacent chunks
            chunks = repair_broken_spans(chunks)

            # 3) optionally: merge very small trailing chunk with previous
            MIN_CHUNK_CHARS = 250
            merged_chunks: List[str] = []
            for ch in chunks:
                if merged_chunks and len(ch) < MIN_CHUNK_CHARS:
                    merged_chunks[-1] = (merged_chunks[-1] + " " + ch).strip()
                else:
                    merged_chunks.append(ch)
            chunks = merged_chunks

            # 4) write final records
            for idx, chunk_text in enumerate(chunks):
                record = build_chunk_record(
                    base,
                    chunk_text,
                    idx,
                    is_index_page=is_index,
                    max_chars_used=max_chars,
                )
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1

    print(f"Processed raw passages: {total_raw}")
    print(f"Generated chunks: {total_chunks}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    process_file()
