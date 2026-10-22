"""Config equivalence: the YAML specs must equal the legacy behavior exactly.

Hardening Phase 5 moved the ten collection agent classes into one
spec-driven RAGPipeline. Before the classes were deleted, every hardcoded
value and every rendered output they produced for fixed inputs was captured
into tests/agent_spec_expected.json. This test asserts the YAML specs still
reproduce that capture, field for field and byte for byte.

If it fails, the YAML files or the spec loader drifted from the behavior the
system was verified against. Update the YAML deliberately, together with the
capture, never one without the other.
"""

import json
from pathlib import Path

import pytest

from src.agents.spec_loader import load_all_agent_specs
from src.verification.suite_builder import build_verification_suite_for

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "agent_spec_expected.json"

QUERY_SENTINEL = "«QUERY»"
PASSAGES_SENTINEL = "«PASSAGES»"
LANG_SENTINEL = "«LANG»"
PROBE_PASSAGES = [
    {"content": "النص الأول"},
    {"content": "B" * 700},
    {"content": "C" * 50},
]


@pytest.fixture(scope="module")
def capture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def specs() -> dict:
    return load_all_agent_specs()


class TestSpecValues:
    """Every value in the YAML matches the frozen capture."""

    def test_every_agent_is_present(self, specs, capture):
        assert sorted(specs) == sorted(capture)

    @pytest.mark.parametrize(
        "field",
        [
            "name",
            "collection",
            "intent",
            "temperature",
            "max_tokens",
            "system_prompt_file",
            "system_prompt_fallback",
            "system_prompt_fallback_includes_preamble",
            "user_prompt_template",
            "no_passages_message",
            "top_k",
            "score_threshold",
            "rerank",
            "dense_weight",
            "sparse_weight",
            "passage_header",
            "passage_truncate",
            "fallback_strategy",
        ],
    )
    def test_field_matches_capture(self, specs, capture, field):
        for agent, spec in specs.items():
            assert getattr(spec, field) == capture[agent][field], f"{agent}.{field}"


class TestSpecRenders:
    """The spec reproduces the legacy outputs byte for byte."""

    def test_user_prompt_render_matches(self, specs, capture):
        for agent, spec in specs.items():
            rendered = spec.render_user_prompt(QUERY_SENTINEL, PASSAGES_SENTINEL, LANG_SENTINEL)
            assert rendered == capture[agent]["probes"]["user_prompt"], f"{agent} user prompt"

    def test_passage_render_matches(self, specs, capture):
        for agent, spec in specs.items():
            rendered = spec.render_passages(PROBE_PASSAGES)
            assert rendered == capture[agent]["probes"]["passages"], f"{agent} passages"


class TestVerificationSuites:
    """The YAML suites equal the suites the verification layer builds."""

    def test_suite_matches_capture(self, specs, capture):
        for agent, spec in specs.items():
            expected = capture[agent]
            assert spec.verification_fail_fast == expected["verification_fail_fast"], agent
            checks = [
                {"name": c.name, "fail_policy": c.fail_policy, "enabled": c.enabled, "stage": c.stage}
                for c in spec.verification_checks
            ]
            assert checks == expected["verification_checks"], agent

    def test_suite_matches_verification_layer(self, specs):
        for agent, spec in specs.items():
            suite = build_verification_suite_for(spec.name)
            assert suite.fail_fast == spec.verification_fail_fast, agent
            live = [
                {"name": c.name, "fail_policy": c.fail_policy, "enabled": c.enabled, "stage": c.stage}
                for c in suite.checks
            ]
            wanted = [
                {"name": c.name, "fail_policy": c.fail_policy, "enabled": c.enabled, "stage": c.stage}
                for c in spec.verification_checks
            ]
            assert live == wanted, f"{agent}: suite_builder and YAML disagree"
