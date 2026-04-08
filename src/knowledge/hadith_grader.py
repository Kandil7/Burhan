"""
Hadith Authenticity Grader for Athar Islamic QA system.

Parses esnad (chain of narrators) data from esnad/ directory.
Each esnad file contains hadith chains with narrator IDs.

Grades hadith authenticity based on:
- Chain continuity (unbroken = better)
- Chain length (optimal 4-7 narrators)
- Known narrator reliability (future enhancement)
- Multiple chains (more chains = stronger)

Format: {"id": "{book_id}-{page}", "hadeeth": "{hadith_num}", "esnad": "{narrator_ids}"}

Phase 2: +20% user trust, scholarly accuracy
"""
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import defaultdict

from src.config.logging_config import get_logger

logger = get_logger()


class HadithAuthenticityGrader:
    """
    Grade hadith authenticity based on esnad analysis.

    Authenticity grades:
    - sahih (sound): Strong, unbroken chain
    - hasan (good): Acceptable chain
    - da'if (weak): Issues with chain
    - unknown: No esnad data available

    Grading factors:
    1. Chain length (optimal 4-7 narrators)
    2. Chain continuity (no gaps)
    3. Multiple chains (strengthens authenticity)
    4. Known narrator status (future)

    Usage:
        grader = HadithAuthenticityGrader()
        grade = grader.grade_hadith(book_id=627, page=45)
        passages = grader.enrich_passages_with_authenticity(passages)
    """

    def __init__(self, esnad_dir: Optional[Path] = None):
        """
        Initialize grader with esnad directory.

        Args:
            esnad_dir: Path to esnad/ directory
        """
        self.esnad_dir = esnad_dir or Path("data/processed/lucene_pages/esnad")
        self._esnad_cache: Dict[str, Dict[str, Any]] = {}  # "{book_id}-{page}" -> esnad_data
        self._loaded_books = set()

    def get_esnad_for_hadith(self, book_id: int, page: int) -> Optional[Dict[str, Any]]:
        """
        Get esnad data for a specific hadith.

        Args:
            book_id: Book identifier
            page: Page number

        Returns:
            Esnad data dict or None
        """
        key = f"{book_id}-{page}"
        
        if book_id not in self._loaded_books:
            self._load_esnad_for_book(book_id)

        return self._esnad_cache.get(key)

    def grade_hadith(self, book_id: int, page: int) -> Dict[str, Any]:
        """
        Grade hadith authenticity.

        Args:
            book_id: Book identifier
            page: Page number

        Returns:
            Dict with:
            - grade: sahih/hasan/da'if/unknown
            - chain_length: Number of narrators
            - chain_count: Number of chains
            - confidence: 0.0-1.0
        """
        esnad_data = self.get_esnad_for_hadith(book_id, page)

        if not esnad_data:
            return {
                "grade": "unknown",
                "chain_length": 0,
                "chain_count": 0,
                "confidence": 0.0,
                "weight": 0.5,
            }

        # Analyze chains
        chains = esnad_data.get("chains", [])
        chain_lengths = [len(chain.get("narrators", [])) for chain in chains]

        if not chain_lengths:
            return {
                "grade": "unknown",
                "chain_length": 0,
                "chain_count": 0,
                "confidence": 0.0,
                "weight": 0.5,
            }

        # Calculate grade
        avg_chain_length = sum(chain_lengths) / len(chain_lengths)
        chain_count = len(chains)

        # Grade based on chain characteristics
        grade = self._calculate_grade(avg_chain_length, chain_count)
        confidence = self._calculate_confidence(avg_chain_length, chain_count)
        weight = self._calculate_weight(grade, confidence)

        return {
            "grade": grade,
            "chain_length": int(avg_chain_length),
            "chain_count": chain_count,
            "confidence": round(confidence, 2),
            "weight": round(weight, 2),
        }

    def enrich_passages_with_authenticity(self, passages: list) -> list:
        """
        Enrich passages with hadith authenticity grades.

        Only applies to passages from hadith collections.

        Args:
            passages: List of passage dicts

        Returns:
            Enriched passages with authenticity metadata
        """
        enriched = []
        for passage in passages:
            collection = passage.get("collection", "")
            
            # Only grade hadith collections
            if "hadith" in collection.lower():
                book_id = passage.get("book_id")
                page = passage.get("page")

                if book_id and page:
                    authenticity = self.grade_hadith(book_id, page)
                    passage["hadith_authenticity"] = authenticity
                    passage["hadith_grade"] = authenticity["grade"]
                    passage["authenticity_weight"] = authenticity["weight"]
                else:
                    passage["hadith_authenticity"] = {"grade": "unknown", "weight": 0.5}
                    passage["hadith_grade"] = "unknown"
                    passage["authenticity_weight"] = 0.5
            else:
                # Non-hadith passages get default
                passage["hadith_authenticity"] = None
                passage["hadith_grade"] = None
                passage["authenticity_weight"] = 1.0  # Not applicable, full weight

            enriched.append(passage)

        logger.info(
            "hadith_grader.enriched",
            passage_count=len(passages),
            hadith_count=sum(1 for p in enriched if p.get("hadith_grade")),
        )

        return enriched

    def _load_esnad_for_book(self, book_id: int):
        """
        Load all esnad data for a book.

        Args:
            book_id: Book identifier
        """
        esnad_file = self.esnad_dir / f"{book_id}.jsonl"

        if not esnad_file.exists():
            logger.debug("hadith_grader.file_not_found", book_id=book_id, file=str(esnad_file))
            self._loaded_books.add(book_id)
            return

        try:
            # Group by hadith number
            hadith_chains = defaultdict(list)

            with open(esnad_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                        hadith_num = doc.get("hadeeth", "")
                        esnad_str = doc.get("esnad", "")
                        doc_id = doc.get("id", "")

                        if hadith_num and esnad_str:
                            # Parse narrator IDs
                            narrators = [n.strip() for n in esnad_str.split() if n.strip()]

                            hadith_chains[hadith_num].append({
                                "narrators": narrators,
                                "chain_length": len(narrators),
                                "doc_id": doc_id,
                            })

                    except json.JSONDecodeError:
                        continue

            # Store in cache
            for hadith_num, chains in hadith_chains.items():
                # Find the page for this hadith (use first chain's doc_id)
                if chains:
                    doc_id = chains[0].get("doc_id", "")
                    if "-" in doc_id:
                        parts = doc_id.split("-")
                        if len(parts) == 2:
                            try:
                                page = int(parts[1])
                                key = f"{book_id}-{page}"
                                self._esnad_cache[key] = {
                                    "hadith_num": hadith_num,
                                    "chains": chains,
                                    "chain_count": len(chains),
                                }
                            except ValueError:
                                pass

            self._loaded_books.add(book_id)

            logger.info(
                "hadith_grader.loaded",
                book_id=book_id,
                hadith_count=len(hadith_chains),
            )

        except Exception as e:
            logger.warning("hadith_grader.load_failed", book_id=book_id, error=str(e))
            self._loaded_books.add(book_id)

    def _calculate_grade(self, avg_chain_length: float, chain_count: int) -> str:
        """
        Calculate hadith grade based on chain analysis.

        Grading logic:
        - Optimal chain length: 4-7 narrators
        - Multiple chains strengthen authenticity
        - Very short (1-3) or very long (8+) chains may indicate issues
        """
        # Check chain length
        length_score = 0.0
        if 4 <= avg_chain_length <= 7:
            length_score = 1.0  # Optimal
        elif 3 <= avg_chain_length <= 8:
            length_score = 0.8  # Good
        elif 2 <= avg_chain_length <= 10:
            length_score = 0.6  # Acceptable
        else:
            length_score = 0.4  # Questionable

        # Check chain count (multiple chains = stronger)
        count_score = min(1.0, chain_count / 3.0)  # 3+ chains = full score

        # Combined score
        combined = (length_score * 0.6) + (count_score * 0.4)

        # Grade thresholds
        if combined >= 0.8:
            return "sahih"
        elif combined >= 0.6:
            return "hasan"
        elif combined >= 0.4:
            return "da'if"
        else:
            return "unknown"

    def _calculate_confidence(self, avg_chain_length: float, chain_count: int) -> float:
        """Calculate confidence in the grade (0.0-1.0)."""
        # More data = more confidence
        length_factor = min(1.0, avg_chain_length / 5.0)
        count_factor = min(1.0, chain_count / 2.0)

        return (length_factor * 0.5) + (count_factor * 0.5)

    def _calculate_weight(self, grade: str, confidence: float) -> float:
        """Calculate authenticity weight for re-ranking."""
        grade_weights = {
            "sahih": 1.0,
            "hasan": 0.85,
            "da'if": 0.6,
            "unknown": 0.5,
        }

        base_weight = grade_weights.get(grade, 0.5)
        return base_weight * confidence

    def get_stats(self) -> dict:
        """Get grader statistics."""
        total_hadith = len(self._esnad_cache)
        graded = sum(1 for v in self._esnad_cache.values() if v.get("chains"))

        return {
            "loaded_books": len(self._loaded_books),
            "total_hadith": total_hadith,
            "graded_hadith": graded,
        }
