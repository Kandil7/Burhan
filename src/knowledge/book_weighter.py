"""
Book Importance Weighter for Athar Islamic QA system.

Scores books by importance based on:
- Category canonical status (Sahih > Sunan > Commentary)
- Author authority (from authority_scorer)
- Citation frequency (how often cited)
- Historical significance

Uses: master_catalog.json (8,425 books with categories)

Phase 2: +10% relevance, prioritizes canonical texts
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.config.logging_config import get_logger

logger = get_logger()


class BookImportanceWeighter:
    """
    Calculate importance scores for books.

    Importance factors:
    1. Category weight (Sahih books = 1.0)
    2. Author authority (from era/status)
    3. Citation frequency (future)
    4. Book size (larger = more comprehensive)

    Usage:
        weighter = BookImportanceWeighter()
        score = weighter.get_importance_score(book_id=622)
        passages = weighter.weight_passages_by_importance(passages)
    """

    # Category importance weights
    CATEGORY_WEIGHTS = {
        # Hadith collections (most authoritative)
        "صحيح": 1.0,              # Sahih (Bukhari, Muslim)
        "sahih": 1.0,
        "سنن": 0.9,               # Sunan
        "sunan": 0.9,
        "مسند": 0.85,             # Musnad
        "musnad": 0.85,
        
        # Fiqh books
        "الفقه الحنفي": 0.9,
        "الفقه المالكي": 0.9,
        "الفقه الشافعي": 0.9,
        "الفقه الحنبلي": 0.9,
        
        # Tafsir
        "التفسير": 0.85,
        "tafsir": 0.85,
        
        # Aqeedah
        "العقيدة": 0.85,
        "aqeedah": 0.85,
        
        # Seerah
        "السيرة": 0.8,
        "seerah": 0.8,
        
        # General/Islamic history
        "general": 0.7,
        "history": 0.75,
    }

    def __init__(self, master_catalog_path: Optional[Path] = None):
        """
        Initialize weighter with master catalog.

        Args:
            master_catalog_path: Path to master_catalog.json
        """
        self.master_catalog_path = master_catalog_path or Path("data/processed/master_catalog.json")
        self._books: Dict[int, Dict[str, Any]] = {}
        self._loaded = False

    def load_catalog(self):
        """Load master catalog."""
        if self._loaded:
            return

        if not self.master_catalog_path.exists():
            logger.warning("book_weighter.catalog_not_found", path=str(self.master_catalog_path))
            self._loaded = True
            return

        try:
            with open(self.master_catalog_path, "r", encoding="utf-8") as f:
                books_list = json.load(f)

            # Index by book_id
            for book in books_list:
                book_id = book.get("id") or book.get("book_id")
                if book_id:
                    self._books[int(book_id)] = book

            self._loaded = True
            logger.info("book_weighter.loaded", book_count=len(self._books))

        except Exception as e:
            logger.error("book_weighter.load_failed", error=str(e))
            self._loaded = True

    def get_importance_score(self, book_id: int) -> float:
        """
        Get importance score for a book (0.0-1.0).

        Args:
            book_id: Book identifier

        Returns:
            Importance score
        """
        if not self._loaded:
            self.load_catalog()

        book = self._books.get(book_id, {})
        
        # Get category weight
        category = book.get("category", "").lower()
        category_weight = self._get_category_weight(category)

        # Get author authority bonus (if death year available)
        author_death = book.get("author_death")
        author_bonus = self._get_author_bonus(author_death)

        # Calculate final score
        score = min(1.0, category_weight + author_bonus)

        return score

    def weight_passages_by_importance(self, passages: list) -> list:
        """
        Weight passages by book importance.

        Adds 'book_importance_weight' field.

        Args:
            passages: List of passage dicts

        Returns:
            Weighted passages
        """
        for passage in passages:
            book_id = passage.get("book_id")
            
            if book_id:
                importance = self.get_importance_score(book_id)
                passage["book_importance_weight"] = importance
            else:
                passage["book_importance_weight"] = 0.5  # Default

        return passages

    def _get_category_weight(self, category: str) -> float:
        """Get weight for category."""
        for key, weight in self.CATEGORY_WEIGHTS.items():
            if key in category:
                return weight
        return 0.6  # Default for uncategorized

    def _get_author_bonus(self, death_year: Optional[int]) -> float:
        """Get bonus based on author era."""
        if not death_year:
            return 0.0
        
        # Earlier = more bonus
        if death_year <= 200:
            return 0.1  # Tabi'un era
        elif death_year <= 500:
            return 0.08  # Classical
        elif death_year <= 900:
            return 0.05  # Medieval
        else:
            return 0.02  # Later
