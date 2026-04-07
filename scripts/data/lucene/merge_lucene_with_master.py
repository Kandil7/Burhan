#!/usr/bin/env python3
"""
C. Merge Lucene-extracted content with master catalog.

Joins page/title/esnad content with master_catalog.json metadata,
enriches every document with book metadata, and organises into
RAG-ready collection JSONL files with hierarchical chunks.

Actual data locations (updated):
  - Flat JSON arrays:
      data/processed/lucene_esnad.json     (35,526 hadith chains)
      data/processed/lucene_title.json     (3,914,618 titles)
      data/processed/lucene_page.json      (17.4 GB, pages)
      data/processed/lucene_author.json    (author bios)
      data/processed/lucene_book.json      (8,425 book descriptions)
  - Per-book JSONL:
      data/processed/lucene_pages/books/*.jsonl
      data/processed/lucene_pages/raw/page_batch_1.jsonl
  - Metadata:
      data/processed/master_catalog.json   (8,465 books with collection mapping)
      data/processed/category_mapping.json (category -> collection mapping)

Document ID format: "{book_id}-{page_number}" (e.g., "622-1" = book 622, page 1)

Pipeline:
  1. Load master_catalog.json (book metadata with collection assignment)
  2. Load category_mapping.json (category -> collection mapping)
  3. Load flat Lucene JSON arrays (esnad, title) and iterate page data
  4. Parse book_id from document IDs (split on "-")
  5. Enrich each document with: book_id, title, author, category, collection
  6. Build hierarchical chunks respecting title boundaries
  7. Write 10 collection JSONL files (one per RAG collection)

Usage:
    python scripts/data/lucene/merge_lucene_with_master.py
    python scripts/data/lucene/merge_lucene_with_master.py --collections fiqh_passages hadith_passages
    python scripts/data/lucene/merge_lucene_with_master.py --chunk-size 2000
    python scripts/data/lucene/merge_lucene_with_master.py --dry-run
    python scripts/data/lucene/merge_lucene_with_master.py --skip-pages  # Skip 17GB page file

Output:
    data/processed/lucene_pages/collections/
        fiqh_passages.jsonl
        hadith_passages.jsonl
        quran_tafsir.jsonl
        aqeedah_passages.jsonl
        seerah_passages.jsonl
        islamic_history_passages.jsonl
        arabic_language_passages.jsonl
        spirituality_passages.jsonl
        general_islamic.jsonl
        usul_fiqh.jsonl
    data/processed/lucene_pages/chunks/
        Hierarchical chunks with title boundaries
    data/processed/lucene_pages/merge_report.json
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from scripts.utils import (
    ensure_dir,
    format_duration,
    format_size,
    get_data_dir,
    get_project_root,
    setup_script_logger,
)

# ── Configuration ─────────────────────────────────────────────────────────

logger = setup_script_logger("merge_lucene_with_master")

PROJECT_ROOT = get_project_root()
PROCESSED_DIR = get_data_dir("processed")

# Flat Lucene JSON files (actual locations)
LUCENE_ESNAD = PROCESSED_DIR / "lucene_esnad.json"
LUCENE_TITLE = PROCESSED_DIR / "lucene_title.json"
LUCENE_PAGE = PROCESSED_DIR / "lucene_page.json"
LUCENE_AUTHOR = PROCESSED_DIR / "lucene_author.json"
LUCENE_BOOK = PROCESSED_DIR / "lucene_book.json"

# Per-book JSONL locations
LUCENE_PAGES_DIR = PROCESSED_DIR / "lucene_pages"
LUCENE_BOOKS_DIR = LUCENE_PAGES_DIR / "books"
LUCENE_RAW_DIR = LUCENE_PAGES_DIR / "raw"

# Metadata
MASTER_CATALOG = PROCESSED_DIR / "master_catalog.json"
CATEGORY_MAPPING = PROCESSED_DIR / "category_mapping.json"

# Output directories
COLLECTIONS_DIR = LUCENE_PAGES_DIR / "collections"
CHUNKS_DIR = LUCENE_PAGES_DIR / "chunks"

# Default chunk size (characters)
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200

# Collection names (must match category_mapping.json collections)
COLLECTION_NAMES = [
    "fiqh_passages",
    "hadith_passages",
    "quran_tafsir",
    "aqeedah_passages",
    "seerah_passages",
    "islamic_history_passages",
    "arabic_language_passages",
    "spirituality_passages",
    "general_islamic",
    "usul_fiqh",
]


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class BookMetadata:
    """Metadata for a single book from master catalog."""
    book_id: int
    title: str
    category_id: Optional[int]
    category_name: Optional[str]
    author_id: Optional[int]
    author_name: Optional[str]
    author_death: Optional[int]
    printed: bool
    collection: str
    group_id: Optional[int] = None
    pdf_links: Optional[Dict] = None
    meta_data: Optional[Dict] = None


@dataclass
class EnrichedDocument:
    """A document enriched with book metadata."""
    content: str
    content_type: str  # "page", "title", "esnad", "chunk"
    book_id: int
    book_title: str
    category: str
    author: str
    author_death: Optional[int]
    collection: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    hadith_number: Optional[str] = None
    sanad: Optional[str] = None
    hierarchy: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "content": self.content,
            "content_type": self.content_type,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "category": self.category,
            "author": self.author,
            "author_death": self.author_death,
            "collection": self.collection,
        }
        if self.page_number is not None:
            result["page_number"] = self.page_number
        if self.section_title is not None:
            result["section_title"] = self.section_title
        if self.hadith_number is not None:
            result["hadith_number"] = self.hadith_number
        if self.sanad is not None:
            result["sanad"] = self.sanad
        if self.hierarchy:
            result["hierarchy"] = self.hierarchy
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class MergeStats:
    """Statistics for the merge operation."""
    books_loaded: int = 0
    books_with_content: int = 0
    total_documents: int = 0
    pages_merged: int = 0
    titles_merged: int = 0
    esnad_merged: int = 0
    chunks_created: int = 0
    collection_counts: Dict[str, int] = field(default_factory=dict)
    total_output_size_bytes: int = 0
    duration_seconds: float = 0.0


# ── ID Parsing ────────────────────────────────────────────────────────────

def parse_doc_id(doc_id: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse a Lucene document ID into (book_id, page_number).

    ID format: "{book_id}-{page_number}" (e.g., "622-1")

    Args:
        doc_id: Document ID string.

    Returns:
        Tuple of (book_id, page_number). Returns (None, None) if parsing fails.
    """
    if not doc_id or "-" not in doc_id:
        return None, None
    parts = doc_id.split("-", 1)
    try:
        book_id = int(parts[0])
        page_num = int(parts[1])
        return book_id, page_num
    except (ValueError, IndexError):
        return None, None


def extract_book_id(doc_id: str) -> Optional[int]:
    """Extract book_id from a document ID."""
    book_id, _ = parse_doc_id(doc_id)
    return book_id


# ── Catalog Loading ───────────────────────────────────────────────────────

def load_master_catalog(catalog_path: Path) -> Dict[int, BookMetadata]:
    """
    Load master catalog and build book_id -> metadata index.

    Args:
        catalog_path: Path to master_catalog.json.

    Returns:
        Dictionary mapping book_id to BookMetadata.
    """
    logger.info(f"Loading master catalog from {catalog_path}")

    if not catalog_path.exists():
        logger.error(f"Master catalog not found: {catalog_path}")
        return {}

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    books: Dict[int, BookMetadata] = {}
    for book_data in data.get("books", []):
        book_id = book_data.get("book_id")
        if book_id is None:
            continue

        metadata = BookMetadata(
            book_id=book_id,
            title=book_data.get("title", ""),
            category_id=book_data.get("category_id"),
            category_name=book_data.get("category_name"),
            author_id=book_data.get("author_id"),
            author_name=book_data.get("author_name"),
            author_death=book_data.get("author_death"),
            printed=book_data.get("printed", False),
            collection=book_data.get("collection", "general_islamic"),
            group_id=book_data.get("group_id"),
            pdf_links=book_data.get("pdf_links"),
            meta_data=book_data.get("meta_data"),
        )
        books[book_id] = metadata

    logger.info(f"Loaded {len(books):,} books from master catalog")
    return books


def load_category_mapping(mapping_path: Path) -> Dict[str, str]:
    """
    Load category -> collection mapping from category_mapping.json.

    Returns a dict mapping category_name -> collection_name.

    Args:
        mapping_path: Path to category_mapping.json.

    Returns:
        Dictionary mapping category names to collection names.
    """
    logger.info(f"Loading category mapping from {mapping_path}")

    if not mapping_path.exists():
        logger.warning(f"Category mapping not found: {mapping_path}")
        return {}

    with open(mapping_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build category -> collection mapping from the books dict
    cat_to_collection: Dict[str, str] = {}
    books_data = data.get("books", {})
    for book_id_str, book_info in books_data.items():
        cat = book_info.get("category", "")
        coll = book_info.get("collection", "general_islamic")
        if cat and cat not in cat_to_collection:
            cat_to_collection[cat] = coll

    logger.info(f"Loaded {len(cat_to_collection)} category -> collection mappings")
    return cat_to_collection


# ── Content Loading ───────────────────────────────────────────────────────

def load_flat_json_array(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load a flat JSON array file.

    Args:
        filepath: Path to JSON file containing an array of objects.

    Returns:
        List of dictionaries.
    """
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return []

    logger.info(f"Loading {filepath.name} ({format_size(filepath.stat().st_size)})")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        logger.info(f"  Loaded {len(data):,} items from {filepath.name}")
        return data

    logger.warning(f"  Expected array in {filepath.name}, got {type(data).__name__}")
    return []


def iter_jsonl_file(filepath: Path) -> Iterator[Dict[str, Any]]:
    """
    Iterate over lines in a JSONL file.

    Args:
        filepath: Path to JSONL file.

    Yields:
        Parsed JSON objects.
    """
    if not filepath.exists():
        return

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def load_per_book_jsonl(directory: Path) -> Dict[int, List[Dict[str, Any]]]:
    """
    Load all per-book JSONL files from a directory.

    Args:
        directory: Directory containing {book_id}.jsonl files.

    Returns:
        Dictionary mapping book_id to list of documents.
    """
    if not directory.exists():
        return {}

    result: Dict[int, List[Dict[str, Any]]] = {}
    for filepath in sorted(directory.glob("*.jsonl")):
        try:
            book_id = int(filepath.stem)
            docs = list(iter_jsonl_file(filepath))
            if docs:
                result[book_id] = docs
        except ValueError:
            continue

    logger.info(f"Loaded per-book JSONL from {directory.name}: {len(result)} books")
    return result


def group_by_book_id(
    docs: List[Dict[str, Any]],
    id_field: str = "id",
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Group a list of documents by book_id extracted from their ID field.

    Args:
        docs: List of documents with ID field.
        id_field: Name of the ID field (default: "id").

    Returns:
        Dictionary mapping book_id to list of documents.
    """
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    skipped = 0
    for doc in docs:
        doc_id = doc.get(id_field, "")
        book_id = extract_book_id(doc_id)
        if book_id is not None:
            grouped[book_id].append(doc)
        else:
            skipped += 1

    if skipped > 0:
        logger.warning(f"  Skipped {skipped:,} documents with unparseable IDs")

    return dict(grouped)


def find_lucene_content() -> Dict[str, Path]:
    """
    Find all available Lucene content files in their actual locations.

    Returns:
        Dictionary mapping content type to file/directory path.
    """
    sources: Dict[str, Path] = {}

    # Flat JSON arrays
    flat_files = {
        "esnad": LUCENE_ESNAD,
        "title": LUCENE_TITLE,
        "page": LUCENE_PAGE,
        "author": LUCENE_AUTHOR,
        "book": LUCENE_BOOK,
    }
    for content_type, filepath in flat_files.items():
        if filepath.exists():
            sources[f"flat_{content_type}"] = filepath

    # Per-book JSONL directories
    if LUCENE_BOOKS_DIR.exists() and any(LUCENE_BOOKS_DIR.glob("*.jsonl")):
        sources["per_book_books"] = LUCENE_BOOKS_DIR

    if LUCENE_RAW_DIR.exists():
        for jsonl_file in LUCENE_RAW_DIR.glob("*.jsonl"):
            sources[f"raw_{jsonl_file.stem}"] = jsonl_file

    # Per-book pages/titles/esnad directories (original expected structure)
    for subdir in ["pages", "titles", "esnad"]:
        dirpath = LUCENE_PAGES_DIR / subdir
        if dirpath.exists() and any(dirpath.glob("*.jsonl")):
            sources[f"per_book_{subdir}"] = dirpath

    return sources


# ── Chunking ──────────────────────────────────────────────────────────────

def build_title_index(titles: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Build a page_number -> title mapping from title documents.

    Args:
        titles: List of title documents.

    Returns:
        Dictionary mapping page number to title text.
    """
    title_map: Dict[int, str] = {}
    for doc in titles:
        # Title IDs are "book_id-page_number"
        doc_id = doc.get("id", "")
        _, page_num = parse_doc_id(doc_id)
        body = doc.get("body", "")
        if page_num and body:
            title_map[page_num] = body
    return title_map


def create_hierarchical_chunks(
    pages: List[Dict[str, Any]],
    title_map: Dict[int, str],
    book_title: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Create hierarchical chunks respecting title boundaries.

    Strategy:
    1. Group pages by their section title
    2. Within each section, split into chunks of ~chunk_size characters
    3. Preserve title context in each chunk's metadata

    Args:
        pages: List of page documents.
        title_map: Mapping of page_number -> title.
        book_title: Title of the book.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks in characters.

    Returns:
        List of chunk documents with hierarchy metadata.
    """
    if not pages:
        return []

    # Sort pages by page number
    sorted_pages = sorted(pages, key=lambda p: _extract_page_number(p))

    chunks: List[Dict[str, Any]] = []
    current_section = book_title  # Default section
    current_hierarchy = [book_title]
    buffer = ""
    buffer_pages = []

    for page_doc in sorted_pages:
        page_num = _extract_page_number(page_doc)
        body = page_doc.get("body", "")
        foot = page_doc.get("foot", "")

        # Check if this page has a title
        if page_num in title_map:
            # Save current buffer as chunk(s)
            if buffer.strip():
                chunks.extend(
                    _split_buffer(buffer, current_hierarchy, buffer_pages)
                )
            buffer = ""
            buffer_pages = []

            # Start new section
            current_section = title_map[page_num]
            current_hierarchy = [book_title, current_section]

        # Add content to buffer
        content = body
        if foot:
            content += "\n\n" + foot

        buffer += content + "\n\n"
        buffer_pages.append(page_num)

        # Split if buffer exceeds chunk size
        if len(buffer) > chunk_size:
            chunks.extend(
                _split_buffer(buffer, current_hierarchy, buffer_pages)
            )
            # Keep overlap for continuity
            overlap_start = max(0, len(buffer) - chunk_overlap)
            buffer = buffer[overlap_start:]
            buffer_pages = buffer_pages[-3:]  # Keep last few pages

    # Handle remaining buffer
    if buffer.strip():
        chunks.extend(
            _split_buffer(buffer, current_hierarchy, buffer_pages)
        )

    return chunks


def _extract_page_number(doc: Dict[str, Any]) -> int:
    """Extract page number from document."""
    doc_id = doc.get("id", "")
    if isinstance(doc_id, str) and "-" in doc_id:
        try:
            return int(doc_id.split("-")[1])
        except (ValueError, IndexError):
            pass
    page = doc.get("page", "")
    if page:
        try:
            return int(page)
        except (ValueError, TypeError):
            pass
    return 0


def _split_buffer(
    buffer: str,
    hierarchy: List[str],
    pages: List[int],
) -> List[Dict[str, Any]]:
    """
    Split a text buffer into chunks.

    Args:
        buffer: Text to split.
        hierarchy: Section hierarchy.
        pages: Page numbers in this buffer.

    Returns:
        List of chunk documents.
    """
    chunks = []
    text = buffer.strip()
    if not text:
        return chunks

    # Try to split at paragraph boundaries
    paragraphs = text.split("\n\n")
    current_chunk = ""
    chunk_pages = []
    page_idx = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > DEFAULT_CHUNK_SIZE and current_chunk:
            # Save current chunk
            chunk_doc = {
                "content": current_chunk.strip(),
                "content_type": "chunk",
                "hierarchy": hierarchy,
                "section_title": hierarchy[-1] if hierarchy else None,
                "page_range": f"{chunk_pages[0]}-{chunk_pages[-1]}" if chunk_pages else None,
            }
            chunks.append(chunk_doc)
            current_chunk = ""
            chunk_pages = []

        current_chunk += para + "\n\n"
        if page_idx < len(pages):
            chunk_pages.append(pages[page_idx])
            page_idx += 1

    # Final chunk
    if current_chunk.strip():
        chunk_doc = {
            "content": current_chunk.strip(),
            "content_type": "chunk",
            "hierarchy": hierarchy,
            "section_title": hierarchy[-1] if hierarchy else None,
            "page_range": f"{chunk_pages[0]}-{chunk_pages[-1]}" if chunk_pages else None,
        }
        chunks.append(chunk_doc)

    return chunks


# ── Enrichment & Output ───────────────────────────────────────────────────

def enrich_and_merge(
    books: Dict[int, BookMetadata],
    pages_grouped: Dict[int, List[Dict[str, Any]]],
    titles_grouped: Dict[int, List[Dict[str, Any]]],
    esnad_grouped: Dict[int, List[Dict[str, Any]]],
    collections_dir: Path,
    chunks_dir: Path,
    target_collections: Optional[List[str]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    dry_run: bool = False,
) -> MergeStats:
    """
    Main merge operation: enrich documents and write to collections.

    Args:
        books: Master catalog book metadata.
        pages_grouped: Pages grouped by book_id.
        titles_grouped: Titles grouped by book_id.
        esnad_grouped: Esnad grouped by book_id.
        collections_dir: Output directory for collection JSONL files.
        chunks_dir: Output directory for hierarchical chunks.
        target_collections: If specified, only process these collections.
        chunk_size: Target chunk size in characters.
        dry_run: If True, only count without writing.

    Returns:
        MergeStats with operation results.
    """
    stats = MergeStats()
    start_time = time.time()

    if target_collections is None:
        target_collections = COLLECTION_NAMES

    ensure_dir(collections_dir)
    ensure_dir(chunks_dir)

    # Open collection file handles
    collection_files: Dict[str, Any] = {}
    chunk_files: Dict[str, Any] = {}
    if not dry_run:
        for collection in target_collections:
            collection_files[collection] = open(
                collections_dir / f"{collection}.jsonl",
                "w",
                encoding="utf-8",
            )
            chunk_files[collection] = open(
                chunks_dir / f"{collection}_chunks.jsonl",
                "w",
                encoding="utf-8",
            )

    # Find all book IDs that have content across any source
    book_ids_with_content: Set[int] = set()
    for source in [pages_grouped, titles_grouped, esnad_grouped]:
        for book_id in source.keys():
            if book_id in books:
                book_ids_with_content.add(book_id)

    stats.books_loaded = len(books)
    stats.books_with_content = len(book_ids_with_content)

    logger.info(
        f"Merging {stats.books_with_content:,} books with content "
        f"into {len(target_collections)} collections"
    )

    # Process each book
    processed = 0
    skipped_no_collection = 0
    for book_id in sorted(book_ids_with_content):
        book = books[book_id]
        if book.collection not in target_collections:
            skipped_no_collection += 1
            continue

        processed += 1
        if processed % 500 == 0:
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            logger.info(
                f"  Processed {processed:,}/{stats.books_with_content:,} books "
                f"({rate:.0f} books/sec, {stats.total_documents:,} docs)"
            )

        # Load content for this book
        pages = pages_grouped.get(book_id, [])
        titles = titles_grouped.get(book_id, [])
        esnad_docs = esnad_grouped.get(book_id, [])

        # Enrich pages
        title_map = build_title_index(titles)
        for page_doc in pages:
            enriched = _enrich_page(page_doc, book, title_map)
            if not dry_run:
                collection_files[book.collection].write(
                    json.dumps(enriched.to_dict(), ensure_ascii=False) + "\n"
                )
            stats.pages_merged += 1
            stats.total_documents += 1
            stats.collection_counts[book.collection] = (
                stats.collection_counts.get(book.collection, 0) + 1
            )

        # Enrich titles
        for title_doc in titles:
            enriched = _enrich_title(title_doc, book)
            if not dry_run:
                collection_files[book.collection].write(
                    json.dumps(enriched.to_dict(), ensure_ascii=False) + "\n"
                )
            stats.titles_merged += 1
            stats.total_documents += 1
            stats.collection_counts[book.collection] = (
                stats.collection_counts.get(book.collection, 0) + 1
            )

        # Enrich esnad
        for esnad_doc in esnad_docs:
            enriched = _enrich_esnad(esnad_doc, book)
            if not dry_run:
                collection_files[book.collection].write(
                    json.dumps(enriched.to_dict(), ensure_ascii=False) + "\n"
                )
            stats.esnad_merged += 1
            stats.total_documents += 1
            stats.collection_counts[book.collection] = (
                stats.collection_counts.get(book.collection, 0) + 1
            )

        # Create hierarchical chunks (for pages)
        if pages:
            chunks = create_hierarchical_chunks(pages, title_map, book.title)
            for chunk_doc in chunks:
                chunk_doc["book_id"] = book.book_id
                chunk_doc["book_title"] = book.title
                chunk_doc["category"] = book.category_name or ""
                chunk_doc["author"] = book.author_name or ""
                chunk_doc["author_death"] = book.author_death
                chunk_doc["collection"] = book.collection
                if not dry_run:
                    chunk_files[book.collection].write(
                        json.dumps(chunk_doc, ensure_ascii=False) + "\n"
                    )
                stats.chunks_created += 1

    # Close all file handles
    for fh in list(collection_files.values()) + list(chunk_files.values()):
        fh.close()

    # Calculate output sizes
    if not dry_run:
        for collection in target_collections:
            coll_file = collections_dir / f"{collection}.jsonl"
            chunk_file = chunks_dir / f"{collection}_chunks.jsonl"
            if coll_file.exists():
                stats.total_output_size_bytes += coll_file.stat().st_size
            if chunk_file.exists():
                stats.total_output_size_bytes += chunk_file.stat().st_size

    stats.duration_seconds = time.time() - start_time
    logger.info(
        f"Skipped {skipped_no_collection:,} books (collection not in target list)"
    )
    return stats


def _enrich_page(
    doc: Dict[str, Any],
    book: BookMetadata,
    title_map: Dict[int, str],
) -> EnrichedDocument:
    """Enrich a page document with book metadata."""
    page_num = _extract_page_number(doc)
    section_title = title_map.get(page_num)

    content_parts = []
    body = doc.get("body", "")
    if body:
        content_parts.append(body)
    foot = doc.get("foot", "")
    if foot:
        content_parts.append(foot)

    content = "\n\n".join(content_parts)

    hierarchy = [book.title]
    if section_title:
        hierarchy.append(section_title)

    return EnrichedDocument(
        content=content,
        content_type="page",
        book_id=book.book_id,
        book_title=book.title,
        category=book.category_name or "",
        author=book.author_name or "",
        author_death=book.author_death,
        collection=book.collection,
        page_number=page_num,
        section_title=section_title,
        hierarchy=hierarchy,
    )


def _enrich_title(
    doc: Dict[str, Any],
    book: BookMetadata,
) -> EnrichedDocument:
    """Enrich a title document with book metadata."""
    _, page_num = parse_doc_id(doc.get("id", ""))
    body = doc.get("body", "")

    return EnrichedDocument(
        content=body,
        content_type="title",
        book_id=book.book_id,
        book_title=book.title,
        category=book.category_name or "",
        author=book.author_name or "",
        author_death=book.author_death,
        collection=book.collection,
        page_number=page_num,
        section_title=body,
        hierarchy=[book.title, body],
    )


def _enrich_esnad(
    doc: Dict[str, Any],
    book: BookMetadata,
) -> EnrichedDocument:
    """Enrich an esnad (hadith chain) document with book metadata."""
    hadeeth = doc.get("hadeeth", "")
    esnad = doc.get("esnad", "")

    content = ""
    if esnad:
        content += f"الاسناد: {esnad}"
    if hadeeth:
        content += f"\n\nالحديث: {hadeeth}"

    return EnrichedDocument(
        content=content.strip(),
        content_type="esnad",
        book_id=book.book_id,
        book_title=book.title,
        category=book.category_name or "",
        author=book.author_name or "",
        author_death=book.author_death,
        collection=book.collection,
        hadith_number=hadeeth,
        sanad=esnad,
        hierarchy=[book.title, "احاديث"],
    )


# ── Reporting ─────────────────────────────────────────────────────────────

def write_merge_report(stats: MergeStats) -> Path:
    """Write merge operation report."""
    report = {
        "merge_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "books_loaded": stats.books_loaded,
        "books_with_content": stats.books_with_content,
        "total_documents": stats.total_documents,
        "pages_merged": stats.pages_merged,
        "titles_merged": stats.titles_merged,
        "esnad_merged": stats.esnad_merged,
        "chunks_created": stats.chunks_created,
        "collection_counts": stats.collection_counts,
        "total_output_size_bytes": stats.total_output_size_bytes,
        "total_output_size": format_size(stats.total_output_size_bytes),
        "duration_seconds": stats.duration_seconds,
        "duration": format_duration(stats.duration_seconds),
    }

    report_path = LUCENE_PAGES_DIR / "merge_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Merge report saved to {report_path}")
    return report_path


def print_merge_summary(stats: MergeStats) -> None:
    """Print human-readable merge summary."""
    print(f"\n{'=' * 70}")
    print("MERGE WITH MASTER CATALOG COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Books loaded:        {stats.books_loaded:,}")
    print(f"  Books with content:  {stats.books_with_content:,}")
    print(f"  Total documents:     {stats.total_documents:,}")
    print(f"    Pages merged:      {stats.pages_merged:,}")
    print(f"    Titles merged:     {stats.titles_merged:,}")
    print(f"    Esnad merged:      {stats.esnad_merged:,}")
    print(f"  Chunks created:      {stats.chunks_created:,}")
    print(f"  Output size:         {format_size(stats.total_output_size_bytes)}")
    print(f"  Duration:            {format_duration(stats.duration_seconds)}")

    print(f"\n  Collection distribution:")
    for collection in sorted(stats.collection_counts.keys()):
        count = stats.collection_counts[collection]
        print(f"    {collection:30s}: {count:>8,} documents")

    print(f"\n  Output directories:")
    print(f"    Collections: {COLLECTIONS_DIR}")
    print(f"    Chunks:      {CHUNKS_DIR}")
    print(f"{'=' * 70}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge Lucene content with master catalog"
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        choices=COLLECTION_NAMES,
        default=COLLECTION_NAMES,
        help="Which collections to generate (default: all)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Target chunk size in characters (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be merged without writing",
    )
    parser.add_argument(
        "--skip-pages",
        action="store_true",
        help="Skip the large lucene_page.json file (17.4 GB)",
    )
    parser.add_argument(
        "--max-books",
        type=int,
        default=None,
        help="Limit to first N books (for testing)",
    )
    args = parser.parse_args()

    print(f"{'=' * 70}")
    print("ATHAR - MERGE LUCENE CONTENT WITH MASTER CATALOG")
    print(f"{'=' * 70}")
    print(f"  Collections:   {', '.join(args.collections)}")
    print(f"  Chunk size:    {args.chunk_size}")
    print(f"  Dry run:       {args.dry_run}")
    print(f"  Skip pages:    {args.skip_pages}")
    print(f"  Max books:     {args.max_books or 'all'}")
    print(f"  Output dir:    {COLLECTIONS_DIR}")
    print(f"{'=' * 70}")

    # Check prerequisites
    if not MASTER_CATALOG.exists():
        logger.error(f"Master catalog not found: {MASTER_CATALOG}")
        logger.error("Run extract_master_catalog.py first")
        sys.exit(1)

    if not CATEGORY_MAPPING.exists():
        logger.warning(f"Category mapping not found: {CATEGORY_MAPPING}")

    # Find available Lucene content
    sources = find_lucene_content()
    if not sources:
        logger.error(
            "No Lucene content found. Run extract_lucene_pages.py first.\n"
            f"Expected files in:\n"
            f"  {LUCENE_ESNAD}\n"
            f"  {LUCENE_TITLE}\n"
            f"  {LUCENE_PAGE}\n"
            f"  {LUCENE_BOOKS_DIR}/*.jsonl\n"
            f"  {LUCENE_RAW_DIR}/*.jsonl"
        )
        sys.exit(1)

    logger.info(f"Found {len(sources)} Lucene content sources:")
    for source_type, source_path in sources.items():
        if source_path.is_file():
            size = format_size(source_path.stat().st_size)
            logger.info(f"  {source_type}: {source_path.name} ({size})")
        else:
            count = len(list(source_path.glob("*.jsonl")))
            logger.info(f"  {source_type}: {source_path.name}/ ({count} files)")

    # Load master catalog
    books = load_master_catalog(MASTER_CATALOG)
    if not books:
        logger.error("Failed to load master catalog")
        sys.exit(1)

    # Load category mapping
    cat_mapping = load_category_mapping(CATEGORY_MAPPING)

    # ── Load and group content ────────────────────────────────────────

    pages_grouped: Dict[int, List[Dict[str, Any]]] = {}
    titles_grouped: Dict[int, List[Dict[str, Any]]] = {}
    esnad_grouped: Dict[int, List[Dict[str, Any]]] = {}

    # 1. Load flat JSON arrays (esnad, title)
    if "flat_esnad" in sources:
        logger.info("Loading esnad from flat JSON array...")
        esnad_docs = load_flat_json_array(sources["flat_esnad"])
        if esnad_docs:
            grouped = group_by_book_id(esnad_docs)
            esnad_grouped.update(grouped)
            logger.info(f"  Grouped into {len(grouped):,} books")

    if "flat_title" in sources:
        logger.info("Loading titles from flat JSON array...")
        title_docs = load_flat_json_array(sources["flat_title"])
        if title_docs:
            grouped = group_by_book_id(title_docs)
            titles_grouped.update(grouped)
            logger.info(f"  Grouped into {len(grouped):,} books")

    # 2. Load flat page JSON array (17.4 GB - optionally skip)
    if args.skip_pages:
        logger.info("Skipping lucene_page.json (--skip-pages flag set)")
    elif "flat_page" in sources:
        logger.info("Loading pages from flat JSON array (this may take a while)...")
        page_docs = load_flat_json_array(sources["flat_page"])
        if page_docs:
            grouped = group_by_book_id(page_docs)
            pages_grouped.update(grouped)
            logger.info(f"  Grouped into {len(grouped):,} books")

    # 3. Load per-book JSONL files (books directory)
    if "per_book_books" in sources:
        logger.info("Loading per-book JSONL from books/ directory...")
        books_data = load_per_book_jsonl(sources["per_book_books"])
        # These are book metadata entries, not pages - skip for page content
        logger.info(f"  Found {len(books_data)} book metadata files")

    # 4. Load raw batch JSONL files (page content)
    for key, path in sources.items():
        if key.startswith("raw_") and path.suffix == ".jsonl":
            logger.info(f"Loading raw batch: {path.name}...")
            batch_docs: List[Dict[str, Any]] = []
            count = 0
            for doc in iter_jsonl_file(path):
                batch_docs.append(doc)
                count += 1
                if count % 100000 == 0:
                    logger.info(f"  Read {count:,} documents...")

            if batch_docs:
                grouped = group_by_book_id(batch_docs)
                # Merge with existing pages_grouped
                for book_id, docs in grouped.items():
                    if book_id in pages_grouped:
                        pages_grouped[book_id].extend(docs)
                    else:
                        pages_grouped[book_id] = docs
                logger.info(f"  Grouped into {len(grouped):,} books")

    # 5. Load per-book pages/titles/esnad directories (original structure)
    for content_type, group_dict in [
        ("pages", pages_grouped),
        ("titles", titles_grouped),
        ("esnad", esnad_grouped),
    ]:
        key = f"per_book_{content_type}"
        if key in sources:
            logger.info(f"Loading per-book {content_type} from directory...")
            for filepath in sorted(sources[key].glob("*.jsonl")):
                try:
                    book_id = int(filepath.stem)
                    docs = list(iter_jsonl_file(filepath))
                    if docs:
                        if book_id in group_dict:
                            group_dict[book_id].extend(docs)
                        else:
                            group_dict[book_id] = docs
                except ValueError:
                    continue

    # ── Summary of loaded content ─────────────────────────────────────

    total_pages = sum(len(v) for v in pages_grouped.values())
    total_titles = sum(len(v) for v in titles_grouped.values())
    total_esnad = sum(len(v) for v in esnad_grouped.values())

    logger.info(f"\nContent summary:")
    logger.info(f"  Pages:  {total_pages:>10,} documents across {len(pages_grouped):,} books")
    logger.info(f"  Titles: {total_titles:>10,} documents across {len(titles_grouped):,} books")
    logger.info(f"  Esnad:  {total_esnad:>10,} documents across {len(esnad_grouped):,} books")

    if total_pages == 0 and total_titles == 0 and total_esnad == 0:
        logger.error("No Lucene content found after loading. Check file paths and formats.")
        sys.exit(1)

    # ── Limit books for testing ───────────────────────────────────────

    if args.max_books:
        all_book_ids = set()
        for d in [pages_grouped, titles_grouped, esnad_grouped]:
            all_book_ids.update(d.keys())
        all_book_ids = sorted(all_book_ids & set(books.keys()))
        limited_ids = set(all_book_ids[:args.max_books])

        pages_grouped = {k: v for k, v in pages_grouped.items() if k in limited_ids}
        titles_grouped = {k: v for k, v in titles_grouped.items() if k in limited_ids}
        esnad_grouped = {k: v for k, v in esnad_grouped.items() if k in limited_ids}

        logger.info(f"Limited to {args.max_books} books for testing")

    # ── Perform merge ─────────────────────────────────────────────────

    stats = enrich_and_merge(
        books=books,
        pages_grouped=pages_grouped,
        titles_grouped=titles_grouped,
        esnad_grouped=esnad_grouped,
        collections_dir=COLLECTIONS_DIR,
        chunks_dir=CHUNKS_DIR,
        target_collections=args.collections,
        chunk_size=args.chunk_size,
        dry_run=args.dry_run,
    )

    # Write report and print summary
    if not args.dry_run:
        write_merge_report(stats)
    print_merge_summary(stats)


if __name__ == "__main__":
    main()
