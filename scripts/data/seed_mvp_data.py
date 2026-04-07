#!/usr/bin/env python3
"""
Complete MVP Data Seeder for Athar Islamic QA System.

Creates sample data for ALL collections from existing datasets:
1. hadith_passages - From Sanadset CSV + existing hadith_chunks.json
2. fiqh_passages - Already has 10K (skip)
3. quran_tafsir - From Quran ayahs in PostgreSQL + sample tafsir
4. aqeedah_passages - From aqeedah books
5. seerah_passages - From seerah books
6. islamic_history_passages - From history/trajim books
7. arabic_language_passages - From Arabic language books
8. general_islamic_passages - From general Islamic books
9. duas_adhkar - Already has 10 (skip)
10. spirituality_passages - From riqaaq/adab books

Each collection gets 200-500 quality samples for MVP functionality.
"""
import asyncio
import json
import csv
import random
import re
import sqlite3
from pathlib import Path
from typing import Optional

# Increase CSV field size limit
csv.field_size_limit(10000000)

import numpy as np
from tqdm import tqdm

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "datasets" / "data"
DATASETS_DIR = BASE_DIR / "datasets"

# Target samples per collection for MVP
TARGET_SAMPLES = {
    "hadith_passages": 500,
    "quran_tafsir": 200,
    "aqeedah_passages": 300,
    "seerah_passages": 300,
    "islamic_history_passages": 300,
    "arabic_language_passages": 300,
    "general_islamic_passages": 300,
    "spirituality_passages": 300,
}


def load_random_lines(filepath: Path, n: int, encoding='utf-8') -> list[str]:
    """Load n random lines from a text file."""
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            lines = [l.strip() for l in f.readlines() if len(l.strip()) > 50]
        if not lines:
            return []
        return random.sample(lines, min(n, len(lines)))
    except Exception as e:
        logger.warning("file_read_error", path=str(filepath), error=str(e))
        return []


def get_books_by_category(cat_name: str, limit: int = 10) -> list[dict]:
    """Get book info by category from books.db"""
    db_path = DATA_DIR / "metadata" / "books.db"
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Try exact match first, then LIKE
    cur.execute("SELECT * FROM books WHERE cat_name = ? OR cat_name LIKE ? LIMIT ?", 
                (cat_name, f"%{cat_name}%", limit))
    books = [dict(r) for r in cur.fetchall()]
    conn.close()
    return books


def extract_chunks_from_book(book_file: Path, num_chunks: int, min_chunk_size: 200, max_chunk_size: 500) -> list[dict]:
    """Extract random chunks from a book file."""
    if not book_file.exists():
        return []
    
    try:
        with open(book_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean content
        content = re.sub(r'\[Page \d+\]', '', content)
        content = re.sub(r'\[Footnotes\].*$', '', content, flags=re.DOTALL)
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > min_chunk_size]
        
        if not paragraphs:
            # Try splitting by single newlines
            paragraphs = [p.strip() for p in content.split('\n') if len(p.strip()) > min_chunk_size]
        
        chunks = []
        selected = random.sample(paragraphs, min(num_chunks, len(paragraphs)))
        
        for para in selected:
            # Truncate if too long
            chunk_text = para[:max_chunk_size]
            if len(chunk_text) > min_chunk_size:
                chunks.append(chunk_text)
        
        return chunks
    except Exception as e:
        logger.warning("book_extract_error", path=str(book_file), error=str(e))
        return []


async def seed_collection(
    collection_name: str,
    documents: list[dict],
    embedding_model: EmbeddingModel,
    vector_store: VectorStore,
    batch_size: int = 32
):
    """Embed and upsert documents to a collection."""
    if not documents:
        logger.info("seed.skip_no_docs", collection=collection_name)
        return 0
    
    logger.info("seed.start", collection=collection_name, count=len(documents))
    
    # Ensure collection exists
    try:
        await vector_store.ensure_collection(collection_name, dimension=embedding_model.DIMENSION)
    except:
        pass  # Collection may already exist
    
    # Disable Redis cache for this seed run (use local cache only)
    embedding_model.cache_enabled = False
    
    # Embed in batches with progress bar
    total_upserted = 0
    pbar = tqdm(total=len(documents), desc=f"Embedding {collection_name}", unit="docs")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        texts = [d["content"] for d in batch]
        
        # Embed
        embeddings = await embedding_model.encode(texts)
        
        # Upsert
        count = await vector_store.upsert(collection_name, batch, embeddings)
        total_upserted += count
        pbar.update(len(batch))
    
    pbar.close()
    logger.info("seed.complete", collection=collection_name, upserted=total_upserted)
    return total_upserted


async def main():
    """Seed all collections with sample data."""
    random.seed(42)  # Reproducible
    
    logger.info("mvp_seed.start", targets=list(TARGET_SAMPLES.keys()))
    
    # Initialize components
    logger.info("mvp_seed.loading_components")
    embedding_model = EmbeddingModel()
    await embedding_model.load_model()
    
    vector_store = VectorStore()
    await vector_store.initialize()
    
    total_embedded = 0
    
    # 1. Hadith from Sanadset CSV
    logger.info("mvp_seed.hadith")
    hadith_docs = []
    sanadset_csv = DATASETS_DIR / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators" / "sanadset.csv"
    
    if sanadset_csv.exists():
        with open(sanadset_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            sample_rows = random.sample(rows, min(TARGET_SAMPLES["hadith_passages"], len(rows)))
            
            for i, row in enumerate(sample_rows):
                sanad = re.sub(r'<[^>]+>', '', row.get('Sanad', '')).strip()
                matn = row.get('Matn', '').strip()
                book = row.get('Book', '')
                
                content_parts = []
                if matn:
                    content_parts.append(matn)
                if sanad and sanad != "No SANAD":
                    content_parts.append(sanad)
                if book:
                    content_parts.append(book)
                
                content = " | ".join(content_parts)[:3000]
                
                hadith_docs.append({
                    "chunk_index": i,
                    "content": content,
                    "metadata": {
                        "type": "hadith",
                        "book": book,
                        "num_hadith": row.get('Num_hadith', ''),
                        "matn": matn[:2000],
                        "sanad": sanad[:1000],
                        "sanad_length": row.get('Sanad_Length', ''),
                        "dataset": "sanadset_368k",
                        "language": "ar",
                    }
                })
        
        count = await seed_collection("hadith_passages", hadith_docs, embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.hadith_done", count=count)
    
    # 2. Quran Ayahs to quran_tafsir
    logger.info("mvp_seed.quran_tafsir")
    quran_docs = []
    try:
        import psycopg2
        db_conn = psycopg2.connect(
            host="localhost",
            database="athar_db",
            user="athar",
            password="athar_password"
        )
        cur = db_conn.cursor()
        
        # Get sample ayahs with translations
        cur.execute("""
            SELECT s.name_ar, s.name_en, a.number_in_surah, a.text_uthmani,
                   t.text as translation, t.language, t.translator
            FROM ayahs a
            JOIN surahs s ON a.surah_id = s.id
            LEFT JOIN translations t ON a.id = t.ayah_id AND t.language = 'en'
            ORDER BY RANDOM()
            LIMIT %s
        """, (TARGET_SAMPLES["quran_tafsir"],))
        
        rows = cur.fetchall()
        for i, row in enumerate(rows):
            content = f"Quran {row[1]} ({row[0]}) {row[2]}: {row[3]}"
            if row[4]:
                content += f"\nTranslation: {row[4]}"
            
            quran_docs.append({
                "chunk_index": i,
                "content": content[:3000],
                "metadata": {
                    "type": "quran_ayah",
                    "surah_name_en": row[1],
                    "surah_name_ar": row[0],
                    "ayah_number": row[2],
                    "translation": row[4] or '',
                    "language": "ar",
                }
            })
        
        cur.close()
        db_conn.close()
        count = await seed_collection("quran_tafsir", quran_docs, embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.quran_tafsir_done", count=count)
    except Exception as e:
        logger.error("mvp_seed.quran_error", error=str(e))
    
    # 3. Aqeedah from books
    logger.info("mvp_seed.aqeedah")
    aqeeda_docs = []
    aqeeda_books = get_books_by_category("العقيدة", limit=20)
    
    for book in aqeeda_books:
        book_id = book.get('book_id') or book.get('short_id', '')
        book_name = book.get('title', '')
        
        # Try to find the extracted book file
        books_dir = DATA_DIR / "extracted_books"
        book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
        
        if not book_files:
            # Try by title match
            book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
        
        for bf in book_files[:2]:
            chunks = extract_chunks_from_book(bf, 15, 200, 500)
            for j, chunk in enumerate(chunks):
                aqeeda_docs.append({
                    "chunk_index": len(aqeeda_docs),
                    "content": chunk[:2000],
                    "metadata": {
                        "type": "aqeedah",
                        "book": book_name,
                        "book_id": book_id,
                        "category": "العقيدة",
                        "language": "ar",
                    }
                })
    
    if aqeeda_docs:
        count = await seed_collection("aqeedah_passages", aqeeda_docs[:TARGET_SAMPLES["aqeedah_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.aqeeda_done", count=count)
    
    # 4. Seerah from books
    logger.info("mvp_seed.seerah")
    seerah_docs = []
    seerah_books = get_books_by_category("السيرة النبوية", limit=20)
    
    for book in seerah_books:
        book_id = book.get('book_id') or book.get('short_id', '')
        book_name = book.get('title', '')
        
        books_dir = DATA_DIR / "extracted_books"
        book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
        
        if not book_files:
            book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
        
        for bf in book_files[:2]:
            chunks = extract_chunks_from_book(bf, 15, 200, 500)
            for j, chunk in enumerate(chunks):
                seerah_docs.append({
                    "chunk_index": len(seerah_docs),
                    "content": chunk[:2000],
                    "metadata": {
                        "type": "seerah",
                        "book": book_name,
                        "book_id": book_id,
                        "category": "السيرة النبوية",
                        "language": "ar",
                    }
                })
    
    if seerah_docs:
        count = await seed_collection("seerah_passages", seerah_docs[:TARGET_SAMPLES["seerah_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.seerah_done", count=count)
    
    # 5. Islamic History from books
    logger.info("mvp_seed.islamic_history")
    history_docs = []
    history_categories = ["التاريخ", "التراجم والطبقات", "البلدان والرحلات"]
    
    for cat in history_categories:
        cat_books = get_books_by_category(cat, limit=15)
        for book in cat_books:
            book_id = book.get('book_id') or book.get('short_id', '')
            book_name = book.get('title', '')
            
            books_dir = DATA_DIR / "extracted_books"
            book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
            
            if not book_files:
                book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
            
            for bf in book_files[:1]:
                chunks = extract_chunks_from_book(bf, 10, 200, 500)
                for j, chunk in enumerate(chunks):
                    history_docs.append({
                        "chunk_index": len(history_docs),
                        "content": chunk[:2000],
                        "metadata": {
                            "type": "islamic_history",
                            "book": book_name,
                            "book_id": book_id,
                            "category": cat,
                            "language": "ar",
                        }
                    })
    
    if history_docs:
        count = await seed_collection("islamic_history_passages", history_docs[:TARGET_SAMPLES["islamic_history_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.history_done", count=count)
    
    # 6. Arabic Language from books
    logger.info("mvp_seed.arabic_language")
    arabic_docs = []
    arabic_categories = ["النحو والصرف", "الأدب", "كتب اللغة", "البلاغة"]
    
    for cat in arabic_categories:
        cat_books = get_books_by_category(cat, limit=15)
        for book in cat_books:
            book_id = book.get('book_id') or book.get('short_id', '')
            book_name = book.get('title', '')
            
            books_dir = DATA_DIR / "extracted_books"
            book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
            
            if not book_files:
                book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
            
            for bf in book_files[:1]:
                chunks = extract_chunks_from_book(bf, 10, 200, 500)
                for j, chunk in enumerate(chunks):
                    arabic_docs.append({
                        "chunk_index": len(arabic_docs),
                        "content": chunk[:2000],
                        "metadata": {
                            "type": "arabic_language",
                            "book": book_name,
                            "book_id": book_id,
                            "category": cat,
                            "language": "ar",
                        }
                    })
    
    if arabic_docs:
        count = await seed_collection("arabic_language_passages", arabic_docs[:TARGET_SAMPLES["arabic_language_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.arabic_done", count=count)
    
    # 7. General Islamic from books
    logger.info("mvp_seed.general_islamic")
    general_docs = []
    general_categories = ["كتب عامة", "الرقائق والآداب والأذكار", "الجوامع"]
    
    for cat in general_categories:
        cat_books = get_books_by_category(cat, limit=15)
        for book in cat_books:
            book_id = book.get('book_id') or book.get('short_id', '')
            book_name = book.get('title', '')
            
            books_dir = DATA_DIR / "extracted_books"
            book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
            
            if not book_files:
                book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
            
            for bf in book_files[:1]:
                chunks = extract_chunks_from_book(bf, 10, 200, 500)
                for j, chunk in enumerate(chunks):
                    general_docs.append({
                        "chunk_index": len(general_docs),
                        "content": chunk[:2000],
                        "metadata": {
                            "type": "general_islamic",
                            "book": book_name,
                            "book_id": book_id,
                            "category": cat,
                            "language": "ar",
                        }
                    })
    
    if general_docs:
        count = await seed_collection("general_islamic_passages", general_docs[:TARGET_SAMPLES["general_islamic_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.general_done", count=count)
    
    # 8. Spirituality from riqaaq books
    logger.info("mvp_seed.spirituality")
    spirituality_docs = []
    spirituality_books = get_books_by_category("الرقائق والآداب والأذكار", limit=20)
    
    for book in spirituality_books:
        book_id = book.get('book_id') or book.get('short_id', '')
        book_name = book.get('title', '')
        
        books_dir = DATA_DIR / "extracted_books"
        book_files = list(books_dir.glob(f"*{book_id}_*.txt")) if book_id else []
        
        if not book_files:
            book_files = list(books_dir.glob(f"*{book_name[:20]}*.txt"))
        
        for bf in book_files[:2]:
            chunks = extract_chunks_from_book(bf, 15, 200, 500)
            for j, chunk in enumerate(chunks):
                spirituality_docs.append({
                    "chunk_index": len(spirituality_docs),
                    "content": chunk[:2000],
                    "metadata": {
                        "type": "spirituality",
                        "book": book_name,
                        "book_id": book_id,
                        "category": "الرقائق والآداب والأذكار",
                        "language": "ar",
                    }
                })
    
    if spirituality_docs:
        count = await seed_collection("spirituality_passages", spirituality_docs[:TARGET_SAMPLES["spirituality_passages"]], embedding_model, vector_store)
        total_embedded += count
        logger.info("mvp_seed.spirituality_done", count=count)
    
    # Final summary
    logger.info("mvp_seed.complete", total_embedded=total_embedded)
    print(f"\n{'='*60}")
    print(f"✅ MVP DATA SEEDING COMPLETE")
    print(f"   Total documents embedded: {total_embedded}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
