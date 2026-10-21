#!/usr/bin/env python3
"""
Import script for azkar-db from https://github.com/osamayy/azkar-db

Downloads the azkar database and converts it to Burhan's dua format, which is
what :class:`src.tools.dua_retrieval_tool.DuaRetrievalTool` reads.

The upstream repository publishes two files:

* ``azkar.json`` - an SQLite dump (``columns`` + ``rows``)
* ``azkar_obj.json`` - the same data as a list of objects (preferred)

Both shapes are accepted here so the importer keeps working if upstream
switches which file it publishes.

Arabic categories are mapped onto the English occasion/category ids the tool
filters on, because a stored occasion of "أذكار الصباح" would never match
``occasion="morning"``.

Usage:
    python scripts/ingestion/import_azkar_db.py
    python scripts/ingestion/import_azkar_db.py --output data/seed/azkar_imported.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger()

AZKAR_DB_URLS: tuple[str, ...] = (
    "https://raw.githubusercontent.com/osamayy/azkar-db/master/azkar_obj.json",
    "https://raw.githubusercontent.com/osamayy/azkar-db/master/azkar.json",
)
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "seed" / "azkar_imported.json"
REQUEST_TIMEOUT_SECONDS = 120

# (substring in the Arabic category, category, occasion)
CATEGORY_RULES: tuple[tuple[str, str, str], ...] = (
    ("صباح", "morning_evening", "morning"),
    ("مساء", "morning_evening", "evening"),
    ("النوم", "prayer", "before_sleep"),
    ("الاستيقاظ", "prayer", "upon_waking"),
    ("سفر", "travel", "traveling"),
    ("طعام", "food", "before_eating"),
    ("الأكل", "food", "before_eating"),
    ("الرقية", "protection", "protection"),
    ("استغفار", "protection", "general"),
    ("التوبة", "protection", "general"),
)
DEFAULT_CATEGORY = ("general", "general")


def fetch_azkar() -> list[dict[str, Any]]:
    """Download azkar entries, trying each published URL in order."""
    last_error: Exception | None = None

    for url in AZKAR_DB_URLS:
        try:
            response = httpx.get(url, follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            entries = _normalise_payload(payload)
            if entries:
                logger.info("azkar.downloaded", url=url, entries=len(entries))
                return entries
            logger.warning("azkar.empty_payload", url=url)
        except Exception as exc:  # network, JSON, or shape problems
            last_error = exc
            logger.warning("azkar.fetch_failed", url=url, error=str(exc))

    raise SystemExit(f"Could not download azkar data: {last_error}")


def _normalise_payload(payload: Any) -> list[dict[str, Any]]:
    """Return a list of entry dicts from either upstream file shape."""
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]

    if isinstance(payload, dict) and isinstance(payload.get("columns"), list):
        columns = payload["columns"]
        rows = payload.get("rows") or []
        normalised: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, dict):
                normalised.append(row)
            elif isinstance(row, list):
                normalised.append(dict(zip(columns, row, strict=False)))
        return normalised

    return []


def _map_category(arabic_category: str) -> tuple[str, str]:
    """Map an Arabic azkar-db category onto the tool's (category, occasion) ids."""
    for needle, category, occasion in CATEGORY_RULES:
        if needle in arabic_category:
            return category, occasion
    return DEFAULT_CATEGORY


def convert(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert azkar-db entries into Burhan's dua format."""
    converted: list[dict[str, Any]] = []

    for index, entry in enumerate(entries, start=1):
        arabic_text = (entry.get("zekr") or "").strip()
        if not arabic_text:
            continue

        arabic_category = (entry.get("category") or "").strip()
        category, occasion = _map_category(arabic_category)

        try:
            repeat_count = int(entry.get("count") or 1)
        except (TypeError, ValueError):
            repeat_count = 1

        converted.append(
            {
                "id": index,
                "category": category,
                "category_ar": arabic_category,
                "occasion": occasion,
                "arabic_text": arabic_text,
                "translation": "",
                "transliteration": "",
                "source": entry.get("reference") or "Azkar Database",
                "reference": (entry.get("reference") or "").strip(),
                "narrator": "",
                "grade": "",
                "repeat_count": repeat_count,
                "virtues": (entry.get("description") or "").strip(),
                "search_keywords": (entry.get("search") or "").strip(),
            }
        )

    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description="Import azkar-db into data/seed/azkar_imported.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Destination JSON file (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    entries = fetch_azkar()
    converted = convert(entries)

    if not converted:
        raise SystemExit("No usable azkar entries after conversion; nothing written.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(converted, handle, ensure_ascii=False, indent=2)

    occasions: dict[str, int] = {}
    for entry in converted:
        occasions[entry["occasion"]] = occasions.get(entry["occasion"], 0) + 1

    logger.info(
        "azkar.import_complete",
        output=str(args.output),
        downloaded=len(entries),
        written=len(converted),
        occasions=occasions,
    )


if __name__ == "__main__":
    main()
