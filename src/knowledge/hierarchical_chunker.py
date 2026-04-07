"""
Hierarchical Chunker for Islamic books.

Production-ready chunking engine that respects:
- Book metadata (book_id, title, author, category)
- Chapter boundaries (<span data-type="title" id=toc-N>)
- Page boundaries ([Page N])
- Content-based splitting (hadith numbers, section headers, fatwa Q&A pairs)
- Target: 300-600 tokens per chunk (600-1800 Arabic characters)
- Overlap: 50-75 tokens between chunks

Special handling for:
- Fatwa files: Split by individual Q&A pairs
- Hadith books: Keep hadith + chain + explanation together
- Tafsir books: Split by verse/surah
- Tiny books (<5KB): Single chunk
- HTML span cleaning: Strip <span> but use as markers

Usage:
    from src.knowledge.hierarchical_chunker import HierarchicalChunker, BookMetadata

    chunker = HierarchicalChunker()
    metadata = BookMetadata(
        book_id=1, title="Book Title", author="Author Name",
        author_death=1225, category="العقيدة", category_en="creed",
    )
    chunks = chunker.chunk_book(text, metadata)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ── Constants ─────────────────────────────────────────────────────────────

# Target chunk sizes in characters (approx 3 chars/token for Arabic)
MIN_CHUNK_CHARS = 600   # ~200 tokens
TARGET_CHUNK_CHARS = 1200  # ~400 tokens
MAX_CHUNK_CHARS = 1800   # ~600 tokens
OVERLAP_CHARS = 225      # ~75 tokens

# Tiny book threshold (bytes)
TINY_BOOK_THRESHOLD = 5 * 1024  # 5 KB

# Fatwa file book IDs
FATWA_BOOK_IDS = {27107}

# Category → collection mapping (40+ categories → 10 RAG collections)
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


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class BookMetadata:
    """Metadata for a book, used to enrich every chunk."""
    book_id: int
    title: str
    author: str = ""
    author_death: Optional[int] = None
    category: str = ""
    category_en: str = ""
    file_path: str = ""
    source: str = "shamela"

    def to_chunk_payload(self) -> dict[str, Any]:
        """Convert to dict for embedding in chunk payloads."""
        return {
            "book_id": self.book_id,
            "book_title": self.title,
            "author": self.author,
            "author_death": self.author_death,
            "category": self.category,
            "category_en": self.category_en,
            "collection": CATEGORY_TO_COLLECTION.get(self.category, "general_islamic"),
            "source": self.source,
        }

    @classmethod
    def from_books_json_entry(cls, entry: dict[str, Any]) -> BookMetadata:
        """Create from a books.json entry dict."""
        authors = entry.get("authors", [])
        main_author = ""
        author_death: Optional[int] = None
        for a in authors:
            if a.get("role") == "main":
                main_author = a.get("name", "")
                author_death = a.get("death")
                break
        if not main_author and authors:
            main_author = authors[0].get("name", "")
            author_death = authors[0].get("death")

        cat_name = entry.get("cat_name", "")
        return cls(
            book_id=entry.get("id", 0),
            title=entry.get("title", ""),
            author=main_author,
            author_death=author_death,
            category=cat_name,
            category_en=CATEGORY_TO_COLLECTION.get(cat_name, "general_islamic"),
            file_path=entry.get("file", ""),
        )


@dataclass
class Chunk:
    """A single chunk of text with full metadata."""
    chunk_id: str
    book_id: int
    book_title: str
    author: str
    author_death: Optional[int]
    category: str
    category_en: str
    page_number: Optional[int]
    chapter_title: str
    chapter_id: Optional[int]
    chunk_index: int
    content: str
    content_length: int
    chunk_type: str  # fatwa_qa, hadith, tafsir_verse, chapter, page, content
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = {
            "chunk_id": self.chunk_id,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "author": self.author,
            "author_death": self.author_death,
            "category": self.category,
            "category_en": self.category_en,
            "page_number": self.page_number,
            "chapter_title": self.chapter_title,
            "chapter_id": self.chapter_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "content_length": self.content_length,
            "chunk_type": self.chunk_type,
        }
        d.update(self.metadata)
        return d


# ── Hierarchical Chunker ─────────────────────────────────────────────────

class HierarchicalChunker:
    """
    Production-ready hierarchical chunker for Islamic texts.

    Chunking hierarchy:
        Level 1: Book metadata
        Level 2: Chapter boundaries (<span data-type="title" id=toc-N>)
        Level 3: Page boundaries ([Page N])
        Level 4: Content-based splitting (fatwa Q&A, hadith, verses)
        Level 5: Size-based splitting with overlap

    Special strategies per content type:
        - Fatwa files: Split by السؤال/الجواب pairs
        - Hadith books: Keep hadith + isnad + sharh together
        - Tafsir books: Split by verse references
        - Tiny books (<5KB): Single chunk

    Args:
        min_chars: Minimum chunk size in characters.
        target_chars: Target chunk size in characters.
        max_chars: Maximum chunk size in characters.
        overlap_chars: Overlap size in characters.
    """

    def __init__(
        self,
        min_chars: int = MIN_CHUNK_CHARS,
        target_chars: int = TARGET_CHUNK_CHARS,
        max_chars: int = MAX_CHUNK_CHARS,
        overlap_chars: int = OVERLAP_CHARS,
    ) -> None:
        self.min_chars = min_chars
        self.target_chars = target_chars
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

        # Compiled regex patterns
        self._span_pattern = re.compile(
            r'<span\s+data-type=["\']title["\']\s+id=toc-(\d+)["\']?[^>]*>(.*?)</span>',
            re.DOTALL,
        )
        self._span_open_pattern = re.compile(
            r'<span\s+data-type=["\']title["\']\s+id=toc-(\d+)[^>]*>',
        )
        self._span_close_pattern = re.compile(r"</span>")
        self._page_pattern = re.compile(r"\[Page\s+(\d+)\]")
        self._footnote_inline = re.compile(r"¬[٠-٩0-9]+")
        self._html_tags = re.compile(r"<[^>]+>")
        self._verse_pattern = re.compile(r"﴿[^﴾]*﴾")
        self._quran_ref = re.compile(r"(?:قوله\s+تعالى|قال\s+الله|قال\s+الله\s+تعالى)")

    # ── Public API ─────────────────────────────────────────────────────

    def chunk_book(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """
        Chunk a complete book using the hierarchical strategy.

        Args:
            text: Full book text.
            metadata: Book metadata.

        Returns:
            List of Chunk objects with enriched metadata.
        """
        # Tiny book → single chunk
        if len(text.encode("utf-8")) < TINY_BOOK_THRESHOLD:
            return self._single_chunk(text, metadata)

        # Fatwa file → Q&A pair splitting
        if metadata.book_id in FATWA_BOOK_IDS:
            return self._chunk_fatwa(text, metadata)

        # Category-specific strategies
        if metadata.category in ("التفسير", "علوم القرآن وأصول التفسير"):
            return self._chunk_tafsir(text, metadata)

        if metadata.category in ("كتب السنة", "الجوامع"):
            return self._chunk_hadith_collection(text, metadata)

        # Default: hierarchical chapter → page → content splitting
        return self._chunk_hierarchical(text, metadata)

    # ── Fatwa Chunking ─────────────────────────────────────────────────

    def _chunk_fatwa(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """
        Chunk fatwa file by individual Q&A pairs.

        Pattern: السؤال ... [الفَتْوَى] ... الجواب
        Each Q&A pair is kept as one chunk (or split if too large).
        """
        cleaned = self._clean_html(text)
        # Strip book header
        header_end = cleaned.find("[Footnotes]")
        if header_end > 0:
            # Find the second [Footnotes] which ends the header section
            second_footnote = cleaned.find("[Footnotes]", header_end + 10)
            if second_footnote > 0:
                next_page = cleaned.find("[Page", second_footnote)
                if next_page > 0:
                    cleaned = cleaned[next_page:]

        # Split by السؤال
        parts = cleaned.split("السؤال")
        if len(parts) <= 1:
            return self._chunk_hierarchical(text, metadata)

        chunks: list[Chunk] = []
        chunk_index = 0

        for i, part in enumerate(parts[1:], start=1):
            # Reconstruct the QA pair
            qa_text = f"السؤال{part}"

            # Extract page number
            page_match = self._page_pattern.search(qa_text)
            page_num = int(page_match.group(1)) if page_match else None

            # Extract fatwa title if present
            fatwa_title = ""
            fatwa_match = re.search(r"\[الفَتْوَى\]", qa_text)
            if fatwa_match:
                fatwa_title = "فتوى"

            # If the QA pair is within size limits, keep it whole
            if len(qa_text) <= self.max_chars:
                chunks.append(self._make_chunk(
                    content=qa_text.strip(),
                    metadata=metadata,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    chapter_title=fatwa_title,
                    chunk_type="fatwa_qa",
                ))
                chunk_index += 1
            else:
                # Split large Q&A pairs by content boundaries
                sub_chunks = self._split_oversized(qa_text.strip())
                for sub_content in sub_chunks:
                    chunks.append(self._make_chunk(
                        content=sub_content,
                        metadata=metadata,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        chapter_title=fatwa_title,
                        chunk_type="fatwa_qa",
                    ))
                    chunk_index += 1

        return chunks

    # ── Tafsir Chunking ────────────────────────────────────────────────

    def _chunk_tafsir(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """
        Chunk tafsir by verse/surah references.

        Splits on Quranic verse markers (﴿...﴾) and chapter boundaries.
        """
        chapters = self._extract_chapters(text)
        chunks: list[Chunk] = []
        chunk_index = 0

        for chapter_title, chapter_id, chapter_text in chapters:
            # Find verse boundaries within chapter
            verse_splits = self._split_by_verses(chapter_text)

            current = ""
            for segment in verse_splits:
                if len(current) + len(segment) > self.max_chars and current.strip():
                    # Save current chunk
                    page_num = self._extract_page_number(current)
                    chunks.append(self._make_chunk(
                        content=current.strip(),
                        metadata=metadata,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        chapter_title=chapter_title,
                        chapter_id=chapter_id,
                        chunk_type="tafsir_verse",
                    ))
                    chunk_index += 1

                    # Start with overlap
                    current = self._get_overlap(current) + segment
                else:
                    current += segment

            if current.strip():
                page_num = self._extract_page_number(current)
                chunks.append(self._make_chunk(
                    content=current.strip(),
                    metadata=metadata,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    chapter_title=chapter_title,
                    chapter_id=chapter_id,
                    chunk_type="tafsir_verse",
                ))
                chunk_index += 1

        return chunks

    # ── Hadith Collection Chunking ─────────────────────────────────────

    def _chunk_hadith_collection(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """
        Chunk hadith collection keeping each hadith atomic.

        Preserves hadith text + isnad (chain) + sharh (explanation) together.
        """
        chapters = self._extract_chapters(text)
        chunks: list[Chunk] = []
        chunk_index = 0

        for chapter_title, chapter_id, chapter_text in chapters:
            # Split chapter into content segments
            segments = self._split_by_paragraphs(chapter_text)

            current = ""
            for segment in segments:
                if len(current) + len(segment) > self.max_chars and current.strip():
                    page_num = self._extract_page_number(current)
                    chunks.append(self._make_chunk(
                        content=current.strip(),
                        metadata=metadata,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        chapter_title=chapter_title,
                        chapter_id=chapter_id,
                        chunk_type="hadith",
                    ))
                    chunk_index += 1
                    current = self._get_overlap(current) + segment
                else:
                    current += segment

            if current.strip():
                page_num = self._extract_page_number(current)
                chunks.append(self._make_chunk(
                    content=current.strip(),
                    metadata=metadata,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    chapter_title=chapter_title,
                    chapter_id=chapter_id,
                    chunk_type="hadith",
                ))
                chunk_index += 1

        return chunks

    # ── Default Hierarchical Chunking ──────────────────────────────────

    def _chunk_hierarchical(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """
        Default hierarchical chunking: chapter → page → content.

        Uses HTML span markers for chapters, page markers for pages,
        and size-based splitting for content.
        """
        chapters = self._extract_chapters(text)
        chunks: list[Chunk] = []
        chunk_index = 0

        for chapter_title, chapter_id, chapter_text in chapters:
            # Split chapter by page boundaries
            pages = self._split_by_pages(chapter_text)

            current = ""
            for page_text, page_num in pages:
                if len(current) + len(page_text) > self.max_chars and current.strip():
                    # Save current chunk
                    p_num = self._extract_page_number(current) or page_num
                    chunks.append(self._make_chunk(
                        content=current.strip(),
                        metadata=metadata,
                        chunk_index=chunk_index,
                        page_number=p_num,
                        chapter_title=chapter_title,
                        chapter_id=chapter_id,
                        chunk_type="chapter",
                    ))
                    chunk_index += 1

                    # Start new chunk with overlap
                    current = self._get_overlap(current) + page_text
                else:
                    current += page_text

            # Flush remaining
            if current.strip():
                p_num = self._extract_page_number(current)
                chunks.append(self._make_chunk(
                    content=current.strip(),
                    metadata=metadata,
                    chunk_index=chunk_index,
                    page_number=p_num,
                    chapter_title=chapter_title,
                    chapter_id=chapter_id,
                    chunk_type="page" if pages else "content",
                ))
                chunk_index += 1

        # If no chapters were found, do basic content splitting
        if not chunks:
            chunks = self._chunk_by_content(text, metadata)

        return chunks

    # ── Content-Based Splitting ────────────────────────────────────────

    def _chunk_by_content(
        self,
        text: str,
        metadata: BookMetadata,
    ) -> list[Chunk]:
        """Fallback: split by paragraphs with size limits."""
        paragraphs = self._split_by_paragraphs(text)
        chunks: list[Chunk] = []
        chunk_index = 0
        current = ""

        for para in paragraphs:
            if len(current) + len(para) > self.max_chars and current.strip():
                chunks.append(self._make_chunk(
                    content=current.strip(),
                    metadata=metadata,
                    chunk_index=chunk_index,
                    page_number=self._extract_page_number(current),
                    chapter_title="",
                    chunk_type="content",
                ))
                chunk_index += 1
                current = self._get_overlap(current) + para
            else:
                current += para

        if current.strip():
            chunks.append(self._make_chunk(
                content=current.strip(),
                metadata=metadata,
                chunk_index=chunk_index,
                page_number=self._extract_page_number(current),
                chapter_title="",
                chunk_type="content",
            ))

        return chunks

    def _split_oversized(self, text: str) -> list[str]:
        """Split an oversized chunk by natural boundaries."""
        # Try splitting by page markers
        pages = self._page_pattern.split(text)
        if len(pages) > 1:
            result = []
            for i in range(0, len(pages) - 1, 2):
                page_num = pages[i + 1] if i + 1 < len(pages) else ""
                result.append(f"[Page {page_num}]{pages[i]}")
            # Re-split any still-oversized
            final = []
            for r in result:
                if len(r) > self.max_chars:
                    final.extend(self._split_by_content_size(r))
                else:
                    final.append(r)
            return final

        return self._split_by_content_size(text)

    def _split_by_content_size(self, text: str) -> list[str]:
        """Split text by character size with sentence/paragraph awareness."""
        if len(text) <= self.max_chars:
            return [text]

        chunks: list[str] = []
        # Split by double newlines first
        segments = re.split(r"\n\n+", text)
        current = ""

        for seg in segments:
            if len(current) + len(seg) > self.max_chars and current.strip():
                chunks.append(current.strip())
                current = seg
            else:
                current += ("\n\n" if current else "") + seg

        if current.strip():
            chunks.append(current.strip())

        # Final pass: hard-split any still-oversized chunks
        result = []
        for c in chunks:
            if len(c) > self.max_chars:
                result.extend(self._hard_split(c))
            else:
                result.append(c)

        return result

    def _hard_split(self, text: str) -> list[str]:
        """Hard split text at character boundary, trying to break at sentence end."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + self.max_chars
            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to find a good break point
            search_area = text[max(start, end - 200):end]
            # Try sentence-ending punctuation
            for punct in ["۔", ".", "؟", "!", "\n"]:
                idx = search_area.rfind(punct)
                if idx > 50:  # Avoid very short segments
                    end = start + max(0, end - 200) + idx + 1
                    break

            chunks.append(text[start:end])
            start = end

        return chunks

    # ── Text Parsing Helpers ───────────────────────────────────────────

    def _extract_chapters(self, text: str) -> list[tuple[str, Optional[int], str]]:
        """
        Extract chapters from text using span markers.

        Returns list of (chapter_title, chapter_id, chapter_text).
        """
        # Find all chapter markers
        markers = list(self._span_pattern.finditer(text))

        if not markers:
            # No chapter markers found → treat whole text as one chapter
            cleaned = self._clean_html(text)
            # Strip header
            cleaned = self._strip_header(cleaned)
            return [("المحتوى الرئيسي", None, cleaned)]

        chapters: list[tuple[str, Optional[int], str]] = []

        for i, match in enumerate(markers):
            chapter_id = int(match.group(1))
            chapter_title = match.group(2).strip()

            # Text starts after the closing </span>
            start = match.end()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)

            chapter_text = text[start:end]
            chapter_text = self._clean_html(chapter_text)
            chapter_text = self._strip_header(chapter_text)

            if chapter_title:
                chapter_text = f"{chapter_title}\n{chapter_text}"

            chapters.append((chapter_title, chapter_id, chapter_text))

        return chapters

    def _split_by_pages(self, text: str) -> list[tuple[str, Optional[int]]]:
        """
        Split text by page boundaries [Page N].

        Returns list of (page_text, page_number).
        """
        positions = [(m.start(), int(m.group(1))) for m in self._page_pattern.finditer(text)]

        if not positions:
            return [(text, None)]

        pages: list[tuple[str, Optional[int]]] = []
        for i, (pos, page_num) in enumerate(positions):
            start = pos
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            page_text = text[start:end]
            pages.append((page_text, page_num))

        return pages

    def _split_by_verses(self, text: str) -> list[str]:
        """
        Split tafsir text by verse references.

        Keeps verses with their surrounding commentary together.
        """
        # Split on verse markers but keep the verses
        parts: list[str] = []
        current = ""

        # Find verse positions
        verse_positions = [
            (m.start(), m.end()) for m in self._verse_pattern.finditer(text)
        ]
        quran_ref_positions = [
            (m.start(), m.end()) for m in self._quran_ref.finditer(text)
        ]
        all_positions = sorted(verse_positions + quran_ref_positions)

        if not all_positions:
            # Fallback to paragraph splitting
            return self._split_by_paragraphs(text)

        last_end = 0
        for start, end in all_positions:
            # Add text before this verse reference
            prefix = text[last_end:start]
            if prefix.strip():
                current += prefix
            # Add the verse marker itself
            current += text[start:end]

            if len(current) > self.min_chars:
                parts.append(current)
                current = ""

            last_end = end

        if text[last_end:].strip():
            current += text[last_end:]

        if current.strip():
            parts.append(current)

        if not parts:
            return self._split_by_paragraphs(text)

        return parts

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """Split text by paragraph boundaries, filtering very short ones."""
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if len(p.strip()) > 20]

    # ── Text Cleaning ──────────────────────────────────────────────────

    def _clean_html(self, text: str) -> str:
        """
        Clean HTML from text while preserving semantic structure.

        - Strips <span> tags but preserves their content
        - Keeps page markers intact
        - Removes other HTML tags
        """
        # Remove closing span tags
        text = self._span_close_pattern.sub("", text)
        # Remove opening span tags (keeping content)
        text = self._span_open_pattern.sub("", text)
        # Remove any remaining HTML tags
        text = self._html_tags.sub("", text)
        # Clean up extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _strip_header(self, text: str) -> str:
        """Strip the book header (Book ID, Book Name, separator line)."""
        # Remove the standard Shamela header
        lines = text.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("=" * 40):
                start_idx = i + 1
                break
            if line.startswith("Book ID:"):
                continue
            if line.startswith("Book Name:"):
                continue
            if line.strip() and not line.startswith("[") and not line.startswith("="):
                break
        return "\n".join(lines[start_idx:]).strip()

    # ── Chunk Creation ─────────────────────────────────────────────────

    def _make_chunk(
        self,
        content: str,
        metadata: BookMetadata,
        chunk_index: int,
        page_number: Optional[int] = None,
        chapter_title: str = "",
        chapter_id: Optional[int] = None,
        chunk_type: str = "content",
    ) -> Chunk:
        """Create a Chunk object with full metadata."""
        return Chunk(
            chunk_id=f"{metadata.book_id}_{chunk_index:06d}",
            book_id=metadata.book_id,
            book_title=metadata.title,
            author=metadata.author,
            author_death=metadata.author_death,
            category=metadata.category,
            category_en=metadata.category_en,
            page_number=page_number,
            chapter_title=chapter_title,
            chapter_id=chapter_id,
            chunk_index=chunk_index,
            content=content,
            content_length=len(content),
            chunk_type=chunk_type,
            metadata=metadata.to_chunk_payload(),
        )

    def _single_chunk(self, text: str, metadata: BookMetadata) -> list[Chunk]:
        """Create a single chunk for tiny books."""
        cleaned = self._clean_html(text)
        return [self._make_chunk(
            content=cleaned.strip(),
            metadata=metadata,
            chunk_index=0,
            chapter_title="",
            chunk_type="tiny_book",
        )]

    # ── Overlap Helpers ────────────────────────────────────────────────

    def _get_overlap(self, text: str) -> str:
        """Extract overlap text from the end of a chunk."""
        if len(text) <= self.overlap_chars:
            return text
        return text[-self.overlap_chars:]

    def _extract_page_number(self, text: str) -> Optional[int]:
        """Extract page number from text."""
        match = self._page_pattern.search(text)
        return int(match.group(1)) if match else None
