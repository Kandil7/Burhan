"""
Citation Normalization Engine for Athar Islamic QA system.

Converts various citation formats to standardized [C1], [C2], [C3] format
with structured metadata for display and verification.

Handles:
- Quran citations (Quran 2:255, البقرة 255, Ayat al-Kursi)
- Hadith citations (Sahih Bukhari 1234, رواه البخاري)
- Fiqh book citations (Kitab al-Fiqh, chapter X)
- Fatwa citations (IslamWeb fatwa #12345)

Based on Fanar-Sadiq citation normalization approach.
"""
import re
from typing import Optional

from src.agents.base import Citation
from src.config.logging_config import get_logger

logger = get_logger()


class CitationNormalizer:
    """
    Normalizes citations from various formats to standard [C1], [C2] format.
    
    This engine:
    1. Detects citation patterns in text
    2. Extracts structured metadata
    3. Replaces with normalized [C1], [C2] tags
    4. Maintains mapping for later display
    
    Usage:
        normalizer = CitationNormalizer()
        text = "As stated in Quran 2:255 and Sahih Bukhari 1234..."
        normalized = normalizer.normalize(text)
        # "As stated in [C1] and [C2]..."
        
        citations = normalizer.get_citations()
        # [Citation(id="C1", type="quran", source="Quran 2:255", ...),
        #  Citation(id="C2", type="hadith", source="Sahih Bukhari", ...)]
    """
    
    # ==========================================
    # Citation patterns for detection
    # ==========================================
    PATTERNS = [
        # Quran: "Quran 2:255" or "القرآن 2:255" or "البقرة 255"
        (
            r'(?:quran|القرآن|سورة)\s*(\d+)\s*[:\-]\s*(\d+)',
            "quran",
            "quran_reference"
        ),
        
        # Quran by surah name: "سورة البقرة آية 255"
        (
            r'(?:سورة)\s+([\u0600-\u06FF\s]+?)\s*(?:آية|اية)\s*(\d+)',
            "quran",
            "quran_surah_ayah"
        ),
        
        # Hadith: "صحيح البخاري، حديث 1234" or "Sahih Bukhari 1234"
        (
            r'(?:صحيح|سنن|مسند)\s+(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)'
            r'\s*(?:،|,)?\s*(?:حديث|رقم|hadith|no\.?)\s*(\d+)',
            "hadith",
            "hadith_reference"
        ),
        
        # Simplified hadith: "رواه البخاري"
        (
            r'(?:رواه|mentioned in)\s+(صحيح\s+)?(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)',
            "hadith",
            "hadith_book"
        ),
        
        # Fatwa: "فتوى رقم 12345" or "IslamWeb Fatwa #12345"
        (
            r'(?:فتوى|fatwa)\s*(?:رقم|#)?\s*(\d+)',
            "fatwa",
            "fatwa_reference"
        ),
        
        # Generic book: "كتاب كذا، باب كذا، رقم 123"
        (
            r'([\u0600-\u06FFa-zA-Z\s]+?)\s*(?:،|,)\s*(?:باب|chapter)\s+([\u0600-\u06FFa-zA-Z\s]+?)'
            r'\s*(?:،|,)?\s*(?:رقم|no\.?|hadith)\s*(\d+)',
            "fiqh_book",
            "fiqh_reference"
        ),
    ]
    
    # ==========================================
    # External URL mappings
    # ==========================================
    QURAN_URL_TEMPLATE = "https://quran.com/{surah}/{ayah}"
    HADITH_URLS = {
        "البخاري": "https://sunnah.com/bukhari",
        "bukhari": "https://sunnah.com/bukhari",
        "مسلم": "https://sunnah.com/muslim",
        "muslim": "https://sunnah.com/muslim",
        "الترمذي": "https://sunnah.com/tirmidhi",
        "tirmidhi": "https://sunnah.com/tirmidhi",
        "أبو داود": "https://sunnah.com/abudawud",
        "abudawud": "https://sunnah.com/abudawud",
        "النسائي": "https://sunnah.com/nasai",
        "nasai": "https://sunnah.com/nasai",
        "ابن ماجه": "https://sunnah.com/ibnmajah",
        "ibnmajah": "https://sunnah.com/ibnmajah",
    }
    FATWA_URL_TEMPLATE = "https://www.islamweb.net/en/fatwa/{id}"
    
    def __init__(self):
        self.citation_counter: int = 0
        self.citation_map: dict[str, Citation] = {}
    
    def normalize(self, text: str) -> str:
        """
        Normalize all citations in text to [C1], [C2] format.
        
        Args:
            text: Text containing citations in various formats
            
        Returns:
            Text with citations replaced by [C1], [C2], etc.
        """
        normalized_text = text
        self.citation_counter = 0
        self.citation_map = {}
        
        for pattern, citation_type, pattern_name in self.PATTERNS:
            matches = list(re.finditer(pattern, normalized_text, re.IGNORECASE))
            
            # Process matches in reverse to preserve positions
            for match in reversed(matches):
                self.citation_counter += 1
                citation_id = f"C{self.citation_counter}"
                
                # Build citation object
                citation = self._build_citation(match, citation_type, pattern_name)
                citation.id = citation_id
                self.citation_map[citation_id] = citation
                
                # Replace in text
                normalized_text = (
                    normalized_text[:match.start()] +
                    f"[{citation_id}]" +
                    normalized_text[match.end():]
                )
        
        # Reverse the order since we processed in reverse
        self.citation_map = dict(
            sorted(self.citation_map.items(), key=lambda x: int(x[0][1:]))
        )
        
        if self.citation_counter > 0:
            logger.info(
                "citation.normalized",
                count=self.citation_counter,
                citations=list(self.citation_map.keys())
            )
        
        return normalized_text
    
    def _build_citation(
        self,
        match,
        citation_type: str,
        pattern_name: str
    ) -> Citation:
        """Build structured citation from regex match."""
        
        if citation_type == "quran":
            return self._build_quran_citation(match, pattern_name)
        elif citation_type == "hadith":
            return self._build_hadith_citation(match, pattern_name)
        elif citation_type == "fatwa":
            return self._build_fatwa_citation(match)
        elif citation_type == "fiqh_book":
            return self._build_fiqh_citation(match)
        else:
            return Citation(
                id="",
                type="unknown",
                source=match.group(0),
                reference=match.group(0)
            )
    
    def _build_quran_citation(self, match, pattern_name: str) -> Citation:
        """Build Quran citation from match."""
        if pattern_name == "quran_reference":
            surah = match.group(1)
            ayah = match.group(2)
            return Citation(
                id="",
                type="quran",
                source=f"Quran {surah}:{ayah}",
                reference=f"Surah {surah}, Ayah {ayah}",
                url=self.QURAN_URL_TEMPLATE.format(surah=surah, ayah=ayah)
            )
        else:
            # Surah name + ayah pattern
            surah_name = match.group(1).strip()
            ayah = match.group(2)
            return Citation(
                id="",
                type="quran",
                source=f"Quran: {surah_name}:{ayah}",
                reference=f"Surah {surah_name}, Ayah {ayah}",
                url=None  # Would need surah number lookup
            )
    
    def _build_hadith_citation(self, match, pattern_name: str) -> Citation:
        """Build Hadith citation from match."""
        if pattern_name == "hadith_reference":
            book = match.group(1)
            number = match.group(2)
            book_key = book.strip().lower().replace(" ", "")
            url = self.HADITH_URLS.get(book_key, self.HADITH_URLS.get(book, ""))
            
            return Citation(
                id="",
                type="hadith",
                source=f"Sahih {book}",
                reference=f"Hadith #{number}",
                url=f"{url}/{number}" if url else None
            )
        else:
            # Simplified: "رواه البخاري"
            book = match.group(2) if match.group(2) else match.group(1)
            book_key = book.strip().lower().replace(" ", "")
            url = self.HADITH_URLS.get(book_key, self.HADITH_URLS.get(book, ""))
            
            return Citation(
                id="",
                type="hadith",
                source=f"Collected by {book}",
                reference=match.group(0),
                url=url
            )
    
    def _build_fatwa_citation(self, match) -> Citation:
        """Build Fatwa citation from match."""
        fatwa_number = match.group(1)
        return Citation(
            id="",
            type="fatwa",
            source=f"IslamWeb Fatwa",
            reference=f"Fatwa #{fatwa_number}",
            url=self.FATWA_URL_TEMPLATE.format(id=fatwa_number)
        )
    
    def _build_fiqh_citation(self, match) -> Citation:
        """Build Fiqh book citation from match."""
        book = match.group(1).strip()
        chapter = match.group(2).strip()
        number = match.group(3)
        
        return Citation(
            id="",
            type="fiqh_book",
            source=book,
            reference=f"Chapter: {chapter}, #{number}"
        )
    
    def get_citations(self) -> list[Citation]:
        """Get all normalized citations in order."""
        return list(self.citation_map.values())
    
    def reset(self):
        """Reset the normalizer for new text."""
        self.citation_counter = 0
        self.citation_map = {}
