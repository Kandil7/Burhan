"""
Search endpoint for Athar Islamic QA system.

Provides RAG-based search operations.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.schemas.search import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
    SearchRequest,
    SearchResponse,
    SimpleRAGRequest,
    SimpleRAGResponse,
    SearchResult,
)
from src.api.schemas.common import ErrorResponse
from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()
search_router = APIRouter(prefix="/search", tags=["Search"])
GENERIC_SEARCH_ERROR = "Search service temporarily unavailable."


# ── Availability flag ────────────────────────────────────────────────────
try:
    import torch
    import transformers

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# ── Sentinel ─────────────────────────────────────────────────────────────
class _Unavailable:
    """Typed sentinel — replaces the 'fallback' string anti-pattern."""


UNAVAILABLE = _Unavailable()


# ── Compiled regexes ─────────────────────────────────────────────────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CARRIAGE_RE = re.compile(r"\r")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _build_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


# ── Pure helpers ────────────────────────────────────────────────────────
def _require_rag_available() -> None:
    """Check if RAG features are available."""
    if not RAG_AVAILABLE:
        raise HTTPException(503, detail="RAG features not available.")


def _agent_unavailable_response() -> RAGQueryResponse:
    """Return unavailable response."""
    return RAGQueryResponse(
        answer=(
            "نموذج التضمين غير متاح حالياً. "
            "الرجاء تثبيت torch و transformers للبحث المتقدم."
        ),
        citations=[],
        metadata={"rag_available": False},
        confidence=0.0,
        requires_human_review=True,
        trace_id="unavailable",
        processing_time_ms=0,
    )


def _clean_content(text: str) -> str:
    """Strip HTML tags and normalise carriage returns."""
    text = _HTML_TAG_RE.sub("", text)
    text = _CARRIAGE_RE.sub("\n", text)
    return text.strip()


def _strip_thinking(text: str) -> str:
    """Remove <think>… reasoning blocks emitted by models."""
    return _THINK_RE.sub("", text).strip()


def _deduplicate_results(results: list[dict]) -> list[dict]:
    """
    Remove exact duplicate chunks via content fingerprint.

    Uses first ~200 chars of cleaned content as a fingerprint.
    """
    seen: set[int] = set()
    unique: list[dict] = []
    for r in results:
        raw = r.get("content", "") or ""
        # نظف أولاً ثم خذ أوّل 200 حرف
        cleaned = _clean_content(raw)
        fp = hash(cleaned[:200])
        if fp not in seen:
            seen.add(fp)
            unique.append(r)
    return unique


def _build_context(results: list[dict]) -> tuple[str, list[dict]]:
    """
    Dedup → cap → strip HTML → number passages.

    Returns:
        context_str: النص الذي سيُمرّر للـ LLM (مع [1], [2], ...)
        context_results: نفس النتائج بعد dedup + cap (تُستخدم كمصادر).
    """
    deduped = _deduplicate_results(results)
    capped = deduped[:10]
    parts: list[str] = []
    for i, r in enumerate(capped, 1):
        clean = _clean_content(r.get("content", "") or "")
        if clean:
            parts.append(f"[{i}] {clean}")
    return "\n\n".join(parts), capped


def _build_llm_prompt(context: str, query: str, language: str) -> tuple[str, str]:
    """Build LLM prompt for generation, orchestrating multiple Islamic domains."""

    if language == "en":
        system = (
            "You are an Islamic scholar assistant within a retrieval-based system. "
            "You answer ONLY based on the provided excerpts from trusted Islamic sources.\n"
            "\n"
            "General methodology:\n"
            "- Do not issue personal fatwas or new ijtihad. Just report what is in the sources.\n"
            "- Do not invent information or attribute views to scholars without clear basis in the excerpts.\n"
            "- Preserve Qur'an and hadith wording accurately when quoted, and clearly distinguish between text and explanation.\n"
            "- When there is scholarly disagreement in the excerpts, present it fairly without claiming consensus.\n"
            "\n"
            "Multi-domain integration (collections):\n"
            "- You may have excerpts from multiple domains: creed (aqeedah), fiqh, hadith, tafsir, seerah, "
            "history, Arabic language, tazkiyah, usul al-fiqh, and general Islamic information.\n"
            "- Combine all relevant domains into ONE coherent answer: connect verses, hadiths, juristic views, "
            "aqeedah points, historical context, and spiritual insights when available in the context.\n"
            "- If the question is fiqh-related, describe the views of the madhhabs and their evidence as shown "
            "in the excerpts, and explicitly state that this is a presentation from the books, not a personal fatwa.\n"
            "- If the question is about aqeedah, state the Sunni position as reflected in the excerpts and mention other views only if they appear there.\n"
            "- If hadith excerpts appear, mention their grading and sources only as stated in the context.\n"
            "\n"
            "Safety and balance:\n"
            "- For sensitive topics (sects, other religions, historical conflicts), provide a balanced, factual description.\n"
            "- Do not generalize beyond what the excerpts state. Distinguish between those who keep covenants and those who betray them when the context indicates this.\n"
            "- Avoid inflammatory language. Stick to academic, respectful tone.\n"
            "\n"
            "Answer structure:\n"
            "1. Direct answer (2–4 sentences) summarizing the key point.\n"
            "2. Structured explanation that integrates the different domains present in the excerpts "
            "(e.g., verses/tafsir, hadith and their explanation, fiqh positions, aqeedah aspects, historical/seerah context, language notes, tazkiyah insights).\n"
            "3. Evidence section: quote or paraphrase the relevant excerpts with inline citations [1], [2], …\n"
            "4. Limitations: clearly state if the provided context is insufficient, one-sided, or does not allow a complete or applied ruling.\n"
            "\n"
            "Critical constraints:\n"
            "- Answer ONLY from the provided excerpts.\n"
            "- If the excerpts are not enough to answer or to give a balanced view, explicitly say that.\n"
            "- Do NOT fabricate verses, hadiths, attributions, or detailed rulings that are not grounded in the context."
        )

        user = (
            "You are given Islamic source excerpts (labelled [1], [2], …) which may span multiple domains:\n"
            "- Qur'anic verses and tafsir\n"
            "- Hadith texts and their gradings\n"
            "- Fiqh discussions from different madhhabs\n"
            "- Aqeedah (creed) texts\n"
            "- Seerah and Islamic history\n"
            "- Arabic language explanations\n"
            "- Tazkiyah (purification) and spiritual advice\n"
            "- Usul al-fiqh principles\n\n"
            f"Excerpts:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Requirements:\n"
            "- Answer strictly from the excerpts above.\n"
            "- Integrate all relevant domains into a single coherent answer when possible.\n"
            "- Use inline citations [1], [2], … whenever you rely on a specific excerpt.\n"
            "- If the excerpts focus on only one aspect (e.g. punishment), but also contain other aspects "
            "such as covenant, mercy, justice or good treatment, make sure to mention them as well.\n"
            "- If there is not enough information for a balanced or applied answer, clearly state that the context is incomplete."
        )

    else:
        system = (
            "أنت مساعد علمي في نظام استرجاع معرفي إسلامي (أثر)، "
            "تعمل على دمج مخرجات عدّة مجموعات متخصصة (عقيدة، فقه، حديث، تفسير، سيرة، تاريخ، لغة، تزكية، أصول فقه، معلومات عامة).\n"
            "\n"
            "المنهج العام:\n"
            "- مهمّتك عرض ما في المقاطع المسترجعة من الكتب المعتمدة بدقّة وأمانة، دون اجتهاد شخصي جديد.\n"
            "- لا تُصدر فتوى شخصية، ولا تنسب ترجيحًا لنفسك، بل انقل ما في كلام العلماء كما ورد في المقاطع.\n"
            "- لا تخترع معلومات أو تنسب أقوالًا إلى العلماء أو المذاهب ما لم تكن ظاهرة في المقاطع.\n"
            "- حافظ على نصوص القرآن الكريم والأحاديث كما هي عند الاقتباس، وميّز بين النص والشرح.\n"
            "- عند وجود خلاف معتبر في المقاطع، اذكر الأقوال بأدب وإنصاف، دون ادعاء إجماع بلا نص.\n"
            "\n"
            "دمج المجالات (collections):\n"
            "- قد تحتوي المقاطع على آيات وتفسيرها، وأحاديث وتخريجها، وأقوال فقهية لمذاهب مختلفة، "
            "ونصوص في العقيدة، وأحداث من السيرة والتاريخ، وشرح لغوي، ونصوص في التزكية، وقواعد أصولية.\n"
            "- اجمع هذه العناصر في جواب واحد متماسك: اربط بين الآيات وتفسيرها، والأحاديث وشرحها، "
            "وأقوال الفقهاء، وتصور أهل السنة في العقيدة، والسياق التاريخي، والتنبيه اللغوي، والتوجيه الإيماني؛ "
            "كل ذلك فقط إذا كان موجودًا في المقاطع المعطاة.\n"
            "- في المسائل الفقهية: اذكر أقوال المذاهب وأدلتها كما في المقاطع، واستعمل عبارات مثل «قول الجمهور»، "
            "«قول الحنفية»، «قول المالكية» إن كانت ظاهرة في النص، ثم نبّه في الختام أن هذا عرض لأقوال الفقهاء لا فتوى شخصية.\n"
            "- في مسائل العقيدة: بيّن معتقد أهل السنة كما يظهر في المقاطع، واذكر سائر الأقوال إن كانت مذكورة.\n"
            "- في الأحاديث: لا تحكم أنت على درجة الحديث، بل انقل الحكم كما في المقاطع (صححه فلان، ضعّفه فلان...).\n"
            "\n"
            "السلامة والتوازن:\n"
            "- في الأسئلة المتعلّقة بالطوائف أو الأمم الأخرى أو الصراعات التاريخية، التزم بالوصف العلمي المتوازن.\n"
            "- فرّق بين من التزم بالعهد ومن خان وغدر إذا دلّت المقاطع على ذلك، ولا تعمّم بلا دليل.\n"
            "- تجنّب الخطاب الانفعالي أو التحريضي، والتزم بأسلوب علمي وقور.\n"
            "\n"
            "تنظيم الجواب:\n"
            "١. الجواب المباشر في فقرتين إلى أربع فقرات قصيرة يوضّح خلاصة المسألة.\n"
            "٢. شرحٌ منظَّم يدمج المجالات ذات الصلة الموجودة في المقاطع "
            "(تفسير الآيات، شرح الأحاديث، أقوال الفقهاء، تقريرات العقيدة، السياق التاريخي/السيري، التنبيه اللغوي، لمحات التزكية).\n"
            "٣. قسم الأدلّة: الاستشهاد بالمقاطع ذات الصلة مع استعمال أرقامها [1]، [2]، ...\n"
            "٤. بيان حدود السياق: إن كانت المقاطع ناقصة، أو أحادية الجانب، أو لا تسمح بتنزيل الحكم على نازلة معيّنة، فاذكر ذلك بوضوح.\n"
            "\n"
            "قيود أساسية:\n"
            "- التزم بالمقاطع المعطاة فقط.\n"
            "- إن لم تكفِ المقاطع لتكوين صورة متوازنة أو حكم مفصّل، صرّح بأن السياق غير كافٍ، "
            "وأن المسألة تحتاج إلى مزيد من البحث أو سؤال أهل العلم."
        )

        user = (
            "المقاطع الآتية مرقّمة [1]، [2]، ... وهي مقتطفات من مصادر إسلامية متنوعة "
            "(تفسير، حديث، فقه، عقيدة، سيرة، تاريخ، لغة، تزكية، أصول فقه):\n"
            f"{context}\n\n"
            f"السؤال: {query}\n\n"
            "المطلوب:\n"
            "- أجب بالعربية الفصحى الواضحة.\n"
            "- التزم التزامًا تامًا بالمقاطع أعلاه، ولا تضف معلومات من خارجها.\n"
            "- حاول دمج جميع الجوانب ذات الصلة الموجودة في المقاطع (النصوص، الشرح، السياق التاريخي، الفقه، العقيدة، التزكية...).\n"
            "- استخدم أرقام المقاطع [1]، [2]، ... عند الاستشهاد.\n"
            "- إن كان السياق المتاح ناقصًا أو منحازًا لجانب واحد، فاذكر صراحةً أن الصورة غير مكتملة، "
            "ولا تقدّم حكمًا جازمًا يتجاوز ما في النصوص."
        )

    return system, user


def _format_sources(results: list[dict]) -> list[dict]:
    """
    Format search results as sources.

    Adds 'index' لربط [1] في الجواب بالمصدر.
    """
    sources: list[dict] = []
    for i, r in enumerate(results, 1):
        cleaned = _clean_content(r.get("content", "") or "")
        sources.append(
            {
                "index": i,
                "score": r.get("score", 0.0),
                "content": cleaned[:500],
                "content_truncated": len(cleaned) > 500,
                "metadata": r.get("metadata", {}) or {},
            }
        )
    return sources


# ── Dependencies ─────────────────────────────────────────────────────────
def _get_state(request: Request, attr: str, label: str):
    """Get state attribute from app state."""
    obj = getattr(request.app.state, attr, None)
    if obj is None:
        raise HTTPException(503, detail=f"{label} is not initialised.")
    return obj


def get_fiqh_agent(request: Request):
    return _get_state(request, "fiqh_agent", "FiqhAgent")


def get_general_agent(request: Request):
    return _get_state(request, "general_agent", "GeneralIslamicAgent")


def get_embedding_model(request: Request):
    return _get_state(request, "embedding_model", "EmbeddingModel")


def get_vector_store(request: Request):
    return _get_state(request, "vector_store", "VectorStore")


def get_llm_client(request: Request):
    return _get_state(request, "llm_client", "LLM client")


# ── GET /search/stats ────────────────────────────────────────────────────
@search_router.get(
    "/stats",
    response_model=RAGStatsResponse,
    summary="Get RAG statistics",
    responses={503: {"model": ErrorResponse, "description": "Service unavailable"}},
)
async def get_rag_stats(
    request: Request,
    vector_store=Depends(get_vector_store),
    embedding_model=Depends(get_embedding_model),
):
    """Get RAG system statistics."""
    trace_id = _build_trace_id()
    _require_rag_available()

    if not getattr(vector_store, "client", None):
        raise HTTPException(503, detail="Vector store connection is not available.")

    collections: dict[str, Any] = {}
    total_docs = 0
    for coll in vector_store.list_collections():
        try:
            stats = vector_store.get_collection_stats(coll)
            collections[coll] = stats
            total_docs += stats.get("vectors_count", 0)
        except Exception as e:
            logger.warning(
                "search.stats_failed",
                trace_id=trace_id,
                collection=coll,
                error=str(e),
            )
            collections[coll] = {"vectors_count": 0, "error": "unavailable"}

    return RAGStatsResponse(
        collections=collections,
        total_documents=total_docs,
        embedding_model=embedding_model.MODEL_NAME,
    )


# ── POST /search/simple ──────────────────────────────────────────────────
@search_router.post(
    "/simple",
    response_model=SimpleRAGResponse,
    summary="Simple RAG search (single-turn Islamic QA)",
)
async def simple_rag_query(
    request: Request,
    req: SimpleRAGRequest,
    embedding_model=Depends(get_embedding_model),
    vector_store=Depends(get_vector_store),
    llm_client=Depends(get_llm_client),
):
    trace_id = _build_trace_id()
    start_time = time.time()
    _require_rag_available()

    # 1. استخدم SearchService عشان يفسّر "all"
    search_service = request.app.state.search_service
    if req.collection == "all":
        retrieval_output = await search_service.search(
            query=req.query,
            collections=None,  # all = DEFAULT_COLLECTIONS
            top_k=req.top_k,
            filters=None,
        )
    else:
        retrieval_output = await search_service.search(
            query=req.query,
            collections=[req.collection],
            top_k=req.top_k,
            filters=None,
        )

    results: list[dict] = retrieval_output.results

    if not results:
        processing_time_ms = int((time.time() - start_time) * 1000)
        return SimpleRAGResponse(
            answer="لم يتم العثور على نتائج.",
            sources=[],
            metadata={
                "collection": req.collection,
                "retrieved_count": 0,
                "unique_count": 0,
                "context_passages": 0,
                "language": req.language,
                "embedding_model": embedding_model.MODEL_NAME,
                "llm_model": settings.llm_model,
            },
            trace_id=trace_id,
            processing_time_ms=processing_time_ms,
        )

    # 2. Build context (dedup + cap inside)
    context, context_results = _build_context(results)
    # deduped = context_results  # نفس النتائج بعد إزالة التكرار وتحديد الحد الأعلى

    # 3. Generate with LLM
    system_prompt, user_prompt = _build_llm_prompt(context, req.query, req.language)
    response = await llm_client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.rag_temperature,
        max_tokens=settings.rag_max_tokens,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    # نستخدم context_results في sources حتى تطابق ما رآه الـ LLM
    formatted_sources_dicts = _format_sources(context_results)
    # تحويلها لنماذج SearchResult سيقوم به Pydantic تلقائيًا عند بناء SimpleRAGResponse

    return SimpleRAGResponse(
        answer=_strip_thinking(response.choices[0].message.content),
        sources=[SearchResult(**s) for s in formatted_sources_dicts],
        metadata={
            "collection": req.collection,
            "retrieved_count": len(results),
            "unique_count": len(context_results),
            "context_passages": len(context_results),
            "language": req.language,
            "embedding_model": embedding_model.MODEL_NAME,
            "llm_model": settings.llm_model,
        },
        trace_id=trace_id,
        processing_time_ms=processing_time_ms,
    )


# ── 