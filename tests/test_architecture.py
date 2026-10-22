"""Architecture guards for the live surface.

The source tree holds two architectures: the one the API runs, and one that no
entry point reaches. These tests keep the second one from growing back, and
keep a duplicated name from gaining a third home. The plan behind them is
`docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md`.

The manifest is refreshed on purpose, never by accident:

    python scripts/quality/reachability_report.py --write-manifest
"""

import ast
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "scripts" / "quality" / "reachability_report.py"
MANIFEST_PATH = PROJECT_ROOT / "scripts" / "quality" / "legacy_manifest.json"


def _load_report_module():
    """Load the analysis script by path, without relying on package layout."""
    spec = importlib.util.spec_from_file_location("burhan_reachability_report", REPORT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report() -> dict:
    return _load_report_module().analyze()


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class TestLegacyFence:
    """The quarantined layer must stay quarantined."""

    def test_no_live_module_imports_a_legacy_module(self, report):
        assert report["live_to_legacy_imports"] == []

    def test_unreachable_surface_does_not_grow(self, report, manifest):
        known = set(manifest["unreachable_modules"])
        current = set(report["unreachable_modules"])

        assert current <= known, f"new unreachable modules: {sorted(current - known)}"

    def test_unreachable_code_lines_do_not_grow(self, report, manifest):
        assert report["unreachable_code_lines"] <= manifest["unreachable_code_lines"]

    def test_manifest_covers_every_unreachable_module(self, report, manifest):
        assert set(manifest["unreachable_modules"]) == set(report["unreachable_modules"])


class TestDuplicateDefinitions:
    """A name that lives in two places is two sources of truth."""

    def test_no_duplicated_name_gains_a_definition(self, report, manifest):
        baseline = manifest["duplicate_definitions"]
        current = report["duplicate_definitions"]

        for name, modules in current.items():
            allowed = baseline.get(name, [])
            assert len(modules) <= len(allowed), f"{name} is now defined in {modules}"

    def test_duplicate_count_does_not_grow(self, report, manifest):
        assert len(report["duplicate_definitions"]) <= len(manifest["duplicate_definitions"])


class TestLiveSurface:
    """The live surface must keep answering."""

    def test_the_api_entry_point_is_live(self, report):
        assert report["reachable_modules"] > 0
        assert report["live_to_legacy_imports"] == []

    def test_no_legacy_module_is_imported_by_the_live_tree(self, report):
        legacy = set(report["unreachable_modules"])
        for name, modules in report["duplicate_definitions"].items():
            for module in modules:
                assert module not in legacy, f"{name} lives only in a legacy module"


class TestLayerRules:
    """The hardening plan's layer rules, enforced mechanically."""

    VERIFICATION_BANNED_PREFIXES = ("src.adapters", "src.infrastructure", "src.quran")

    def test_verification_never_imports_adapters_or_infrastructure(self):
        offenders: list[str] = []
        for path in sorted((PROJECT_ROOT / "src" / "verification").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                elif isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                for module in modules:
                    if module.startswith(self.VERIFICATION_BANNED_PREFIXES):
                        rel = path.relative_to(PROJECT_ROOT).as_posix()
                        offenders.append(f"{rel} imports {module}")
        assert offenders == [], f"verification layer imports adapters: {offenders}"


class TestTestFilePlacement:
    """pytest collects only tests/; a `test_*.py` outside it is a lying name."""

    SKIP_DIRECTORIES = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".qdrant",
        ".venv",
        "htmlcov",
        "node_modules",
    }

    def test_no_test_named_file_lives_outside_the_test_tree(self):
        offenders: list[str] = []
        for path in PROJECT_ROOT.rglob("test_*"):
            if not path.is_file():
                continue
            parts = path.relative_to(PROJECT_ROOT).parts
            if self.SKIP_DIRECTORIES & set(parts):
                continue
            if parts[0] == "tests" or parts[0].startswith("."):
                continue
            if path.suffix == ".py":
                offenders.append("/".join(parts))
        assert offenders == [], (
            "files named test_*.py outside tests/: "
            f"{offenders}. Rename them to probe_* or smoke_* so pytest's "
            "collection scope matches their purpose."
        )
