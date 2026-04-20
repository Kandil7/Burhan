import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re
import statistics as stats

INPUT_PATH = Path("data/mini_dataset_v2/seerah_chunks_v3.jsonl")  # seerah_chunks_v2.jsonl


def analyze_file(path: Path) -> None:
    sizes: List[int] = []
    sizes_non_index: List[int] = []
    per_book_counts: Dict[str, int] = {}
    per_section_counts: Dict[Tuple[int, str], int] = {}
    index_pages = 0
    total = 0

    # check for potentially broken Quran/Hadith spans
    broken_quran_like = 0
    broken_arabic_quotes = 0

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec: Dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1
            content: str = rec.get("content", "") or ""
            size = len(content)
            sizes.append(size)

            if rec.get("is_index_page"):
                index_pages += 1
            else:
                sizes_non_index.append(size)

            book = rec.get("book_title", "UNKNOWN")
            per_book_counts[book] = per_book_counts.get(book, 0) + 1

            key = (rec.get("book_id", -1), rec.get("section_title", ""))
            per_section_counts[key] = per_section_counts.get(key, 0) + 1

            # broken Quran-like spans: ﴿ without ﴾
            if "﴿" in content and "﴾" not in content:
                broken_quran_like += 1

            # broken Arabic quotes: « without » or » without «
            if "«" in content and "»" not in content:
                broken_arabic_quotes += 1
            if "»" in content and "«" not in content:
                broken_arabic_quotes += 1

    print("=== Global Stats ===")
    print(f"Total chunks: {total}")
    print(f"Index-page chunks: {index_pages}")
    print(f"Non-index chunks: {total - index_pages}")
    if sizes:
        print(f"Chunk size (chars) - min: {min(sizes)}, max: {max(sizes)}, mean: {stats.mean(sizes):.1f}")
    if sizes_non_index:
        print(
            f"Non-index size - min: {min(sizes_non_index)}, "
            f"max: {max(sizes_non_index)}, mean: {stats.mean(sizes_non_index):.1f}"
        )

    print("\n=== Per Book (top 10) ===")
    for book, cnt in sorted(per_book_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{book}: {cnt} chunks")

    print("\n=== Sections with many chunks (top 10) ===")
    for (book_id, section), cnt in sorted(per_section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"[book_id={book_id}] {section}: {cnt} chunks")

    print("\n=== Potentially Broken Spans ===")
    print(f"Chunks with Quran-like start without end (﴿ ... no ﴾): {broken_quran_like}")
    print(f"Chunks with mismatched Arabic quotes (« or » alone): {broken_arabic_quotes}")


if __name__ == "__main__":
    analyze_file(INPUT_PATH)