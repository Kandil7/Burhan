#!/usr/bin/env python3
"""Report which modules of the source tree the running system can reach.

The Burhan tree grew two architectures at once: the one the API runs, and a
designed one that no request reaches. This script measures the split with an
AST import graph, so the dead surface is a number instead of a suspicion.

Usage:
    python scripts/quality/reachability_report.py
    python scripts/quality/reachability_report.py --json out.json
    python scripts/quality/reachability_report.py --check
    python scripts/quality/reachability_report.py --check --manifest scripts/quality/legacy_manifest.json

``--check`` exits with status 1 when a live module imports a module that the
manifest marks as legacy, or when the unreachable set grew beyond the
manifest. It is the gate that keeps the dead surface from growing back.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"

ENTRY_POINTS = (
    "src.api.main",
    "src.core.registry",
    "src.config.settings",
    "src.evaluation.cli",
)

# Modules that carry a __main__ block and are run with "python -m". They are
# live tooling even though no module imports them.
MODULE_ENTRY_POINTS = (
    "src.indexing.pipelines.build_collection_indexes",
    "src.indexing.pipelines.build_catalog_indexes",
    "src.indexing.pipelines.build_seerah_chunks_camel",
)

# Scripts reach modules that no request does, such as the Quran loader and
# the indexing pipelines. They are live tooling, not dead code, so every src
# module a script imports counts as an entry point.
SCRIPT_DIRS = ("scripts",)  # alembic was removed; see migrations/README.md


def script_entry_points(modules: dict[str, Path]) -> set[str]:
    """Return the src modules imported by the maintenance scripts."""
    entries: set[str] = set()
    for directory in SCRIPT_DIRS:
        base = PROJECT_ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            entries |= collect_imports(parse_tree(path), modules)
    return entries


def module_name(path: Path) -> str:
    """Return the dotted module path of a file."""
    rel = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def parse_tree(path: Path) -> ast.Module:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return ast.Module(body=[], type_ignores=[])


def collect_imports(tree: ast.Module, modules: dict[str, Path]) -> set[str]:
    """Return the internal modules one module imports."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in modules:
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                continue
            if node.module not in modules:
                continue
            found.add(node.module)
            for alias in node.names:
                child = f"{node.module}.{alias.name}"
                if child in modules:
                    found.add(child)
    return found


def duplicate_definitions(reachable: set[str], modules: dict[str, Path]) -> dict[str, list[str]]:
    """Return the public names defined in more than one live module.

    A name that lives in two places is two sources of truth. The count is the
    baseline the architecture test refuses to let grow.
    """
    names: dict[str, list[str]] = defaultdict(list)
    for name in sorted(reachable):
        if not modules[name].exists():
            continue
        tree = parse_tree(modules[name])
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    names[node.name].append(name)
    return {key: sorted(value) for key, value in sorted(names.items()) if len(value) > 1}


def analyze() -> dict[str, Any]:
    """Measure the live surface and the unreachable surface."""
    files = [p for p in sorted(SRC.rglob("*.py")) if "__pycache__" not in p.parts]
    modules: dict[str, Path] = {}
    code_lines: dict[str, int] = {}

    for path in files:
        name = module_name(path)
        modules[name] = path
        text = path.read_text(encoding="utf-8", errors="replace")
        code_lines[name] = sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))

    edges: dict[str, set[str]] = defaultdict(set)
    for name, path in modules.items():
        edges[name] = collect_imports(parse_tree(path), modules)

    reachable: set[str] = set()
    stack = [entry for entry in ENTRY_POINTS if entry in modules]
    stack.extend(entry for entry in MODULE_ENTRY_POINTS if entry in modules)
    stack.extend(sorted(script_entry_points(modules) & set(modules)))
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        stack.extend(edges.get(node, set()) - reachable)

    unreachable = {
        name: code_lines[name] for name in modules if name not in reachable and not name.endswith("__init__")
    }

    by_package: dict[str, dict[str, int]] = defaultdict(lambda: {"modules": 0, "code": 0})
    for name, lines in unreachable.items():
        parts = name.split(".")
        key = ".".join(parts[:3]) if len(parts) >= 3 else ".".join(parts[:2])
        by_package[key]["modules"] += 1
        by_package[key]["code"] += lines

    # Live modules that reach into the unreachable set. These are the edges
    # that keep dead code alive.
    legacy = set(unreachable)
    leaks: list[str] = []
    for name in sorted(reachable):
        for target in sorted(edges.get(name, set()) & legacy):
            leaks.append(f"{name} -> {target}")

    return {
        "total_modules": len(modules),
        "total_code_lines": sum(code_lines.values()),
        "reachable_modules": len(reachable),
        "unreachable_module_count": len(unreachable),
        "unreachable_code_lines": sum(unreachable.values()),
        "unreachable_by_package": dict(sorted(by_package.items(), key=lambda kv: -kv[1]["code"])),
        "unreachable_modules": dict(sorted(unreachable.items(), key=lambda kv: -kv[1])),
        "live_to_legacy_imports": leaks,
        "duplicate_definitions": duplicate_definitions(reachable, modules),
    }


def check(report: dict[str, Any], manifest_path: Path) -> list[str]:
    """Return the list of violations against the manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    known = set(manifest.get("unreachable_modules", []))
    current = set(report["unreachable_modules"])

    problems: list[str] = []
    for leak in report["live_to_legacy_imports"]:
        problems.append(f"live module imports a legacy module: {leak}")

    grown = sorted(current - known)
    for name in grown:
        problems.append(f"unreachable module is not in the manifest: {name}")

    baseline_lines = manifest.get("unreachable_code_lines")
    if baseline_lines is not None and report["unreachable_code_lines"] > baseline_lines:
        problems.append(f"unreachable code lines grew: {report['unreachable_code_lines']} > {baseline_lines}")

    return problems


def write_manifest(report: dict[str, Any], manifest_path: Path) -> None:
    """Record the current unreachable set and duplicate baseline."""
    manifest = {
        "generated_at": "2026-10-21",
        "note": (
            "Modules no entry point reaches. They are quarantined, not deleted. "
            "The architecture test fails when a live module imports one of them, "
            "when this list grows, or when a duplicated name gains a definition."
        ),
        "total_modules": report["total_modules"],
        "reachable_modules": report["reachable_modules"],
        "unreachable_code_lines": report["unreachable_code_lines"],
        "unreachable_modules": sorted(report["unreachable_modules"]),
        "duplicate_definitions": report["duplicate_definitions"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"manifest written to {manifest_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report the reachable surface of the source tree")
    parser.add_argument("--json", dest="json_path", help="Write the full report to this file")
    parser.add_argument("--check", action="store_true", help="Fail when the manifest is violated")
    parser.add_argument(
        "--manifest",
        default=str(PROJECT_ROOT / "scripts" / "quality" / "legacy_manifest.json"),
        help="Manifest of known unreachable modules",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Record the current unreachable set and duplicate baseline",
    )
    args = parser.parse_args()

    report = analyze()

    print("Live surface")
    print(f"  modules            {report['reachable_modules']} of {report['total_modules']}")
    print(f"  code lines         {report['total_code_lines'] - report['unreachable_code_lines']} live")
    print(f"  unreachable        {report['unreachable_module_count']} modules")
    print(f"  unreachable lines  {report['unreachable_code_lines']}")
    print("  live imports into the unreachable set: " + str(len(report["live_to_legacy_imports"])))
    print()
    print("Unreachable by package")
    for package, data in list(report["unreachable_by_package"].items())[:12]:
        print(f"  {package:<38} {data['modules']:>3} modules {data['code']:>6} lines")

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nreport written to {args.json_path}")

    if args.write_manifest:
        write_manifest(report, Path(args.manifest))
        print()

    if args.check:
        problems = check(report, Path(args.manifest))
        if problems:
            print("\nmanifest violations")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("\nmanifest satisfied")

    return 0


if __name__ == "__main__":
    sys.exit(main())
