"""
Document Chunker for Islamic books.

Splits Islamic texts into RAG-ready chunks while respecting:
- Paragraph boundaries
- Chapter/section breaks
- Ayah/hadith boundaries
- Maximum chunk size (500 tokens)
- Overlap for context (50 tokens)

Phase 3: Foundation for Fiqh and General Knowledge RAG.
"""
import re
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger()


class IslamicDocumentChunker:
    """
    Chunker optimized for Islamic texts.
    
    Handles:
    - Quran commentary (tafsir)
    - Hadith collections
    - Fiqh books
    - Islamic history
    - Arabic literature
    
    Usage:
        chunker = IslamicDocumentChunker()
        chunks = chunker.chunk_book(text, book_metadata)
    """
    
    MAX_CHUNK_SIZE = 500  # tokens
    OVERLAP_SIZE = 50  # tokens
    
    def __init__(self):
        """Initialize chunker."""
        pass
    
    def chunk_book(
        self,
        text: str,
        metadata: dict,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> list[dict]:
        """
        Chunk a complete book into RAG-ready passages.
        
        Args:
            text: Book text
            metadata: Book metadata
            chunk_size: Max chunk size in tokens (default: 500)
            overlap: Overlap size in tokens (default: 50)
            
        Returns:
            List of chunk dicts with metadata
        """
        chunk_size = chunk_size or self.MAX_CHUNK_SIZE
        overlap = overlap or self.OVERLAP_SIZE
        
        # Split by semantic boundaries
        sections = self._split_by_sections(text)
        
        chunks = []
        chunk_index = 0
        
        for section_text in sections:
            # Further split by paragraphs if needed
            paragraphs = self._split_by_paragraphs(section_text)
            
            current_chunk = ""
            for para in paragraphs:
                # Check if adding paragraph exceeds chunk size
                if len(current_chunk) + len(para) > chunk_size * 4:  # Approx 4 chars per token
                    # Save current chunk
                    if current_chunk.strip():
                        chunks.append(self._create_chunk(
                            current_chunk.strip(),
                            chunk_index,
                            metadata
                        ))
                        chunk_index += 1
                    
                    # Start new chunk with overlap
                    if overlap > 0 and current_chunk.strip():
                        # Get last N characters as overlap
                        overlap_chars = current_chunk.strip()[-overlap*4:]
                        current_chunk = overlap_chars + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
            
            # Save remaining chunk
            if current_chunk.strip():
                chunks.append(self._create_chunk(
                    current_chunk.strip(),
                    chunk_index,
                    metadata
                ))
                chunk_index += 1
        
        logger.info(
            "chunker.book_chunked",
            book=metadata.get("title", "unknown"),
            total_chunks=len(chunks)
        )
        
        return chunks
    
    def _split_by_sections(self, text: str) -> list[str]:
        """
        Split text by section markers.
        
        Looks for:
        - Chapter markers (الفصل، الباب، الجزء)
        - Numbered sections
        - Large whitespace gaps
        """
        # Try to split by common Arabic section markers
        section_pattern = r'(?:الفصل\s+\d+|الباب\s+\d+|الجزء\s+\d+|القسم\s+\d+)'
        sections = re.split(section_pattern, text)
        
        # If no sections found, return full text
        if len(sections) <= 1:
            return [text]
        
        return [s.strip() for s in sections if s.strip()]
    
    def _split_by_paragraphs(self, text: str) -> list[str]:
        """
        Split text by paragraph boundaries.
        
        Handles:
        - Double newlines
        - Arabic paragraph markers
        - Single newlines (as fallback)
        """
        # Split by double newlines first
        paragraphs = text.split("\n\n")
        
        # Filter out empty/very short paragraphs
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
        
        return paragraphs
    
    def _create_chunk(
        self,
        content: str,
        index: int,
        metadata: dict
    ) -> dict:
        """
        Create a chunk dict with metadata.
        
        Args:
            content: Chunk text
            index: Chunk index
            metadata: Book metadata
            
        Returns:
            Chunk dict
        """
        return {
            "chunk_index": index,
            "content": content,
            "metadata": {
                **metadata,
                "chunk_type": "book_passage",
                "language": metadata.get("language", "ar")
            }
        }
    
    def chunk_hadith_collection(self, text: str, metadata: dict) -> list[dict]:
        """
        Chunk hadith collection.
        
        Each hadith is kept atomic (never split mid-hadith).
        
        Args:
            text: Hadith collection text
            metadata: Collection metadata
            
        Returns:
            List of chunk dicts
        """
        # Split by hadith markers (حديث، أخبرنا، حدثنا)
        hadith_pattern = r'(?:حديث\s+\d+|أخبرنا|حدثنا|قال\s+الرسول\s+ﷺ)'
        hadiths = re.split(hadith_pattern, text)
        
        chunks = []
        for i, hadith in enumerate(hadiths):
            if hadith.strip():
                chunks.append(self._create_chunk(
                    hadith.strip(),
                    i,
                    {**metadata, "chunk_type": "hadith"}
                ))
        
        return chunks
    
    def chunk_tafsir(self, text: str, metadata: dict) -> list[dict]:
        """
        Chunk tafsir (Quran commentary).
        
        Respects ayah boundaries.
        
        Args:
            text: Tafsir text
            metadata: Tafsir metadata
            
        Returns:
            List of chunk dicts
        """
        # Split by ayah references (قوله تعالى، قوله سبحانه)
        ayah_pattern = r'(?:قوله\s+تعالى|قوله\s+سبحانه|في\s+تفسير\s+قوله)'
        sections = re.split(ayah_pattern, text)
        
        chunks = []
        for i, section in enumerate(sections):
            if section.strip():
                chunks.append(self._create_chunk(
                    section.strip(),
                    i,
                    {**metadata, "chunk_type": "tafsir_passage"}
                ))
        
        return chunks
