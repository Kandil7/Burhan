# Enrichment Module
"""Metadata enrichment pipeline for Burhan RAG system.

Phase 3.1: Collection-Aware RAG enrichment pipeline.
Enrichs raw passages with author, era, and category information.

Key features:
- Era classification based on author death year
- Author/madhhab/school enrichment
- Category hierarchy mapping
- Collection-aware metadata for better retrieval
"""

from typing import Dict, Optional, Any
import json
from pathlib import Path

from src.indexing.metadata.master_catalog import (
    MasterCatalog,
    master_catalog as default_master_catalog,
    BookEntry,
)
from src.indexing.metadata.author_catalog import (
    AuthorCatalog,
    author_catalog as default_author_catalog,
    Author,
)
from src.indexing.metadata.category_mapping import (
    get_subcategories,
    map_category,
    CategoryHierarchy,
)

from src.config.logging_config import get_logger

logger = get_logger()


class EraClassifier:
    """
    Classify authors into era buckets based on death year in Hijri calendar.

    Era buckets:
    - sahabah: Died 0-100 AH (first generation)
    - tabiin: Died 100-200 AH (second generation)
    - classical: Died 200-500 AH (classical period)
    - medieval: Died 500-900 AH (medieval period)
    - contemporary: Died 900+ AH (contemporary period)
    """

    SAHABAH_MAX = 100
    TABIIIN_MAX = 200
    CLASSICAL_MAX = 500
    MEDIEVAL_MAX = 900

    ERA_BUCKETS = {
        (0, 100): "sahabah",
        (101, 200): "tabiin",
        (201, 500): "classical",
        (501, 900): "medieval",
        (901, float("inf")): "contemporary",
    }

    ERA_DISPLAY_NAMES = {
        "sahabah": "Sahabah (Companions)",
        "tabiin": "Tabi'in (Followers)",
        "classical": "Classical Period",
        "medieval": "Medieval Period",
        "contemporary": "Contemporary Period",
    }

    def classify_era(self, death_year: int) -> str:
        """
        Classify author into era bucket based on death year.

        Args:
            death_year: Author's death year in AH

        Returns:
            Era bucket string (e.g., "sahabah", "classical")
        """
        if death_year is None:
            return "unknown"

        for (min_year, max_year), era in self.ERA_BUCKETS.items():
            if min_year <= death_year <= max_year:
                return era

        return "unknown"

    def get_era_display_name(self, era: str) -> str:
        """Get human-readable era name."""
        return self.ERA_DISPLAY_NAMES.get(era, era.title())


# Default era classifier
era_classifier = EraClassifier()


# Known madhhab affiliations for authors
MADHHAB_AFFILIATIONS: Dict[str, Dict[str, str]] = {
    "imam_bukhari": {"madhhab": "hanbali", "inferred": False},
    "imam_muslim": {"madhhab": "shafi'i", "inferred": False},
    "imam_ibn_qayyim": {"madhhab": "hanbali", "inferred": False},
    "imam_al-ghazali": {"madhhab": "shafi'i", "inferred": False},
    "imam_abu_hanifa": {"madhhab": "hanafi", "inferred": False},
    "imam_malik": {"madhhab": "maliki", "inferred": False},
    "imam_al-shafi": {"madhhab": "shafi'i", "inferred": False},
    "imam_ahmad": {"madhhab": "hanbali", "inferred": False},
    "al-marghinani": {"madhhab": "hanafi", "inferred": False},
    "ibn_ataullah": {"madhhab": "shafi'i", "inferred": False},
}

# Known aqeedah schools
AQEEDAH_SCHOOLS: Dict[str, str] = {
    "imam_bukhari": "Burhani",
    "imam_muslim": "Burhani",
    "imam_ibn_qayyim": "Burhani",
    "imam_al-ghazali": "ashari",
    "imam_abu_hanifa": "Burhani",
    "imam_malik": "Burhani",
    "imam_al-shafi": "ashari",
    "imam_ahmad": "Burhani",
}


def get_madhhab(author_id: str) -> tuple[Optional[str], bool]:
    """
    Get madhhab for an author.

    Args:
        author_id: Author identifier

    Returns:
        Tuple of (madhhab, inferred_flag)
    """
    if author_id in MADHHAB_AFFILIATIONS:
        info = MADHHAB_AFFILIATIONS[author_id]
        return info["madhhab"], info["inferred"]

    return None, True


def get_aqeedah_school(author_id: str) -> Optional[str]:
    """Get aqeedah school for an author."""
    return AQEEDAH_SCHOOLS.get(author_id)


def enrich_passage(
    row: dict,
    master_cat: Optional[MasterCatalog] = None,
    author_cat: Optional[AuthorCatalog] = None,
    cat_map: Optional[Any] = None,
) -> dict:
    """
    Enrich a passage with author, era, category, and collection metadata.

    Args:
        row: Raw passage dict with at least 'content' and 'metadata'
        master_cat: Master catalog instance (optional, uses default)
        author_cat: Author catalog instance (optional, uses default)
        cat_map: Category mapping module (optional)

    Returns:
        Enriched passage dict with additional metadata fields:
        - book_title: Human-readable book title
        - author_name: Author name
        - author_death_year: Author death year
        - madhhab: Author's legal school
        - madhhab_inferred: Whether madhhab was inferred
        - aqeedah_school: Author's theology school
        - era: Era bucket (sahabah, tabiin, classical, medieval, contemporary)
        - category_main: Primary category
        - category_sub: Secondary category
        - collection: Collection name
        - hierarchy: Category hierarchy info
    """
    master_cat = master_cat or default_master_catalog
    author_cat = author_cat or default_author_catalog

    metadata = row.get("metadata", {})
    book_id = metadata.get("book_id", "")
    author_id = metadata.get("author_id", "") or book_id

    # Start with original row
    enriched = dict(row)
    enriched_metadata = dict(metadata)

    # Get book info from master catalog
    book_entry = master_cat.get_book(book_id)
    if book_entry:
        enriched_metadata["book_title"] = book_entry.title
        enriched_metadata["author"] = book_entry.author
    else:
        enriched_metadata["book_title"] = book_id
        enriched_metadata["author"] = author_id

    # Get author info
    author = author_cat.get_author(author_id)
    if author:
        enriched_metadata["author_name"] = author.name
        enriched_metadata["author_death_year"] = author.death_year
        enriched_metadata["author_death_year_ah"] = author.death_year_ah
        enriched_metadata["madhhab"] = author.madhhab if author.madhhab else enriched_metadata.get("madhhab")

        # Classify era using death_year_ah (Hijri) for proper era classification
        era_year = author.death_year_ah if author.death_year_ah else author.death_year
        if era_year:
            era = era_classifier.classify_era(era_year)
        else:
            era = "unknown"
        enriched_metadata["era"] = era
    else:
        enriched_metadata["author_name"] = author_id
        enriched_metadata["author_death_year"] = None
        enriched_metadata["author_death_year_ah"] = None
        enriched_metadata["era"] = "unknown"

    # Get madhhab
    madhhab, inferred = get_madhhab(author_id)
    enriched_metadata["madhhab"] = madhhab if madhhab else "unknown"
    enriched_metadata["madhhab_inferred"] = inferred

    # Get aqeedah school
    aqeedah = get_aqeedah_school(author_id)
    enriched_metadata["aqeedah_school"] = aqeedah if aqeedah else "unknown"

    # Determine category from content if not provided
    content = row.get("content", "")
    if content:
        categories = map_category(content)
        if categories:
            enriched_metadata["category_main"] = categories[0]
            enriched_metadata["category_sub"] = (
                categories[1] if len(categories) > 1 else get_subcategories(categories[0])[0] if categories else None
            )
        else:
            enriched_metadata["category_main"] = "unknown"
            enriched_metadata["category_sub"] = None
    else:
        enriched_metadata["category_main"] = metadata.get("category", "unknown")
        enriched_metadata["category_sub"] = metadata.get("subcategory")

    # Collection info
    enriched_metadata["collection"] = metadata.get("collection", book_id)

    # Build hierarchy info
    hierarchy = {
        "category_main": enriched_metadata.get("category_main"),
        "category_sub": enriched_metadata.get("category_sub"),
        "era": enriched_metadata.get("era"),
        "madhhab": enriched_metadata.get("madhhab"),
    }
    enriched_metadata["hierarchy"] = hierarchy

    enriched["metadata"] = enriched_metadata

    logger.debug(
        "enrichment.passage_enriched",
        book_id=book_id,
        era=enriched_metadata.get("era"),
        madhhab=enriched_metadata.get("madhhab"),
    )

    return enriched


def build_metadata_csv(
    input_path: str,
    output_path: str,
    input_format: str = "jsonl",
    master_cat: Optional[MasterCatalog] = None,
    author_cat: Optional[AuthorCatalog] = None,
) -> Dict[str, Any]:
    """
    Build enriched metadata CSV from input dataset.

    Reads passages from Burhan-Datasets (JSON/JSONL), applies enrichment,
    and outputs enriched JSONL ready for Qdrant vector DB.

    Args:
        input_path: Path to input data (JSON or JSONL)
        output_path: Path to output enriched JSONL
        input_format: Input format ("jsonl" or "json")
        master_cat: Master catalog instance
        author_cat: Author catalog instance

    Returns:
        Statistics dict with counts
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    master_cat = master_cat or default_master_catalog
    author_cat = author_cat or default_author_catalog

    stats = {
        "input_file": str(input_file),
        "output_file": str(output_file),
        "total_passages": 0,
        "enriched_passages": 0,
        "errors": 0,
        "by_era": {},
        "by_madhhab": {},
    }

    # Read input
    passages = []
    with open(input_file, encoding="utf-8") as f:
        if input_format == "jsonl":
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    passages.append(doc)
                except json.JSONDecodeError:
                    stats["errors"] += 1
        else:
            # Try JSON array
            content = f.read()
            try:
                passages = json.loads(content)
                if not isinstance(passages, list):
                    passages = [passages]
            except json.JSONDecodeError:
                logger.error("build_metadata_csv.invalid_json", path=str(input_file))
                raise

    stats["total_passages"] = len(passages)

    # Enrich passages
    enriched_passages = []
    for passage in passages:
        try:
            enriched = enrich_passage(
                passage,
                master_cat=master_cat,
                author_cat=author_cat,
            )
            enriched_passages.append(enriched)

            # Track stats
            era = enriched.get("metadata", {}).get("era", "unknown")
            madhhab = enriched.get("metadata", {}).get("madhhab", "unknown")

            stats["by_era"][era] = stats["by_era"].get(era, 0) + 1
            stats["by_madhhab"][madhhab] = stats["by_madhhab"].get(madhhab, 0) + 1

        except Exception as e:
            logger.warning("build_metadata_csv.enrich_error", error=str(e))
            stats["errors"] += 1

    stats["enriched_passages"] = len(enriched_passages)

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for passage in enriched_passages:
            f.write(json.dumps(passage, ensure_ascii=False) + "\n")

    logger.info(
        "build_metadata_csv.complete",
        total=stats["total_passages"],
        enriched=stats["enriched_passages"],
        output=str(output_file),
    )

    return stats


def enrich_batch(
    passages: list,
    master_cat: Optional[MasterCatalog] = None,
    author_cat: Optional[AuthorCatalog] = None,
) -> list:
    """
    Enrich a batch of passages.

    Args:
        passages: List of passage dicts
        master_cat: Master catalog instance
        author_cat: Author catalog instance

    Returns:
        List of enriched passage dicts
    """
    master_cat = master_cat or default_master_catalog
    author_cat = author_cat or default_author_catalog

    enriched = []
    for passage in passages:
        enriched.append(
            enrich_passage(
                passage,
                master_cat=master_cat,
                author_cat=author_cat,
            )
        )

    return enriched
