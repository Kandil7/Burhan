#!/usr/bin/env python3
"""
Complete Data Ingestion Pipeline for Burhan Islamic QA System.

Processes:
1. Extracted Islamic books with metadata (categories, authors)
2. Sanadset 368K Hadith Narrators data
3. Generates chunks for RAG pipeline
4. Prepares for embedding generation

Usage:
    python scripts/complete_ingestion.py --books 100 --hadith 1000
"""
import os
import sys
import json
import re
import csv
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
BOOKS_DIR = DATASETS_DIR / "data" / "extracted_books"
METADATA_DIR = DATASETS_DIR / "data" / "metadata"
SANADSET_DIR = DATASETS_DIR / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Chunking parameters
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_metadata() -> Dict:
    """Load book metadata (categories, authors, books)."""
    metadata = {
        "categories": {},
        "authors": [],
        "books": []
    }
    
    # Load categories
    categories_file = METADATA_DIR / "categories.json"
    if categories_file.exists():
        with open(categories_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata["categories"] = {cat["id"]: cat["name"] for cat in data.get("categories", [])}
    
    # Load books metadata
    books_file = METADATA_DIR / "books.json"
    if books_file.exists():
        with open(books_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata["books"] = data.get("books", [])
    
    print(f"  ✓ Loaded {len(metadata['categories'])} categories")
    print(f"  ✓ Loaded {len(metadata['books'])} book records")
    
    return metadata


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks respecting paragraph boundaries."""
    result_chunks = []
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk = ""
    
    for para in paragraphs:
        if len(para) < 20:  # Skip very short paragraphs
            continue
        
        if len(current_chunk) + len(para) > chunk_size:
            if current_chunk:
                result_chunks.append(current_chunk.strip())
            
            if len(para) > chunk_size:
                # Split long paragraph by sentences
                sentences = re.split(r'[.!?،۔]+', para)
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) > chunk_size:
                        if current_chunk:
                            result_chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk.strip():
        result_chunks.append(current_chunk.strip())
    
    return result_chunks


def get_category_from_filename(filename: str, metadata: Dict) -> str:
    """Guess category from filename or book title."""
    # Map common keywords to categories
    keyword_map = {
        "فقه": "الفقه العام",
        "حديث": "كتب السنة",
        "تفسير": "التفسير",
        "سيرة": "السيرة النبوية",
        "تاريخ": "التاريخ",
        "عقيدة": "العقيدة",
        "أصول": "أصول الفقه",
        "حديث": "علوم الحديث",
        "أدب": "الأدب",
        "لغة": "كتب اللغة",
    }
    
    for keyword, category in keyword_map.items():
        if keyword in filename:
            return category
    
    return "كتب عامة"


def process_books(limit: int = 100) -> List[Dict]:
    """Process Islamic books into chunks with metadata."""
    print("\n" + "="*60)
    print("PROCESSING ISLAMIC BOOKS")
    print("="*60 + "\n")
    
    # Load metadata
    metadata = load_metadata()
    
    # Get book files
    book_files = sorted([f for f in BOOKS_DIR.glob("*.txt") if f.name != "file_list.txt" and f.name != "extraction_state.json"])
    
    if not book_files:
        print("  ✗ No book files found!")
        return []
    
    books_to_process = book_files[:limit]
    print(f"\n  📚 Processing {len(books_to_process)} books (limit: {limit})...\n")
    
    all_chunks = []
    processed_count = 0
    total_chunks = 0
    
    for i, book_file in enumerate(books_to_process, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(books_to_process)} books ({total_chunks} chunks)")
        
        try:
            # Read book content
            with open(book_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Extract metadata from filename
            filename_parts = book_file.stem.split("_", 1)
            book_id = filename_parts[0] if len(filename_parts) > 0 else ""
            book_name = filename_parts[1].replace("_", " ") if len(filename_parts) > 1 else book_file.stem
            
            # Determine category
            category = get_category_from_filename(book_file.name, metadata)
            
            # Clean text (remove page markers, footnotes)
            content_lines = []
            for line in text.split('\n'):
                if re.match(r'\[Page \d+\]', line.strip()):
                    continue
                if line.strip().startswith('[Footnotes]:'):
                    continue
                content_lines.append(line)
            
            cleaned_text = '\n'.join(content_lines)
            
            # Chunk the text
            chunks = chunk_text(cleaned_text)
            
            # Create chunk documents
            for j, chunk_content in enumerate(chunks):
                if len(chunk_content) < 100:
                    continue
                
                chunk_doc = {
                    "chunk_index": j,
                    "content": chunk_content[:1000],
                    "metadata": {
                        "source": book_name,
                        "book_id": book_id,
                        "filename": book_file.name,
                        "type": "islamic_book",
                        "category": category,
                        "language": "ar",
                        "chunk_size": len(chunk_content),
                        "dataset": "extracted_books"
                    }
                }
                all_chunks.append(chunk_doc)
            
            total_chunks += len(chunks)
            processed_count += 1
            
        except Exception as e:
            print(f"  ⚠ Error processing {book_file.name}: {e}")
    
    print(f"\n  ✓ Books processed: {processed_count}/{len(books_to_process)}")
    print(f"  ✓ Total chunks: {len(all_chunks)}")
    
    return all_chunks


def process_hadith_data(limit: int = 1000) -> List[Dict]:
    """Process Sanadset hadith data."""
    print("\n" + "="*60)
    print("PROCESSING HADITH DATA (Sanadset)")
    print("="*60 + "\n")
    
    sanadset_file = SANADSET_DIR / "sanadset.csv"
    
    if not sanadset_file.exists():
        print(f"  ⚠ Sanadset file not found: {sanadset_file}")
        return []
    
    print(f"  📖 Reading hadith data from Sanadset...")
    
    hadith_chunks = []
    processed_count = 0
    
    try:
        with open(sanadset_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                
                # Extract hadith text (Matn)
                matn = row.get('Matn', '').strip()
                sanad = row.get('Sanad', '').strip()
                book = row.get('Book', '').strip()
                
                # Skip if no content
                if not matn and not sanad:
                    continue
                
                # Create chunk
                content = matn
                if sanad and sanad != "No SANAD":
                    content = f"السند: {sanad}\n\nالمتن: {matn}"
                
                chunk_doc = {
                    "chunk_index": processed_count,
                    "content": content[:1000],
                    "metadata": {
                        "source": book if book else "Sanadset",
                        "type": "hadith",
                        "language": "ar",
                        "has_sanad": sanad != "No SANAD",
                        "sanad_length": int(row.get('Sanad_Length', 0)),
                        "dataset": "sanadset_368k"
                    }
                }
                
                hadith_chunks.append(chunk_doc)
                processed_count += 1
                
                if processed_count % 200 == 0:
                    print(f"  Progress: {processed_count} hadith processed")
    
    except Exception as e:
        print(f"  ⚠ Error reading Sanadset: {e}")
    
    print(f"\n  ✓ Hadith processed: {processed_count}")
    
    return hadith_chunks


def save_chunks(book_chunks: List[Dict], hadith_chunks: List[Dict]):
    """Save all chunks to files."""
    print("\n" + "="*60)
    print("SAVING PROCESSED DATA")
    print("="*60 + "\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save book chunks
    if book_chunks:
        books_file = OUTPUT_DIR / "islamic_books_chunks.json"
        with open(books_file, 'w', encoding='utf-8') as f:
            json.dump(book_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Saved {len(book_chunks)} book chunks")
        print(f"    File: {books_file}")
        print(f"    Size: {books_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Save hadith chunks
    if hadith_chunks:
        hadith_file = OUTPUT_DIR / "hadith_chunks.json"
        with open(hadith_file, 'w', encoding='utf-8') as f:
            json.dump(hadith_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"\n  ✓ Saved {len(hadith_chunks)} hadith chunks")
        print(f"    File: {hadith_file}")
        print(f"    Size: {hadith_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Create combined dataset
    all_chunks = book_chunks + hadith_chunks
    if all_chunks:
        combined_file = OUTPUT_DIR / "all_chunks.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"\n  ✓ Combined dataset: {len(all_chunks)} chunks")
        print(f"    File: {combined_file}")
        print(f"    Size: {combined_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Print statistics
    print(f"\n{'='*60}")
    print("DATA STATISTICS")
    print(f"{'='*60}\n")
    
    # Category breakdown
    categories = {}
    for chunk in all_chunks:
        cat = chunk["metadata"].get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("  Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    • {cat}: {count}")
    
    # Dataset breakdown
    datasets = {}
    for chunk in all_chunks:
        ds = chunk["metadata"].get("dataset", "unknown")
        datasets[ds] = datasets.get(ds, 0) + 1
    
    print(f"\n  Datasets:")
    for ds, count in datasets.items():
        print(f"    • {ds}: {count}")
    
    print(f"\n{'='*60}")
    print("✓ INGESTION COMPLETE!")
    print(f"{'='*60}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Data Ingestion")
    parser.add_argument("--books", type=int, default=100, help="Number of books to process")
    parser.add_argument("--hadith", type=int, default=1000, help="Number of hadith to process")
    args = parser.parse_args()
    
    print_header("🕌 Burhan ISLAMIC QA SYSTEM - COMPLETE DATA INGESTION")
    
    print(f"\n{Colors.BOLD}This script will:{Colors.ENDC}")
    print(f"  1. Process {args.books} Islamic books with metadata")
    print(f"  2. Ingest {args.hadith} hadith from Sanadset 368K")
    print(f"  3. Generate chunks for RAG pipeline")
    print(f"  4. Save processed data for embedding generation\n")
    
    # Process books
    book_chunks = process_books(args.books)
    
    # Process hadith
    hadith_chunks = process_hadith_data(args.hadith)
    
    # Save everything
    save_chunks(book_chunks, hadith_chunks)
    
    # Next steps
    print(f"\n{Colors.GREEN}{Colors.BOLD}Next Steps:{Colors.ENDC}\n")
    print(f"  1. Start Docker services (if not already running):")
    print(f"     docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant\n")
    print(f"  2. Install dependencies:")
    print(f"     pip install -e .\n")
    print(f"  3. Start the API:")
    print(f"     uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000\n")
    print(f"  4. Test the API:")
    print(f"     python scripts/test_api.py\n")
    print(f"  5. (Optional) Generate embeddings:")
    print(f"     python scripts/generate_embeddings.py --limit {len(book_chunks) + len(hadith_chunks)}\n")


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
