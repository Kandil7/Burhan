"""
Pytest configuration and fixtures for Burhan tests.

Provides common fixtures and configuration for all tests.
"""

import pytest

# NOTE: an earlier session-scoped `event_loop` fixture lived here. It is the
# deprecated pytest-asyncio pattern and left the main thread without a current
# loop when several async test modules ran together. The default
# function-scoped loop is correct for this suite; see
# docs/learning/sessions/2026-10-22-session-structure-cleanup.md.


@pytest.fixture
async def mock_llm_client():
    """
    Mock LLM client for testing.

    Returns predefined responses instead of calling actual LLM.
    """

    class MockMessage:
        content = '{"intent": "fiqh", "confidence": 0.95, "language": "ar"}'

    class MockChoices:
        message = MockMessage()

    class MockCompletions:
        async def create(self, *args, **kwargs):
            response = type("Response", (), {})()
            response.choices = [MockChoices()]
            return response

    class MockChat:
        completions = MockCompletions()

    class MockLLMClient:
        chat = MockChat()

    return MockLLMClient()


@pytest.fixture
def sample_queries():
    """Sample queries for testing intent classification."""
    return {
        "fiqh": [
            "ما حكم ترك صلاة الجمعة عمداً؟",
            "هل يجوز أكل لحوم الحيوانات غير المذبوحة؟",
            "ما حكم صلاة التراويح؟",
        ],
        "quran": [
            "كم عدد آيات سورة البقرة؟",
            "ما هي أطول سورة في القرآن؟",
            "آتني آية الكرسي",
        ],
        "zakat": [
            "كيف أحسب زكاة مالي؟",
            "هل على الذهب زكاة؟",
            "زكاة الفطر كم تساوي؟",
        ],
        "inheritance": [
            "كيف أقسم الميراث بين الورثة؟",
            "ما نصيب الزوجة من تركة زوجها؟",
            "تركة رجل ترك زوجة وأبوين وابنًا",
        ],
        "greeting": [
            "السلام عليكم",
            "Ramadan Kareem",
            "مرحبا",
        ],
        "dua": [
            "ما دعاء السفر؟",
            "أذكار الصباح والمساء",
            "دعاء الاستخارة",
        ],
        "prayer_times": [
            "ما وقت صلاة الظهر؟",
            "اتجاه القبلة من الدوحة",
            "Prayer times in Cairo",
        ],
        "hijri_calendar": [
            "متى يبدأ رمضان هذا العام؟",
            "م�� التاريخ الهجري اليوم؟",
            "متى عيد الفطر؟",
        ],
    }


# ============================================================================
# Regression Test Fixtures (Epic 8)
# ============================================================================


@pytest.fixture
def regression_classifier():
    """
    Create a HybridIntentClassifier instance for regression tests.

    This uses the same configuration as production to ensure
    accurate testing of intent classification behavior.
    """
    from src.application.router.hybrid_classifier import HybridIntentClassifier

    return HybridIntentClassifier(low_conf_threshold=0.55)


@pytest.fixture
def regression_router(regression_classifier):
    """
    Create a RouterAgent instance for regression tests.

    Uses the configured classifier for intent routing tests.
    """
    from src.application.router.router_agent import RouterAgent

    return RouterAgent(classifier=regression_classifier)
