#!/usr/bin/env python3
"""
Extracted Books Ingestion Script for Burhan Islamic QA system.

Processes thousands of Islamic books from datasets/data/extracted_books/
and prepares them for RAG pipeline ingestion.

Book categories include:
- Fiqh (Islamic jurisprudence)
- Quranic sciences
- Hadith collections
- Islamic history
- Aqeedah (theology)
- Arabic literature

Usage:
    python scripts/ingest_extracted_books.py --scan (scan books only)
    python scripts/ingest_extracted_books.py --process (process all books)
    python scripts/ingest_extracted_books.py --limit 100 (process first 100)
"""
import argparse
import json
from pathlib import Path
from typing import Optional

from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

BOOKS_DIR = Path(__file__).parent.parent / "datasets" / "data" / "extracted_books"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed" / "extracted_books"


def scan_books(books_dir: Path = BOOKS_DIR) -> dict:
    """
    Scan extracted books and categorize them.
    
    Args:
        books_dir: Path to extracted books directory
        
    Returns:
        Statistics dict with book counts by category
    """
    if not books_dir.exists():
        logger.error("books.directory_not_found", path=str(books_dir))
        return {}
    
    # Get all text files
    text_files = list(books_dir.glob("*.txt"))
    
    stats = {
        "total_books": len(text_files),
        "categories": {},
        "sample_books": []
    }
    
    # Categorize by keywords in filenames
    categories = {
        "fiqh": ["فقه", "فوائد", "أحكام", "حلال", "حرام"],
        "quran": ["قرآن", "القرآن", "تفسير", "سور", "آيات"],
        "hadith": ["حديث", "أحاديث", "صحيح", "سنن", "مسند"],
        "history": ["تاريخ", "سيرة", "وفيات", "أعلام"],
        "aqeedah": ["عقيدة", "توحيد", "أصول", "دين"],
        "literature": ["أدب", "شعر", "نثر", "بلاغ"],
        "other": []
    }
    
    for book_file in text_files[:20]:  # Sample first 20
        filename = book_file.name
        file_size = book_file.stat().st_size
        
        # Read first 200 chars to analyze
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                preview = f.read(200)
        except Exception as e:
            logger.warning("books.read_error", file=filename, error=str(e))
            preview = ""
        
        # Determine category
        book_category = "other"
        for category, keywords in categories.items():
            if any(kw in filename for kw in keywords):
                book_category = category
                categories[category].append(filename)
                break
        
        if book_category not in stats["categories"]:
            stats["categories"][book_category] = 0
        stats["categories"][book_category] += 1
        
        stats["sample_books"].append({
            "filename": filename,
            "size_bytes": file_size,
            "category": book_category,
            "preview": preview[:100]
        })
    
    logger.info("books.scan_complete", **stats)
    return stats


def process_book(book_file: Path, output_dir: Path = OUTPUT_DIR) -> Optional[dict]:
    """
    Process a single book file into RAG-ready chunks.
    
    Args:
        book_file: Path to book text file
        output_dir: Output directory for processed data
        
    Returns:
        Processed book metadata or None on error
    """
    try:
        # Read book content
        with open(book_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata from filename
        filename = book_file.name
        book_id = filename.split("_")[0] if "_" in filename else "unknown"
        title = filename.replace(f"{book_id}_", "").replace(".txt", "") if "_" in filename else filename.replace(".txt", "")
        
        # Split into chunks (simple paragraph-based for now)
        paragraphs = content.split("\n\n")
        chunks = []
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) < 50:  # Skip very short paragraphs
                continue
            
            chunk = {
                "book_id": book_id,
                "title": title,
                "chunk_index": i,
                "content": para[:1000],  # Limit chunk size
                "metadata": {
                    "source": "extracted_books",
                    "category": detect_category(title),
                    "language": "ar"
                }
            }
            chunks.append(chunk)
        
        # Save processed chunks
        output_file = output_dir / f"{book_id}_chunks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(
            "books.book_processed",
            book=title,
            chunks=len(chunks),
            output=str(output_file)
        )
        
        return {
            "book_id": book_id,
            "title": title,
            "chunks": len(chunks),
            "output_file": str(output_file)
        }
        
    except Exception as e:
        logger.error("books.process_error", book=book_file.name, error=str(e))
        return None


def detect_category(title: str) -> str:
    """Detect book category from title."""
    categories = {
        "fiqh": ["فقه", "أحكام", "حلال", "حرام", "صلاة", "زكاة", "صيام"],
        "quran": ["قرآن", "تفسير", "سور", "آيات", "قراءات"],
        "hadith": ["حديث", "صحيح", "سنن", "مسند", "أحاديث"],
        "history": ["تاريخ", "سيرة", "وفيات", "أعلام", "دول"],
        "aqeedah": ["عقيدة", "توحيد", "أصول", "إيمان"],
        "literature": ["أدب", "شعر", "نثر", "بلاغ"]
    }
    
    for category, keywords in categories.items():
        if any(kw in title for kw in keywords):
            return category
    
    return "other"


def process_all_books(limit: Optional[int] = None):
    """
    Process all extracted books.
    
    Args:
        limit: Maximum number of books to process (None for all)
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all text files
    text_files = sorted(BOOKS_DIR.glob("*.txt"))
    if limit:
        text_files = text_files[:limit]
    
    logger.info("books.processing_started", total_books=len(text_files))
    
    results = []
    for i, book_file in enumerate(text_files, 1):
        result = process_book(book_file)
        if result:
            results.append(result)
        
        # Progress logging every 100 books
        if i % 100 == 0:
            logger.info("books.progress", processed=i, total=len(text_files))
    
    # Save summary
    summary_file = OUTPUT_DIR / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_processed": len(results),
            "books": results
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(
        "books.processing_complete",
        total=len(results),
        summary=str(summary_file)
    )
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ingest Extracted Books")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan books only (don't process)"
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process all books"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of books to process"
    )
    
    args = parser.parse_args()
    
    if args.scan:
        stats = scan_books()
        print(f"\n📚 Books Scan Results:")
        print(f"   Total books: {stats.get('total_books', 0)}")
        print(f"   Categories: {stats.get('categories', {})}")
        print(f"\n📝 Sample books:")
        for book in stats.get('sample_books', [])[:5]:
            print(f"   - {book['filename']} ({book['category']}, {book['size_bytes']:,} bytes)")
    
    elif args.process:
        results = process_all_books(args.limit)
        print(f"\n✅ Processed {len(results)} books")
        print(f"📂 Output: {OUTPUT_DIR}")
    
    else:
        # Default: scan then ask
        stats = scan_books()
        print(f"\n📚 Found {stats.get('total_books', 0)} books")
        print(f"   Run with --process to ingest, or --scan for details")


if __name__ == "__main__":
    main()
