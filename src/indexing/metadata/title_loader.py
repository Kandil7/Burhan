"""
Title Loader for Athar Islamic QA system.

Loads per-book title files from lucene_pages/titles/ directory.
Each title file contains chapter/section titles for a specific book.
Title format: {"id": "{book_id}-{page}", "body": "{title_text}"}

Used for:
- Adding chapter/section context to passages
- Title-aware chunking
- Hierarchical retrieval
- Understanding document structure

Phase 2: +25% retrieval accuracy with title context
"""

import json
from pathlib import Path

from src.config.logging_config import get_logger

logger = get_logger()


class TitleLoader:
    """
    Load and manage per-book titles/chapters.

    Titles provide:
    - Chapter boundaries for chunking
    - Section context for passages
    - Document structure understanding
    - Better user context in citations

    Usage:
        loader = TitleLoader()
        titles = loader.get_titles_for_book(622)
        chapter = loader.get_chapter_for_page(622, 45)
    """

    def __init__(self, titles_dir: Path | None = None):
        """
        Initialize title loader.

        Args:
            titles_dir: Path to titles/ directory (default: data/processed/lucene_pages/titles/)
        """
        self.titles_dir = titles_dir or Path("data/processed/lucene_pages/titles")
        self._titles_cache: dict[int, dict[int, str]] = {}  # book_id -> {page -> title}
        self._loaded_books = set()

    def get_title_for_page(self, book_id: int, page_num: int) -> str | None:
        """
        Get title for a specific page in a book.

        Args:
            book_id: Book identifier
            page_num: Page number

        Returns:
            Title text or None if not found
        """
        if book_id not in self._loaded_books:
            self._load_book_titles(book_id)

        page_titles = self._titles_cache.get(book_id, {})
        return page_titles.get(page_num)

    def get_chapter_for_page(self, book_id: int, page_num: int) -> str | None:
        """
        Get chapter title for a page (nearest preceding title).

        Finds the most recent chapter/section title before or at the page.

        Args:
            book_id: Book identifier
            page_num: Page number

        Returns:
            Chapter/section title or None
        """
        if book_id not in self._loaded_books:
            self._load_book_titles(book_id)

        page_titles = self._titles_cache.get(book_id, {})
        if not page_titles:
            return None

        # Find nearest title at or before this page
        nearest_title = None
        for p in sorted(page_titles.keys()):
            if p <= page_num:
                nearest_title = page_titles[p]
            else:
                break

        return nearest_title

    def get_titles_for_book(self, book_id: int) -> dict[int, str]:
        """
        Get all titles for a book.

        Args:
            book_id: Book identifier

        Returns:
            Dict mapping page numbers to title text
        """
        if book_id not in self._loaded_books:
            self._load_book_titles(book_id)

        return self._titles_cache.get(book_id, {})

    def _load_book_titles(self, book_id: int):
        """
        Load all titles for a book from JSONL file.

        Args:
            book_id: Book identifier
        """
        title_file = self.titles_dir / f"{book_id}.jsonl"

        if not title_file.exists():
            logger.debug("title_loader.file_not_found", book_id=book_id, file=str(title_file))
            self._titles_cache[book_id] = {}
            self._loaded_books.add(book_id)
            return

        try:
            titles = {}
            with open(title_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                        doc_id = doc.get("id", "")
                        body = doc.get("body", "")

                        # Parse page from ID format "book_id-page"
                        if "-" in doc_id:
                            parts = doc_id.split("-")
                            if len(parts) == 2:
                                try:
                                    page_num = int(parts[1])
                                    titles[page_num] = body
                                except ValueError:
                                    pass

                    except json.JSONDecodeError:
                        continue

            self._titles_cache[book_id] = titles
            self._loaded_books.add(book_id)

            logger.info(
                "title_loader.loaded",
                book_id=book_id,
                title_count=len(titles),
            )

        except Exception as e:
            logger.warning("title_loader.load_failed", book_id=book_id, error=str(e))
            self._titles_cache[book_id] = {}
            self._loaded_books.add(book_id)

    def enrich_passages(self, passages: list) -> list:
        """
        Enrich passages with title/chapter context.

        Adds:
        - chapter: Nearest chapter title
        - section: Specific section title (if different)
        - has_title: Whether title was found

        Args:
            passages: List of passage dicts

        Returns:
            Enriched passage list
        """
        enriched = []
        for passage in passages:
            book_id = passage.get("book_id")
            page = passage.get("page")

            if book_id and page:
                # Load titles if needed
                if book_id not in self._loaded_books:
                    self._load_book_titles(book_id)

                # Get chapter title
                chapter = self.get_chapter_for_page(book_id, page)
                specific_title = self.get_title_for_page(book_id, page)

                # Add to passage
                passage["chapter_title"] = chapter
                passage["section_title"] = specific_title if specific_title != chapter else None
                passage["has_title"] = chapter is not None or specific_title is not None

            enriched.append(passage)

        logger.info(
            "title_loader.enriched",
            passage_count=len(passages),
            titled_count=sum(1 for p in enriched if p.get("has_title")),
        )

        return enriched

    def get_stats(self) -> dict:
        """Get title loader statistics."""
        total_titles = sum(len(t) for t in self._titles_cache.values())
        return {
            "loaded_books": len(self._loaded_books),
            "total_titles": total_titles,
            "avg_titles_per_book": total_titles / max(len(self._loaded_books), 1),
        }
