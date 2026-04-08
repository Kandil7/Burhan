"""
Embedding Model Wrapper for Athar Islamic QA system.

Supports multiple embedding models:
- Qwen3-Embedding-0.6B (1024 dimensions, fast)
- BAAI/bge-m3 (1024 dimensions, superior Arabic, hybrid retrieval)

Features:
- Automatic model selection based on config
- GPU support with automatic device selection
- Redis-based caching (7-day TTL)
- Batch processing optimization
- Half-precision inference for memory efficiency
- Hybrid retrieval support (dense + sparse for BGE-M3)

Phase 7: Added BGE-M3 support for superior Arabic/Islamic text embeddings.
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
    Multi-model embedding wrapper for Islamic text embeddings.

    Supports:
    - Qwen3-Embedding-0.6B: Fast, good for English
    - BAAI/bge-m3: Superior Arabic, hybrid retrieval (dense + sparse)

    Optimized for Arabic/Islamic content with:
    - 1024-dimensional vectors
    - 8192 token context window (BGE-M3) / 512 (Qwen3)
    - Batch processing (up to 32 texts)
    - SHA-256 caching for repeated texts

    Usage:
        model = EmbeddingModel(model_name="BAAI/bge-m3")
        await model.load_model()
        embeddings = await model.encode(["النص الأول", "النص الثاني"])
    """

    # Model configurations
    MODEL_CONFIGS = {
        "Qwen/Qwen3-Embedding-0.6B": {
            "dimension": 1024,
            "max_length": 512,
            "batch_size": 32,
            "requires_instruction": False,
            "supports_sparse": False,
        },
        "BAAI/bge-m3": {
            "dimension": 1024,
            "max_length": 8192,
            "batch_size": 16,  # Smaller batch due to larger model
            "requires_instruction": False,
            "supports_sparse": True,
        },
    }

    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize embedding model.

        Args:
            model_name: Model to use (default: from settings or BAAI/bge-m3)
            cache_enabled: Enable Redis-based caching
        """
        # Determine model name
        self.model_name = model_name or getattr(settings, "embedding_model", "BAAI/bge-m3")
        
        # Load config
        if self.model_name not in self.MODEL_CONFIGS:
            raise EmbeddingModelError(
                f"Unsupported model: {self.model_name}. "
                f"Supported: {list(self.MODEL_CONFIGS.keys())}"
            )
        
        config = self.MODEL_CONFIGS[self.model_name]
        self.dimension = config["dimension"]
        self.max_length = config["max_length"]
        self.batch_size = config["batch_size"]
        self.supports_sparse = config["supports_sparse"]
        
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.cache_enabled = cache_enabled
        self.cache = EmbeddingCache() if cache_enabled else None
        self._loaded = False
        
        logger.info(
            "embedding.init",
            model=self.model_name,
            dimension=self.dimension,
            max_length=self.max_length,
            supports_sparse=self.supports_sparse,
        )

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

        For BGE-M3:
        - Uses FlagEmbedding library if available
        - Falls back to transformers if not
        - Enables FP16 on GPU

        For Qwen3:
        - Uses transformers directly
        - FP16 on GPU, FP32 on CPU
        """
        if self._loaded:
            logger.info("embedding.already_loaded")
            return

        try:
            logger.info("embedding.loading", model=self.model_name)

            # Get token from environment
            token = os.environ.get("HF_TOKEN") or getattr(settings, "hf_token", None)

            # Determine precision
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            # Load based on model type
            if self.model_name == "BAAI/bge-m3":
                await self._load_bge_m3(token, dtype)
            else:
                await self._load_qwen3(token, dtype)

            self._loaded = True
            logger.info(
                "embedding.loaded",
                model=self.model_name,
                device=self.device,
                dimension=self.dimension,
            )

        except Exception as e:
            logger.error("embedding.load_error", error=str(e))
            raise EmbeddingModelError(f"Failed to load embedding model: {str(e)}")

    async def _load_bge_m3(self, token: Optional[str], dtype: torch.dtype):
        """Load BGE-M3 model."""
        try:
            # Try FlagEmbedding first (recommended)
            try:
                from FlagEmbedding import BGEM3FlagModel
                
                logger.info("embedding.using_flag_embedding")
                self.model = BGEM3FlagModel(
                    self.model_name,
                    use_fp16=(self.device == "cuda"),
                )
                self.tokenizer = self.model.tokenizer
                self.use_flag_embedding = True
                
            except ImportError:
                # Fallback to transformers
                logger.warning("embedding.flag_embedding_not_found, using transformers")
                self.use_flag_embedding = False
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    token=token,
                )
                
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    torch_dtype=dtype,
                    trust_remote_code=True,
                    token=token,
                ).to(self.device)
                self.model.eval()
                
        except Exception as e:
            logger.error("embedding.bge_load_error", error=str(e))
            raise

    async def _load_qwen3(self, token: Optional[str], dtype: torch.dtype):
        """Load Qwen3 embedding model."""
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            token=token,
        )
        
        self.model = AutoModel.from_pretrained(
            self.model_name,
            torch_dtype=dtype,
            trust_remote_code=True,
            token=token,
        ).to(self.device)
        
        self.model.eval()
        self.use_flag_embedding = False

    async def encode(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
        return_sparse: bool = False,
    ) -> dict:
        """
        Encode multiple texts to embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size (default: model-specific)
            return_sparse: Return sparse embeddings (BGE-M3 only)

        Returns:
            Dict with:
            - dense_vecs: numpy array (len(texts) x 1024)
            - lexical_weights: list of dicts (BGE-M3 only, if return_sparse=True)
        """
        if not self._loaded:
            await self.load_model()

        batch_size = batch_size or self.batch_size
        all_dense = []
        all_sparse = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Check cache first
            if self.cache_enabled:
                cached, uncached = self._split_by_cache(batch)
                embeddings_from_cache = []
                sparse_from_cache = []

                if cached:
                    # Get cached embeddings
                    for text, text_hash in cached:
                        cached_data = self.cache.get(text_hash)
                        if cached_data:
                            if isinstance(cached_data, dict):
                                # Has both dense and sparse
                                embeddings_from_cache.append(cached_data.get("dense"))
                                if return_sparse:
                                    sparse_from_cache.append(cached_data.get("sparse"))
                            else:
                                # Old format (dense only)
                                embeddings_from_cache.append(cached_data)
                                if return_sparse:
                                    sparse_from_cache.append(None)

                if uncached:
                    # Encode uncached texts
                    uncached_texts = [t for t, _ in uncached]
                    result = await self._encode_batch(uncached_texts, return_sparse)
                    
                    new_dense = result["dense_vecs"]
                    new_sparse = result.get("lexical_weights", [None] * len(uncached_texts))

                    # Cache them
                    for (text, text_hash), dense, sparse in zip(uncached, new_dense, new_sparse):
                        cache_data = {"dense": dense}
                        if sparse is not None:
                            cache_data["sparse"] = sparse
                        self.cache.set(text_hash, cache_data)

                    embeddings_from_cache.extend(new_dense)
                    if return_sparse:
                        sparse_from_cache.extend(new_sparse)

                all_dense.extend(embeddings_from_cache)
                if return_sparse:
                    all_sparse.extend(sparse_from_cache)
            else:
                # No caching, encode directly
                result = await self._encode_batch(batch, return_sparse)
                all_dense.extend(result["dense_vecs"])
                if return_sparse:
                    all_sparse.extend(result.get("lexical_weights", [None] * len(batch)))

        output = {"dense_vecs": np.array(all_dense)}
        if return_sparse and all_sparse:
            output["lexical_weights"] = all_sparse

        return output

    async def encode_query(self, query: str, return_sparse: bool = False) -> dict:
        """
        Encode a single query.

        Args:
            query: Query text
            return_sparse: Return sparse embedding (BGE-M3 only)

        Returns:
            Dict with dense_vecs and optionally lexical_weights
        """
        result = await self.encode([query], return_sparse=return_sparse)
        output = {"dense_vecs": result["dense_vecs"][0]}
        if return_sparse and "lexical_weights" in result:
            output["lexical_weights"] = result["lexical_weights"][0]
        return output

    async def encode_documents(
        self,
        documents: list[dict],
        text_field: str = "content",
        return_sparse: bool = False,
    ) -> dict:
        """
        Encode documents (extracts text from dict).

        Args:
            documents: List of document dicts
            text_field: Field containing text to encode
            return_sparse: Return sparse embeddings

        Returns:
            Dict with dense_vecs and optionally lexical_weights
        """
        texts = [doc.get(text_field, "") for doc in documents]
        return await self.encode(texts, return_sparse=return_sparse)

    async def _encode_batch(
        self,
        texts: list[str],
        return_sparse: bool = False,
    ) -> dict:
        """
        Encode a batch of texts.

        Args:
            texts: Batch of texts
            return_sparse: Return sparse embeddings

        Returns:
            Dict with dense_vecs and optionally lexical_weights
        """
        if not texts:
            return {"dense_vecs": []}

        try:
            if self.use_flag_embedding and hasattr(self.model, 'encode'):
                # FlagEmbedding encode method
                result = self.model.encode(
                    texts,
                    batch_size=len(texts),
                    max_length=self.max_length,
                    return_dense=True,
                    return_sparse=return_sparse,
                )
                
                output = {"dense_vecs": result['dense_vecs']}
                if return_sparse and 'lexical_weights' in result:
                    output["lexical_weights"] = result['lexical_weights']
                
                return output
            else:
                # Transformers encode method
                inputs = self.tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                ).to(self.device)

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

                    return {"dense_vecs": [emb.numpy() for emb in embeddings]}

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
            "model": self.model_name,
            "dimension": self.dimension,
            "max_length": self.max_length,
            "device": self.device,
            "loaded": self._loaded,
            "cache_enabled": self.cache_enabled,
            "supports_sparse": self.supports_sparse,
            "use_flag_embedding": getattr(self, 'use_flag_embedding', False),
        }

        if self.cache_enabled and self.cache:
            stats["cache"] = self.cache.stats()

        return stats
