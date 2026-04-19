"""
BAAI/bge-m3 Embedding Model Wrapper for Athar Islamic QA system.

Phase 6 Refactoring:
- Fixed missing await on _split_by_cache (root cause of index OOB error)
- Fixed embedding order preservation in cache path
- torch_dtype= instead of dtype= for AutoModel
- run_in_executor for tokenizer + model inference (non-blocking)
- float16 on GPU only, float32 on CPU

[DEPRECATED] Moved to src.indexing.embeddings.embedding_model
This module is kept for backward compatibility. Please update imports.
"""

# Backward compatibility shim - imports from new location
from src.indexing.embeddings.embedding_model import EmbeddingModel, EmbeddingModelError

__all__ = ["EmbeddingModel", "EmbeddingModelError"]
