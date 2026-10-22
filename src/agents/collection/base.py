"""
Collection-Aware RAG Agent Base for Burhan Islamic QA system.

This module provides the canonical base class for all v2 collection agents,
integrating retrieval, verification, and generation into a unified pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentInput, Citation, strip_cot_leakage
from src.application.ports import EmbeddingPort, VectorSearchPort
from src.domain.intents import Intent

# One-release shim: AgentOutput moved to src.domain.models (Phase 2).
from src.domain.models import AgentOutput as AgentOutput
from src.verification import (
    VerificationCheck as VerificationCheck,
)
from src.verification import (
    VerificationReport,
    VerificationSuite,
)

logger = logging.getLogger(__name__)

# Arabic sentence-ending characters for truncation detection
_SENTENCE_ENDINGS = {".", "؟", "!", ")", "﴾", "»", "\u06d4"}

# Normalize "المائدة: 82" → "المائدة:82" for VerseRetrievalEngine
_COLON_SPACES_RE = re.compile(r"\s*:\s*")

# Maximum seconds allowed for retrieve_candidates() before TimeoutError
_RETRIEVAL_TIMEOUT_SECONDS = 8.0

# Markers of a provider rejection that a smaller output budget can fix.
_BUDGET_ERROR_MARKERS = (
    "output tokens per minute",
    "tokens per minute",
    "request too large",
    "otpm",
    "max_tokens",
)


def _is_output_budget_error(exc: Exception) -> bool:
    """Return True when the provider refused the request over its budget."""
    text = str(exc).lower()
    return any(marker in text for marker in _BUDGET_ERROR_MARKERS)


def _normalize_source_ref(src: str) -> str:
    """Remove spaces around colon in verse references."""
    return _COLON_SPACES_RE.sub(":", src.strip())


def _is_answer_truncated(answer: str) -> bool:
    """Return True if answer appears cut mid-sentence (max_tokens reached)."""
    stripped = answer.rstrip()
    return not stripped or stripped[-1] not in _SENTENCE_ENDINGS


class RetrievalStrategy(BaseModel):
    """Configuration for retrieval pipeline."""

    dense_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for dense (semantic) retrieval",
    )
    sparse_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for sparse (keyword) retrieval",
    )
    top_k: int = Field(
        default=12,
        ge=1,
        le=100,
        description="Number of candidates to retrieve",
    )
    rerank: bool = Field(default=True, description="Whether to apply reranking")
    score_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold for inclusion",
    )


class FallbackPolicy(BaseModel):
    """Fallback strategy when primary retrieval fails or is insufficient."""

    strategy: str = Field(
        default="chatbot",
        description="Strategy: chatbot/human_review/clarify",
    )
    message: str | None = Field(default=None, description="Custom fallback message")


class CollectionAgentConfig(BaseModel):
    """Complete configuration for a CollectionAgent."""

    collection_name: str = Field(description="Qdrant collection name")
    strategy: RetrievalStrategy = Field(
        default_factory=RetrievalStrategy,
        description="Retrieval strategy configuration",
    )
    verification_suite: VerificationSuite = Field(
        default_factory=VerificationSuite,
        description="Verification suite configuration",
    )
    fallback_policy: FallbackPolicy = Field(
        default_factory=FallbackPolicy,
        description="Fallback policy configuration",
    )
    system_prompt: str = Field(
        default="",
        description="Optional system prompt loaded from the prompt file",
    )


class CollectionAgent(ABC):
    """
    Abstract base class for collection-aware RAG agents.

    Provides the full pipeline:
    1. query_intake         - Normalize and prepare query
    2. classify_intent      - Classify to agent-specific intent
    3. retrieve_candidates  - Retrieve passages from collection
    4. rerank_candidates    - Apply reranking
    5. run_verification     - Verify candidates
    6. generate_answer      - Generate answer from verified passages
    7. assemble_citations   - Build citation references
    """

    name: str = "collection_agent"
    COLLECTION: str = ""

    def __init__(self, config: CollectionAgentConfig | None = None) -> None:
        self.config = config or CollectionAgentConfig(
            collection_name=self.COLLECTION,
        )
        # Set by generate_answer when the LLM call fails and raw evidence is
        # returned instead of a composed answer.
        self._generation_failed = False
        # The collaborators are injected by the registry. They default to
        # None here so the base class can talk about them safely.
        self.embedding_model: EmbeddingPort | None = None
        self.vector_store: VectorSearchPort | None = None
        self.llm_client: Any = None

    @abstractmethod
    def query_intake(self, query: str) -> str: ...

    @abstractmethod
    def classify_intent(self, query: str) -> Intent: ...

    @abstractmethod
    async def retrieve_candidates(self, query: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def rerank_candidates(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def run_verification(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        answer: str = "",
        stage: str = "evidence",
    ) -> VerificationReport: ...

    @abstractmethod
    async def generate_answer(self, query: str, verified_passages: list[dict[str, Any]], language: str) -> str: ...

    @abstractmethod
    def assemble_citations(self, passages: list[dict[str, Any]]) -> list[Citation]: ...

    def _format_passages(self, passages: list[dict[str, Any]]) -> str:
        """Render passages for the prompt; subclasses override this."""
        return ""

    # ==========================================
    # Shared Helpers
    # ==========================================

    def _verify(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        answer: str = "",
        stage: str = "evidence",
    ) -> VerificationReport:
        """Run the configured suite, falling back to the per-agent default.

        A configured suite with no checks used to mean "verify nothing", and
        several agents returned `is_verified=True` unconditionally. Falling
        back to the named suite keeps every agent honest.
        """
        from src.verification.suite_builder import (
            build_verification_suite_for,
            run_verification_suite,
        )

        suite = self.config.verification_suite if self.config else None
        if suite is None or not suite.checks:
            suite = build_verification_suite_for(self.name)

        return run_verification_suite(
            suite=suite,
            query=query,
            candidates=candidates,
            answer=answer,
            stage=stage,
        )

    @staticmethod
    def _deduplicate_passages(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[int] = set()
        deduped: list[dict[str, Any]] = []
        for p in passages:
            content_hash = hash(p.get("content", "")[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                deduped.append(p)
        return deduped

    @staticmethod
    def _load_shared_preamble() -> str:
        try:
            from src.config import PROMPTS_DIR

            preamble_path = PROMPTS_DIR / "_shared_preamble.txt"
            if preamble_path.exists():
                return preamble_path.read_text(encoding="utf-8").strip()
        except ImportError:
            pass

        try:
            with open("prompts/_shared_preamble.txt", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    async def _complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Call the model, and survive a rejection over the output budget.

        Metered providers cap the output tokens per minute. Groq's free tier
        rejects a request whose budget is above the cap with a message about
        output tokens per minute, and the answer then degrades to the raw
        evidence even though a smaller request would have been accepted. When
        the rejection is a budget rejection, the request is retried with a
        smaller budget before the answer is given up on.
        """
        from src.config.settings import settings

        if not self.llm_client:
            raise RuntimeError("no language model client is configured")

        budgets = [max_tokens]
        if max_tokens > 1000:
            budgets.append(1000)
        if max_tokens > 512:
            budgets.append(512)

        last_error: Exception | None = None
        for budget in budgets:
            try:
                response = await self.llm_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    max_tokens=settings.resolve_max_tokens(budget),
                )
                return strip_cot_leakage(response.choices[0].message.content)
            except Exception as exc:
                last_error = exc
                if not _is_output_budget_error(exc):
                    raise
                logger.warning(
                    "generation.budget_rejected: agent=%s max_tokens=%s error=%s",
                    self.name,
                    budget,
                    str(exc)[:200],
                )

        raise last_error if last_error else RuntimeError("the model call failed")

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        meta = input_data.metadata or {}
        if "language" not in meta:
            meta["language"] = input_data.language
        return await self.run(input_data.query, meta=meta)

    # ==========================================
    # Main Pipeline
    # ==========================================

    async def run(
        self,
        raw_question: str,
        meta: dict[str, Any] | None = None,
    ) -> AgentOutput:
        """Execute the full RAG pipeline end-to-end."""
        from src.generation.policies.answer_policy import AnswerMode, AnswerPolicy

        meta = meta or {}
        language = meta.get("language", "ar")
        timing: dict[str, Any] = {}

        # Step 1: Query intake
        t0 = time.perf_counter()
        normalized = self.query_intake(raw_question)
        timing["intake_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 2: Classify intent
        t0 = time.perf_counter()
        intent = self.classify_intent(normalized)
        timing["classification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 3: Retrieve candidates (bounded by timeout)
        retrieval_issues: list[dict[str, Any]] = []
        t0 = time.perf_counter()
        try:
            candidates = await asyncio.wait_for(
                self.retrieve_candidates(normalized),
                timeout=_RETRIEVAL_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(
                "retrieve_candidates timed out after %.1fs — query='%s…'",
                _RETRIEVAL_TIMEOUT_SECONDS,
                normalized[:60],
            )
            candidates = []
            timing["retrieval_timeout"] = True
            retrieval_issues.append(
                {
                    "type": "retrieval_timeout",
                    "message": (
                        f"Retrieval exceeded {_RETRIEVAL_TIMEOUT_SECONDS:.0f}s timeout and returned 0 results."
                    ),
                    "details": {"elapsed_ms": elapsed_ms},
                }
            )
        timing["retrieval_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 4: Rerank + deduplicate
        t0 = time.perf_counter()
        ranked = await self.rerank_candidates(normalized, candidates)
        ranked = self._deduplicate_passages(ranked)
        timing["rerank_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 5: Verify evidence before generation
        t0 = time.perf_counter()
        verification = await self.run_verification(normalized, ranked, stage="evidence")
        timing["verification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Attach retrieval issues to verification
        verification.issues.extend(retrieval_issues)

        # Track filtered evidence. Dropping candidates is normal: reranking keeps
        # top_k and verification rejects weak passages. Report it only when every
        # candidate was removed, which means the query found no usable evidence.
        removed_count = len(candidates) - len(verification.verified_passages)
        if removed_count > 0:
            verification.confidence = min(verification.confidence, 0.90)
        if candidates and not verification.verified_passages:
            verification.issues.append(
                {
                    "type": "evidence_filtered_out",
                    "removed_count": removed_count,
                    "message": (f"تم استبعاد {removed_count} من المقاطع أثناء التصفية والتحقق من الأدلة."),
                }
            )

        # Step 6: Policy gate
        policy = AnswerPolicy()
        has_evidence = len(verification.verified_passages) > 0
        answer_mode = policy.determine_mode(
            confidence=verification.confidence,
            verification_passed=verification.is_verified,
            has_evidence=has_evidence,
        )

        if answer_mode == AnswerMode.ABSTAIN:
            abstain_msg = getattr(
                self,
                "NO_PASSAGES_MESSAGE",
                "عذراً، لم أجد في النصوص المتاحة ما يجيب على سؤالك.",
            )
            abstain_issues = list(verification.issues)
            if not has_evidence:
                abstain_issues.append(
                    {
                        "type": "no_evidence_found",
                        "message": "Retrieval returned 0 passages.",
                    }
                )
            return AgentOutput(
                answer=abstain_msg,
                citations=[],
                metadata={
                    "intent": intent.value if isinstance(intent, Intent) else intent,
                    "sub_intent": intent.value if isinstance(intent, Intent) else intent,
                    "collection": self.config.collection_name,
                    "answer_mode": "abstain",
                    "retrieved": len(candidates),
                    "verified": 0,
                    "is_verified": False,
                    "verification_confidence": (0.0 if not has_evidence else verification.confidence),
                    "verification_issues": abstain_issues,
                    "timing": timing,
                },
                confidence=0.0 if not has_evidence else verification.confidence,
                requires_human_review=True,
            )

        if answer_mode == AnswerMode.CLARIFY:
            return AgentOutput(
                answer=("سؤالك يحتمل أكثر من معنى. هل يمكنك توضيح سؤالك بشكل أدق حتى أتمكن من تقديم إجابة دقيقة؟"),
                citations=[],
                metadata={
                    "intent": intent.value if isinstance(intent, Intent) else intent,
                    "collection": self.config.collection_name,
                    "answer_mode": "clarify",
                    "retrieved": len(candidates),
                    "verified": len(verification.verified_passages),
                    "is_verified": verification.is_verified,
                    "verification_confidence": verification.confidence,
                    "verification_issues": verification.issues,
                    "timing": timing,
                },
                confidence=verification.confidence,
                requires_human_review=False,
            )

        # Step 7: Generate answer + strip CoT leakage
        t0 = time.perf_counter()
        self._generation_failed = False
        answer = await self.generate_answer(normalized, verification.verified_passages, language)
        answer = strip_cot_leakage(answer)
        timing["generation_ms"] = int((time.perf_counter() - t0) * 1000)

        # Every agent falls back to the raw evidence text when the LLM client is
        # missing or the call raises. That response has no composed prose, so it
        # is reported as evidence rather than as an answer.
        evidence_text = self._format_passages(verification.verified_passages).strip()
        if evidence_text and answer.strip() == evidence_text:
            self._generation_failed = True

        if self._generation_failed:
            verification.issues.append(
                {
                    "type": "generation_fallback",
                    "detail": "LLM generation failed; the answer is the evidence text.",
                }
            )

        # ==========================================
        # Post-generation Checks (Canonical Paths)
        # ==========================================
        from src.verification.checks.exact_quote import exact_quote_verifier
        from src.verification.checks.groundedness_judge import groundedness_judge
        from src.verification.checks.misattribution import detect_misattributed_quran
        from src.verification.checks.missing_evidence import detect_missing_requested_evidence
        from src.verification.checks.source_attribution import source_attribution_verifier

        # a. Strict Grounding Check
        quote_eval = await exact_quote_verifier.verify(answer, verification.verified_passages)
        if not quote_eval.passed:
            verification.issues.append(
                {
                    "type": "strict_grounding_violation",
                    "message": (
                        "Answer contains exact string quotes (verses, hadiths, "
                        "or excerpts) not strictly grounded in passages."
                    ),
                    "details": quote_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.80)
            verification.is_verified = False

        # b. Source Attribution Check
        source_eval = await source_attribution_verifier.verify(answer, verification.verified_passages)
        if not source_eval.passed:
            verification.issues.append(
                {
                    "type": "source_attribution_violation",
                    "message": ("Answer claims sources that are not present in the verified passages."),
                    "details": source_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.85)
            verification.is_verified = False

        # c. Speculative / Groundedness Check
        groundedness_eval = await groundedness_judge.verify(answer, verification.verified_passages)
        if not groundedness_eval.passed:
            verification.issues.append(
                {
                    "type": "speculative_answer",
                    "message": ("Answer adds speculative or ungrounded factual claims beyond the provided evidence."),
                    "details": groundedness_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.70)
            verification.is_verified = False

        # ==========================================
        # Auto-Healing for Quran
        # ==========================================
        invalid_sources = source_eval.details.get("invalid_sources", []) if not source_eval.passed else []
        failed_quotes = quote_eval.details.get("failed_quotes", []) if not quote_eval.passed else []

        if invalid_sources or failed_quotes:
            from src.infrastructure.database import get_sync_session
            from src.quran.quotation_validator import QuotationValidator
            from src.quran.verse_retrieval import VerseRetrievalEngine

            def fetch_quran_healing() -> Any:
                new_passages: list[dict[str, Any]] = []
                rem_sources = list(invalid_sources)
                rem_quotes = list(failed_quotes)

                with get_sync_session() as session:
                    engine = VerseRetrievalEngine(session)
                    validator = QuotationValidator(session)
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        for src in invalid_sources:
                            normalized_src = _normalize_source_ref(str(src))
                            try:
                                v_info = new_loop.run_until_complete(engine.lookup(normalized_src))
                                verses = v_info if isinstance(v_info, list) else [v_info]
                                for v in verses:
                                    new_passages.append(
                                        {
                                            "id": f"quran_{v['surah_number']}_{v['ayah_number']}",
                                            "content": v["text_uthmani"],
                                            "metadata": {
                                                "book": "القرآن الكريم",
                                                "source": f"سورة {v.get('surah_name_ar', '')}",
                                            },
                                        }
                                    )
                                if verses and src in rem_sources:
                                    rem_sources.remove(src)
                            except Exception:
                                pass

                        for q_text in failed_quotes:
                            try:
                                val_res = new_loop.run_until_complete(validator.validate(str(q_text)))
                                if val_res.get("is_quran") and val_res.get("matched_ayah"):
                                    ayah = val_res["matched_ayah"]
                                    new_passages.append(
                                        {
                                            "id": f"quran_{ayah['surah_number']}_{ayah['ayah_number']}",
                                            "content": ayah["text_uthmani"],
                                            "metadata": {"book": "القرآن الكريم"},
                                        }
                                    )
                                    if q_text in rem_quotes:
                                        rem_quotes.remove(q_text)
                            except Exception:
                                pass
                    finally:
                        new_loop.close()
                return new_passages, rem_sources, rem_quotes

            try:
                new_ps, rs, rq = await asyncio.to_thread(fetch_quran_healing)
                if new_ps:
                    existing = {p.get("content", "") for p in verification.verified_passages}
                    for np in new_ps:
                        if np["content"] not in existing:
                            verification.verified_passages.append(np)
                            existing.add(np["content"])
            except Exception:
                logger.warning("quran_healing_error", exc_info=True)

        # Final Citation Assembly
        citations = self.assemble_citations(verification.verified_passages)

        # d. Misattributed Quran Check
        misattributed = await detect_misattributed_quran(
            answer=answer,
            citations=[c.model_dump() for c in citations],
            exact_quote_verifier=exact_quote_verifier,
        )
        if misattributed:
            verification.issues.append({"type": "misattributed_quran_text", "segments": misattributed})
            verification.confidence = min(verification.confidence, 0.80)

        # e. Missing Requested Evidence
        missing_ev = detect_missing_requested_evidence(query=raw_question, answer=answer)
        if missing_ev:
            verification.issues.append({"type": "missing_requested_evidence", "violations": missing_ev})
            verification.confidence = min(verification.confidence, 0.85)

        # f. Post-generation verification suite (answer-stage checks)
        if verification.verified_passages:
            try:
                answer_report = await self.run_verification(
                    normalized,
                    verification.verified_passages,
                    answer=answer,
                    stage="answer",
                )
            except Exception:
                logger.exception("post_generation_verification_failed")
                answer_report = None

            if answer_report is not None:
                verification.check_results.update(answer_report.check_results)
                verification.issues.extend(answer_report.issues)
                if not answer_report.is_verified:
                    verification.is_verified = False
                    verification.confidence = min(verification.confidence, answer_report.confidence)

        # Build output metadata
        output_meta: dict[str, Any] = {
            "intent": intent.value if isinstance(intent, Intent) else intent,
            "collection": self.config.collection_name,
            "answer_mode": "evidence" if self._generation_failed else "answer",
            "is_verified": verification.is_verified,
            "verification_confidence": verification.confidence,
            "verification_issues": verification.issues,
            "timing": timing,
        }

        # Build citation_chunks
        citation_chunks: list[dict[str, Any]] = []
        for p in verification.verified_passages:
            md = p.get("metadata", {}) or {}
            citation_chunks.append(
                {
                    "chunk_id": str(p.get("id", "")),
                    "source_id": str(md.get("book_id", "")),
                    "text": p.get("content") or p.get("text", ""),
                    "metadata": md,
                }
            )

        return AgentOutput(
            answer=answer,
            citations=citations,
            citation_chunks=citation_chunks,
            metadata=output_meta,
            confidence=verification.confidence,
            requires_human_review=not verification.is_verified
            or verification.confidence < 0.7
            or self._generation_failed,
        )

    def __repr__(self) -> str:
        return f"<CollectionAgent: {self.name}, collection={self.config.collection_name}>"
