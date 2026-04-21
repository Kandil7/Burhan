#!/usr/bin/env python3
"""
Complete MVP Data Seeder for Athar Islamic QA System.

Seeds sample data for ALL collections from existing datasets:
1. hadith_passages - From Sanadset CSV
2. quran_tafsir - From Quran ayahs in PostgreSQL + sample tafsir
3. aqeedah_passages - From aqeedah books
4. seerah_passages - From seerah books
5. islamic_history_passages - From history/trajim books
6. arabic_language_passages - From Arabic language books
7. general_islamic_passages - From general Islamic books
8. spirituality_passages - From riqaaq/adab books

Each collection gets 200-500 quality samples for MVP functionality.

Usage:
    python scripts/data/seed_mvp_data.py
    python scripts/data/seed_mvp_data.py --collections hadith_passages aqeedah_passages
    python scripts/data/seed_mvp_data.py --limit 50  # Limit docs per collection

Author: Athar Engineering Team
"""

import argparse
import asyncio
import csv
import json
import random
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Increase CSV field size limit
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils import (
    get_project_root,
    get_data_dir,
    get_datasets_dir,
    setup_script_logger,
    ProgressBar,
    add_project_root_to_path,
)

# Ensure src modules are importable
add_project_root_to_path()

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore

logger = setup_script_logger("seed-mvp-data")

# ── Configuration ────────────────────────────────────────────────────────

random.seed(42)

PROJECT_ROOT = get_project_root()
DATA_DIR = get_datasets_dir("data")
DATASETS_DIR = get_datasets_dir()

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


# ── Data Loading Helpers ─────────────────────────────────────────────────


def load_random_lines(filepath: Path, n: int, encoding: str = "utf-8") -> list[str]:
    """
    Load n random lines from a text file.

    Args:
        filepath: Path to text file.
        n: Number of random lines to load.
        encoding: File encoding.

    Returns:
        List of random lines (stripped).
    """
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding=encoding) as f:
            lines = [l.strip() for l in f.readlines() if len(l.strip()) > 50]
        if not lines:
            return []
        return random.sample(lines, min(n, len(lines)))
    except Exception as e:
        logger.warning("file_read_error", path=str(filepath), error=str(e))
        return []


def get_books_by_category(cat_name: str, limit: int = 10) -> list[dict]:
    """
    Get book info by category from books.db metadata.

    Args:
        cat_name: Category name to search for.
        limit: Maximum number of books to return.

    Returns:
        List of book info dicts.
    """
    db_path = DATA_DIR / "metadata" / "books.db"
    if not db_path.exists():
        logger.warning("books_db_not_found", path=str(db_path))
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Try exact match first, then LIKE
    cur.execute(
        "SELECT * FROM books WHERE cat_name = ? OR cat_name LIKE ? LIMIT ?",
        (cat_name, f"%{cat_name}%", limit),
    )
    books = [dict(r) for r in cur.fetchall()]
    conn.close()
    return books


def extract_chunks_from_book(
    book_file: Path,
    num_chunks: int,
    min_chunk_size: int = 200,
    max_chunk_size: int = 500,
) -> list[str]:
    """
    Extract random chunks from a book file.

    Args:
        book_file: Path to book text file.
        num_chunks: Number of chunks to extract.
        min_chunk_size: Minimum chunk size in characters.
        max_chunk_size: Maximum chunk size in characters.

    Returns:
        List of chunk strings.
    """
    if not book_file.exists():
        return []

    try:
        with open(book_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Clean content
        content = re.sub(r"\[Page \d+\]", "", content)
        content = re.sub(r"\[Footnotes\].*$", "", content, flags=re.DOTALL)

        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > min_chunk_size]

        if not paragraphs:
            paragraphs = [p.strip() for p in content.split("\n") if len(p.strip()) > min_chunk_size]

        chunks: list[str] = []
        selected = random.sample(paragraphs, min(num_chunks, len(paragraphs)))

        for para in selected:
            chunk_text = para[:max_chunk_size]
            if len(chunk_text) > min_chunk_size:
                chunks.append(chunk_text)

        return chunks
    except Exception as e:
        logger.warning("book_extract_error", path=str(book_file), error=str(e))
        return []


def find_book_files_by_id_or_name(
    book_id: str,
    book_name: str,
    limit: int = 2,
) -> list[Path]:
    """
    Find extracted book files by book ID or name.

    Args:
        book_id: Book ID from metadata.
        book_name: Book title from metadata.
        limit: Maximum number of files to return.

    Returns:
        List of matching file paths.
    """
    books_dir = DATA_DIR / "extracted_books"
    if not books_dir.exists():
        return []

    files: list[Path] = []

    # Try by book_id first
    if book_id:
        files = list(books_dir.glob(f"*{book_id}_*.txt"))

    # Fall back to name matching
    if not files and book_name:
        search_term = book_name[:20]
        files = list(books_dir.glob(f"*{search_term}*.txt"))

    return files[:limit]


# ── Collection Seeding ───────────────────────────────────────────────────


async def seed_collection(
    collection_name: str,
    documents: list[dict],
    embedding_model: EmbeddingModel,
    vector_store: VectorStore,
    batch_size: int = 32,
) -> int:
    """
    Embed and upsert documents to a Qdrant collection.

    Disables Redis cache to avoid connection issues during seeding.
    Uses local in-model caching only.

    Args:
        collection_name: Qdrant collection name.
        documents: List of document dicts with 'content' and 'metadata'.
        embedding_model: EmbeddingModel instance.
        vector_store: VectorStore instance.
        batch_size: Batch size for embedding.

    Returns:
        Number of documents upserted.
    """
    if not documents:
        logger.info("seed.skip_no_docs", collection=collection_name)
        return 0

    logger.info("seed.start", collection=collection_name, count=len(documents))

    # Ensure collection exists
    try:
        await vector_store.ensure_collection(collection_name, dimension=embedding_model.DIMENSION)
    except Exception as e:
        logger.warning("collection_create_warning", collection=collection_name, error=str(e))

    # Disable Redis cache for seeding (use local cache only)
    embedding_model.cache_enabled = False

    # Embed in batches with progress bar
    total_upserted = 0

    with ProgressBar(total=len(documents), desc=f"Embedding {collection_name}", unit="docs") as bar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            texts = [d["content"] for d in batch]

            try:
                # Embed
                embeddings = await embedding_model.encode(texts)

                # Upsert
                count = await vector_store.upsert(collection_name, batch, embeddings)
                total_upserted += count
                bar.update(len(batch))

            except Exception as e:
                logger.error(
                    "seed.batch_error",
                    collection=collection_name,
                    batch=i // batch_size,
                    error=str(e),
                )
                bar.update(len(batch))  # Still advance progress

    logger.info("seed.complete", collection=collection_name, upserted=total_upserted)
    return total_upserted


# ── Collection Builders ──────────────────────────────────────────────────


def build_hadith_docs(target: int) -> list[dict]:
    """Build hadith documents from Sanadset CSV."""
    sanadset_csv = (
        DATASETS_DIR
        / "Sanadset 368K Data on Hadith Narrators"
        / "Sanadset 368K Data on Hadith Narrators"
        / "sanadset.csv"
    )

    if not sanadset_csv.exists():
        logger.warning("sanadset_not_found", path=str(sanadset_csv))
        return []

    logger.info("building_hadith_docs", target=target)
    docs: list[dict] = []

    with open(sanadset_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        sample_rows = random.sample(rows, min(target, len(rows)))

        for i, row in enumerate(sample_rows):
            sanad = re.sub(r"<[^>]+>", "", row.get("Sanad", "")).strip()
            matn = row.get("Matn", "").strip()
            book = row.get("Book", "")

            content_parts = []
            if matn:
                content_parts.append(matn)
            if sanad and sanad != "No SANAD":
                content_parts.append(sanad)
            if book:
                content_parts.append(book)

            content = " | ".join(content_parts)[:3000]

            docs.append(
                {
                    "chunk_index": i,
                    "content": content,
                    "metadata": {
                        "type": "hadith",
                        "book": book,
                        "num_hadith": row.get("Num_hadith", ""),
                        "matn": matn[:2000],
                        "sanad": sanad[:1000],
                        "sanad_length": row.get("Sanad_Length", ""),
                        "dataset": "sanadset_368k",
                        "language": "ar",
                    },
                }
            )

    return docs


def build_quran_docs(target: int) -> list[dict]:
    """Build Quran documents from PostgreSQL."""
    docs: list[dict] = []

    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2_not_installed", msg="Install with: pip install psycopg2-binary")
        return []

    try:
        import os

        db_url = os.environ.get("DATABASE_URL", "postgresql://athar:athar_password@localhost:5432/athar_db")
        # Parse the URL for psycopg2 connection
        from urllib.parse import urlparse

        parsed = urlparse(db_url)
        db_conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            database=parsed.path.lstrip("/") or "athar_db",
            user=parsed.username or "athar",
            password=parsed.password or "athar_password",
        )
        cur = db_conn.cursor()

        cur.execute(
            """
            SELECT s.name_ar, s.name_en, a.number_in_surah, a.text_uthmani,
                   t.text as translation, t.language, t.translator
            FROM ayahs a
            JOIN surahs s ON a.surah_id = s.id
            LEFT JOIN translations t ON a.id = t.ayah_id AND t.language = 'en'
            ORDER BY RANDOM()
            LIMIT %s
        """,
            (target,),
        )

        rows = cur.fetchall()
        for i, row in enumerate(rows):
            content = f"Quran {row[1]} ({row[0]}) {row[2]}: {row[3]}"
            if row[4]:
                content += f"\nTranslation: {row[4]}"

            docs.append(
                {
                    "chunk_index": i,
                    "content": content[:3000],
                    "metadata": {
                        "type": "quran_ayah",
                        "surah_name_en": row[1],
                        "surah_name_ar": row[0],
                        "ayah_number": row[2],
                        "translation": row[4] or "",
                        "language": "ar",
                    },
                }
            )

        cur.close()
        db_conn.close()

    except Exception as e:
        logger.warning("quran_db_error", error=str(e))

    return docs


def build_book_docs(
    category: str,
    collection_name: str,
    doc_type: str,
    target: int,
    chunks_per_book: int = 15,
) -> list[dict]:
    """
    Build documents from extracted books by category.

    Args:
        category: Category name in books.db.
        collection_name: Target collection name.
        doc_type: Document type for metadata.
        target: Maximum number of documents.
        chunks_per_book: Chunks to extract per book.

    Returns:
        List of document dicts.
    """
    docs: list[dict] = []
    books = get_books_by_category(category, limit=20)

    for book in books:
        if len(docs) >= target:
            break

        book_id = book.get("book_id") or book.get("short_id", "")
        book_name = book.get("title", "")

        book_files = find_book_files_by_id_or_name(book_id, book_name, limit=2)

        for bf in book_files:
            if len(docs) >= target:
                break

            chunks = extract_chunks_from_book(bf, chunks_per_book, 200, 500)
            for chunk in chunks:
                if len(docs) >= target:
                    break

                docs.append(
                    {
                        "chunk_index": len(docs),
                        "content": chunk[:2000],
                        "metadata": {
                            "type": doc_type,
                            "book": book_name,
                            "book_id": book_id,
                            "category": category,
                            "language": "ar",
                        },
                    }
                )

    return docs


# ── Main Pipeline ────────────────────────────────────────────────────────


async def main(
    collections: Optional[list[str]] = None,
    limit: Optional[int] = None,
    batch_size: int = 32,
) -> None:
    """
    Seed all specified collections with sample data.

    Args:
        collections: List of collection names to seed (default: all).
        limit: Override target samples per collection.
        batch_size: Batch size for embedding.
    """
    target_collections = collections or list(TARGET_SAMPLES.keys())

    print(f"\n{'=' * 70}")
    print("  ATHAR MVP DATA SEEDER")
    print(f"{'=' * 70}")
    print(f"  Collections: {', '.join(target_collections)}")
    if limit:
        print(f"  Limit: {limit} docs per collection")
    print(f"{'=' * 70}\n")

    # Initialize components
    logger.info("loading_components")

    print("  Loading embedding model...")
    embedding_model = EmbeddingModel()
    await embedding_model.load_model()
    print(f"  ✓ Model: {embedding_model.MODEL_NAME} ({embedding_model.DIMENSION}d, {embedding_model.device})")

    print("  Connecting to Qdrant...")
    vector_store = VectorStore()
    await vector_store.initialize()
    print(f"  ✓ Collections: {', '.join(vector_store.list_collections())}")
    print()

    total_embedded = 0

    # Define builders for each collection
    builders = {
        "hadith_passages": lambda t: build_hadith_docs(t),
        "quran_tafsir": lambda t: build_quran_docs(t),
        "aqeedah_passages": lambda t: build_book_docs("العقيدة", "aqeedah_passages", "aqeedah", t, 15),
        "seerah_passages": lambda t: build_book_docs("السيرة النبوية", "seerah_passages", "seerah", t, 15),
        "islamic_history_passages": lambda t: (
            build_book_docs("التاريخ", "islamic_history_passages", "islamic_history", t // 3, 10)
            + build_book_docs("التراجم والطبقات", "islamic_history_passages", "islamic_history", t // 3, 10)
            + build_book_docs("البلدان والرحلات", "islamic_history_passages", "islamic_history", t // 3, 10)
        ),
        "arabic_language_passages": lambda t: (
            build_book_docs("النحو والصرف", "arabic_language_passages", "arabic_language", t // 4, 10)
            + build_book_docs("الأدب", "arabic_language_passages", "arabic_language", t // 4, 10)
            + build_book_docs("كتب اللغة", "arabic_language_passages", "arabic_language", t // 4, 10)
            + build_book_docs("البلاغة", "arabic_language_passages", "arabic_language", t // 4, 10)
        ),
        "general_islamic_passages": lambda t: (
            build_book_docs("كتب عامة", "general_islamic_passages", "general_islamic", t // 3, 10)
            + build_book_docs("الرقائق والآداب والأذكار", "general_islamic_passages", "general_islamic", t // 3, 10)
            + build_book_docs("الجوامع", "general_islamic_passages", "general_islamic", t // 3, 10)
        ),
        "spirituality_passages": lambda t: build_book_docs(
            "الرقائق والآداب والأذكار", "spirituality_passages", "spirituality", t, 15
        ),
    }

    for coll_name in target_collections:
        if coll_name not in builders:
            logger.warning("unknown_collection", collection=coll_name)
            continue

        target = limit or TARGET_SAMPLES.get(coll_name, 300)
        print(f"  Building documents for: {coll_name} (target: {target})")

        docs = builders[coll_name](target)
        print(f"  ✓ Built {len(docs)} documents")

        if docs:
            count = await seed_collection(coll_name, docs, embedding_model, vector_store, batch_size)
            total_embedded += count
            print(f"  ✓ Embedded {count} documents\n")
        else:
            print(f"  ⚠ No documents to embed\n")

    # Final summary
    print(f"\n{'=' * 70}")
    print("  MVP DATA SEEDING COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total documents embedded: {total_embedded}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed MVP data for Athar collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/data/seed_mvp_data.py
  python scripts/data/seed_mvp_data.py --collections hadith_passages
  python scripts/data/seed_mvp_data.py --limit 50
        """,
    )
    parser.add_argument("--collections", nargs="+", default=None, help="Collections to seed (default: all)")
    parser.add_argument("--limit", type=int, default=None, help="Limit docs per collection")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    args = parser.parse_args()

    try:
        asyncio.run(
            main(
                collections=args.collections,
                limit=args.limit,
                batch_size=args.batch_size,
            )
        )
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)
