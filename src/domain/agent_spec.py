"""
Agent specification: the data one collection agent is made of.

This is a pure value object. It imports nothing from the project and nothing
that talks to the outside world. The YAML files under config/agents/ are the
record of these values; src/agents/spec_loader.py loads them.

Hardening Phase 5 (docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md):
the ten agent classes collapsed into one RAGPipeline driven by this spec.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationCheckSpec:
    """One check in an agent's verification suite."""

    name: str
    fail_policy: str
    enabled: bool = True
    stage: str = "both"


@dataclass(frozen=True)
class AgentSpec:
    """Everything that makes one collection agent behave the way it does."""

    name: str
    collection: str
    intent: str

    # Generation
    temperature: float
    max_tokens: int
    system_prompt_file: str
    system_prompt_fallback: str
    system_prompt_fallback_includes_preamble: bool
    user_prompt_template: str
    no_passages_message: str

    # Retrieval
    top_k: int
    score_threshold: float
    rerank: bool
    dense_weight: float
    sparse_weight: float

    # Passage rendering
    passage_header: str
    passage_truncate: int

    # Verification
    verification_fail_fast: bool
    verification_checks: tuple[VerificationCheckSpec, ...]

    # Fallback when retrieval or generation fails
    fallback_strategy: str

    def render_user_prompt(self, query: str, passages: str, language: str) -> str:
        """Fill the user prompt template with one query and its passages."""
        return self.user_prompt_template.format(query=query, language=language, passages=passages)

    def render_passages(self, passages: list[dict]) -> str:
        """Render passages for the prompt, capped per passage."""
        if not passages:
            return ""
        parts = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")
            if len(content) > self.passage_truncate:
                content = content[: self.passage_truncate] + "…"
            parts.append(self.passage_header.format(index=i, content=content))
        return "\n\n".join(parts)
