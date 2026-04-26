"""Metadata module for Burhan Islamic QA system."""

from src.indexing.metadata.title_loader import TitleLoader
from src.indexing.metadata.master_catalog import MasterCatalog, master_catalog, BookEntry, TextCategory
from src.indexing.metadata.author_catalog import AuthorCatalog, author_catalog, Author
from src.indexing.metadata.category_mapping import get_subcategories, map_category, CategoryHierarchy
from src.indexing.metadata.enrichment import (
    EraClassifier,
    era_classifier,
    enrich_passage,
    enrich_batch,
    build_metadata_csv,
    get_madhhab,
    get_aqeedah_school,
)

__all__ = [
    # Title loader
    "TitleLoader",
    # Master catalog
    "MasterCatalog",
    "master_catalog",
    "BookEntry",
    "TextCategory",
    # Author catalog
    "AuthorCatalog",
    "author_catalog",
    "Author",
    # Category mapping
    "get_subcategories",
    "map_category",
    "CategoryHierarchy",
    # Enrichment
    "EraClassifier",
    "era_classifier",
    "enrich_passage",
    "enrich_batch",
    "build_metadata_csv",
    "get_madhhab",
    "get_aqeedah_school",
]
