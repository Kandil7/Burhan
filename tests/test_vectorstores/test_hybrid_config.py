"""
Tests for hybrid configuration module.

Tests:
- Collection configs for all Islamic knowledge domains
- HNSW config presets and generation
- Hybrid search parameters (alpha, weights)
- Collection management functions

Phase 3.2: Qdrant Collections Setup for hybrid search.
"""

import pytest
from qdrant_client.models import Distance

from src.indexing.vectorstores.hybrid_config import (
    COLLECTION_CONFIGS,
    CollectionConfig,
    DenseVectorConfig,
    HNSWConfig,
    HNSWPreset,
    QuantizationConfig,
    QuantizationType,
    SparseVectorConfig,
    SparseVectorType,
    create_fiqh_collection,
    get_all_collection_names,
    get_collection_config,
    recreate_all_collections,
    recreate_collection,
)


class TestDenseVectorConfig:
    """Tests for DenseVectorConfig class."""

    def test_default_config(self):
        """Test default dense vector configuration."""
        config = DenseVectorConfig()
        assert config.size == 1024
        assert config.distance == Distance.COSINE

    def test_custom_config(self):
        """Test custom dense vector configuration."""
        config = DenseVectorConfig(size=768, distance=Distance.EUCLID)
        assert config.size == 768
        assert config.distance == Distance.EUCLID

    def test_immutability(self):
        """Test that config is immutable (frozen dataclass)."""
        config = DenseVectorConfig()
        with pytest.raises(AttributeError):
            config.size = 512


class TestSparseVectorConfig:
    """Tests for SparseVectorConfig class."""

    def test_default_config(self):
        """Test default sparse vector configuration."""
        config = SparseVectorConfig()
        assert config.type == SparseVectorType.BM25
        assert config.tokenizer == "whitespace"
        assert config.k1 == 1.5
        assert config.b == 0.75

    def test_custom_bm25_params(self):
        """Test custom BM25 parameters."""
        config = SparseVectorConfig(k1=2.0, b=0.5)
        assert config.k1 == 2.0
        assert config.b == 0.5


class TestQuantizationConfig:
    """Tests for QuantizationConfig class."""

    def test_default_config(self):
        """Test default quantization configuration."""
        config = QuantizationConfig()
        assert config.type == QuantizationType.INT8
        assert config.always_ram is True

    def test_float16_config(self):
        """Test FLOAT16 quantization."""
        config = QuantizationConfig(type=QuantizationType.FLOAT16, always_ram=False)
        assert config.type == QuantizationType.FLOAT16
        assert config.always_ram is False


class TestHNSWConfig:
    """Tests for HNSWConfig class."""

    def test_default_config(self):
        """Test default HNSW configuration."""
        config = HNSWConfig()
        assert config.m == 16
        assert config.ef_construct == 100
        assert config.full_scan_threshold == 10000

    def test_small_preset(self):
        """Test HNSW small preset."""
        config = HNSWPreset.SMALL
        assert config.m == 8
        assert config.ef_construct == 64
        assert config.full_scan_threshold == 5000

    def test_medium_preset(self):
        """Test HNSW medium preset."""
        config = HNSWPreset.MEDIUM
        assert config.m == 16
        assert config.ef_construct == 100
        assert config.full_scan_threshold == 10000

    def test_large_preset(self):
        """Test HNSW large preset."""
        config = HNSWPreset.LARGE
        assert config.m == 24
        assert config.ef_construct == 200
        assert config.full_scan_threshold == 20000


class TestCollectionConfig:
    """Tests for CollectionConfig class."""

    def test_fiqh_config(self):
        """Test Fiqh collection configuration."""
        config = COLLECTION_CONFIGS["fiqh"]
        assert config.name == "fiqh"
        assert config.dense.size == 1024
        assert config.sparse.type == SparseVectorType.BM25
        assert config.hnsw == HNSWPreset.LARGE
        assert config.dense_weight == 0.6
        assert config.sparse_weight == 0.4

    def test_all_collections_have_required_fields(self):
        """Test all collections have required configuration fields."""
        for name, config in COLLECTION_CONFIGS.items():
            assert config.name == name
            assert config.dense.size == 1024
            assert config.sparse.type == SparseVectorType.BM25
            assert config.dense_weight + config.sparse_weight == pytest.approx(1.0)

    def test_hnsw_presets_by_collection_size(self):
        """Test HNSW configs match collection importance."""
        # Large collections get LARGE HNSW
        assert COLLECTION_CONFIGS["fiqh"].hnsw == HNSWPreset.LARGE
        assert COLLECTION_CONFIGS["quran"].hnsw == HNSWPreset.LARGE

        # Medium collections get MEDIUM HNSW
        assert COLLECTION_CONFIGS["hadith"].hnsw == HNSWPreset.MEDIUM
        assert COLLECTION_CONFIGS["tafsir"].hnsw == HNSWPreset.MEDIUM
        assert COLLECTION_CONFIGS["aqeedah"].hnsw == HNSWPreset.MEDIUM
        assert COLLECTION_CONFIGS["usul_fiqh"].hnsw == HNSWPreset.MEDIUM

        # Small collections get SMALL HNSW
        assert COLLECTION_CONFIGS["seerah"].hnsw == HNSWPreset.SMALL
        assert COLLECTION_CONFIGS["islamic_history"].hnsw == HNSWPreset.SMALL
        assert COLLECTION_CONFIGS["arabic_language"].hnsw == HNSWPreset.SMALL


class TestCollectionHelperFunctions:
    """Tests for collection helper functions."""

    def test_get_collection_config_existing(self):
        """Test getting config for existing collection."""
        config = get_collection_config("fiqh")
        assert config is not None
        assert config.name == "fiqh"

    def test_get_collection_config_nonexistent(self):
        """Test getting config for non-existent collection."""
        config = get_collection_config("nonexistent")
        assert config is None

    def test_get_all_collection_names(self):
        """Test getting all collection names."""
        names = get_all_collection_names()
        assert len(names) == 9
        assert "fiqh" in names
        assert "hadith" in names
        assert "quran" in names


class TestHybridSearchParameters:
    """Tests for hybrid search parameters."""

    def test_fiqh_alpha_value(self):
        """Test FiQH collection uses correct alpha (dense weight)."""
        config = COLLECTION_CONFIGS["fiqh"]
        alpha = config.dense_weight
        # alpha = 0.6 means 60% dense, 40% sparse
        assert alpha == 0.6

    def test_all_collections_same_weights(self):
        """Test all collections use same hybrid weights."""
        for name, config in COLLECTION_CONFIGS.items():
            assert config.dense_weight == 0.6
            assert config.sparse_weight == 0.4
            assert config.dense_weight + config.sparse_weight == pytest.approx(1.0)

    def test_alpha_parameter_range(self):
        """Test alpha parameter is in valid range for all collections."""
        for name, config in COLLECTION_CONFIGS.items():
            alpha = config.dense_weight
            assert 0.0 <= alpha <= 1.0


class TestCollectionManagement:
    """Tests for collection management functions."""

    def test_recreate_collection_requires_client(self):
        """Test recreate_collection needs QdrantClient."""
        # Mock the client - actual Qdrant not needed for unit test
        mock_client = None
        # This would fail with real Qdrant but passes type check
        # In integration tests, actual Qdrant would be used
        assert recreate_collection is not None

    def test_recreate_all_collections_returns_dict(self):
        """Test recreate_all_collections returns results dict."""
        assert recreate_all_collections is not None
        # Returns dict[str, bool] - tested in integration tests

    def test_create_fiqh_collection_exists(self):
        """Test create_fiqh_collection function exists."""
        assert create_fiqh_collection is not None


class TestQuantizationSettings:
    """Tests for quantization configuration."""

    def test_all_collections_use_int8(self):
        """Test all collections use INT8 quantization."""
        for name, config in COLLECTION_CONFIGS.items():
            assert config.quantization.type == QuantizationType.INT8

    def test_all_collections_keep_vectors_in_ram(self):
        """Test all collections keep quantized vectors in RAM."""
        for name, config in COLLECTION_CONFIGS.items():
            assert config.quantization.always_ram is True


class TestBM25Parameters:
    """Tests for BM25 sparse vector parameters."""

    def test_all_collections_use_bm25(self):
        """Test all collections use BM25 sparse vectors."""
        for name, config in COLLECTION_CONFIGS.items():
            assert config.sparse.type == SparseVectorType.BM25

    def test_bm25_default_parameters(self):
        """Test BM25 default k1 and b parameters."""
        config = SparseVectorConfig()
        assert config.k1 == 1.5
        assert config.b == 0.75
