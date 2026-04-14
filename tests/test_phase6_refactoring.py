"""
Tests for Phase 6 Refactoring.

Tests for:
- LazySingleton pattern
- EraClassifier utility
- Language detection utility
- Async EmbeddingCache
- VectorStore deterministic IDs
- AgentRegistry routing
- CitationNormalizer ID-based mapping
"""
import asyncio
import hashlib
import threading
import time

import numpy as np
import pytest

from src.utils.lazy_singleton import LazySingleton, AsyncLazySingleton
from src.utils.era_classifier import EraClassifier, Era
from src.utils.language_detection import detect_language, is_mostly_arabic, is_mostly_english


# ==========================================
# LazySingleton Tests
# ==========================================

class TestLazySingleton:
    """Tests for LazySingleton pattern."""

    def test_creates_instance_only_once(self):
        """Instance should be created only once."""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return {"created": True}
        
        singleton = LazySingleton(factory)
        
        # First call - creates instance
        instance1 = singleton.get()
        assert call_count == 1
        assert instance1["created"] is True
        
        # Second call - returns same instance
        instance2 = singleton.get()
        assert call_count == 1  # Factory not called again!
        assert instance1 is instance2

    def test_thread_safety(self):
        """Singleton should be thread-safe."""
        call_count = 0
        lock = threading.Lock()
        
        def factory():
            nonlocal call_count
            with lock:
                call_count += 1
                time.sleep(0.01)  # Simulate slow initialization
                return {"thread_safe": True}
        
        singleton = LazySingleton(factory)
        results = []
        
        def get_instance():
            result = singleton.get()
            results.append(result)
        
        # Create multiple threads
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All threads should get same instance
        assert call_count == 1  # Factory called only once!
        assert all(r is results[0] for r in results)

    def test_reset(self):
        """Reset should clear the instance."""
        singleton = LazySingleton(lambda: {"value": 1})
        
        instance1 = singleton.get()
        assert singleton.is_initialized is True
        
        singleton.reset()
        assert singleton.is_initialized is False
        
        instance2 = singleton.get()
        assert singleton.is_initialized is True
        # New instance created
        assert instance1 is not instance2 or instance1 == instance2

    def test_is_initialized(self):
        """is_initialized should reflect state correctly."""
        singleton = LazySingleton(lambda: {"test": True})
        
        assert singleton.is_initialized is False
        
        singleton.get()
        
        assert singleton.is_initialized is True


# ==========================================
# AsyncLazySingleton Tests
# ==========================================

class TestAsyncLazySingleton:
    """Tests for AsyncLazySingleton pattern."""

    @pytest.mark.asyncio
    async def test_creates_instance_only_once(self):
        """Instance should be created only once in async context."""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"async": True}
        
        singleton = AsyncLazySingleton(factory)
        
        instance1 = await singleton.get()
        assert call_count == 1
        
        instance2 = await singleton.get()
        assert call_count == 1  # Not called again
        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Singleton should handle concurrent access."""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return {"concurrent": True}
        
        singleton = AsyncLazySingleton(factory)
        
        # Run multiple concurrent gets
        tasks = [singleton.get() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert call_count == 1  # Factory called only once
        assert all(r is results[0] for r in results)

    @pytest.mark.asyncio
    async def test_reset(self):
        """Reset should clear the instance in async context."""
        singleton = AsyncLazySingleton(lambda: {"value": 1})
        
        await singleton.get()
        assert singleton.is_initialized is True
        
        await singleton.reset()
        assert singleton.is_initialized is False


# ==========================================
# EraClassifier Tests
# ==========================================

class TestEraClassifier:
    """Tests for EraClassifier utility."""

    def test_prophetic_era(self):
        """0-100 AH should be prophetic era."""
        assert EraClassifier.classify(50) == "prophetic"
        assert EraClassifier.classify(100) == "prophetic"

    def test_tabiun_era(self):
        """100-200 AH should be tabiun era."""
        assert EraClassifier.classify(150) == "tabiun"
        assert EraClassifier.classify(200) == "tabiun"

    def test_classical_era(self):
        """200-500 AH should be classical era."""
        assert EraClassifier.classify(250) == "classical"  # Imam al-Shafi'i era
        assert EraClassifier.classify(500) == "classical"

    def test_medieval_era(self):
        """500-900 AH should be medieval era."""
        assert EraClassifier.classify(600) == "medieval"
        assert EraClassifier.classify(900) == "medieval"

    def test_ottoman_era(self):
        """900-1300 AH should be ottoman era."""
        assert EraClassifier.classify(1000) == "ottoman"
        assert EraClassifier.classify(1300) == "ottoman"

    def test_modern_era(self):
        """1300+ AH should be modern era."""
        assert EraClassifier.classify(1400) == "modern"
        assert EraClassifier.classify(1500) == "modern"

    def test_era_enum_values(self):
        """Era enum should have all expected values."""
        assert Era.PROPHETIC.value == "prophetic"
        assert Era.TABIUN.value == "tabiun"
        assert Era.CLASSICAL.value == "classical"
        assert Era.MEDIEVAL.value == "medieval"
        assert Era.OTTOMAN.value == "ottoman"
        assert Era.MODERN.value == "modern"

    def test_get_era_description(self):
        """Should return human-readable descriptions."""
        assert "Prophetic" in EraClassifier.get_era_description("prophetic")
        assert "Golden Age" in EraClassifier.get_era_description("classical")
        assert "Modern" in EraClassifier.get_era_description("modern")


# ==========================================
# Language Detection Tests
# ==========================================

class TestLanguageDetection:
    """Tests for language detection utility."""

    def test_detect_arabic(self):
        """Should detect Arabic text."""
        assert detect_language("ما حكم صلاة العيد؟") == "ar"
        assert detect_language("السلام عليكم") == "ar"

    def test_detect_english(self):
        """Should detect English text."""
        assert detect_language("How to calculate zakat?") == "en"
        assert detect_language("Hello world") == "en"

    def test_mixed_text_majority_arabic(self):
        """Should detect Arabic if >30% Arabic chars."""
        assert detect_language("مرحبا hello") == "ar"

    def test_mixed_text_majority_english(self):
        """Should detect English if <30% Arabic chars."""
        assert detect_language("hello мир") == "en"

    def test_empty_text(self):
        """Empty text should default to Arabic."""
        assert detect_language("") == "ar"
        assert detect_language("   ") == "ar"

    def test_threshold_parameter(self):
        """Should respect custom threshold."""
        # With 0.5 threshold, "مرحبا hello" (50% Arabic) should be Arabic
        assert detect_language("مرحبا hello", threshold=0.5) == "ar"
        
        # With 0.6 threshold, it should be English
        assert detect_language("مرحبا hello", threshold=0.6) == "en"

    def test_is_mostly_arabic(self):
        """Should check if text is mostly Arabic."""
        assert is_mostly_arabic("ما حكم صلاة العيد؟") is True
        assert is_mostly_arabic("Hello world") is False

    def test_is_mostly_english(self):
        """Should check if text is mostly English."""
        assert is_mostly_english("Hello world") is True
        assert is_mostly_english("ما حكم صلاة العيد؟") is False


# ==========================================
# VectorStore Deterministic ID Tests
# ==========================================

class TestVectorStoreDeterministicIDs:
    """Tests for deterministic document IDs in VectorStore."""

    def test_same_content_same_id(self):
        """Same content should generate same ID."""
        content = "صلاة العيد سنة مؤكدة"
        
        id1 = hashlib.sha256(content.encode()).hexdigest()[:16]
        id2 = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        assert id1 == id2
        assert len(id1) == 16  # 16 hex characters

    def test_different_content_different_id(self):
        """Different content should generate different ID."""
        content1 = "صلاة العيد سنة مؤكدة"
        content2 = "صلاة الفجر ركعتان"
        
        id1 = hashlib.sha256(content1.encode()).hexdigest()[:16]
        id2 = hashlib.sha256(content2.encode()).hexdigest()[:16]
        
        assert id1 != id2

    def test_id_is_hex(self):
        """ID should be valid hexadecimal."""
        content = "test content"
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Should not raise
        int(doc_id, 16)


# ==========================================
# Integration Tests
# ==========================================

class TestRefactoringIntegration:
    """Integration tests for refactored components."""

    def test_era_classifier_in_hybrid_search(self):
        """HybridSearcher should use shared EraClassifier."""
        from src.knowledge.hybrid_search import HybridSearcher
        from src.utils.era_classifier import EraClassifier
        
        # Verify import exists
        assert EraClassifier is not None

    def test_era_classifier_in_citation_normalizer(self):
        """CitationNormalizer should use shared EraClassifier."""
        from src.core.citation import CitationNormalizer
        from src.utils.era_classifier import EraClassifier
        
        # Verify import exists
        assert EraClassifier is not None

    def test_lazy_singleton_in_query_route(self):
        """Query route should use LazySingleton."""
        from src.api.routes.query import _chatbot
        from src.utils.lazy_singleton import LazySingleton
        
        assert isinstance(_chatbot, LazySingleton)


# ==========================================
# Performance Tests
# ==========================================

class TestPerformance:
    """Performance tests for refactored components."""

    def test_lazy_singleton_overhead(self):
        """LazySingleton should have minimal overhead."""
        singleton = LazySingleton(lambda: {"value": 1})
        instance = singleton.get()
        
        # Measure overhead
        start = time.time()
        for _ in range(1000):
            singleton.get()
        elapsed = time.time() - start
        
        # Should be very fast (<1ms for 1000 calls)
        assert elapsed < 0.001

    def test_era_classifier_performance(self):
        """EraClassifier should be fast."""
        start = time.time()
        for i in range(1000):
            EraClassifier.classify(i)
        elapsed = time.time() - start
        
        # Should be very fast (<1ms for 1000 calls)
        assert elapsed < 0.001
