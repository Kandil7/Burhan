"""
Title Loader for Athar Islamic QA system.

Loads per-book title files from lucene_pages/titles/ directory.
Each title file contains chapter/section titles for a specific book.
Title format: {"id": "{book_id}-{page}", "body": "{title_text}"}

Used for:
- Adding chapter/section context to passages
- Title-aware chunking
- Hierarchical retrieval
- Understanding document structure

Phase 2: +25% retrieval accuracy with title context

[DEPRECATED] Moved to src.indexing.metadata.title_loader
This module is kept for backward compatibility. Please update imports.
"""

# Backward compatibility shim - imports from new location
from src.indexing.metadata.title_loader import TitleLoader

__all__ = ["TitleLoader"]
