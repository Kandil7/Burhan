"""
Unit tests for HybridIntentClassifier.

Tests the keyword fast-path and Jaccard fallback classification pipeline.
"""

import pytest

from src.application.router import HybridIntentClassifier
from src.domain.intents import Intent, QuranSubIntent


@pytest.fixture
def clf():
    """Create a fresh classifier instance for each test."""
    return HybridIntentClassifier(low_conf_threshold=0.55)


# ============================================================================
# FiQH Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fiqh_ar(clf):
    """Test FiQH intent classification in Arabic."""
    r = await clf.classify("ما حكم ترك صلاة الجمعة عمداً؟")
    assert r.intent == Intent.FIQH
    assert r.confidence >= 0.85
    assert r.requires_retrieval is True


@pytest.mark.asyncio
async def test_fiqh_en(clf):
    """Test FiQH intent classification in English."""
    r = await clf.classify("Is cryptocurrency trading halal?")
    assert r.intent == Intent.FIQH


# ============================================================================
# Quran Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quran_analytics(clf):
    """Test Quran analytics sub-intent."""
    r = await clf.classify("كم عدد آيات سورة البقرة؟")
    assert r.intent == Intent.QURAN
    assert r.quran_subintent == QuranSubIntent.ANALYTICS
    assert r.requires_retrieval is False  # analytics doesn't need RAG


@pytest.mark.asyncio
async def test_quran_verse_lookup(clf):
    """Test Quran verse lookup sub-intent."""
    r = await clf.classify("اقرأ آية الكرسي 2:255")
    assert r.intent == Intent.QURAN
    assert r.quran_subintent == QuranSubIntent.VERSE_LOOKUP


@pytest.mark.asyncio
async def test_quran_interpretation(clf):
    """Test Quran interpretation sub-intent."""
    r = await clf.classify("ما معنى قوله تعالى")
    assert r.intent == Intent.QURAN
    assert r.quran_subintent == QuranSubIntent.INTERPRETATION


# ============================================================================
# Hadith Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_hadith_ar(clf):
    """Test Hadith intent classification in Arabic."""
    r = await clf.classify("ما صحة حديث إنما الأعمال بالنيات؟")
    assert r.intent == Intent.HADITH
    assert r.requires_retrieval is True


@pytest.mark.asyncio
async def test_hadith_sanad(clf):
    """Test Hadith with sanad (chain of transmission)."""
    r = await clf.classify("حديث سند البخاري")
    assert r.intent == Intent.HADITH


# ============================================================================
# Tafsir Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_tafsir(clf):
    """Test Tafsir intent classification."""
    r = await clf.classify("تفسير ابن كثير للآية 255")
    assert r.intent == Intent.TAFSIR


# ============================================================================
# Aqeedah Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aqeedah(clf):
    """Test Aqeedah (creed) intent classification."""
    r = await clf.classify("ما هي أركان الإيمان؟")
    assert r.intent == Intent.AQEEDAH


# ============================================================================
# Seerah Intent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_seerah(clf):
    """Test Seerah (Prophet biography) intent classification."""
    r = await clf.classify("السيرة النبوية وغزوة بدر")
    assert r.intent == Intent.SEERAH


# ============================================================================
# Fallback Tests
# ============================================================================


@pytest.mark.asyncio
async def test_empty_query(clf):
    """Test empty query defaults to ISLAMIC_KNOWLEDGE."""
    r = await clf.classify("")
    assert r.intent == Intent.ISLAMIC_KNOWLEDGE
    assert r.confidence == 0.50


# ============================================================================
# Language Detection Tests
# ============================================================================


@pytest.mark.asyncio
async def test_language_ar(clf):
    """Test Arabic language detection."""
    r = await clf.classify("ما حكم الزكاة في الإسلام؟")
    assert r.language == "ar"


@pytest.mark.asyncio
async def test_language_en(clf):
    """Test English language detection."""
    r = await clf.classify("What is the ruling on fasting in Islam?")
    assert r.language == "en"


@pytest.mark.asyncio
async def test_language_mixed(clf):
    """Test mixed language detection."""
    r = await clf.classify("ما حكم_salah في Islam؟")
    assert r.language == "mixed"


# ============================================================================
# Priority Tests
# ============================================================================


@pytest.mark.asyncio
async def test_priority_quran_over_fiqh(clf):
    """Test that more specific intents have higher priority."""
    # "آية" should match QURAN, not FIQH
    r = await clf.classify("آية عن الصبر")
    assert r.intent == Intent.QURAN


# ============================================================================
# Method Tests
# ============================================================================


@pytest.mark.asyncio
async def test_method_keyword(clf):
    """Test keyword matching method."""
    r = await clf.classify("حديث نبوي")
    assert r.method == "keyword"


# ============================================================================
# RouterAgent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_low_confidence_override():
    """Test confidence threshold override."""
    from src.application.router import RouterAgent

    clf = HybridIntentClassifier()
    router = RouterAgent(clf, conf_threshold=0.99)  # very high threshold
    d = await router.route("something ambiguous")
    assert d.result.intent == Intent.ISLAMIC_KNOWLEDGE  # fallback


@pytest.mark.asyncio
async def test_route_construction(clf):
    """Test route string construction."""
    from src.application.router import RouterAgent

    router = RouterAgent(clf)
    d = await router.route("ما حكم الصلاة؟")
    assert d.route == "fiqh_agent"


@pytest.mark.asyncio
async def test_route_quran_subintents(clf):
    """Test Quran sub-intent route construction."""
    from src.application.router import RouterAgent

    router = RouterAgent(clf)

    # verse_lookup
    d = await router.route("آية الكرسي 2:255")
    assert d.route == "quran:verse_lookup"

    # analytics
    d = await router.route("كم عدد آيات سورة البقرة؟")
    assert d.route == "quran:nl2sql"
