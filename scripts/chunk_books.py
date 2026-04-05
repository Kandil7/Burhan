#!/usr/bin/env python3
"""
Process and chunk extracted Islamic books for RAG pipeline.

Reads raw text files from datasets/data/extracted_books/,
chunks them into passages, and saves for embedding generation.

Usage:
    python scripts/chunk_books.py --limit 50  # Process first 50 books
    python scripts/chunk_books.py --all       # Process all books
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
BOOKS_DIR = PROJECT_ROOT / "datasets" / "data" / "extracted_books"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 50  # characters


def extract_book_metadata(text: str, filename: str) -> Dict:
    """Extract metadata from book text."""
    lines = text.split('\n')
    
    metadata = {
        "filename": filename,
        "book_name": "",
        "book_id": "",
    }
    
    # Extract book ID and name from first lines
    for line in lines[:5]:
        if line.startswith("Book ID:"):
            metadata["book_id"] = line.replace("Book ID:", "").strip()
        elif line.startswith("Book Name:"):
            metadata["book_name"] = line.replace("Book Name:", "").strip()
    
    return metadata


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.
    Respects paragraph boundaries when possible.
    """
    result_chunks = []
    
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk = ""
    
    for para in paragraphs:
        # Skip very short paragraphs (footnotes markers, etc.)
        if len(para) < 20:
            continue
        
        # If adding this paragraph exceeds chunk size
        if len(current_chunk) + len(para) > chunk_size:
            # Save current chunk if not empty
            if current_chunk:
                result_chunks.append(current_chunk.strip())
            
            # If paragraph itself is too long, split it
            if len(para) > chunk_size:
                # Split by sentences
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
    
    # Don't forget the last chunk
    if current_chunk.strip():
        result_chunks.append(current_chunk.strip())
    
    return result_chunks


def process_book(filepath: Path) -> List[Dict]:
    """Process a single book file into chunks."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"  ⚠ Error reading {filepath.name}: {e}")
        return []
    
    # Extract metadata
    metadata = extract_book_metadata(text, filepath.name)
    
    # Clean text - remove page markers, footnotes headers
    # Keep actual content
    content_lines = []
    for line in text.split('\n'):
        # Skip page markers like [Page X]
        if re.match(r'\[Page \d+\]', line.strip()):
            continue
        # Skip footnote markers
        if line.strip().startswith('[Footnotes]:'):
            continue
        content_lines.append(line)
    
    cleaned_text = '\n'.join(content_lines)
    
    # Chunk the text
    text_chunks = chunk_text(cleaned_text)
    
    # Create chunk documents
    chunk_docs = []
    for i, chunk_content in enumerate(text_chunks):
        # Skip very small chunks
        if len(chunk_content) < 100:
            continue
        
        chunk_doc = {
            "chunk_index": i,
            "content": chunk_content[:1000],  # Limit chunk size
            "metadata": {
                "source": metadata.get("book_name", filepath.name),
                "book_id": metadata.get("book_id", ""),
                "filename": metadata.get("filename", ""),
                "type": "fiqh_book",
                "language": "ar",
                "chunk_size": len(chunk_content),
            }
        }
        chunk_docs.append(chunk_doc)
    
    return chunk_docs


def main():
    """Main processing function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chunk Islamic Books")
    parser.add_argument("--limit", type=int, default=100, help="Number of books to process")
    parser.add_argument("--all", action="store_true", help="Process all books")
    args = parser.parse_args()
    
    # Check if books directory exists
    if not BOOKS_DIR.exists():
        print(f"❌ Books directory not found: {BOOKS_DIR}")
        return
    
    # Get list of book files
    book_files = sorted([f for f in BOOKS_DIR.glob("*.txt")])
    
    if not book_files:
        print("❌ No book files found!")
        return
    
    # Determine how many to process
    if args.all:
        books_to_process = book_files
        print(f"📚 Processing ALL {len(books_to_process)} books...")
    else:
        books_to_process = book_files[:args.limit]
        print(f"📚 Processing {len(books_to_process)} books (limit: {args.limit})...")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process books
    all_chunks = []
    processed_count = 0
    error_count = 0
    
    print("\n" + "="*60)
    print("Processing Books")
    print("="*60 + "\n")
    
    for i, book_file in enumerate(books_to_process, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(books_to_process)} books")
        
        chunks = process_book(book_file)
        
        if chunks:
            all_chunks.extend(chunks)
            processed_count += 1
        else:
            error_count += 1
    
    # Save chunks
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}\n")
    print(f"  ✓ Books processed: {processed_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"  ✓ Total chunks: {len(all_chunks)}")
    
    if all_chunks:
        # Save to file
        output_file = OUTPUT_DIR / "extracted_books_chunks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"\n  💾 Saved to: {output_file}")
        print(f"  📊 File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Print sample
        print(f"\n  📖 Sample chunk:")
        print(f"  {'─'*60}")
        sample = all_chunks[0]
        print(f"  Content: {sample['content'][:200]}...")
        print(f"  Source: {sample['metadata']['source']}")
        print(f"  Language: {sample['metadata']['language']}")
        print(f"  {'─'*60}")
    else:
        print("\n  ⚠ No chunks generated!")
    
    print(f"\n{'='*60}")
    print("✓ Processing Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
