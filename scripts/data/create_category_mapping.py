#!/usr/bin/env python3
"""
Create category mapping from books.json.

Maps 40+ Shamela categories to 10 RAG collections:
  - aqeedah (creed)
  - quran_tafsir (Quran & tafsir)
  - hadith (hadith collections & commentary)
  - fiqh (jurisprudence & fatwas)
  - usul_fiqh (principles of jurisprudence)
  - islamic_history (biographies & history)
  - arabic_language (Arabic language sciences)
  - spirituality (spirituality & ethics)
  - seerah (Prophet biography)
  - adab (literature)
  - general_islamic (general Islamic knowledge)

Usage:
    python scripts/create_category_mapping.py

Output:
    data/processed/category_mapping.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path for src imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import (
    ensure_dir,
    get_data_dir,
    get_datasets_dir,
    get_script_logger,
)

# ── Configuration ────────────────────────────────────────────────────────

BOOKS_JSON_PATH = get_datasets_dir("data/metadata/books.json")
OUTPUT_FILE = get_data_dir("processed/category_mapping.json")

logger = get_script_logger("category-mapping")

# Category → Collection mapping (complete - all 40+ categories)
CATEGORY_TO_COLLECTION: dict[str, str] = {
    # Aqeedah (creed)
    "العقيدة": "aqeedah",
    "الفرق والردود": "aqeedah",

    # Quran & Tafsir
    "التفسير": "quran_tafsir",
    "علوم القرآن وأصول التفسير": "quran_tafsir",
    "التجويد والقراءات": "quran_tafsir",

    # Hadith
    "كتب السنة": "hadith",
    "الجوامع": "hadith",
    "شروح الحديث": "hadith",
    "علوم الحديث": "hadith",
    "التخريج والأطراف": "hadith",
    "العلل والسؤلات الحديثية": "hadith",

    # Fiqh
    "الفقه العام": "fiqh",
    "الفقه الحنفي": "fiqh",
    "الفقه المالكي": "fiqh",
    "الفقه الشافعي": "fiqh",
    "الفقه الحنبلي": "fiqh",
    "مسائل فقهية": "fiqh",
    "علوم الفقه والقواعد الفقهية": "fiqh",
    "الفتاوى": "fiqh",
    "السياسة الشرعية والقضاء": "fiqh",
    "الفرائض والوصايا": "fiqh",

    # Usul al-Fiqh
    "أصول الفقه": "usul_fiqh",

    # Islamic History
    "التراجم والطبقات": "islamic_history",
    "التاريخ": "islamic_history",
    "الأنساب": "islamic_history",
    "البلدان والرحلات": "islamic_history",

    # Arabic Language
    "كتب اللغة": "arabic_language",
    "النحو والصرف": "arabic_language",
    "البلاغة والنقد": "arabic_language",
    "العروض والقوافي": "arabic_language",
    "المعاجم": "arabic_language",
    "اللغة العربية": "arabic_language",
    "البلاغة": "arabic_language",
    "الغريب والمعاجم": "arabic_language",

    # Spirituality
    "الرقائق والآداب والأذكار": "spirituality",
    "السلوك والآداب": "spirituality",

    # Adab (Literature)
    "الأدب": "adab",
    "الدواوين الشعرية": "adab",

    # Seerah
    "السير والمناقب": "seerah",
    "السيرة النبوية": "seerah",
    "المغازي": "seerah",
    "الدلائل": "seerah",
    "الشمائل": "seerah",

    # General Islamic
    "كتب عامة": "general_islamic",
    "الردود": "general_islamic",
    "الموسوعات": "general_islamic",
    "كتب مصورة": "general_islamic",
    "برامج الكتب": "general_islamic",
    "مسائل عامة": "general_islamic",
    "الفهرس": "general_islamic",
    "الطب": "general_islamic",
    "المنطق": "general_islamic",
    "علوم أخرى": "general_islamic",
    "فهارس الكتب والأدلة": "general_islamic",
}

# Collection metadata
COLLECTION_INFO: dict[str, dict[str, str]] = {
    "aqeedah": {
        "name_ar": "العقيدة",
        "name_en": "Creed & Theology",
        "description": "Islamic creed, theology, and beliefs",
    },
    "quran_tafsir": {
        "name_ar": "القرآن والتفسير",
        "name_en": "Quran & Tafsir",
        "description": "Quranic exegesis, recitation, and Quranic sciences",
    },
    "hadith": {
        "name_ar": "الحديث",
        "name_en": "Hadith",
        "description": "Prophetic traditions, collections, and commentary",
    },
    "fiqh": {
        "name_ar": "الفقه",
        "name_en": "Jurisprudence",
        "description": "Islamic law, rulings, and fatwas",
    },
    "usul_fiqh": {
        "name_ar": "أصول الفقه",
        "name_en": "Principles of Jurisprudence",
        "description": "Methodology of Islamic legal theory",
    },
    "islamic_history": {
        "name_ar": "التاريخ الإسلامي",
        "name_en": "Islamic History",
        "description": "Islamic history, biographies, and scholarly generations",
    },
    "arabic_language": {
        "name_ar": "اللغة العربية",
        "name_en": "Arabic Language",
        "description": "Arabic grammar, morphology, rhetoric, and lexicography",
    },
    "spirituality": {
        "name_ar": "الرقائق والروحانيات",
        "name_en": "Spirituality & Ethics",
        "description": "Spiritual refinement, ethics, and supplications",
    },
    "adab": {
        "name_ar": "الأدب",
        "name_en": "Literature",
        "description": "Arabic and Islamic literature",
    },
    "seerah": {
        "name_ar": "السيرة النبوية",
        "name_en": "Prophet Biography",
        "description": "Life of Prophet Muhammad (peace be upon him)",
    },
    "general_islamic": {
        "name_ar": "معارف إسلامية عامة",
        "name_en": "General Islamic Knowledge",
        "description": "General Islamic knowledge and reference works",
    },
}


def create_category_mapping() -> dict[str, Any]:
    """
    Create full category mapping from books.json.

    Returns:
        Mapping dict with book_id→category, category→collection, and stats.
    """
    logger.info(f"Loading books from {BOOKS_JSON_PATH}")
    with open(BOOKS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    books = data.get("books", [])
    logger.info(f"Processing {len(books)} books")

    # Build mappings
    book_to_category: dict[int, str] = {}
    book_to_collection: dict[int, str] = {}
    category_stats: dict[str, dict[str, Any]] = {}
    collection_stats: dict[str, dict[str, Any]] = {}

    unmapped_categories: set[str] = set()

    for book in books:
        book_id = book.get("id")
        cat_name = book.get("cat_name", "")
        collection = CATEGORY_TO_COLLECTION.get(cat_name, "general_islamic")

        if cat_name and cat_name not in CATEGORY_TO_COLLECTION:
            unmapped_categories.add(cat_name)

        book_to_category[book_id] = cat_name
        book_to_collection[book_id] = collection

        # Category stats
        if cat_name not in category_stats:
            category_stats[cat_name] = {
                "book_count": 0,
                "collection": collection,
            }
        category_stats[cat_name]["book_count"] += 1

        # Collection stats
        if collection not in collection_stats:
            collection_stats[collection] = {
                "book_count": 0,
                "categories": [],
            }
        collection_stats[collection]["book_count"] += 1
        if cat_name not in collection_stats[collection]["categories"]:
            collection_stats[collection]["categories"].append(cat_name)

    # Build final mapping
    mapping: dict[str, Any] = {
        "version": "1.0",
        "total_books": len(books),
        "total_categories": len(category_stats),
        "total_collections": len(collection_stats),
        # Direct mappings
        "book_id_to_category": book_to_category,
        "book_id_to_collection": book_to_collection,
        # Category → Collection
        "category_to_collection": CATEGORY_TO_COLLECTION,
        # Collection info
        "collection_info": COLLECTION_INFO,
        # Stats
        "category_stats": dict(
            sorted(category_stats.items(), key=lambda x: -x[1]["book_count"])
        ),
        "collection_stats": dict(
            sorted(collection_stats.items(), key=lambda x: -x[1]["book_count"])
        ),
        # Unmapped categories (should be empty if mapping is complete)
        "unmapped_categories": sorted(unmapped_categories),
    }

    return mapping


def print_report(mapping: dict[str, Any]) -> None:
    """Print formatted category mapping report."""
    print("\n" + "=" * 70)
    print("  CATEGORY MAPPING REPORT")
    print("=" * 70)

    print(f"\n  Total books:        {mapping['total_books']}")
    print(f"  Total categories:   {mapping['total_categories']}")
    print(f"  Total collections:  {mapping['total_collections']}")

    print(f"\n  Collection summary:")
    for coll, info in sorted(
        mapping["collection_stats"].items(), key=lambda x: -x[1]["book_count"]
    ):
        coll_info = mapping["collection_info"].get(coll, {})
        name_en = coll_info.get("name_en", coll)
        name_ar = coll_info.get("name_ar", "")
        print(
            f"    {coll:20s} {name_ar:25s} {name_en:30s} "
            f"{info['book_count']:>6,} books ({len(info['categories'])} categories)"
        )

    print(f"\n  Category breakdown:")
    for cat, stats in list(mapping["category_stats"].items())[:15]:
        coll = stats["collection"]
        print(f"    {cat:35s} → {coll:20s} {stats['book_count']:>6,} books")

    unmapped = mapping.get("unmapped_categories", [])
    if unmapped:
        print(f"\n  Unmapped categories ({len(unmapped)}):")
        for cat in unmapped:
            print(f"    - {cat}")
    else:
        print(f"\n  All categories mapped")

    print("\n" + "=" * 70)
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 70)


def main() -> None:
    """CLI entry point."""
    mapping = create_category_mapping()

    # Save
    ensure_dir(OUTPUT_FILE.parent)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved category mapping to {OUTPUT_FILE}")
    print_report(mapping)


if __name__ == "__main__":
    main()
