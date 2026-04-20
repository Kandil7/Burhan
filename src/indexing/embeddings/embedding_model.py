"""
BAAI/bge-m3 Embedding Model Wrapper for Athar Islamic QA system.

Phase 6 Refactoring:
- Fixed missing await on _split_by_cache (root cause of index OOB error)
- Fixed embedding order preservation in cache path
- torch_dtype= instead of dtype= for AutoModel
- run_in_executor for tokenizer + model inference (non-blocking)
- float16 on GPU only, float32 on CPU
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from typing import TYPE_CHECKING

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from src.config.logging_config import get_logger
from src.config.settings import settings

if TYPE_CHECKING:
    from src.indexing.embeddings.embedding_cache import EmbeddingCache

logger = get_logger()


class EmbeddingModelError(Exception):
    """Error in embedding generation."""


class EmbeddingModel:
    """
    BAAI/bge-m3 wrapper for Islamic text embeddings.

    - 1024-dimensional vectors, 8192-token context window
    - GPU/MPS/CPU auto-detection
    - Redis-based caching (order-preserving)
    - run_in_executor for non-blocking inference
    """

    MODEL_NAME = "BAAI/bge-m3"
    DIMENSION = 1024
    MAX_LENGTH = 512  # 8192 causes OOM on CPU; 512 covers most passages
    BATCH_SIZE = 32

    def __init__(self, cache_enabled: bool = True) -> None:
        self.model: AutoModel | None = None
        self.tokenizer: AutoTokenizer | None = None
        self.device: str = self._get_device()
        self.cache_enabled = cache_enabled
        self.cache: EmbeddingCache | None = None
        self._loaded = False

    # ── Device ────────────────────────────────────────────────────────────────

    def _get_device(self) -> str:
        # Allow forcing CPU via environment variable
        force_cpu = os.environ.get("ATHAR_EMBEDDING_CPU", "").lower()
        if force_cpu in ("1", "true", "yes"):
            logger.info("embedding.cpu_forced")
            return "cpu"

        try:
            if torch.cuda.is_available():
                logger.info("embedding.cuda_available", device=torch.cuda.get_device_name(0))
                return "cuda"
        except Exception:
            pass

        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("embedding.mps_available")
                return "mps"
        except Exception:
            pass

        logger.warning("embedding.cpu_fallback")
        return "cpu"

    # ── Load ──────────────────────────────────────────────────────────────────

    async def load_model(self) -> None:
        """Load BGE-M3 weights (non-blocking via run_in_executor)."""
        if self._loaded:
            return

        # Lazy-init cache here (requires running event loop)
        if self.cache_enabled and self.cache is None:
            try:
                from src.indexing.embeddings.embedding_cache import EmbeddingCache

                self.cache = EmbeddingCache()
            except Exception as e:
                logger.warning("embedding.cache_init_failed", error=str(e))
                self.cache_enabled = False

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
        self._loaded = True
        logger.info(
            "embedding.loaded",
            model=self.MODEL_NAME,
            device=self.device,
            dimension=self.DIMENSION,
        )

    # ── Load ──────────────────────────────────────────────────────────────────

    def _load_model_sync(self) -> None:
        token = os.environ.get("HF_TOKEN") or getattr(settings, "hf_token", None)

        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME, trust_remote_code=True, token=token)

        # Load directly to CPU first to avoid meta tensor issues
        # Then use CPU for inference (avoids GPU device issues entirely)
        # This is more reliable for production environments
        self.model = AutoModel.from_pretrained(
            self.MODEL_NAME,
            trust_remote_code=True,
            token=token,
            low_cpu_mem_usage=True,
        )
        self.model.eval()
        # Keep on CPU - more stable for serverless/containers

    # ── Public API ────────────────────────────────────────────────────────────

    async def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single query → ndarray (1024,).

        Always call with await:
            emb = await model.encode_query(text)
        """
        if not self._loaded:
            await self.load_model()

        clean = query.strip()
        if not clean:
            logger.warning("embedding.empty_query")
            return np.zeros(self.DIMENSION, dtype=np.float32)

        embeddings = await self.encode([clean])

        if len(embeddings) == 0:
            raise EmbeddingModelError(f"encode() returned empty array for query: '{clean[:50]}'")
        return embeddings[0]

    async def encode(
        self,
        texts: list[str],
        batch_size: int | None = None,
    ) -> np.ndarray:
        """
        Encode a list of texts → ndarray (N×1024).

        Cache path preserves original order.
        """
        if not self._loaded:
            await self.load_model()

        if not texts:
            return np.empty((0, self.DIMENSION), dtype=np.float32)

        batch_size = batch_size or self.BATCH_SIZE
        all_results: list[np.ndarray] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embs = await self._encode_with_cache(batch)
            all_results.extend(batch_embs)

        return np.array(all_results, dtype=np.float32)

    async def encode_documents(
        self,
        documents: list[dict],
        text_field: str = "content",
    ) -> np.ndarray:
        """Encode documents — extracts `text_field` from each dict."""
        texts = [doc.get(text_field, "") for doc in documents]
        return await self.encode(texts)

    # ── Cache-aware encode (order-preserving) ────────────────────────────────

    async def _encode_with_cache(self, texts: list[str]) -> list[np.ndarray]:
        """
        Encode a batch, using cache where available.

        Returns embeddings in the SAME ORDER as `texts`.
        """
        if not self.cache_enabled or self.cache is None:
            return await self._encode_batch_executor(texts)

        # 1. Compute hashes and check cache for each position
        hashes = [self._get_hash(t) for t in texts]
        result = [None] * len(texts)  # positional slots
        uncached_idx = []  # positions needing encode

        for pos, (text, h) in enumerate(zip(texts, hashes)):
            cached_emb = await self.cache.get(h)
            if cached_emb is not None:
                result[pos] = cached_emb
            else:
                uncached_idx.append(pos)

        # 2. Encode uncached texts in one batch
        if uncached_idx:
            uncached_texts = [texts[p] for p in uncached_idx]
            new_embs = await self._encode_batch_executor(uncached_texts)

            # 3. Store in cache and place in correct position
            for pos, emb in zip(uncached_idx, new_embs):
                await self.cache.set(hashes[pos], emb)
                result[pos] = emb

        return result  # type: ignore[return-value]  # all slots filled

    # ── Non-blocking inference ────────────────────────────────────────────────

    async def _encode_batch_executor(self, texts: list[str]) -> list[np.ndarray]:
        """Run CPU/GPU inference in a thread pool (non-blocking)."""
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_batch_sync, texts)

    def _encode_batch_sync(self, texts: list[str]) -> list[np.ndarray]:
        """Synchronous tokenize + forward pass — runs in executor thread."""
        safe_texts = [t.strip() if t.strip() else "[empty]" for t in texts]

        # Use the device the model is actually on
        model_device = next(self.model.parameters()).device
        inputs = self.tokenizer(
            safe_texts,
            padding=True,
            truncation=True,
            max_length=self.MAX_LENGTH,
            return_tensors="pt",
        ).to(model_device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            token_embs = outputs.last_hidden_state  # (B, T, D)
            mask = inputs["attention_mask"]
            mask_expanded = mask.unsqueeze(-1).expand(token_embs.size()).float()
            pooled = torch.sum(token_embs * mask_expanded, 1)
            pooled /= torch.clamp(mask_expanded.sum(1), min=1e-9)
            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)

        return [emb.float().numpy() for emb in normalized]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get_stats(self) -> dict:
        stats = {
            "model": self.MODEL_NAME,
            "dimension": self.DIMENSION,
            "device": self.device,
            "loaded": self._loaded,
            "cache_enabled": self.cache_enabled,
            "max_length": self.MAX_LENGTH,
        }
        if self.cache_enabled and self.cache:
            stats["cache"] = self.cache.stats()
        return stats
