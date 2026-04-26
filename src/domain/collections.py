# Collections Domain Module
"""Domain model for Burhan collections."""

from typing import List, Optional


class Collection:
    """Represents an Burhan collection."""

    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        description: Optional[str] = None,
        authority_weight: float = 1.0,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.authority_weight = authority_weight

    def __repr__(self) -> str:
        return f"Collection(id={self.id!r}, name={self.name!r})"


# Collection categories
CATEGORY_QURAN = "quran"
CATEGORY_HADITH = "hadith"
CATEGORY_FIQH = "fiqh"
CATEGORY_TAFSIR = "tafsir"
CATEGORY_AQEEDAH = "aqeedah"
CATEGORY_SEERAH = "seerah"
CATEGORY_HISTORY = "history"
CATEGORY_LANGUAGE = "language"
CATEGORY_TAZKIYAH = "tazkiyah"
CATEGORY_USUL_FIQH = "usul_fiqh"
CATEGORY_GENERAL = "general"


# Predefined collections
PREDEFINED_COLLECTIONS: List[Collection] = [
    Collection(
        id="quran",
        name="Quran",
        category=CATEGORY_QURAN,
        description="The Holy Quran",
        authority_weight=1.0,
    ),
    Collection(
        id="sahih_bukhari",
        name="Sahih al-Bukhari",
        category=CATEGORY_HADITH,
        description="Sahih al-Bukhari - Authenticated hadith collection",
        authority_weight=0.95,
    ),
    Collection(
        id="sahih_muslim",
        name="Sahih Muslim",
        category=CATEGORY_HADITH,
        description="Sahih Muslim - Authenticated hadith collection",
        authority_weight=0.95,
    ),
    Collection(
        id="fiqh_islami",
        name="Fiqh al-Islami",
        category=CATEGORY_FIQH,
        description="Islamic jurisprudence",
        authority_weight=0.85,
    ),
    Collection(
        id="ibn_qayyim",
        name=" Ibn Qayyim al-Jawziyya",
        category=CATEGORY_FIQH,
        description="Works of Ibn Qayyim",
        authority_weight=0.9,
    ),
]
