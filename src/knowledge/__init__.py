"""
Knowledge Layer - DEPRECATED.

This module is DEPRECATED. The canonical retrieval layer is now in src/retrieval/.

Migration:
- src/knowledge/vector_store.py -> src/infrastructure/qdrant/client.py
- src/knowledge/hybrid_search.py -> src/retrieval/retrievers/hybrid.py
- src/knowledge/bm25_retriever.py -> src/retrieval/retrievers/sparse.py
- src/knowledge/reranker.py -> src/retrieval/ranking/reranker.py
- src/knowledge/query_expander.py -> src/retrieval/expanders/
- src/knowledge/hierarchical_retriever.py -> src/retrieval/retrievers/hierarchical.py
- src/knowledge/title_loader.py -> src/retrieval/mapping/
- src/knowledge/hadith_grader.py -> src/verification/checks/hadith_grade.py
- src/knowledge/book_weighter.py -> src/retrieval/ranking/book_weighter.py
- src/knowledge/embedding_model.py -> src/indexing/embeddings/embedding_model.py
- src/knowledge/embedding_cache.py -> src/infrastructure/redis.py or src/retrieval/caching/
"""

import warnings

warnings.warn(
    "src.knowledge is DEPRECATED. Use src.retrieval, src.infrastructure.qdrant, or src.verification instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new locations for backward compatibility
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher

__all__ = ["VectorStore", "HybridSearcher"]
