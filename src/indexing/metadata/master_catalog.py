# Master Catalog Module
"""Master catalog for all Burhan collections and texts."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TextCategory(str, Enum):
    """Categories of Islamic texts."""

    QURAN = "quran"
    HADITH = "hadith"
    FIQH = "fiqh"
    TAFSIR = "tafsir"
    AQEEDAH = "aqeedah"
    SEERAH = "seerah"
    HISTORY = "history"
    LANGUAGE = "language"
    ETHICS = "ethics"


@dataclass
class BookEntry:
    """Entry in the master catalog."""

    book_id: str
    title: str
    author: str
    category: TextCategory
    language: str = "arabic"
    authority_weight: float = 0.8
    collection: Optional[str] = None


# Master catalog of all books
MASTER_CATALOG: Dict[str, BookEntry] = {
    # Quran
    "quran": BookEntry(
        book_id="quran",
        title="The Holy Quran",
        author="Allah",
        category=TextCategory.QURAN,
        authority_weight=1.0,
    ),
    # Hadith
    "sahih_bukhari": BookEntry(
        book_id="sahih_bukhari",
        title="Sahih al-Bukhari",
        author="Imam al-Bukhari",
        category=TextCategory.HADITH,
        authority_weight=0.95,
    ),
    "sahih_muslim": BookEntry(
        book_id="sahih_muslim",
        title="Sahih Muslim",
        author="Imam Muslim",
        category=TextCategory.HADITH,
        authority_weight=0.95,
    ),
    # Fiqh
    "hidayah": BookEntry(
        book_id="hidayya",
        title="Al-Hidayah",
        author="Al-Marghinani",
        category=TextCategory.FIQH,
        authority_weight=0.90,
    ),
    "ibn_qayyim": BookEntry(
        book_id="ibn_qayyim",
        title="Ibn Qayyim Collection",
        author="Ibn Qayyim al-Jawziyya",
        category=TextCategory.FIQH,
        authority_weight=0.90,
    ),
}


class MasterCatalog:
    """Master catalog for all texts."""

    def __init__(self):
        self.catalog = MASTER_CATALOG

    def get_book(self, book_id: str) -> Optional[BookEntry]:
        """Get book by ID."""
        return self.catalog.get(book_id)

    def get_books_by_category(self, category: TextCategory) -> List[BookEntry]:
        """Get all books in a category."""
        return [b for b in self.catalog.values() if b.category == category]

    def search_books(self, query: str) -> List[BookEntry]:
        """Search books by title."""
        query_lower = query.lower()
        return [b for b in self.catalog.values() if query_lower in b.title.lower()]

    def get_all_books(self) -> List[BookEntry]:
        """Get all books."""
        return list(self.catalog.values())


# Default catalog instance
master_catalog = MasterCatalog()
