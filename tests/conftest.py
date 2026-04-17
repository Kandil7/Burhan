"""
Pytest configuration and fixtures for Athar tests.

Provides common fixtures and configuration for all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_llm_client():
    """
    Mock LLM client for testing.

    Returns predefined responses instead of calling actual LLM.
    """

    class MockLLMClient:
        class MockCompletions:
            class MockChoices:
                class MockMessage:
                    content = '{"intent": "fiqh", "confidence": 0.95, "language": "ar"}'

                message = MockMessage()

            async def create(self, *args, **kwargs):
                response = type("Response", (), {})()
                response.choices = [self.MockChoices()]
                return response

        class MockChat:
            completions = MockLLMClient.MockCompletions()

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
