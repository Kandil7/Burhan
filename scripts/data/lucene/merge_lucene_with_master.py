#!/usr/bin/env python3
"""
C. Merge Lucene-extracted content with master catalog.

Joins page/title/esnad content with master_catalog.json metadata,
enriches every document with book metadata, and organises into
RAG-ready collection JSONL files with hierarchical chunks.

Pipeline:
  1. Load master_catalog.json (book metadata)
  2. Load per-book Lucene content (pages, titles, esnad)
  3. Enrich each document with: book_id, title, author, category, collection
  4. Build hierarchical chunks respecting title boundaries
  5. Write 10 collection JSONL files (one per RAG collection)

Usage:
    python scripts/data/lucene/merge_lucene_with_master.py
    python scripts/data/lucene/merge_lucene_with_master.py --collections fiqh_passages hadith_passages
    python scripts/data/lucene/merge_lucene_with_master.py --chunk-size 2000
    python scripts/data/lucene/merge_lucene_with_master.py --dry-run

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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from scripts.utils import (
    ensure_dir,
    format_duration,
    format_size,
    get_project_root,
    setup_script_logger,
)

# ── Configuration ─────────────────────────────────────────────────────────

logger = setup_script_logger("merge_lucene_with_master")

PROJECT_ROOT = get_project_root()
LUCENE_PAGES_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages"
MASTER_CATALOG = PROJECT_ROOT / "data" / "processed" / "master_catalog.json"
COLLECTIONS_DIR = LUCENE_PAGES_DIR / "collections"
CHUNKS_DIR = LUCENE_PAGES_DIR / "chunks"

# Default chunk size (characters)
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200

# Collection names (must match master catalog)
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


# ── Content Loading ───────────────────────────────────────────────────────

def load_book_pages(pages_dir: Path, book_id: int) -> List[Dict[str, Any]]:
    """
    Load all page documents for a book.

    Args:
        pages_dir: Directory containing per-book page JSONL files.
        book_id: Book ID to load.

    Returns:
        List of page documents.
    """
    filepath = pages_dir / f"{book_id}.jsonl"
    if not filepath.exists():
        return []

    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return docs


def load_book_titles(titles_dir: Path, book_id: int) -> List[Dict[str, Any]]:
    """
    Load all title documents for a book.

    Args:
        titles_dir: Directory containing per-book title JSONL files.
        book_id: Book ID to load.

    Returns:
        List of title documents.
    """
    filepath = titles_dir / f"{book_id}.jsonl"
    if not filepath.exists():
        return []

    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return docs


def load_book_esnad(esnad_dir: Path, book_id: int) -> List[Dict[str, Any]]:
    """
    Load all esnad (hadith chain) documents for a book.

    Args:
        esnad_dir: Directory containing per-book esnad JSONL files.
        book_id: Book ID to load.

    Returns:
        List of esnad documents.
    """
    filepath = esnad_dir / f"{book_id}.jsonl"
    if not filepath.exists():
        return []

    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return docs


def iterate_all_books(content_dir: Path) -> Iterator[int]:
    """
    Iterate over all book IDs that have content files.

    Args:
        content_dir: Directory containing per-book JSONL files.

    Yields:
        Book IDs (integers).
    """
    if not content_dir.exists():
        return

    for filepath in sorted(content_dir.glob("*.jsonl")):
        try:
            book_id = int(filepath.stem)
            yield book_id
        except ValueError:
            continue


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
        page = doc.get("page")
        body = doc.get("body", "")
        if page and body:
            try:
                page_num = int(page)
                title_map[page_num] = body
            except (ValueError, TypeError):
                continue
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
    pages_dir: Path,
    titles_dir: Path,
    esnad_dir: Path,
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
        pages_dir: Directory with per-book page JSONL files.
        titles_dir: Directory with per-book title JSONL files.
        esnad_dir: Directory with per-book esnad JSONL files.
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

    # Find all book IDs that have content
    book_ids_with_content: Set[int] = set()
    for source_dir in [pages_dir, titles_dir, esnad_dir]:
        for book_id in iterate_all_books(source_dir):
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
    for book_id in sorted(book_ids_with_content):
        book = books[book_id]
        if book.collection not in target_collections:
            continue

        processed += 1
        if processed % 500 == 0:
            logger.info(f"  Processed {processed:,}/{stats.books_with_content:,} books")

        # Load content
        pages = load_book_pages(pages_dir, book_id)
        titles = load_book_titles(titles_dir, book_id)
        esnad_docs = load_book_esnad(esnad_dir, book_id)

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
    page_num = _extract_page_number(doc)
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
    args = parser.parse_args()

    print(f"{'=' * 70}")
    print("ATHAR - MERGE LUCENE CONTENT WITH MASTER CATALOG")
    print(f"{'=' * 70}")
    print(f"  Collections:   {', '.join(args.collections)}")
    print(f"  Chunk size:    {args.chunk_size}")
    print(f"  Dry run:       {args.dry_run}")
    print(f"  Output dir:    {COLLECTIONS_DIR}")
    print(f"{'=' * 70}")

    # Check prerequisites
    if not MASTER_CATALOG.exists():
        logger.error(f"Master catalog not found: {MASTER_CATALOG}")
        logger.error("Run extract_master_catalog.py first")
        sys.exit(1)

    pages_dir = LUCENE_PAGES_DIR / "pages"
    titles_dir = LUCENE_PAGES_DIR / "titles"
    esnad_dir = LUCENE_PAGES_DIR / "esnad"

    # Check if any content exists
    has_content = any(d.exists() and any(d.glob("*.jsonl")) for d in [pages_dir, titles_dir, esnad_dir])
    if not has_content:
        logger.error("No Lucene content found. Run extract_lucene_pages.py first.")
        sys.exit(1)

    # Load master catalog
    books = load_master_catalog(MASTER_CATALOG)
    if not books:
        logger.error("Failed to load master catalog")
        sys.exit(1)

    # Perform merge
    stats = enrich_and_merge(
        books=books,
        pages_dir=pages_dir,
        titles_dir=titles_dir,
        esnad_dir=esnad_dir,
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
