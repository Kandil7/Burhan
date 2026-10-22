"""
Load AgentSpec values from config/agents/*.yaml.

The YAML files are the behavior record for the collection agents: every value
there matches what the agent does at runtime, and
tests/test_agent_spec_equivalence.py guards that agreement.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.domain.agent_spec import AgentSpec, VerificationCheckSpec

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config" / "agents"

AGENT_FILE_ORDER = (
    "aqeedah",
    "fiqh",
    "general",
    "hadith",
    "history",
    "language",
    "seerah",
    "tafsir",
    "tazkiyah",
    "usul_fiqh",
)


def load_agent_spec(path: Path) -> AgentSpec:
    """Load one agent spec from its YAML file."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"agent config is not a mapping: {path}")

    generation = doc.get("generation", {}) or {}
    retrieval = doc.get("retrieval", {}) or {}
    passages = doc.get("passages", {}) or {}
    verification = doc.get("verification", {}) or {}
    fallback = doc.get("fallback", {}) or {}

    checks = tuple(
        VerificationCheckSpec(
            name=str(check["name"]),
            fail_policy=str(check["fail_policy"]),
            enabled=bool(check.get("enabled", True)),
            stage=str(check.get("stage", "both")),
        )
        for check in verification.get("checks", []) or []
    )

    return AgentSpec(
        name=str(doc["name"]),
        collection=str(doc["collection"]),
        intent=str(doc["intent"]),
        temperature=float(generation["temperature"]),
        max_tokens=int(generation["max_tokens"]),
        system_prompt_file=str(generation["system_prompt_file"]),
        system_prompt_fallback=str(generation["system_prompt_fallback"]),
        system_prompt_fallback_includes_preamble=bool(generation.get("system_prompt_fallback_includes_preamble", True)),
        user_prompt_template=str(generation["user_prompt_template"]),
        no_passages_message=str(generation["no_passages_message"]),
        top_k=int(retrieval["top_k"]),
        score_threshold=float(retrieval["score_threshold"]),
        rerank=bool(retrieval.get("rerank", True)),
        dense_weight=float(retrieval.get("dense_weight", 0.5)),
        sparse_weight=float(retrieval.get("sparse_weight", 0.5)),
        passage_header=str(passages["header"]),
        passage_truncate=int(passages["truncate"]),
        verification_fail_fast=bool(verification.get("fail_fast", True)),
        verification_checks=checks,
        fallback_strategy=str(fallback.get("strategy", "chatbot")),
    )


def load_all_agent_specs(config_dir: Path | None = None) -> dict[str, AgentSpec]:
    """Load every agent spec, keyed by agent name."""
    directory = config_dir or DEFAULT_CONFIG_DIR
    specs: dict[str, AgentSpec] = {}
    for name in AGENT_FILE_ORDER:
        path = directory / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"missing agent config: {path}")
        spec = load_agent_spec(path)
        if spec.name != name:
            raise ValueError(f"agent config {path.name} declares name {spec.name!r}")
        specs[spec.name] = spec
    return specs
