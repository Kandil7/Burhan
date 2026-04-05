"""
Qwen3-Embedding Model Wrapper for Athar Islamic QA system.

Provides embedding generation with:
- Qwen3-Embedding-0.6B (1024 dimensions)
- GPU support with automatic device selection
- Redis-based caching (7-day TTL)
- Batch processing optimization
- Half-precision inference for memory efficiency

Phase 4: Foundation for all RAG retrieval pipelines.
"""

import hashlib
import os
from typing import Optional
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.knowledge.embedding_cache import EmbeddingCache

logger = get_logger()


class EmbeddingModelError(Exception):
    """Error in embedding generation."""

    pass


class EmbeddingModel:
    """
    Qwen3-Embedding wrapper for Islamic text embeddings.

    Optimized for Arabic/Islamic content with:
    - 1024-dimensional vectors
    - 512 token context window
    - Batch processing (up to 32 texts)
    - SHA-256 caching for repeated texts

    Usage:
        model = EmbeddingModel()
        await model.load_model()
        embeddings = await model.encode(["النص الأول", "النص الثاني"])
    """

    MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
    DIMENSION = 1024
    MAX_LENGTH = 512
    BATCH_SIZE = 32

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize embedding model.

        Args:
            cache_enabled: Enable Redis-based caching
        """
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.cache_enabled = cache_enabled
        self.cache = EmbeddingCache() if cache_enabled else None
        self._loaded = False

    def _get_device(self) -> str:
        """Get optimal device (cuda if available, else cpu)."""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("embedding.cuda_available", device=torch.cuda.get_device_name(0))
        elif hasattr(torch, "mps") and torch.backends.mps.is_available():
            device = "mps"
            logger.info("embedding.mps_available")
        else:
            device = "cpu"
            logger.warning("embedding.cpu_fallback")

        return device

    async def load_model(self) -> None:
        """
        Load embedding model from HuggingFace.

        Optimizations:
        - Half-precision (float16) on GPU
        - Local caching if model already downloaded
        - HuggingFace token authentication
        """
        import os

        if self._loaded:
            logger.info("embedding.already_loaded")
            return

        try:
            logger.info("embedding.loading", model=self.MODEL_NAME)

            # Get token from environment or settings
            token = os.environ.get("HF_TOKEN") or settings.hf_token

            if token:
                logger.info("embedding.using_hf_token")
            else:
                logger.warning("embedding.no_hf_token")

            # Determine precision
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            # Load tokenizer with auth token
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME, trust_remote_code=True, token=token
            )

            # Load model with auth token
            self.model = AutoModel.from_pretrained(
                self.MODEL_NAME, dtype=dtype, trust_remote_code=True, token=token
            ).to(self.device)

            # Set to eval mode
            self.model.eval()

            self._loaded = True
            logger.info("embedding.loaded", model=self.MODEL_NAME, device=self.device, dimension=self.DIMENSION)

        except Exception as e:
            logger.error("embedding.load_error", error=str(e))
            raise EmbeddingModelError(f"Failed to load embedding model: {str(e)}")

    async def encode(self, texts: list[str], batch_size: Optional[int] = None) -> np.ndarray:
        """
        Encode multiple texts to embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size (default: 32)

        Returns:
            Numpy array of embeddings (len(texts) x 1024)
        """
        if not self._loaded:
            await self.load_model()

        batch_size = batch_size or self.BATCH_SIZE
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Check cache first
            if self.cache_enabled:
                cached, uncached = self._split_by_cache(batch)
                embeddings_from_cache = []

                if cached:
                    cached_embeddings = [self.cache.get(self._get_hash(t)) for t, _ in cached]
                    embeddings_from_cache = [e for e in cached_embeddings if e is not None]

                if uncached:
                    # Encode uncached texts
                    new_embeddings = await self._encode_batch([t for t, _ in uncached])

                    # Cache them
                    for (text, text_hash), embedding in zip(uncached, new_embeddings):
                        self.cache.set(text_hash, embedding)

                    embeddings_from_cache.extend(new_embeddings)

                all_embeddings.extend(embeddings_from_cache)
            else:
                # No caching, encode directly
                batch_embeddings = await self._encode_batch(batch)
                all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings)

    async def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single query.

        Args:
            query: Query text

        Returns:
            Embedding array (1024,)
        """
        embeddings = await self.encode([query])
        return embeddings[0]

    async def encode_documents(self, documents: list[dict], text_field: str = "content") -> np.ndarray:
        """
        Encode documents (extracts text from dict).

        Args:
            documents: List of document dicts
            text_field: Field containing text to encode

        Returns:
            Numpy array of embeddings
        """
        texts = [doc.get(text_field, "") for doc in documents]
        return await self.encode(texts)

    async def _encode_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Encode a batch of texts.

        Args:
            texts: Batch of texts

        Returns:
            List of embedding arrays
        """
        if not texts:
            return []

        try:
            # Tokenize
            inputs = self.tokenizer(
                texts, padding=True, truncation=True, max_length=self.MAX_LENGTH, return_tensors="pt"
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Mean pooling
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                    input_mask_expanded.sum(1), min=1e-9
                )

                # Normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                # Convert to numpy
                if self.device == "cuda":
                    embeddings = embeddings.cpu()

                return [emb.numpy() for emb in embeddings]

        except Exception as e:
            logger.error("embedding.encode_error", error=str(e))
            raise EmbeddingModelError(f"Failed to encode texts: {str(e)}")

    def _split_by_cache(self, texts: list[str]) -> tuple[list, list]:
        """
        Split texts into cached and uncached lists.

        Returns:
            (cached: [(text, hash)], uncached: [(text, hash)])
        """
        cached = []
        uncached = []

        for text in texts:
            text_hash = self._get_hash(text)
            if self.cache and self.cache.get(text_hash) is not None:
                cached.append((text, text_hash))
            else:
                uncached.append((text, text_hash))

        return cached, uncached

    def _get_hash(self, text: str) -> str:
        """Get SHA-256 hash for caching."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get_stats(self) -> dict:
        """Get embedding model statistics."""
        stats = {
            "model": self.MODEL_NAME,
            "dimension": self.DIMENSION,
            "device": self.device,
            "loaded": self._loaded,
            "cache_enabled": self.cache_enabled,
        }

        if self.cache_enabled and self.cache:
            stats["cache"] = self.cache.stats()

        return stats
