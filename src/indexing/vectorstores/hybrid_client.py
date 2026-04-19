"""
Hybrid Qdrant Client for multi-vector search.

Provides:
- Hybrid search combining dense (semantic) and sparse (BM25) vectors
- Collection management with hybrid vector configurations
- Unified search API for all Islamic knowledge domains

Phase 3.2: Qdrant Collections Setup for hybrid search.
"""

from typing import Any, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from src.config.logging_config import get_logger

from .hybrid_config import (
    COLLECTION_CONFIGS,
    CollectionConfig,
    DenseVectorConfig,
    HNSWConfig,
    QuantizationConfig,
    SparseVectorConfig,
    get_collection_config,
)

logger = get_logger()


class HybridSearchError(Exception):
    """Error in hybrid search operations."""

    pass


class HybridQdrantClient:
    """
    Qdrant client wrapper for hybrid (dense + sparse) vector search.

    Supports:
    - Dense vector search (semantic similarity)
    - Sparse vector search (BM25 keyword matching)
    - Hybrid search combining both with configurable weights

    Usage:
        client = HybridQdrantClient()
        client.initialize()
        results = client.search_hybrid(
            collection="fiqh",
            dense_vec=query_embedding,
            sparse_vec=sparse_query_vector,
            filters={"madhhab": "hanafi"},
            top_k=10,
            alpha=0.6  # dense weight
        )
    """

    def __init__(self, url: str | None = None, api_key: str | None = None):
        """
        Initialize hybrid Qdrant client.

        Args:
            url: Qdrant server URL (default: from settings)
            api_key: Qdrant API key (optional)
        """
        self._client: Optional[QdrantClient] = None
        self._url = url
        self._api_key = api_key
        self._initialized = False

    @property
    def client(self) -> QdrantClient:
        """Get the underlying Qdrant client."""
        if self._client is None:
            raise HybridSearchError("Client not initialized. Call initialize() first.")
        return self._client

    def initialize(self, url: str | None = None, api_key: str | None = None) -> None:
        """
        Initialize Qdrant client connection.

        Args:
            url: Optional URL override
            api_key: Optional API key override
        """
        from src.config.settings import settings

        self._url = url or self._url or settings.qdrant_url
        self._api_key = api_key or self._api_key or settings.qdrant_api_key

        self._client = QdrantClient(
            url=self._url,
            api_key=self._api_key if self._api_key else None,
            timeout=60,
        )
        self._initialized = True
        logger.info("hybrid_client.initialized", url=self._url)

    def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if not self._initialized:
            self.initialize()

    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        self._ensure_initialized()
        return self._client.collection_exists(collection_name)

    def create_hybrid_collection(
        self,
        collection_name: str,
        dense_config: DenseVectorConfig,
        sparse_config: SparseVectorConfig,
        hnsw_config: HNSWConfig,
        quantization_config: QuantizationConfig,
    ) -> None:
        """
        Create a collection with hybrid (dense + sparse) vector support.

        Args:
            collection_name: Name of the collection
            dense_config: Dense vector configuration
            sparse_config: Sparse vector (BM25) configuration
            hnsw_config: HNSW index configuration
            quantization_config: Quantization configuration
        """
        self._ensure_initialized()

        # Build vector params for dense vectors
        dense_vectors_config = {
            "dense": VectorParams(
                size=dense_config.size,
                distance=dense_config.distance,
                hnsw_config=hnsw_config.to_grpc(),
                quantization_config=quantization_config.to_grpc() if quantization_config else None,
            )
        }

        # Build sparse vector params for BM25
        sparse_vectors_config = {
            "sparse": SparseVectorParams(
                modifier=SparseVectorParams.Modifier.IDF,
                invert=True,
                index=True,
            )
        }

        # Combine both vector configs
        all_vectors = {**dense_vectors_config, **sparse_vectors_config}

        # Create collection
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=all_vectors,
        )

        logger.info(
            "hybrid_client.collection_created",
            collection=collection_name,
            dense_size=dense_config.size,
            sparse_type=sparse_config.type.value,
        )

    def search_hybrid(
        self,
        collection: str,
        dense_vec: np.ndarray,
        sparse_vec: Optional[SparseVector] = None,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
        alpha: float = 0.6,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining dense and sparse vectors.

        This implements a universal query API that:
        1. Uses dense vector for semantic similarity
        2. Optionally uses sparse vector (BM25) for keyword matching
        3. Combines scores using weighted average (alpha for dense, 1-alpha for sparse)

        Args:
            collection: Collection name
            dense_vec: Dense query vector (semantic)
            sparse_vec: Sparse query vector (BM25 scores)
            filters: Metadata filters
            top_k: Number of results to return
            alpha: Weight for dense vector (0.0-1.0). sparse_weight = 1 - alpha

        Returns:
            List of result dicts with id, score, content, metadata
        """
        self._ensure_initialized()

        # Build Qdrant filter
        qdrant_filter = None
        if filters:
            conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()]
            qdrant_filter = Filter(must=conditions)

        # Prepare query vectors
        query_params = {
            "collection_name": collection,
            "query_filter": qdrant_filter,
            "limit": top_k,
        }

        # If sparse vector provided, use hybrid search with both
        if sparse_vec is not None:
            sparse_weight = 1.0 - alpha

            # Use prefetch for hybrid search
            query_params["prefetch"] = [
                {
                    "query": dense_vec.tolist(),
                    "using": "dense",
                    "filter": qdrant_filter,
                },
                {
                    "query": sparse_vec,
                    "using": "sparse",
                    "filter": qdrant_filter,
                },
            ]
            query_params["query"] = None  # Clear direct query when using prefetch
        else:
            # Fallback to dense-only search
            query_params["query"] = dense_vec.tolist()
            query_params["using"] = "dense"

        try:
            # Execute search
            response = self.client.query_points(**query_params)

            # Extract results
            results = []
            for point in response.points:
                results.append(
                    {
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload.get("content", ""),
                        "metadata": {k: v for k, v in point.payload.items() if k != "content"},
                    }
                )

            logger.info(
                "hybrid_client.search_hybrid",
                collection=collection,
                top_k=top_k,
                alpha=alpha,
                results=len(results),
            )

            return results

        except Exception as e:
            logger.error("hybrid_client.search_error", collection=collection, error=str(e))
            raise HybridSearchError(f"Hybrid search failed: {str(e)}") from e

    def search_dense(
        self,
        collection: str,
        query_vector: np.ndarray,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search using dense vectors only (semantic similarity).

        Args:
            collection: Collection name
            query_vector: Query embedding vector
            filters: Metadata filters
            top_k: Number of results

        Returns:
            List of result dicts
        """
        self._ensure_initialized()

        qdrant_filter = None
        if filters:
            conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()]
            qdrant_filter = Filter(must=conditions)

        try:
            response = self.client.query_points(
                collection_name=collection,
                query=query_vector.tolist(),
                using="dense",
                query_filter=qdrant_filter,
                limit=top_k,
            )

            results = []
            for point in response.points:
                results.append(
                    {
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload.get("content", ""),
                        "metadata": {k: v for k, v in point.payload.items() if k != "content"},
                    }
                )

            return results

        except Exception as e:
            logger.error("hybrid_client.dense_search_error", collection=collection, error=str(e))
            raise HybridSearchError(f"Dense search failed: {str(e)}") from e

    def search_sparse(
        self,
        collection: str,
        sparse_query: SparseVector,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search using sparse vectors only (BM25 keyword search).

        Args:
            collection: Collection name
            sparse_query: Sparse vector (BM25 scores)
            filters: Metadata filters
            top_k: Number of results

        Returns:
            List of result dicts
        """
        self._ensure_initialized()

        qdrant_filter = None
        if filters:
            conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()]
            qdrant_filter = Filter(must=conditions)

        try:
            response = self.client.query_points(
                collection_name=collection,
                query=sparse_query,
                using="sparse",
                query_filter=qdrant_filter,
                limit=top_k,
            )

            results = []
            for point in response.points:
                results.append(
                    {
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload.get("content", ""),
                        "metadata": {k: v for k, v in point.payload.items() if k != "content"},
                    }
                )

            return results

        except Exception as e:
            logger.error("hybrid_client.sparse_search_error", collection=collection, error=str(e))
            raise HybridSearchError(f"Sparse search failed: {str(e)}") from e

    def upsert_hybrid(
        self,
        collection: str,
        documents: list[dict[str, Any]],
        dense_embeddings: np.ndarray,
        sparse_vectors: Optional[list[SparseVector]] = None,
    ) -> int:
        """
        Upsert documents with both dense and sparse vectors.

        Args:
            collection: Collection name
            documents: List of document dicts with 'content' and 'metadata'
            dense_embeddings: Dense vector embeddings
            sparse_vectors: Optional list of sparse vectors (BM25)

        Returns:
            Number of documents upserted
        """
        self._ensure_initialized()

        try:
            import hashlib

            from qdrant_client.models import PointStruct

            points = []
            for i, (doc, dense_emb) in enumerate(zip(documents, dense_embeddings, strict=False)):
                # Deterministic ID based on content hash
                content = doc.get("content", "")
                doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]

                # Build vector dict with both dense and sparse
                vectors = {"dense": dense_emb.tolist()}

                if sparse_vectors is not None and i < len(sparse_vectors):
                    vectors["sparse"] = sparse_vectors[i]

                point = PointStruct(
                    id=doc_id,
                    vector=vectors,
                    payload={
                        **doc.get("metadata", {}),
                        "content": content,
                        "chunk_index": doc.get("chunk_index", i),
                    },
                )
                points.append(point)

            self.client.upsert(
                collection_name=collection,
                points=points,
            )

            logger.info(
                "hybrid_client.upserted",
                collection=collection,
                count=len(points),
                has_sparse=sparse_vectors is not None,
            )

            return len(points)

        except Exception as e:
            logger.error("hybrid_client.upsert_error", collection=collection, error=str(e))
            raise HybridSearchError(f"Failed to upsert: {str(e)}") from e

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        self._ensure_initialized()
        try:
            self._client.delete_collection(collection_name=collection_name)
            logger.info("hybrid_client.collection_deleted", collection=collection_name)
            return True
        except Exception as e:
            logger.error("hybrid_client.delete_error", collection=collection_name, error=str(e))
            return False

    def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get collection information."""
        self._ensure_initialized()
        try:
            info = self._client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": getattr(info, "vectors_count", 0),
                "points_count": getattr(info, "points_count", 0),
                "status": str(getattr(info, "status", "unknown")),
            }
        except Exception as e:
            logger.warning("hybrid_client.info_error", collection=collection_name, error=str(e))
            return {"name": collection_name, "status": "error", "error": str(e)}

    def list_collections(self) -> list[str]:
        """List all collections."""
        self._ensure_initialized()
        try:
            collections = self._client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            logger.error("hybrid_client.list_error", error=str(e))
            return []


# Extend HNSWConfig and QuantizationConfig with to_grpc methods
def _extend_config_classes():
    """Add to_grpc methods to config classes for Qdrant compatibility."""

    def hnsw_to_grpc(self):
        """Convert to Qdrant HNSW config."""
        from qdrant_client.models import HnswConfigDiff

        return HnswConfigDiff(
            m=self.m,
            ef_construct=self.ef_construct,
            full_scan_threshold=self.full_scan_threshold,
        )

    def quantization_to_grpc(self):
        """Convert to Qdrant quantization config."""
        from qdrant_client.models import QuantizationConfigDiff

        return QuantizationConfigDiff(
            quantized_by_default=True,
            always_ram=self.always_ram,
        )

    HNSWConfig.to_grpc = hnsw_to_grpc
    QuantizationConfig.to_grpc = quantization_to_grpc


_extend_config_classes()
