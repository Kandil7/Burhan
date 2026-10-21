"""
Answer Query Use Case for Burhan Islamic QA system.

Orchestrates the full query answering flow:
1. Intent classification & routing
2. Agent selection from registry
3. RAG pipeline execution (retrieve -> verify -> generate)
4. Policy enforcement
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from src.agents.base import AgentInput, AgentOutput
from src.config.logging_config import get_logger
from src.tools.base import ToolOutput

logger = get_logger()


@dataclass
class AnswerQueryInput:
    """Input for answer query use case."""

    query: str
    language: str = "ar"
    madhhab: str | None = None
    user_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerQueryOutput:
    """Output for answer query use case."""

    answer: str
    intent: str
    confidence: float
    citations: list[dict[str, Any]]
    citation_chunks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_human_review: bool = False


class AnswerQueryUseCase:
    """
    Main use case for answering user queries.

    Coordinates between the router, the agent registry, and the agents.
    """

    def __init__(self, agent_registry: Any = None, router: Any = None):
        """
        Initialize with injected dependencies.

        Args:
            agent_registry: AgentRegistry instance
            router: RouterAgent instance
        """
        self._registry = agent_registry
        self._router = router

    async def execute(self, input_data: AnswerQueryInput) -> AnswerQueryOutput:
        """
        Execute the answer query flow.

        Args:
            input_data: Request parameters

        Returns:
            AnswerQueryOutput with response and metadata
        """
        start_time = time.time()

        # 1. Resolve Dependencies
        # Use injected or global fallbacks
        router = self._router
        if not router:
            from src.application.router.router_agent import get_router_agent

            router = get_router_agent()

        registry = self._registry
        if not registry:
            from src.core.registry import get_registry

            registry = get_registry()

        # 2. Routing & Intent Classification
        decision = await router.route(input_data.query)
        intent = decision.result.intent

        logger.info(
            "use_case.answer_query.routed",
            intent=intent.value,
            confidence=decision.result.confidence,
        )

        # 2. Agent Selection from Registry
        registry = self._registry
        if not registry:
            from src.core.registry import get_registry

            registry = get_registry()

        # IMPORTANT: Use the intent from the router to find the specialized agent
        agent, is_agent = registry.get_for_intent(intent)

        if not agent:
            logger.warning("use_case.answer_query.no_agent_for_intent", intent=intent.value)
            # Fallback to general agent or chatbot
            agent = registry.get_agent("general_islamic_agent")
            if not agent:
                agent = registry.get_agent("chatbot_agent")
        else:
            logger.info("use_case.answer_query.selected_agent", agent_name=getattr(agent, "name", "unknown"))

        # 4. Agent Execution
        # V2 agents use .run() for the full pipeline; legacy agents use .execute()
        result: AgentOutput
        try:
            if not is_agent:
                # The registry may route a tool intent (duas, prayer times, ...)
                # to a deterministic tool instead of a RAG agent.
                result = await self._run_tool(agent, input_data)
            elif hasattr(agent, "run"):
                # V2 Collection-aware RAG pipeline
                result = await agent.run(
                    input_data.query,
                    meta={
                        "language": input_data.language,
                        "madhhab": input_data.madhhab,
                        "sub_intent": getattr(decision.result, "quran_subintent", None),
                    },
                )
            else:
                # Standard/Legacy adapter
                result = await agent.execute(
                    AgentInput(
                        query=input_data.query,
                        language=input_data.language,
                        metadata={
                            "madhhab": input_data.madhhab,
                            "sub_intent": getattr(decision.result, "quran_subintent", None),
                        },
                    )
                )
        except Exception as e:
            logger.error("use_case.answer_query.agent_error", error=str(e), exc_info=True)
            return self._build_error_output(input_data, str(e))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # 5. Build Output
        # Use router confidence for the top-level 'confidence' field (intent_confidence in API)
        return AnswerQueryOutput(
            answer=result.answer,
            intent=intent.value,
            confidence=decision.result.confidence,  # Correct: intent classification confidence
            citations=[c.model_dump() for c in result.citations],
            metadata={
                **result.metadata,
                "verification_confidence": result.confidence,  # Now separate
                "processing_time_ms": processing_time_ms,
                "router_method": decision.result.method,
            },
            citation_chunks=result.citation_chunks,
            requires_human_review=result.requires_human_review,
        )

    def _build_error_output(self, input_data: AnswerQueryInput, error: str) -> AnswerQueryOutput:
        """Build error response when agent fails."""
        return AnswerQueryOutput(
            answer="عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.",
            intent="unknown",
            confidence=0.0,
            citations=[],
            metadata={"error": error},
            requires_human_review=True,
        )

    async def _run_tool(self, tool: Any, input_data: AnswerQueryInput) -> AgentOutput:
        """
        Execute a deterministic tool and adapt its output to AgentOutput.

        Tools use ``ToolOutput`` and keyword arguments, while the rest of the
        pipeline expects ``AgentOutput``. Calculators that expose no ``execute``
        method are only available through their dedicated /tools endpoint.
        """
        tool_name = getattr(tool, "name", tool.__class__.__name__)

        if not hasattr(tool, "execute"):
            return AgentOutput(
                answer=(
                    "هذه الأداة تُستخدم عبر نقطة النهاية المخصصة لها وليس عبر /ask. "
                    "مثال: /api/v1/tools/zakat أو /api/v1/tools/inheritance."
                ),
                confidence=0.0,
                metadata={
                    "tool": tool_name,
                    "error": "tool_requires_dedicated_endpoint",
                },
            )

        params: dict[str, Any] = {"query": input_data.query}
        for key in (
            "occasion",
            "category",
            "limit",
            "lat",
            "lng",
            "date_str",
            "method",
            "timezone",
            "gregorian_date",
            "hijri_year",
            "hijri_month",
            "hijri_day",
        ):
            if key in input_data.context:
                params[key] = input_data.context[key]

        try:
            output: ToolOutput = await tool.execute(**params)
        except Exception as e:
            logger.error(
                "use_case.answer_query.tool_error",
                tool=tool_name,
                error=str(e),
                exc_info=True,
            )
            return AgentOutput(
                answer="تعذّر تنفيذ الأداة المطلوبة. تحقق من المدخلات وحاول مرة أخرى.",
                confidence=0.0,
                requires_human_review=True,
                metadata={"tool": tool_name, "error": str(e)},
            )

        if not output.success:
            return AgentOutput(
                answer=f"تعذّر تنفيذ الأداة: {output.error}",
                confidence=0.0,
                requires_human_review=True,
                metadata={"tool": tool_name, "error": output.error},
            )

        return AgentOutput(
            answer=self._format_tool_answer(output.result),
            confidence=0.95,
            metadata={
                "tool": tool_name,
                "tool_result": output.result,
                **(output.metadata or {}),
            },
        )

    @staticmethod
    def _format_tool_answer(payload: dict[str, Any]) -> str:
        """Render a deterministic tool result as user-facing text.

        Tools return structured dictionaries. Dumping raw JSON into `answer`
        is not an answer a person can read, so each known shape gets a short
        Arabic rendering and only unknown shapes fall back to JSON.
        """
        duas = payload.get("duas")
        if isinstance(duas, list):
            if not duas:
                return "لم يتم العثور على أدعية مطابقة في المصادر الموثقة."
            blocks = []
            for dua in duas[:3]:
                arabic = str(dua.get("arabic_text", "")).strip()
                translation = str(dua.get("translation", "")).strip()
                block = f"{arabic}\n{translation}".strip()
                if block:
                    blocks.append(block)
            count = payload.get("count", len(duas))
            return f"عدد النتائج: {count}\n\n" + "\n\n".join(blocks)

        hijri = payload.get("hijri_date")
        if isinstance(hijri, dict) and hijri.get("formatted_ar"):
            lines = [
                f"التاريخ الهجري: {hijri['formatted_ar']}",
                f"التاريخ الميلادي: {payload.get('gregorian_date', '')}",
            ]
            if hijri.get("formatted_en"):
                lines.append(f"({hijri['formatted_en']})")
            if payload.get("is_ramadan"):
                lines.append("الشهر الحالي هو شهر رمضان.")
            if payload.get("is_eid"):
                lines.append("هذا اليوم عيد.")
            special = payload.get("special_day")
            if special:
                lines.append(f"مناسبة اليوم: {special}")
            return "\n".join(lines)

        times = payload.get("times")
        if isinstance(times, dict) and times:
            labels = {
                "fajr": "الفجر",
                "sunrise": "الشروق",
                "dhuhr": "الظهر",
                "asr": "العصر",
                "maghrib": "المغرب",
                "isha": "العشاء",
            }
            location = payload.get("location") or {}
            header = f"مواقيت الصلاة ليوم {payload.get('date', '')}"
            if location.get("lat") is not None and location.get("lng") is not None:
                header += f" عند ({location['lat']}, {location['lng']})"
            rows = [header]
            for key, label in labels.items():
                value = times.get(key)
                if value:
                    rows.append(f"- {label}: {value}")
            if payload.get("qibla_direction") is not None:
                rows.append(f"اتجاه القبلة: {payload['qibla_direction']} درجة")
            return "\n".join(rows)

        return json.dumps(payload, ensure_ascii=False)


# Singleton instance
_instance: AnswerQueryUseCase | None = None


def get_answer_query_use_case(agent_registry: Any = None, router: Any = None) -> AnswerQueryUseCase:
    """Get or create global use case instance."""
    global _instance
    if _instance is None:
        _instance = AnswerQueryUseCase(agent_registry=agent_registry, router=router)
    return _instance


# default use case
answer_query_use_case = AnswerQueryUseCase()
