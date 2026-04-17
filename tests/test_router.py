"""
Tests for Hybrid Intent Classifier.

Tests the three-tier classification system:
1. Keyword matching
2. LLM classification
3. Embedding fallback
"""

import pytest
from src.core.router import HybridQueryClassifier
from src.config.intents import Intent


class TestHybridQueryClassifier:
    """Test suite for HybridQueryClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return HybridQueryClassifier()

    # ==========================================
    # Keyword Matching Tests
    # ==========================================

    def test_keyword_zakat_detection(self, classifier):
        """Test zakat keyword detection."""
        result = classifier._keyword_match("ما حكم زكاة المال؟")
        assert result is not None
        assert result.intent == Intent.ZAKAT
        assert result.confidence >= 0.90
        assert result.method == "keyword"

    def test_keyword_inheritance_detection(self, classifier):
        """Test inheritance keyword detection."""
        result = classifier._keyword_match("كيف أقسم الميراث؟")
        assert result is not None
        assert result.intent == Intent.INHERITANCE
        assert result.confidence >= 0.90

    def test_keyword_quran_detection(self, classifier):
        """Test Quran keyword detection."""
        result = classifier._keyword_match("كم عدد آيات سورة البقرة؟")
        assert result is not None
        assert result.intent == Intent.QURAN
        assert result.confidence >= 0.90

    def test_keyword_greeting_detection(self, classifier):
        """Test greeting keyword detection."""
        result = classifier._keyword_match("السلام عليكم ورحمة الله")
        assert result is not None
        assert result.intent == Intent.GREETING
        assert result.confidence >= 0.90

    def test_keyword_dua_detection(self, classifier):
        """Test dua keyword detection."""
        result = classifier._keyword_match("ما دعاء السفر؟")
        assert result is not None
        assert result.intent == Intent.DUA
        assert result.confidence >= 0.90

    def test_keyword_prayer_times_detection(self, classifier):
        """Test prayer times keyword detection."""
        result = classifier._keyword_match("ما وقت صلاة الظهر؟")
        assert result is not None
        assert result.intent == Intent.PRAYER_TIMES
        assert result.confidence >= 0.90

    def test_keyword_hijri_detection(self, classifier):
        """Test Hijri calendar keyword detection."""
        result = classifier._keyword_match("متى يبدأ رمضان؟")
        assert result is not None
        assert result.intent == Intent.HIJRI_CALENDAR
        assert result.confidence >= 0.90

    def test_no_keyword_match(self, classifier):
        """Test when no keywords match."""
        result = classifier._keyword_match("What is the meaning of life?")
        assert result is None

    # ==========================================
    # Language Detection Tests
    # ==========================================

    def test_detect_arabic_language(self, classifier):
        """Test Arabic language detection."""
        query = "ما حكم الصلاة؟"
        lang = classifier._detect_language(query)
        assert lang == "ar"

    def test_detect_english_language(self, classifier):
        """Test English language detection."""
        query = "What is the ruling on prayer?"
        lang = classifier._detect_language(query)
        assert lang == "en"

    def test_detect_mixed_language(self, classifier):
        """Test mixed language detection (majority wins)."""
        query = "ما حكم prayer in Islam?"
        lang = classifier._detect_language(query)
        # Should detect based on ratio
        assert lang in ["ar", "en"]

    # ==========================================
    # Full Classification Tests
    # ==========================================

    @pytest.mark.asyncio
    async def test_classify_zakat_query(self, classifier):
        """Test full classification of zakat query."""
        result = await classifier.classify("كيف أحسب زكاة ذهبي؟")
        assert result.intent == Intent.ZAKAT
        assert result.confidence >= 0.90  # Should match keyword
        assert result.method == "keyword"

    @pytest.mark.asyncio
    async def test_classify_quran_query(self, classifier):
        """Test full classification of Quran query."""
        result = await classifier.classify("آتني سورة الإخلاص")
        assert result.intent == Intent.QURAN
        assert result.confidence >= 0.90

    @pytest.mark.asyncio
    async def test_classify_empty_query(self, classifier):
        """Test classification of empty query."""
        result = await classifier.classify("")
        assert result.intent == Intent.GREETING
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_classify_whitespace_query(self, classifier):
        """Test classification of whitespace query."""
        result = await classifier.classify("   ")
        assert result.intent == Intent.GREETING
        assert result.confidence == 0.5

    # ==========================================
    # Intent-Specific Tests
    # ==========================================

    @pytest.mark.parametrize(
        "query,expected_intent",
        [
            ("ما حكم زكاة الفطر؟", Intent.ZAKAT),
            ("كم عدد آيات الفاتحة؟", Intent.QURAN),
            ("السلام عليكم", Intent.GREETING),
            ("دعاء الاستخارة", Intent.DUAS),
            ("متى رمضان؟", Intent.HIJRI_CALENDAR),
            ("وقت صلاة المغرب", Intent.PRAYER_TIMES),
            ("تقسيم الميراث", Intent.INHERITANCE),
        ],
    )
    def test_keyword_classification_parametrized(self, classifier, query, expected_intent):
        """Test keyword classification for various intents."""
        result = classifier._keyword_match(query)
        assert result is not None
        assert result.intent == expected_intent
