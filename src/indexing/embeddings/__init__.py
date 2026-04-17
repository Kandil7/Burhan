"""Embeddings module for Athar Islamic QA system."""

from src.indexing.embeddings.embedding_model import EmbeddingModel, EmbeddingModelError
from src.indexing.embeddings.embedding_cache import EmbeddingCache, QueryCache

__all__ = [
    "EmbeddingModel",
    "EmbeddingModelError",
    "EmbeddingCache",
    "QueryCache",
]
