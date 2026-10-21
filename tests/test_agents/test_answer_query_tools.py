"""
Tests for tool execution inside the answer-query use case.

Tool intents (duas, prayer times, ...) route to deterministic tools, not RAG
agents. The use case must adapt ToolOutput to AgentOutput instead of assuming
every routed target has an ``answer`` attribute.
"""

from types import SimpleNamespace

import pytest

from src.application.use_cases.answer_query import AnswerQueryInput, AnswerQueryUseCase
from src.domain.intents import Intent
from src.tools.base import ToolOutput


class _StubRouter:
    def __init__(self, intent=Intent.DUAS):
        self.intent = intent

    async def route(self, query):
        result = SimpleNamespace(
            intent=self.intent,
            confidence=0.9,
            method="keyword",
            quran_subintent=None,
        )
        return SimpleNamespace(result=result)


class _StubRegistry:
    def __init__(self, target):
        self.target = target

    def get_for_intent(self, intent):
        return self.target, False

    def get_agent(self, name):
        return None


class _DuaTool:
    name = "dua_tool"

    def __init__(self, output):
        self.output = output

    async def execute(self, **kwargs):
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


class _CalculatorWithoutExecute:
    name = "zakat_tool"


def _use_case(target):
    return AnswerQueryUseCase(agent_registry=_StubRegistry(target), router=_StubRouter())


@pytest.mark.asyncio
async def test_tool_output_is_adapted_to_agent_output():
    tool = _DuaTool(
        ToolOutput(
            result={
                "duas": [
                    {
                        "arabic_text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ",
                        "translation": "We have reached the morning",
                    }
                ],
                "count": 1,
            },
            success=True,
            metadata={"source": "Hisn al-Muslim"},
        )
    )

    output = await _use_case(tool).execute(AnswerQueryInput(query="أدعية الصباح"))

    assert "أَصْبَحْنَا" in output.answer
    assert "عدد النتائج: 1" in output.answer
    assert output.metadata["tool"] == "dua_tool"
    assert output.metadata["source"] == "Hisn al-Muslim"
    assert output.metadata["verification_confidence"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_failed_tool_output_marks_human_review():
    tool = _DuaTool(ToolOutput(result={}, success=False, error="dataset missing"))

    output = await _use_case(tool).execute(AnswerQueryInput(query="دعاء"))

    assert "dataset missing" in output.answer
    assert output.requires_human_review is True
    assert output.metadata["verification_confidence"] == 0


@pytest.mark.asyncio
async def test_tool_exception_is_handled():
    tool = _DuaTool(RuntimeError("boom"))

    output = await _use_case(tool).execute(AnswerQueryInput(query="دعاء"))

    assert output.requires_human_review is True
    assert output.metadata["error"] == "boom"


@pytest.mark.asyncio
async def test_hijri_tool_output_is_rendered_as_text():
    """The Hijri tool returns a dict; the answer must be readable Arabic."""
    tool = _DuaTool(
        ToolOutput(
            result={
                "gregorian_date": "2026-10-21",
                "hijri_date": {
                    "year": 1448,
                    "month": 5,
                    "day": 11,
                    "month_name_en": "Jumada al-Ula",
                    "month_name_ar": "جمادى الأولى",
                    "formatted_en": "11 Jumada al-Ula 1448 AH",
                    "formatted_ar": "11 جمادى الأولى 1448 هـ",
                },
                "is_ramadan": False,
                "is_eid": False,
                "special_day": None,
            },
            success=True,
        )
    )

    output = await _use_case(tool).execute(AnswerQueryInput(query="ما التاريخ الهجري اليوم؟"))

    assert "11 جمادى الأولى 1448 هـ" in output.answer
    assert "2026-10-21" in output.answer
    assert not output.answer.strip().startswith("{")


@pytest.mark.asyncio
async def test_prayer_times_tool_output_is_rendered_as_text():
    """Prayer times are listed per prayer instead of dumped as JSON."""
    tool = _DuaTool(
        ToolOutput(
            result={
                "date": "2026-10-21",
                "location": {"lat": 30.04, "lng": 31.24},
                "times": {
                    "fajr": "05:01",
                    "sunrise": "06:19",
                    "dhuhr": "11:44",
                    "asr": "15:00",
                    "maghrib": "17:09",
                    "isha": "18:29",
                },
                "qibla_direction": 136.5,
            },
            success=True,
        )
    )

    output = await _use_case(tool).execute(AnswerQueryInput(query="مواقيت الصلاة اليوم"))

    assert "الفجر: 05:01" in output.answer
    assert "العشاء: 18:29" in output.answer
    assert "2026-10-21" in output.answer
    assert "{" not in output.answer


@pytest.mark.asyncio
async def test_calculator_without_execute_points_to_dedicated_endpoint():
    output = await _use_case(_CalculatorWithoutExecute()).execute(AnswerQueryInput(query="كم زكاة مالي؟"))

    assert "/api/v1/tools/zakat" in output.answer
    assert output.metadata["error"] == "tool_requires_dedicated_endpoint"


def test_generic_request_word_no_longer_matches_duas():
    """A generic word like طلب must not route a knowledge question to the dua tool."""
    from src.core.router import HybridQueryClassifier

    classifier = HybridQueryClassifier()

    result = classifier._keyword_match("ما هو فضل طلب العلم؟")

    assert result is None or result.intent != Intent.DUAS
