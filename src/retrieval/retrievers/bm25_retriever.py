"""
BM25 Retrieval for Burhan Islamic QA System.

Pure Python BM25 implementation for keyword-based retrieval.
Can be used standalone or combined with semantic search.

Phase 9: Added BM25 retriever for hybrid search optimization.

BM25 Parameters:
- k1: Term frequency saturation parameter (default: 1.5)
- b: Length normalization parameter (default: 0.75)
"""

from __future__ import annotations

from collections import Counter
from math import log
from typing import Any

from src.config.logging_config import get_logger

logger = get_logger()


class BM25:
    """
    BM25 ranking function implementation.

    Okapi BM25 ranking function:
    score(Q, D) = sum(IDF(qi) * (f(qi, D) * (k1 + 1)) /
                     (f(qi, D) + k1 * (1 - b + b * |D| / avgdl)))

    Usage:
        bm25 = BM25()
        bm25.index(documents)
        results = bm25.search("صلاة", top_k=10)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 ranker.

        Args:
            k1: Term frequency saturation (0 = binary, higher = more flexible)
            b: Length normalization (0 = no normalization, 1 = full)
        """
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: Counter = Counter()
        self.doc_len: list[int] = []
        self.corpus: list[list[str]] = []

    def index(self, documents: list[dict[str, Any]]) -> None:
        """
        Build BM25 index from documents.

        Args:
            documents: List of document dicts with 'content' field
        """
        self.corpus = [self._tokenize(doc.get("content", "")) for doc in documents]
        self.corpus_size = len(self.corpus)
        self.doc_len = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_len) / self.corpus_size if self.corpus_size else 0.0

        # Calculate document frequencies
        for doc in self.corpus:
            seen = set()
            for term in doc:
                if term not in seen:
                    self.doc_freqs[term] += 1
                    seen.add(term)

        logger.info(
            "bm25.indexed",
            corpus_size=self.corpus_size,
            unique_terms=len(self.doc_freqs),
            avgdl=round(self.avgdl, 2),
        )

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into terms."""
        import re

        # Normalize Arabic text
        text = text.lower()
        # Remove diacritics
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        # Unify alef variants
        text = re.sub(r"[\u0622\u0623\u0625\u0671]", "\u0627", text)
        # Extract words
        words = re.findall(r"[\u0600-\u06FF]+", text)
        return words

    def _idf(self, term: str) -> float:
        """Calculate IDF for a term."""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        # Standard BM25 IDF
        return log((self.corpus_size - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """
        Calculate BM25 score for query against document.

        Args:
            query: Query text
            doc_idx: Document index

        Returns:
            BM25 score
        """
        if doc_idx >= self.corpus_size:
            return 0.0

        query_terms = self._tokenize(query)
        doc = self.corpus[doc_idx]
        doc_len = self.doc_len[doc_idx]

        score = 0.0
        doc_tf = Counter(doc)

        for term in query_terms:
            if term not in self.doc_freqs:
                continue

            # IDF component
            idf = self._idf(term)

            # TF component
            tf = doc_tf.get(term, 0)
            tf_score = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))

            score += idf * tf_score

        return score

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[int, float]]:
        """
        Search with BM25.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of (document_index, score) tuples
        """
        if self.corpus_size == 0:
            return []

        scores = [(idx, self.score(query, idx)) for idx in range(self.corpus_size)]

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:top_k]

        logger.info(
            "bm25.search",
            query=query[:50],
            top_k=top_k,
            results=len(results),
        )

        return results


class BM25Retriever:
    """
    BM25 retriever for document retrieval.

    Combines BM25 ranking with document storage and retrieval API.

    Usage:
        retriever = BM25Retriever()
        await retriever.index(documents)
        results = await retriever.retrieve("صلاة", top_k=10)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.bm25 = BM25(k1=k1, b=b)
        self._documents: list[dict[str, Any]] = []
        self._indexed = False

    async def index(self, documents: list[dict[str, Any]]) -> None:
        """
        Index documents for retrieval.

        Args:
            documents: List of document dicts
        """
        self._documents = documents
        self.bm25.index(documents)
        self._indexed = True

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Retrieve documents using BM25.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of document dicts with scores
        """
        if not self._indexed:
            logger.warning("bm25_retriever.not_indexed")
            return []

        scores = self.bm25.search(query, top_k=top_k)

        results = []
        for doc_idx, score in scores:
            doc = self._documents[doc_idx].copy()
            doc["bm25_score"] = score
            doc["bm25_rank"] = len(results) + 1
            results.append(doc)

        return results

    async def search_with_filters(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve with metadata filters.

        Args:
            query: Query text
            top_k: Number of results
            filters: Metadata filters

        Returns:
            Filtered and ranked documents
        """
        if not self._indexed:
            return []

        # Apply filters first
        filtered_docs = self._apply_filters(self._documents, filters or {})

        # Re-index for filtered documents
        if len(filtered_docs) != len(self._documents):
            temp_bm25 = BM25(k1=self.bm25.k1, b=self.bm25.b)
            temp_bm25.index(filtered_docs)
            scores = temp_bm25.search(query, top_k=top_k)
        else:
            scores = self.bm25.search(query, top_k=top_k)

        results = []
        for doc_idx, score in scores:
            doc = filtered_docs[doc_idx].copy()
            doc["bm25_score"] = score
            results.append(doc)

        return results

    def _apply_filters(
        self,
        documents: list[dict[str, Any]],
        filters: dict,
    ) -> list[dict[str, Any]]:
        """Apply metadata filters to documents."""
        if not filters:
            return documents

        filtered = []
        for doc in documents:
            match = True
            for key, value in filters.items():
                doc_value = doc.get(key)
                if isinstance(value, list):
                    if doc_value not in value:
                        match = False
                        break
                elif doc_value != value:
                    match = False
                    break

            if match:
                filtered.append(doc)

        return filtered

    @property
    def is_indexed(self) -> bool:
        """Check if retriever is indexed."""
        return self._indexed
