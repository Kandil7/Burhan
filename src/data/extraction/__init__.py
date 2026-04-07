"""
Islamic book data extraction modules.

Provides tools for extracting and processing Shamela system_book_datasets:
- Lucene index reading (title, page, esnad)
- SQLite book database parsing
- Service database processing (hadith, tafsir, morphology)
- Structured document generation for RAG pipelines
"""

from src.data.extraction.lucene_extractor import LuceneIndexReader
from src.data.extraction.book_database import BookDatabaseReader
from src.data.extraction.service_databases import ServiceDatabaseProcessor

__all__ = [
    "LuceneIndexReader",
    "BookDatabaseReader",
    "ServiceDatabaseProcessor",
]
