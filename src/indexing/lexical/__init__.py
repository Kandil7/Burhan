"""Lexical module for Athar Islamic QA system."""

from src.indexing.lexical.bm25_index import BM25Index, BM25IndexError

__all__ = [
    "BM25Index",
    "BM25IndexError",
]
