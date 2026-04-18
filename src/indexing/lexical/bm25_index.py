import re
from typing import Any

import numpy as np

from src.config.logging_config import get_logger

logger = get_logger()


class BM25Index:
    """Functional BM25 implementation for Arabic keyword retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.avgdl = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_lengths: list[int] = []
        self.documents: list[dict] = []
        self.corpus_size = 0

    def _normalize(self, text: str) -> list[str]:
        # Strip diacritics and unify Alef/Ya/Ta-Marbuta
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        text = re.sub(r"[إأآٱ]", "ا", text)
        text = text.replace("ة", "ه").replace("ى", "ي")
        return re.findall(r"[\u0600-\u06FF\w]+", text.lower())

    async def index_documents(self, documents: list[dict], text_field: str = "content") -> int:
        if not documents:
            return 0
        self.documents = documents
        self.corpus_size = len(documents)
        tokenized_corpus = [self._normalize(doc.get(text_field, "")) for doc in documents]
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0

        # Calculate Doc Frequencies
        self.doc_freqs = {}
        for doc in tokenized_corpus:
            for term in set(doc):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Pre-calculate IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = float(np.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0))

        logger.info("bm25.indexed", count=self.corpus_size)
        return self.corpus_size

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        if self.corpus_size == 0 or not query:
            return []
        q_tokens = self._normalize(query)
        scores = np.zeros(self.corpus_size)

        for term in q_tokens:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            for i, doc in enumerate(self.documents):
                # Simple TF calculation for the term in doc i
                # Note: In production, pre-calculate TF per doc for performance
                content = doc.get("content", "")
                tf = self._normalize(content).count(term)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_lengths[i] / self.avgdl)
                scores[i] += idf * (tf * (self.k1 + 1)) / denom

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
            "k1": self.k1,
            "b": self.b,
        }
