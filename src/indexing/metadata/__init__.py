"""Metadata module for Burhan Islamic QA system."""

from src.indexing.metadata.author_catalog import Author, AuthorCatalog, author_catalog
from src.indexing.metadata.category_mapping import CategoryHierarchy, get_subcategories, map_category
from src.indexing.metadata.enrichment import (
    EraClassifier,
    build_metadata_csv,
    enrich_batch,
    enrich_passage,
    era_classifier,
    get_aqeedah_school,
    get_madhhab,
)
from src.indexing.metadata.master_catalog import BookEntry, MasterCatalog, TextCategory, master_catalog
from src.indexing.metadata.title_loader import TitleLoader

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
