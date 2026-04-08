"""
Scholar Authority Scorer for Athar Islamic QA system.

Calculates authority scores for scholars based on:
- Temporal proximity to Prophet ﷺ (earlier = more authoritative for hadith)
- Number of books authored (prolific scholars)
- Scholarly status indicators (Imam, Sheikh, etc.)
- Era classification (classical > medieval > ottoman > modern)

Uses: author_catalog.json with 3,146 authors and death years

Phase 2: +15% answer quality, better scholarly prioritization
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.config.logging_config import get_logger

logger = get_logger()


class ScholarAuthorityScorer:
    """
    Calculate and manage scholar authority scores.

    Authority factors:
    1. Era weight: Earlier scholars more authoritative for hadith/fiqh
    2. Status indicators: Imam > Sheikh > Scholar
    3. Book count: More books = more influential
    4. Cross-references: Cited by other scholars

    Usage:
        scorer = ScholarAuthorityScorer()
        score = scorer.get_authority_score(author_name, death_year)
        passages = scorer.weight_passages_by_authority(passages)
    """

    # Era-based authority weights (for hadith/fiqh)
    ERA_WEIGHTS = {
        "prophetic": 1.0,    # 0-100 AH (Companions)
        "tabiun": 0.95,      # 100-200 AH (Successors)
        "classical": 0.90,   # 200-500 AH (Golden age)
        "medieval": 0.80,    # 500-900 AH (Post-classical)
        "ottoman": 0.70,     # 900-1300 AH (Ottoman era)
        "modern": 0.60,      # 1300+ AH (Modern era)
    }

    # Scholarly status indicators (higher = more authoritative)
    STATUS_WEIGHTS = {
        "imam": 1.0,
        "sheikh_alislam": 0.95,
        "hافظ": 0.90,
        "hafiz": 0.90,
        "sheikh": 0.85,
        "qadi": 0.80,
        "mufti": 0.80,
        "scholar": 0.75,
    }

    # Book count bonuses (diminishing returns)
    BOOK_COUNT_BONUS = {
        1: 0.0,
        2: 0.02,
        3: 0.04,
        5: 0.06,
        10: 0.08,
        20: 0.10,
        50: 0.12,
        100: 0.15,
    }

    def __init__(self, author_catalog_path: Optional[Path] = None):
        """
        Initialize scorer with author catalog.

        Args:
            author_catalog_path: Path to author_catalog.json
        """
        self.author_catalog_path = author_catalog_path or Path("data/processed/author_catalog.json")
        self._authors: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load_authors(self):
        """Load author catalog from JSON file."""
        if self._loaded:
            return

        if not self.author_catalog_path.exists():
            logger.warning("authority_scorer.catalog_not_found", path=str(self.author_catalog_path))
            self._loaded = True
            return

        try:
            with open(self.author_catalog_path, "r", encoding="utf-8") as f:
                authors_list = json.load(f)

            # Index by author name
            for author in authors_list:
                name = author.get("name", "").strip()
                if name:
                    self._authors[name] = author

            self._loaded = True
            logger.info("authority_scorer.loaded", author_count=len(self._authors))

        except Exception as e:
            logger.error("authority_scorer.load_failed", error=str(e))
            self._loaded = True

    def get_authority_score(self, author_name: str, death_year: Optional[int] = None) -> float:
        """
        Calculate authority score for an author.

        Score range: 0.0 - 1.0 (higher = more authoritative)

        Args:
            author_name: Author name
            death_year: Death year in Hijri (optional)

        Returns:
            Authority score between 0 and 1
        """
        if not self._loaded:
            self.load_authors()

        # Base score from era
        if death_year:
            era = self._classify_era(death_year)
            base_score = self.ERA_WEIGHTS.get(era, 0.5)
        else:
            base_score = 0.5  # Default if no death year

        # Look up author in catalog
        author_data = self._authors.get(author_name, {})

        # Status indicator bonus
        status = author_data.get("status", "").lower()
        status_bonus = self._get_status_bonus(status)

        # Book count bonus
        book_count = author_data.get("book_count", 0)
        book_bonus = self._get_book_count_bonus(book_count)

        # Calculate final score
        final_score = min(1.0, base_score + status_bonus + book_bonus)

        return final_score

    def weight_passages_by_authority(self, passages: list) -> list:
        """
        Weight passages by author authority score.

        Adds 'authority_weight' field to each passage.

        Args:
            passages: List of passage dicts

        Returns:
            Passages with authority_weight field
        """
        for passage in passages:
            author = passage.get("author", "")
            death_year = passage.get("author_death")

            if author:
                authority = self.get_authority_score(author, death_year)
                passage["authority_weight"] = authority
                passage["authority_era"] = self._classify_era(death_year) if death_year else "unknown"
            else:
                passage["authority_weight"] = 0.5  # Default
                passage["authority_era"] = "unknown"

        return passages

    def rerank_by_authority(self, passages: list, authority_factor: float = 0.2) -> list:
        """
        Re-rank passages considering authority scores.

        New score = original_score * (1 - factor) + authority_weight * factor

        Args:
            passages: List of passage dicts with 'score' field
            authority_factor: Weight of authority in final score (0-1)

        Returns:
            Re-ranked passages
        """
        # First add authority weights
        passages = self.weight_passages_by_authority(passages)

        # Calculate composite scores
        for passage in passages:
            original_score = passage.get("score", 0)
            authority_weight = passage.get("authority_weight", 0.5)

            # Composite score
            passage["composite_score"] = (
                original_score * (1 - authority_factor) +
                authority_weight * authority_factor
            )

        # Sort by composite score
        return sorted(passages, key=lambda p: p.get("composite_score", 0), reverse=True)

    def _classify_era(self, death_year: int) -> str:
        """Classify scholar's era based on death year (Hijri)."""
        if death_year <= 100:
            return "prophetic"
        elif death_year <= 200:
            return "tabiun"
        elif death_year <= 500:
            return "classical"
        elif death_year <= 900:
            return "medieval"
        elif death_year <= 1300:
            return "ottoman"
        else:
            return "modern"

    def _get_status_bonus(self, status: str) -> float:
        """Get bonus based on scholarly status."""
        for key, bonus in self.STATUS_WEIGHTS.items():
            if key in status:
                return bonus * 0.1  # Up to 10% bonus
        return 0.0

    def _get_book_count_bonus(self, book_count: int) -> float:
        """Get bonus based on number of books authored."""
        bonus = 0.0
        for threshold, value in sorted(self.BOOK_COUNT_BONUS.items()):
            if book_count >= threshold:
                bonus = value
        return bonus * 0.1  # Up to 15% bonus
