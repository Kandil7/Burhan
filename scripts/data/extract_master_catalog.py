#!/usr/bin/env python3
"""
Extract master catalog from master.db.

This is the COMPLETE book catalog with:
- 8,425 books with full metadata
- 41 categories
- 3,146 authors with death years
- Cross-references to Lucene indexes

Usage:
    python scripts/extract_master_catalog.py

Output:
    data/processed/master_catalog.json - Complete book list
    data/processed/category_mapping.json - 41→11 collection mapping
    data/processed/author_catalog.json - Author list with death years
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from scripts.utils import setup_script_logger, get_project_root, get_datasets_dir

# Configuration
logger = setup_script_logger("extract_master_catalog")
PROJECT_ROOT = get_project_root()
DATASETS_DIR = get_datasets_dir()
MASTER_DB = DATASETS_DIR / "system_book_datasets" / "master.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Category mapping: 41 Shamela categories → 11 RAG collections
CATEGORY_TO_COLLECTION = {
    # Fiqh collections
    "الفقه الحنبلي": "fiqh_passages",
    "الفقه الشافعي": "fiqh_passages",
    "الفقه المالكي": "fiqh_passages",
    "الفقه الحنفي": "fiqh_passages",
    "الفقه العام": "fiqh_passages",
    "مسائل فقهية": "fiqh_passages",
    "أصول الفقه": "usul_fiqh",
    "القواعد الفقهية": "usul_fiqh",
    "الفقه المقارن": "fiqh_passages",
    
    # Hadith collections
    "كتب السنة": "hadith_passages",
    "علوم الحديث": "hadith_passages",
    "شروح الحديث": "hadith_passages",
    "أطراف الحديث": "hadith_passages",
    "علل الحديث": "hadith_passages",
    "الجوامع": "hadith_passages",
    "الأربعيات": "hadith_passages",
    
    # Quran & Tafsir
    "التفسير": "quran_tafsir",
    "علوم القرآن وأصول التفسير": "quran_tafsir",
    "التفسير الموضوعي": "quran_tafsir",
    "غريب القرآن": "quran_tafsir",
    "ناسخ ومنسوخ": "quran_tafsir",
    "إعراب القرآن": "quran_tafsir",
    
    # Aqeedah
    "العقيدة": "aqeedah_passages",
    "الفرق والردود": "aqeedah_passages",
    "التوحيد": "aqeedah_passages",
    
    # Seerah & History
    "السيرة النبوية": "seerah_passages",
    "التاريخ": "islamic_history_passages",
    "التراجم والطبقات": "islamic_history_passages",
    "الأنساب": "islamic_history_passages",
    
    # Arabic Language
    "النحو والصرف": "arabic_language_passages",
    "اللغة": "arabic_language_passages",
    "البلاغة": "arabic_language_passages",
    "العروض": "arabic_language_passages",
    "القوافي": "arabic_language_passages",
    "الشعر": "arabic_language_passages",
    "الأدب": "arabic_language_passages",
    "الخطابة": "arabic_language_passages",
    "الأمثال": "arabic_language_passages",
    "المعاجم": "arabic_language_passages",
    
    # Spirituality
    "الرقائق والآداب والأذكار": "spirituality_passages",
    "الزهد": "spirituality_passages",
    "الأدعية والأذكار": "spirituality_passages",
    "السلوك": "spirituality_passages",
    "الرقائق": "spirituality_passages",
    
    # General
    "كتب عامة": "general_islamic",
    "فهارس": "general_islamic",
    "رسائل جامعية": "general_islamic",
    "مجلات": "general_islamic",
    "متون": "general_islamic",
    "الثقافة الإسلامية": "general_islamic",
    
    # Medicine & Science
    "الطب": "general_islamic",
    "البيطرة": "general_islamic",
    "النبات": "general_islamic",
    "الرياضيات": "general_islamic",
    "الفلك": "general_islamic",
}

COLLECTION_INFO = {
    "fiqh_passages": {
        "name_ar": "الفقه الإسلامي",
        "name_en": "Islamic Jurisprudence",
        "description": "Islamic law, rulings, and jurisprudence across all schools"
    },
    "usul_fiqh": {
        "name_ar": "أصول الفقه",
        "name_en": "Principles of Jurisprudence",
        "description": "Methodology and principles of Islamic legal reasoning"
    },
    "hadith_passages": {
        "name_ar": "الحديث الشريف",
        "name_en": "Prophetic Traditions",
        "description": "Hadith collections, sciences, and commentaries"
    },
    "quran_tafsir": {
        "name_ar": "القرآن والتفسير",
        "name_en": "Quran & Tafsir",
        "description": "Quranic exegesis and Quran sciences"
    },
    "aqeedah_passages": {
        "name_ar": "العقيدة الإسلامية",
        "name_en": "Islamic Creed",
        "description": "Islamic theology, beliefs, and creed"
    },
    "seerah_passages": {
        "name_ar": "السيرة النبوية",
        "name_en": "Prophetic Biography",
        "description": "Life and biography of Prophet Muhammad (PBUH)"
    },
    "islamic_history_passages": {
        "name_ar": "التاريخ الإسلامي",
        "name_en": "Islamic History",
        "description": "Islamic civilization, history, and biographical works"
    },
    "arabic_language_passages": {
        "name_ar": "اللغة العربية",
        "name_en": "Arabic Language",
        "description": "Arabic grammar, morphology, rhetoric, and literature"
    },
    "spirituality_passages": {
        "name_ar": "الروحانيات والآداب",
        "name_en": "Spirituality & Ethics",
        "description": "Islamic spirituality, ethics, and devotional practices"
    },
    "general_islamic": {
        "name_ar": "معارف إسلامية عامة",
        "name_en": "General Islamic Knowledge",
        "description": "General Islamic knowledge, culture, and contemporary issues"
    }
}


def extract_master_catalog() -> Dict[str, Any]:
    """
    Extract complete book catalog from master.db.
    
    Returns:
        Dictionary with books, categories, and authors
    """
    logger.info(f"Extracting master catalog from {MASTER_DB}")
    
    if not MASTER_DB.exists():
        logger.error(f"Master database not found: {MASTER_DB}")
        return None
    
    conn = sqlite3.connect(str(MASTER_DB))
    conn.row_factory = sqlite3.Row
    
    # Extract all books with category and author
    query = """
    SELECT 
        b.book_id,
        b.book_name as title,
        b.book_category,
        c.category_name,
        ab.author_id,
        a.author_name,
        a.death_number as author_death,
        b.printed,
        b.group_id,
        b.pdf_links,
        b.meta_data
    FROM book b
    LEFT JOIN category c ON b.book_category = c.category_id
    LEFT JOIN author_book ab ON b.book_id = ab.book_id
    LEFT JOIN author a ON ab.author_id = a.author_id
    ORDER BY b.book_id
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    
    books = []
    for row in cursor.fetchall():
        book = {
            "book_id": row["book_id"],
            "title": row["title"],
            "category_id": row["book_category"],
            "category_name": row["category_name"],
            "author_id": row["author_id"],
            "author_name": row["author_name"],
            "author_death": row["author_death"],
            "printed": bool(row["printed"]),
            "group_id": row["group_id"],
        }
        
        # Parse JSON fields if available
        if row["pdf_links"]:
            try:
                book["pdf_links"] = json.loads(row["pdf_links"])
            except:
                book["pdf_links"] = None
        
        if row["meta_data"]:
            try:
                book["meta_data"] = json.loads(row["meta_data"])
            except:
                book["meta_data"] = None
        
        # Add collection mapping
        collection = CATEGORY_TO_COLLECTION.get(row["category_name"], "general_islamic")
        book["collection"] = collection
        
        books.append(book)
    
    # Extract all categories
    cursor.execute("SELECT * FROM category ORDER BY category_id")
    categories = [dict(row) for row in cursor.fetchall()]
    
    # Extract all authors
    cursor.execute("SELECT author_id, author_name, death_number, death_text, alpha FROM author ORDER BY author_id")
    authors = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    catalog = {
        "books": books,
        "categories": categories,
        "authors": authors,
        "metadata": {
            "total_books": len(books),
            "total_categories": len(categories),
            "total_authors": len(authors),
            "collections": COLLECTION_INFO,
        }
    }
    
    logger.info(f"Extraction complete: {len(books)} books, {len(categories)} categories, {len(authors)} authors")
    
    return catalog


def create_category_mapping(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create category mapping from 41 Shamela categories to 11 RAG collections.
    
    Args:
        catalog: Master catalog dictionary
    
    Returns:
        Category mapping dictionary
    """
    logger.info("Creating category mapping")
    
    # Build book_id → collection mapping
    books_mapping = {}
    for book in catalog["books"]:
        books_mapping[str(book["book_id"])] = {
            "title": book["title"],
            "category": book["category_name"],
            "category_id": book["category_id"],
            "collection": book["collection"],
            "author": book["author_name"],
            "author_death": book["author_death"],
        }
    
    # Count books per collection
    collection_counts = {}
    for book in catalog["books"]:
        collection = book["collection"]
        collection_counts[collection] = collection_counts.get(collection, 0) + 1
    
    # Count books per category
    category_counts = {}
    for book in catalog["books"]:
        category = book["category_name"]
        category_counts[category] = category_counts.get(category, 0) + 1
    
    mapping = {
        "books": books_mapping,
        "categories": category_counts,
        "collections": {
            collection: {
                "count": count,
                "info": COLLECTION_INFO.get(collection, {})
            }
            for collection, count in collection_counts.items()
        },
        "metadata": {
            "total_books": len(catalog["books"]),
            "total_categories": len(catalog["categories"]),
            "total_collections": len(collection_counts),
        }
    }
    
    logger.info(f"Category mapping created: {len(collection_counts)} collections, {len(books_mapping)} books")
    
    return mapping


def save_catalog(catalog: Dict[str, Any], category_mapping: Dict[str, Any]):
    """
    Save catalog and mapping to JSON files.
    
    Args:
        catalog: Master catalog dictionary
        category_mapping: Category mapping dictionary
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save master catalog
    catalog_file = OUTPUT_DIR / "master_catalog.json"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Catalog saved to {catalog_file}")
    
    # Save category mapping
    mapping_file = OUTPUT_DIR / "category_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(category_mapping, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Category mapping saved to {mapping_file}")
    
    # Save author catalog
    author_file = OUTPUT_DIR / "author_catalog.json"
    authors = catalog["authors"]
    with open(author_file, 'w', encoding='utf-8') as f:
        json.dump(authors, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Author catalog saved to {author_file}")


def print_summary(catalog: Dict[str, Any], category_mapping: Dict[str, Any]):
    """Print summary statistics."""
    print("\n" + "="*70)
    print("✅ MASTER CATALOG EXTRACTION COMPLETE")
    print("="*70)
    
    print(f"\n📊 Summary:")
    print(f"   Books: {catalog['metadata']['total_books']:,}")
    print(f"   Categories: {catalog['metadata']['total_categories']}")
    print(f"   Authors: {catalog['metadata']['total_authors']:,}")
    
    print(f"\n📁 Collection Distribution:")
    for collection, info in sorted(category_mapping['collections'].items()):
        count = info['count']
        name_en = info['info'].get('name_en', collection)
        print(f"   {name_en:30s}: {count:5,} books")
    
    print(f"\n💾 Files saved to: {OUTPUT_DIR}")
    print(f"   - master_catalog.json")
    print(f"   - category_mapping.json")
    print(f"   - author_catalog.json")


def main():
    """Main extraction function."""
    print("="*70)
    print("🕌 Burhan - EXTRACT MASTER CATALOG")
    print("="*70)
    
    # Step 1: Extract master catalog
    catalog = extract_master_catalog()
    if not catalog:
        logger.error("Extraction failed")
        return
    
    # Step 2: Create category mapping
    category_mapping = create_category_mapping(catalog)
    
    # Step 3: Save to files
    save_catalog(catalog, category_mapping)
    
    # Step 4: Print summary
    print_summary(catalog, category_mapping)


if __name__ == "__main__":
    main()
