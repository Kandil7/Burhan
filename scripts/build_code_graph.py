#!/usr/bin/env python3
"""
Build a code knowledge graph from Python source files using AST analysis.
Extracts: classes, functions, imports, and relationships.
"""

import argparse
import ast
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "venv",
    ".venv",
    "node_modules",
    "build",
    "dist",
    ".git",
    ".code-graph",
    "data",
    "notebooks",
}


def should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    parts = path.parts
    return any(skip in parts for skip in SKIP_DIRS)


def get_python_files(root: Path) -> list[Path]:
    """Get all Python files in the root directory."""
    python_files = []
    for root_dir, dirs, files in os.walk(root):
        # Filter out skipped directories in-place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            if file.endswith(".py"):
                path = Path(root_dir) / file
                if not should_skip(path):
                    python_files.append(path)
    return python_files


def parse_file(path: Path) -> dict[str, Any]:
    """Parse a Python file and extract AST information."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(path))

        classes = []
        functions = []
        imports = []
        relationships = []

        for node in ast.walk(tree):
            # Extract classes
            if isinstance(node, ast.ClassDef):
                classes.append(
                    {
                        "name": node.name,
                        "lineno": node.lineno,
                        "bases": [
                            b.id if isinstance(b, ast.Name) else str(b) for b in node.bases if isinstance(b, ast.Name)
                        ],
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    }
                )

                # Class -> methods relationships
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        relationships.append(
                            {
                                "from": f"{path}:{node.name}",
                                "to": f"{path}:{node.name}.{method.name}",
                                "type": "defines_method",
                            }
                        )

            # Extract functions
            elif isinstance(node, ast.FunctionDef):
                functions.append(
                    {
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                    }
                )

            # Extract imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "module": alias.name,
                            "alias": alias.asname,
                            "lineno": node.lineno,
                        }
                    )
                    relationships.append(
                        {
                            "from": str(path),
                            "to": alias.name,
                            "type": "imports",
                        }
                    )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "module": f"{module}.{alias.name}" if module else alias.name,
                            "alias": alias.asname,
                            "lineno": node.lineno,
                        }
                    )
                    relationships.append(
                        {
                            "from": str(path),
                            "to": f"{module}.{alias.name}" if module else alias.name,
                            "type": "imports_from",
                        }
                    )

        return {
            "file": str(path),
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "relationships": relationships,
            "error": None,
        }

    except Exception as e:
        return {
            "file": str(path),
            "classes": [],
            "functions": [],
            "imports": [],
            "relationships": [],
            "error": str(e),
        }


def build_graph(root: Path, output: Path) -> dict[str, Any]:
    """Build the code knowledge graph."""
    print(f"Scanning {root} for Python files...")

    python_files = get_python_files(root)
    print(f"Found {len(python_files)} Python files")

    # Parse all files
    nodes = []
    edges = []
    errors = []
    languages = {"Python": 0}

    for path in python_files:
        result = parse_file(path)

        if result["error"]:
            errors.append({"file": result["file"], "error": result["error"]})
            continue

        languages["Python"] += 1

        # Create nodes
        file_node = {
            "id": result["file"],
            "type": "file",
            "name": os.path.basename(result["file"]),
        }
        nodes.append(file_node)

        # Class nodes
        for cls in result["classes"]:
            class_id = f"{result['file']}:{cls['name']}"
            nodes.append(
                {
                    "id": class_id,
                    "type": "class",
                    "name": cls["name"],
                    "lineno": cls["lineno"],
                    "file": result["file"],
                }
            )
            edges.append(
                {
                    "from": result["file"],
                    "to": class_id,
                    "type": "contains",
                }
            )

        # Function nodes
        for func in result["functions"]:
            func_id = f"{result['file']}:{func['name']}"
            nodes.append(
                {
                    "id": func_id,
                    "type": "function",
                    "name": func["name"],
                    "lineno": func["lineno"],
                    "file": result["file"],
                }
            )
            edges.append(
                {
                    "from": result["file"],
                    "to": func_id,
                    "type": "contains",
                }
            )

        # Import nodes
        for imp in result["imports"]:
            imp_id = f"import:{imp['module']}"
            nodes.append(
                {
                    "id": imp_id,
                    "type": "import",
                    "name": imp["module"],
                }
            )
            edges.append(
                {
                    "from": result["file"],
                    "to": imp_id,
                    "type": "imports",
                }
            )

        # Add relationships
        for rel in result["relationships"]:
            edges.append(
                {
                    "from": rel["from"],
                    "to": rel["to"],
                    "type": rel["type"],
                }
            )

    graph = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "files_parsed": len(python_files) - len(errors),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "languages": languages,
            "errors": len(errors),
        },
        "errors": errors,
    }

    # Ensure output directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Write graph to file
    with open(output, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


def main():
    parser = argparse.ArgumentParser(description="Build code knowledge graph from Python AST")
    parser.add_argument("--root", type=Path, default=Path("."), help="Root directory to scan")
    parser.add_argument("--output", type=Path, default=Path(".code-graph/graph.json"), help="Output file path")

    args = parser.parse_args()

    print("=" * 50)
    print("Building Code Knowledge Graph")
    print("=" * 50)

    graph = build_graph(args.root, args.output)

    print("\n" + "=" * 50)
    print("Graph Built Successfully!")
    print("=" * 50)
    print(f"Files parsed: {graph['metadata']['files_parsed']}")
    print(f"Total nodes: {graph['metadata']['total_nodes']}")
    print(f"Total edges: {graph['metadata']['total_edges']}")
    print(f"Languages: {graph['metadata']['languages']}")
    print(f"Errors: {graph['metadata']['errors']}")
    print(f"\nOutput: {args.output}")

    if graph["errors"]:
        print("\nWarning: Some files had parsing errors:")
        for err in graph["errors"][:5]:
            print(f"  - {err['file']}: {err['error']}")


if __name__ == "__main__":
    main()
