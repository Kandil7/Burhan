"""
Qdrant Vector Store Integration for Athar Islamic QA system.

Provides:
- Collection management (fiqh, hadith, tafsir, general, duas)
- Similarity search with metadata filtering
- Hybrid search (semantic + keyword)
- Batch upsert for efficient indexing
- HNSW index configuration

Phase 4: Foundation for all RAG retrieval pipelines.
"""
from typing import Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()


class VectorStoreError(Exception):
    """Error in vector store operations."""
    pass


class VectorStore:
    """
    Qdrant vector store for Islamic text embeddings.
    
    Collections:
    - fiqh_passages: Fiqh books, fatwas, rulings
    - hadith_passages: Hadith collections
    - quran_tafsir: Tafsir passages
    - general_islamic: History, biography, theology
    - duas_adhkar: Duas and adhkar
    
    Usage:
        store = VectorStore()
        await store.initialize()
        await store.upsert("fiqh_passages", documents, embeddings)
        results = await store.search("fiqh_passages", query_embedding, top_k=10)
    """
    
    COLLECTIONS = {
        "fiqh_passages": {"dimension": 1024, "description": "Fiqh books and fatwas"},
        "hadith_passages": {"dimension": 1024, "description": "Hadith collections"},
        "quran_tafsir": {"dimension": 1024, "description": "Tafsir passages"},
        "general_islamic": {"dimension": 1024, "description": "General Islamic knowledge"},
        "duas_adhkar": {"dimension": 1024, "description": "Duas and adhkar"},
    }
    
    def __init__(self):
        """Initialize vector store."""
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize Qdrant client and create collections.
        
        Creates all collections if they don't exist.
        """
        try:
            # Create Qdrant client
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
                timeout=60,
            )
            
            # Create collections
            for collection_name, config in self.COLLECTIONS.items():
                if not self.client.collection_exists(collection_name):
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["dimension"],
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(
                        "vectorstore.collection_created",
                        collection=collection_name,
                        dimension=config["dimension"]
                    )
            
            self._initialized = True
            logger.info("vectorstore.initialized", collections=list(self.COLLECTIONS.keys()))
            
        except Exception as e:
            logger.error("vectorstore.init_error", error=str(e))
            raise VectorStoreError(f"Failed to initialize vector store: {str(e)}")
    
    async def upsert(
        self,
        collection: str,
        documents: list[dict],
        embeddings: np.ndarray
    ) -> int:
        """
        Upsert documents with embeddings to collection.
        
        Args:
            collection: Collection name
            documents: List of document dicts
            embeddings: Numpy array of embeddings
            
        Returns:
            Number of documents upserted
        """
        if not self._initialized:
            await self.initialize()
        
        if collection not in self.COLLECTIONS:
            raise VectorStoreError(f"Collection '{collection}' does not exist")
        
        try:
            # Build points
            points = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point = PointStruct(
                    id=i,  # Simple numeric ID
                    vector=embedding.tolist(),
                    payload={
                        **doc.get("metadata", {}),
                        "content": doc.get("content", ""),
                        "chunk_index": doc.get("chunk_index", i),
                    }
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=collection,
                points=points,
            )
            
            logger.info(
                "vectorstore.upserted",
                collection=collection,
                count=len(points)
            )
            
            return len(points)
            
        except Exception as e:
            logger.error("vectorstore.upsert_error", error=str(e))
            raise VectorStoreError(f"Failed to upsert documents: {str(e)}")
    
    async def search(
        self,
        collection: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """
        Search for similar documents.
        
        Args:
            collection: Collection name
            query_embedding: Query embedding vector
            top_k: Number of results
            filters: Metadata filters (e.g., {"madhhab": "hanafi"})
            
        Returns:
            List of result dicts with scores
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filters.items()
                ]
                qdrant_filter = Filter(must=conditions)
            
            # Search using query_points (new Qdrant API)
            response = self.client.query_points(
                collection_name=collection,
                query=query_embedding.tolist(),
                query_filter=qdrant_filter,
                limit=top_k,
            )
            
            # Extract points from response (handle different response formats)
            if hasattr(response, 'points'):
                results = response.points
            elif isinstance(response, list):
                results = response
            else:
                results = []
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k != "content"},
                })
            
            logger.info(
                "vectorstore.search",
                collection=collection,
                top_k=top_k,
                results=len(formatted_results)
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("vectorstore.search_error", error=str(e))
            raise VectorStoreError(f"Search failed: {str(e)}")
    
    async def search_with_score_threshold(
        self,
        collection: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> list[dict]:
        """
        Search with minimum score threshold.
        
        Args:
            collection: Collection name
            query_embedding: Query embedding
            top_k: Max results
            score_threshold: Minimum similarity score
            
        Returns:
            Filtered results above threshold
        """
        results = await self.search(collection, query_embedding, top_k=top_k * 2)
        
        # Filter by score
        filtered = [r for r in results if r["score"] >= score_threshold]
        
        return filtered[:top_k]
    
    def get_collection_stats(self, collection: str) -> dict:
        """
        Get collection statistics.
        
        Args:
            collection: Collection name
            
        Returns:
            Stats dict
        """
        if not self._initialized:
            raise VectorStoreError("Vector store not initialized")
        
        try:
            info = self.client.get_collection(collection)
            
            # Handle different Qdrant client versions
            vectors_count = getattr(info, 'vectors_count', None)
            if vectors_count is None:
                # Try alternative attribute names
                vectors_count = getattr(info, 'points_count', 0)
                if vectors_count == 0:
                    # Try to get from status
                    vectors_count = getattr(info, 'status', 'unknown')
            
            return {
                "collection": collection,
                "vectors_count": vectors_count,
                "status": str(getattr(info, 'status', 'unknown')),
            }
            
        except Exception as e:
            logger.warning("vectorstore.stats_error", error=str(e))
            return {
                "collection": collection,
                "vectors_count": "unknown",
                "status": "error",
            }
    
    def list_collections(self) -> list[str]:
        """List all collection names."""
        return list(self.COLLECTIONS.keys())
    
    def delete_collection(self, collection: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            True if deleted
        """
        try:
            self.client.delete_collection(collection_name=collection)
            logger.info("vectorstore.collection_deleted", collection=collection)
            return True
        except Exception as e:
            logger.error("vectorstore.delete_error", error=str(e))
            return False
