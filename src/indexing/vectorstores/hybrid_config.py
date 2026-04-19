"""
Hybrid Search Configuration for Qdrant Collections.

Defines configuration classes and collection-specific settings for:
- Dense vector (semantic) search
- Sparse vector (BM25 keyword) search
- HNSW indexing parameters
- Quantization settings

Phase 3.2: Qdrant Collections Setup for hybrid search.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from qdrant_client.models import Distance


class SparseVectorType(str, Enum):
    """Sparse vector types supported by Qdrant."""

    BM25 = "bm25"


class QuantizationType(str, Enum):
    """Quantization types for vector compression."""

    INT8 = "int8"
    FLOAT16 = "float16"


@dataclass(frozen=True)
class DenseVectorConfig:
    """
    Configuration for dense (semantic) vectors.

    Attributes:
        size: Vector dimension (e.g., 1024 for BGE-m3)
        distance: Distance metric for similarity (COSINE, EUCLIDEAN, DOT)
    """

    size: int = 1024
    distance: Distance = Distance.COSINE


@dataclass(frozen=True)
class SparseVectorConfig:
    """
    Configuration for sparse (keyword) vectors using BM25.

    Attributes:
        type: Sparse vector type (BM25)
        tokenizer: Tokenizer for BM25 (default: "whitespace")
        k1: BM25 k1 parameter (term frequency saturation)
        b: BM25 b parameter (document length normalization)
    """

    type: SparseVectorType = SparseVectorType.BM25
    tokenizer: str = "whitespace"
    k1: float = 1.5
    b: float = 0.75


@dataclass(frozen=True)
class QuantizationConfig:
    """
    Configuration for vector quantization.

    Attributes:
        type: Quantization type (INT8 or FLOAT16)
        always_ram: Whether to keep quantized vectors in RAM
    """

    type: QuantizationType = QuantizationType.INT8
    always_ram: bool = True


@dataclass(frozen=True)
class HNSWConfig:
    """
    Configuration for HNSW index.

    Attributes:
        m: Number of bi-directional links per node
        ef_construct: Build-time expansion factor (higher = better build, slower)
        full_scan_threshold: Threshold for using full scan vs index
    """

    m: int = 16
    ef_construct: int = 100
    full_scan_threshold: int = 10000


# Predefined HNSW configurations for different collection sizes
class HNSWPreset:
    """HNSW configuration presets for different collection sizes."""

    SMALL = HNSWConfig(m=8, ef_construct=64, full_scan_threshold=5000)
    MEDIUM = HNSWConfig(m=16, ef_construct=100, full_scan_threshold=10000)
    LARGE = HNSWConfig(m=24, ef_construct=200, full_scan_threshold=20000)


@dataclass(frozen=True)
class CollectionConfig:
    """
    Complete configuration for a Qdrant collection with hybrid search.

    Attributes:
        name: Collection name
        dense: Dense vector configuration
        sparse: Sparse vector (BM25) configuration
        hnsw: HNSW index configuration
        quantization: Quantization configuration
        dense_weight: Weight for dense vectors in hybrid scoring (default: 0.6)
        sparse_weight: Weight for sparse vectors in hybrid scoring (default: 0.4)
    """

    name: str
    dense: DenseVectorConfig
    sparse: SparseVectorConfig
    hnsw: HNSWConfig
    quantization: QuantizationConfig
    dense_weight: float = 0.6
    sparse_weight: float = 0.4


# Collection configurations for all Islamic knowledge domains
COLLECTION_CONFIGS: Dict[str, CollectionConfig] = {
    "fiqh": CollectionConfig(
        name="fiqh",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.LARGE,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "hadith": CollectionConfig(
        name="hadith",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.MEDIUM,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "quran": CollectionConfig(
        name="quran",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.LARGE,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "tafsir": CollectionConfig(
        name="tafsir",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.MEDIUM,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "aqeedah": CollectionConfig(
        name="aqeedah",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.MEDIUM,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "seerah": CollectionConfig(
        name="seerah",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.SMALL,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "usul_fiqh": CollectionConfig(
        name="usul_fiqh",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.MEDIUM,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "islamic_history": CollectionConfig(
        name="islamic_history",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.SMALL,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
    "arabic_language": CollectionConfig(
        name="arabic_language",
        dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
        sparse=SparseVectorConfig(type=SparseVectorType.BM25, k1=1.5, b=0.75),
        hnsw=HNSWPreset.SMALL,
        quantization=QuantizationConfig(type=QuantizationType.INT8, always_ram=True),
        dense_weight=0.6,
        sparse_weight=0.4,
    ),
}


def get_collection_config(collection_name: str) -> CollectionConfig | None:
    """
    Get collection configuration by name.

    Args:
        collection_name: Name of the collection

    Returns:
        CollectionConfig if found, None otherwise
    """
    return COLLECTION_CONFIGS.get(collection_name)


def get_all_collection_names() -> list[str]:
    """Get list of all configured collection names."""
    return list(COLLECTION_CONFIGS.keys())


# ==========================================
# Collection Management Functions
# ==========================================


def recreate_collection(
    client: "QdrantClient",
    collection_name: str,
    dense_size: int = 1024,
    hnsw_preset: "HNSWConfig" = HNSWPreset.MEDIUM,
    use_quantization: bool = True,
    use_sparse: bool = True,
) -> bool:
    """
    Recreate a collection with hybrid search configuration.

    Deletes existing collection if present and creates a new one with:
    - Dense vectors (semantic)
    - Sparse vectors (BM25) if enabled
    - HNSW indexing
    - Quantization if enabled

    Args:
        client: QdrantClient instance
        collection_name: Name of collection to recreate
        dense_size: Dense vector dimension (default: 1024)
        hnsw_preset: HNSW configuration preset
        use_quantization: Enable INT8 quantization
        use_sparse: Enable sparse (BM25) vectors

    Returns:
        True if successful, False otherwise
    """
    from qdrant_client import QdrantClient as QdrantClientType
    from qdrant_client.models import (
        Distance,
        HnswConfigDiff,
        QuantizationConfigDiff,
        SparseVectorParams,
        VectorParams,
    )

    try:
        # Delete existing collection if exists
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name=collection_name)

        # Build vector configs
        vectors_config = {
            "dense": VectorParams(
                size=dense_size,
                distance=Distance.COSINE,
                hnsw_config=HnswConfigDiff(
                    m=hnsw_preset.m,
                    ef_construct=hnsw_preset.ef_construct,
                    full_scan_threshold=hnsw_preset.full_scan_threshold,
                ),
                quantization_config=QuantizationConfigDiff(
                    quantized_by_default=True,
                    always_ram=True,
                )
                if use_quantization
                else None,
            )
        }

        # Add sparse vectors if enabled
        if use_sparse:
            vectors_config["sparse"] = SparseVectorParams(
                modifier=SparseVectorParams.Modifier.IDF,
                invert=True,
                index=True,
            )

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )

        return True

    except Exception:
        return False


def recreate_all_collections(client: "QdrantClient") -> dict[str, bool]:
    """
    Recreate all configured collections with optimal hybrid search settings.

    Args:
        client: QdrantClient instance

    Returns:
        Dict mapping collection names to success status
    """
    results = {}

    # Map collection names to their optimal settings
    collection_settings = {
        "fiqh": {"hnsw": HNSWPreset.LARGE},
        "hadith": {"hnsw": HNSWPreset.MEDIUM},
        "quran": {"hnsw": HNSWPreset.LARGE},
        "tafsir": {"hnsw": HNSWPreset.MEDIUM},
        "aqeedah": {"hnsw": HNSWPreset.MEDIUM},
        "seerah": {"hnsw": HNSWPreset.SMALL},
        "usul_fiqh": {"hnsw": HNSWPreset.MEDIUM},
        "islamic_history": {"hnsw": HNSWPreset.SMALL},
        "arabic_language": {"hnsw": HNSWPreset.SMALL},
    }

    for collection_name, settings in collection_settings.items():
        results[collection_name] = recreate_collection(
            client=client,
            collection_name=collection_name,
            hnsw_preset=settings["hnsw"],
        )

    return results


def create_fiqh_collection(
    client: "QdrantClient",
    collection_name: str = "fiqh_passages",
) -> bool:
    """
    Create fiqh collection with optimal settings for legal text retrieval.

    Optimized configuration:
    - dense_weight=0.6, sparse_weight=0.4 (alpha=0.6)
    - topk_initial=80, topk_final=5 (handled in query, not config)
    - HNSW medium config for balance of speed and accuracy

    Args:
        client: QdrantClient instance
        collection_name: Collection name (default: "fiqh_passages")

    Returns:
        True if successful, False otherwise
    """
    from qdrant_client.models import (
        Distance,
        HnswConfigDiff,
        QuantizationConfigDiff,
        SparseVectorParams,
        VectorParams,
    )

    try:
        # Delete existing collection if exists
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name=collection_name)

        # FiQH optimized config: medium HNSW, INT8 quantization
        vectors_config = {
            "dense": VectorParams(
                size=1024,
                distance=Distance.COSINE,
                hnsw_config=HnswConfigDiff(
                    m=16,  # medium
                    ef_construct=100,
                    full_scan_threshold=10000,
                ),
                quantization_config=QuantizationConfigDiff(
                    quantized_by_default=True,
                    always_ram=True,
                ),
            ),
            "sparse": SparseVectorParams(
                modifier=SparseVectorParams.Modifier.IDF,
                invert=True,
                index=True,
            ),
        }

        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )

        return True

    except Exception:
        return False
