"""Qdrant infrastructure module."""

from src.infrastructure.qdrant.client import QdrantClientWrapper, get_qdrant_client
from src.infrastructure.qdrant.collections import (
    CollectionConfig,
    COLLECTION_CONFIGS,
    get_collection_config,
    list_all_collections,
    get_collections_by_domain,
)
from src.infrastructure.qdrant.payload_indexes import (
    PayloadIndexConfig,
    PAYLOAD_INDEXES,
    get_payload_indexes,
    create_index_operations,
)

__all__ = [
    "QdrantClientWrapper",
    "get_qdrant_client",
    "CollectionConfig",
    "COLLECTION_CONFIGS",
    "get_collection_config",
    "list_all_collections",
    "get_collections_by_domain",
    "PayloadIndexConfig",
    "PAYLOAD_INDEXES",
    "get_payload_indexes",
    "create_index_operations",
]
