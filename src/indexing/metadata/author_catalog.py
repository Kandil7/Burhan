# Author Catalog Module
"""Author catalog for Islamic texts."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Author:
    """Represents an author of Islamic texts."""

    id: str
    name: str
    era: str
    school: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    description: Optional[str] = None


# Major authors in Islamic literature
AUTHOR_CATALOG: Dict[str, Author] = {
    "imam_bukhari": Author(
        id="imam_bukhari",
        name="Muhammad ibn Ismail al-Bukhari",
        era="9th century AH",
        school="Sunni",
        birth_year=810,
        death_year=870,
        description="Compiled Sahih al-Bukhari, the most authentic hadith collection",
    ),
    "imam_muslim": Author(
        id="imam_muslim",
        name="Muslim ibn al-Hajjaj",
        era="9th century AH",
        school="Sunni",
        birth_year=815,
        death_year=875,
        description="Compiled Sahih Muslim, second most authentic hadith collection",
    ),
    "imam_ibn_qayyim": Author(
        id="imam_ibn_qayyim",
        name="Ibn Qayyim al-Jawziyya",
        era="14th century AH",
        school="Sunni",
        birth_year=1292,
        death_year=1350,
        description="Prominent scholar of the Hanbali school",
    ),
    "imam_al-ghazali": Author(
        id="imam_al-ghazali",
        name="Abu Hamid al-Ghazali",
        era="12th century AH",
        school="Sunni",
        birth_year=1058,
        death_year=1111,
        description="Famous theologian and philosopher",
    ),
}


class AuthorCatalog:
    """Catalog for managing author information."""

    def __init__(self):
        self.authors = AUTHOR_CATALOG

    def get_author(self, author_id: str) -> Optional[Author]:
        """Get author by ID."""
        return self.authors.get(author_id)

    def search_authors(self, query: str) -> List[Author]:
        """Search authors by name."""
        query_lower = query.lower()
        return [a for a in self.authors.values() if query_lower in a.name.lower()]

    def get_authors_by_school(self, school: str) -> List[Author]:
        """Get authors by school."""
        return [a for a in self.authors.values() if a.school == school]

    def get_all_authors(self) -> List[Author]:
        """Get all authors."""
        return list(self.authors.values())


# Default catalog instance
author_catalog = AuthorCatalog()
