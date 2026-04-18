"""
BM25 Index for Lexical Search.

Functional implementation for Arabic keyword retrieval.
Uses numpy for efficient scoring.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from src.config.logging_config import get_logger

logger = get_logger()


class BM25IndexError(Exception):
    """Error in BM25 index operations."""

    pass


class BM25Index:
    """
    Functional BM25 implementation for Arabic keyword retrieval.

    Supports:
    - Arabic text normalization (strip diacritics, unify Alef/Ya/Ta-Marbuta)
    - BM25 ranking with k1 and b parameters
    - Batch indexing
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 index.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.avgdl = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_lengths: list[int] = []
        self.documents: list[dict[str, Any]] = []
        self.corpus_size = 0

    def _normalize(self, text: str) -> list[str]:
        """Normalize Arabic text and tokenize into words."""
        # Strip diacritics
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        # Unify Alef variants
        text = re.sub(r"[إأآٱ]", "ا", text)
        # Unify Ta-Marbuta and Ya
        text = text.replace("ة", "ه").replace("ى", "ي")
        # Extract Arabic words and alphanumeric
        return re.findall(r"[\u0600-\u06FF\w]+", text.lower())

    async def index_documents(self, documents: list[dict[str, Any]], text_field: str = "content") -> int:
        """
        Index documents for BM25 search.

        Args:
            documents: List of document dicts
            text_field: Field name containing text

        Returns:
            Number of documents indexed
        """
        if not documents:
            return 0

        self.documents = documents
        self.corpus_size = len(documents)
        
        tokenized_corpus = [self._normalize(doc.get(text_field, "")) for doc in documents]
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0

        # Calculate Document Frequencies
        self.doc_freqs = {}
        for doc in tokenized_corpus:
            for term in set(doc):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Pre-calculate IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = float(np.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0))

        logger.info(
            "bm25.indexed",
            count=self.corpus_size,
            avgdl=round(self.avgdl, 2),
        )
        return self.corpus_size

    async def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Search for documents matching query.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of result dicts with scores
        """
        if self.corpus_size == 0 or not query:
            return []

        q_tokens = self._normalize(query)
        scores = np.zeros(self.corpus_size)

        for term in q_tokens:
            if term not in self.idf:
                continue
            
            idf = self.idf[term]
            # In a production environment, term frequencies should be pre-calculated
            for i, doc in enumerate(self.documents):
                # Simple TF calculation for the term in doc i
                # This is inefficient for large corpora; use inverted index in production
                content = doc.get("content", "")
                tf = self._normalize(content).count(term)
                
                if tf > 0:
                    denom = tf + self.k1 * (1 - self.b + self.b * self.doc_lengths[i] / self.avgdl)
                    scores[i] += idf * (tf * (self.k1 + 1)) / denom

        # Get top-k indices with non-zero scores
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.documents[idx].copy()
                doc["score_sparse"] = float(scores[idx])
                results.append(doc)

        return results

    def get_stats(self) -> dict:
        """Get BM25 index statistics."""
        return {
            "type": "BM25",
            "document_count": self.corpus_size,
            "unique_terms": len(self.doc_freqs),
            "avgdl": round(self.avgdl, 2),
        }


__all__ = ["BM25Index", "BM25IndexError"]
