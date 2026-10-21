#!/usr/bin/env python3
"""
md_to_notebook.py
-----------------
Convert a Markdown file (with ```python ... ``` blocks) into a Jupyter
notebook (.ipynb) ready for Google Colab.

Usage:
    python md_to_notebook.py input.md                 # writes input.ipynb
    python md_to_notebook.py input.md output.ipynb    # custom output name
    python md_to_notebook.py *.md                     # batch convert
"""

import json, re, sys
from pathlib import Path


def md_to_notebook(md_text: str) -> dict:
    """Parse markdown and return a notebook dict."""
    cells = []
    pattern = re.compile(r"(```python\n)(.*?)(```)", re.DOTALL)
    last_end = 0

    for m in pattern.finditer(md_text):
        # Markdown cell (text before code block)
        before = md_text[last_end : m.start()].strip()
        if before:
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": before.splitlines(keepends=True),
                }
            )

        # Code cell
        code = m.group(2).rstrip("\n")
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code.splitlines(keepends=True),
            }
        )
        last_end = m.end()

    # Trailing markdown
    tail = md_text[last_end:].strip()
    if tail:
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": tail.splitlines(keepends=True),
            }
        )

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10.0"},
            "colab": {"provenance": [], "gpuType": "T4"},
            "accelerator": "GPU",
        },
        "cells": cells,
    }


def convert(md_path: Path, out_path: Path | None = None) -> Path:
    out_path = out_path or md_path.with_suffix(".ipynb")
    md_text = md_path.read_text(encoding="utf-8")
    nb = md_to_notebook(md_text)
    out_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    n_code = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    n_md = sum(1 for c in nb["cells"] if c["cell_type"] == "markdown")
    print(f"[OK] {md_path.name} -> {out_path.name} [{n_code} code | {n_md} markdown]")
    return out_path


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # Detect if last arg is an explicit .ipynb output (only valid for single input)
    paths = [Path(a) for a in args]
    if len(paths) == 2 and paths[-1].suffix == ".ipynb":
        convert(paths[0], paths[1])
    else:
        for p in paths:
            if not p.exists():
                print(f"[!!] File not found: {p}")
                continue
            convert(p)


if __name__ == "__main__":
    main()
