#!/usr/bin/env python3
"""Count import cycles in the live source tree.

The reachability report says what is dead. This says what is tangled: it
builds the module import graph from the AST (function-level imports included:
a lazy import is still a dependency) and reports the strongly connected
components. A component with more than one module, or a module importing
itself, is a cycle.

Usage:
    python scripts/quality/import_cycles.py            # summary + members
    python scripts/quality/import_cycles.py --json     # machine-readable

The Phase 3 verification of REFACTOR_PLAN_HARDENING.md is "the cycle count
is zero" for the live modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
MANIFEST = PROJECT_ROOT / "scripts" / "quality" / "legacy_manifest.json"


def module_name(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()[:-3].replace("/", ".")


def module_graph() -> dict[str, set[str]]:
    """Return {module: {imported src modules}} for every file under src/."""
    graph: dict[str, set[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        name = module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        edges: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src."):
                edges.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("src."):
                        edges.add(alias.name)
        graph[name] = edges
    # Keep only edges whose target is a real module: package __init__ re-exports
    # may mention names the graph also has as nodes.
    return {name: {e for e in edges if e in graph} for name, edges in graph.items()}


def strongly_connected(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's algorithm, iterative. Returns every nontrivial SCC."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = [0]

    for root in graph:
        if root in index:
            continue
        work: list[tuple[str, iter]] = [(root, iter(sorted(graph[root])))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter[0]
                    counter[0] += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(graph[child]))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in graph[node]:
                    result.append(sorted(component))
    return sorted(result, key=lambda c: (-len(c), c))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    graph = module_graph()
    components = strongly_connected(graph)

    live: set[str] = set()
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        unreachable = set(manifest.get("unreachable_modules", []))
        live = set(graph) - unreachable

    live_components = [c for c in components if all(m in live for m in c)]
    legacy_components = [c for c in components if any(m not in live for m in c)]

    if args.json:
        print(json.dumps({"cycles": components, "live_cycles": live_components}, ensure_ascii=False, indent=2))
        return 0

    print("Import cycles (strongly connected components)")
    print(f"  modules           {len(graph)}")
    print(f"  cycles (all)      {len(components)}")
    print(f"  cycles (live)     {len(live_components)}")
    for component in live_components:
        print(f"  live cycle ({len(component)}):")
        for member in component:
            targets = sorted(graph[member] & set(component))
            print(f"    {member} -> {targets}")
    if legacy_components:
        print(f"  legacy cycles     {len(legacy_components)} (quarantined layer)")
        for component in legacy_components:
            print(f"    {component}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
