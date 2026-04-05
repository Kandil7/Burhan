"""
Quotation Validation Engine for Athar Islamic QA system.

Verifies if user-provided text is actually from the Quran.
Prevents hallucination and false attribution to Quran.

Phase 3: Critical for Quran authenticity verification.
"""
import re
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.data.models.quran import Ayah
from src.config.logging_config import get_logger

logger = get_logger()


class QuotationValidatoratorError(Exception):
    """Error in quotation validation."""
    pass


class QuotationValidatorator:
    """
    Validates if text is from the Quran.
    
    Uses fuzzy matching to handle:
    - Diacritic differences
    - Alef variations (أ إ آ ا)
    - Ya variations (ى ي)
    - Minor typos
    
    Usage:
        validator = QuotationValidatorator(session)
        result = await validator.validate("بسم الله الرحمن الرحيم")
    """
    
    def __init__(self, session: Session, similarity_threshold: float = 0.85):
        """
        Initialize validator.
        
        Args:
            session: Database session
            similarity_threshold: Minimum similarity score (0.0-1.0)
        """
        self.session = session
        self.threshold = similarity_threshold
    
    async def validate(self, text: str) -> dict:
        """
        Validate if text is from Quran.
        
        Args:
            text: User-provided text claimed to be Quran
            
        Returns:
            Validation result dict:
            - is_quran: bool
            - confidence: float (0.0-1.0)
            - matched_ayah: Optional[dict]
            - suggestion: str (if not exact match)
        """
        if not text or not text.strip():
            return {
                "is_quran": False,
                "confidence": 0.0,
                "matched_ayah": None,
                "suggestion": "No text provided"
            }
        
        # Normalize text
        normalized = self.normalize_arabic(text)
        
        # Try exact match first
        exact_match = await self._find_exact_match(normalized)
        if exact_match:
            return {
                "is_quran": True,
                "confidence": 1.0,
                "matched_ayah": exact_match,
                "suggestion": None
            }
        
        # Try fuzzy match
        fuzzy_match = await self._find_fuzzy_match(normalized, self.threshold)
        if fuzzy_match:
            return {
                "is_quran": True,
                "confidence": fuzzy_match["similarity"],
                "matched_ayah": fuzzy_match["ayah"],
                "suggestion": f"Did you mean: {fuzzy_match['ayah']['text_uthmani']}"
            }
        
        # No match found
        return {
            "is_quran": False,
            "confidence": 0.0,
            "matched_ayah": None,
            "suggestion": "This text does not match any Quranic verse"
        }
    
    def normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for comparison.
        
        - Remove diacritics
        - Standardize alef (أ إ آ → ا)
        - Standardize ya (ى → ي)
        - Remove punctuation
        
        Args:
            text: Arabic text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove diacritics
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        
        # Standardize alef
        text = re.sub(r'[أإآٱ]', 'ا', text)
        
        # Standardize ya
        text = re.sub(r'ى', 'ي', text)
        
        # Standardize hamza
        text = re.sub(r'[ة]', 'ه', text)
        
        # Remove punctuation and whitespace
        text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9]', '', text)
        
        return text.strip()
    
    async def _find_exact_match(self, normalized_text: str) -> Optional[dict]:
        """Find exact match in Quran text."""
        # Search in database
        ayahs = (
            self.session.query(Ayah)
            .filter(Ayah.text_uthmani.contains(normalized_text))
            .limit(1)
            .all()
        )
        
        if ayahs:
            ayah = ayahs[0]
            return {
                "surah_number": ayah.surah.number,
                "surah_name_en": ayah.surah.name_en,
                "ayah_number": ayah.number_in_surah,
                "text_uthmani": ayah.text_uthmani,
                "quran_url": f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}"
            }
        
        return None
    
    async def _find_fuzzy_match(
        self,
        normalized_text: str,
        threshold: float
    ) -> Optional[dict]:
        """
        Find fuzzy match using similarity.
        
        Phase 3: Simple contains-based matching
        Phase 4: Will use pg_trgm similarity scores
        """
        # Search for ayahs that contain the text
        ayahs = (
            self.session.query(Ayah)
            .filter(Ayah.text_uthmani.like(f"%{normalized_text}%"))
            .limit(5)
            .all()
        )
        
        if not ayahs:
            return None
        
        # Calculate similarity for each match
        best_match = None
        best_similarity = 0.0
        
        for ayah in ayahs:
            ayah_normalized = self.normalize_arabic(ayah.text_uthmani)
            similarity = self._calculate_similarity(normalized_text, ayah_normalized)
            
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = {
                    "similarity": similarity,
                    "ayah": {
                        "surah_number": ayah.surah.number,
                        "surah_name_en": ayah.surah.name_en,
                        "ayah_number": ayah.number_in_surah,
                        "text_uthmani": ayah.text_uthmani,
                        "quran_url": f"https://quran.com/{ayah.surah.number}/{ayah.number_in_surah}"
                    }
                }
        
        return best_match
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Simple character-level similarity.
        Phase 4: Will use more advanced algorithms.
        """
        if not text1 or not text2:
            return 0.0
        
        # Use simple ratio
        len1, len2 = len(text1), len(text2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Count matching characters
        matches = sum(1 for c in text1 if c in text2)
        similarity = matches / max(len1, len2)
        
        return min(1.0, similarity)
