"""
Collection-Aware RAG Agent Base for Athar Islamic QA system.

This module provides the canonical base class for all v2 collection agents,
integrating retrieval, verification, and generation into a unified pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Set

from pydantic import BaseModel, Field

from src.agents.base import AgentInput, Citation, strip_cot_leakage
from src.domain.intents import Intent
from src.verification import (
    VerificationReport,
    VerificationStatus,
    VerificationSuite,
    VerificationCheck,
)

logger = logging.getLogger(__name__)

# Arabic sentence-ending characters for truncation detection
_SENTENCE_ENDINGS = {".", "؟", "!", ")", "﴾", "»", "\u06d4"}

# Normalize "المائدة: 82" → "المائدة:82" for VerseRetrievalEngine
_COLON_SPACES_RE = re.compile(r"\s*:\s*")

# Maximum seconds allowed for retrieve_candidates() before TimeoutError
_RETRIEVAL_TIMEOUT_SECONDS = 8.0


def _normalize_source_ref(src: str) -> str:
    """Remove spaces around colon in verse references."""
    return _COLON_SPACES_RE.sub(":", src.strip())


def _is_answer_truncated(answer: str) -> bool:
    """Return True if answer appears cut mid-sentence (max_tokens reached)."""
    stripped = answer.rstrip()
    return not stripped or stripped[-1] not in _SENTENCE_ENDINGS


class AgentOutput(BaseModel):
    """Standardized output for all agents."""

    answer: str = Field(description="Agent answer text")
    citations: List[Citation] = Field(default_factory=list)
    citation_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)


class RetrievalStrategy(BaseModel):
    """Configuration for retrieval pipeline."""

    dense_weight: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Weight for dense (semantic) retrieval",
    )
    sparse_weight: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Weight for sparse (keyword) retrieval",
    )
    top_k: int = Field(
        default=12, ge=1, le=100,
        description="Number of candidates to retrieve",
    )
    rerank: bool = Field(default=True, description="Whether to apply reranking")
    score_threshold: float = Field(
        default=0.65, ge=0.0, le=1.0,
        description="Minimum score threshold for inclusion",
    )


class FallbackPolicy(BaseModel):
    """Fallback strategy when primary retrieval fails or is insufficient."""

    strategy: str = Field(
        default="chatbot",
        description="Strategy: chatbot/human_review/clarify",
    )
    message: Optional[str] = Field(default=None, description="Custom fallback message")


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

    def __init__(self, config: Optional[CollectionAgentConfig] = None) -> None:
        self.config = config or CollectionAgentConfig(
            collection_name=self.COLLECTION,
        )

    @abstractmethod
    def query_intake(self, query: str) -> str: ...

    @abstractmethod
    def classify_intent(self, query: str) -> Intent: ...

    @abstractmethod
    async def retrieve_candidates(self, query: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    async def rerank_candidates(
        self, query: str, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    async def run_verification(
        self, query: str, candidates: List[Dict[str, Any]]
    ) -> VerificationReport: ...

    @abstractmethod
    async def generate_answer(
        self, query: str, verified_passages: List[Dict[str, Any]], language: str
    ) -> str: ...

    @abstractmethod
    def assemble_citations(self, passages: List[Dict[str, Any]]) -> List[Citation]: ...

    # ==========================================
    # Shared Helpers
    # ==========================================

    @staticmethod
    def _deduplicate_passages(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Set[int] = set()
        deduped: List[Dict[str, Any]] = []
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
        meta: Optional[Dict[str, Any]] = None,
    ) -> AgentOutput:
        """Execute the full RAG pipeline end-to-end."""
        from src.generation.policies.answer_policy import AnswerMode, AnswerPolicy

        meta = meta or {}
        language = meta.get("language", "ar")
        timing: Dict[str, Any] = {}

        # Step 1: Query intake
        t0 = time.perf_counter()
        normalized = self.query_intake(raw_question)
        timing["intake_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 2: Classify intent
        t0 = time.perf_counter()
        intent = self.classify_intent(normalized)
        timing["classification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 3: Retrieve candidates (bounded by timeout)
        retrieval_issues: List[Dict[str, Any]] = []
        t0 = time.perf_counter()
        try:
            candidates = await asyncio.wait_for(
                self.retrieve_candidates(normalized),
                timeout=_RETRIEVAL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
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
                        f"Retrieval exceeded {_RETRIEVAL_TIMEOUT_SECONDS:.0f}s "
                        "timeout and returned 0 results."
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

        # Step 5: Verify candidates
        t0 = time.perf_counter()
        verification = await self.run_verification(normalized, ranked)
        timing["verification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Attach retrieval issues to verification
        verification.issues.extend(retrieval_issues)

        # Track filtered evidence
        removed_count = len(candidates) - len(verification.verified_passages)
        if removed_count > 0:
            verification.confidence = min(verification.confidence, 0.90)
            verification.issues.append(
                {
                    "type": "evidence_filtered_out",
                    "removed_count": removed_count,
                    "message": (
                        f"تم استبعاد {removed_count} من المقاطع "
                        "أثناء التصفية والتحقق من الأدلة."
                    ),
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
                    "verification_confidence": (
                        0.0 if not has_evidence else verification.confidence
                    ),
                    "verification_issues": abstain_issues,
                    "timing": timing,
                },
                confidence=0.0 if not has_evidence else verification.confidence,
                requires_human_review=True,
            )

        if answer_mode == AnswerMode.CLARIFY:
            return AgentOutput(
                answer=(
                    "سؤالك يحتمل أكثر من معنى. هل يمكنك توضيح سؤالك بشكل أدق "
                    "حتى أتمكن من تقديم إجابة دقيقة؟"
                ),
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
        answer = await self.generate_answer(
            normalized, verification.verified_passages, language
        )
        answer = strip_cot_leakage(answer)
        timing["generation_ms"] = int((time.perf_counter() - t0) * 1000)

        # ==========================================
        # Post-generation Checks (Canonical Paths)
        # ==========================================
        from src.verification.checks.exact_quote import exact_quote_verifier
        from src.verification.checks.groundedness_judge import groundedness_judge
        from src.verification.checks.misattribution import detect_misattributed_quran
        from src.verification.checks.missing_evidence import detect_missing_requested_evidence
        from src.verification.checks.source_attribution import source_attribution_verifier

        # a. Strict Grounding Check
        quote_eval = await exact_quote_verifier.verify(
            answer, verification.verified_passages
        )
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

        # b. Source Attribution Check
        source_eval = await source_attribution_verifier.verify(
            answer, verification.verified_passages
        )
        if not source_eval.passed:
            verification.issues.append(
                {
                    "type": "source_attribution_violation",
                    "message": (
                        "Answer claims sources that are not present in "
                        "the verified passages."
                    ),
                    "details": source_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.85)

        # c. Speculative / Groundedness Check
        groundedness_eval = await groundedness_judge.verify(
            answer, verification.verified_passages
        )
        if not groundedness_eval.passed:
            verification.issues.append(
                {
                    "type": "speculative_answer",
                    "message": (
                        "Answer adds speculative or ungrounded factual claims "
                        "beyond the provided evidence."
                    ),
                    "details": groundedness_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.70)

        # ==========================================
        # Auto-Healing for Quran
        # ==========================================
        invalid_sources = source_eval.details.get("invalid_sources", []) if not source_eval.passed else []
        failed_quotes = quote_eval.details.get("failed_quotes", []) if not quote_eval.passed else []

        if invalid_sources or failed_quotes:
            from src.infrastructure.database import get_sync_session
            from src.quran.quotation_validator import QuotationValidator
            from src.quran.verse_retrieval import VerseRetrievalEngine

            def fetch_quran_healing():
                new_passages: List[Dict[str, Any]] = []
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
                                    new_passages.append({
                                        "id": f"quran_{v['surah_number']}_{v['ayah_number']}",
                                        "content": v["text_uthmani"],
                                        "metadata": {
                                            "book": "القرآن الكريم",
                                            "source": f"سورة {v.get('surah_name_ar', '')}",
                                        }
                                    })
                                if verses and src in rem_sources:
                                    rem_sources.remove(src)
                            except Exception:
                                pass
                        
                        for q_text in failed_quotes:
                            try:
                                val_res = new_loop.run_until_complete(validator.validate(str(q_text)))
                                if val_res.get("is_quran") and val_res.get("matched_ayah"):
                                    ayah = val_res["matched_ayah"]
                                    new_passages.append({
                                        "id": f"quran_{ayah['surah_number']}_{ayah['ayah_number']}",
                                        "content": ayah["text_uthmani"],
                                        "metadata": {"book": "القرآن الكريم"}
                                    })
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

        # Build output metadata
        output_meta: Dict[str, Any] = {
            "intent": intent.value if isinstance(intent, Intent) else intent,
            "collection": self.config.collection_name,
            "answer_mode": "answer",
            "is_verified": verification.is_verified,
            "verification_confidence": verification.confidence,
            "verification_issues": verification.issues,
            "timing": timing,
        }

        # Build citation_chunks
        citation_chunks: List[Dict[str, Any]] = []
        for p in verification.verified_passages:
            md = p.get("metadata", {}) or {}
            citation_chunks.append({
                "chunk_id": str(p.get("id", "")),
                "source_id": str(md.get("book_id", "")),
                "text": p.get("content") or p.get("text", ""),
                "metadata": md,
            })

        return AgentOutput(
            answer=answer,
            citations=citations,
            citation_chunks=citation_chunks,
            metadata=output_meta,
            confidence=verification.confidence,
            requires_human_review=not verification.is_verified or verification.confidence < 0.7,
        )

    def __repr__(self) -> str:
        return f"<CollectionAgent: {self.name}, collection={self.config.collection_name}>"
