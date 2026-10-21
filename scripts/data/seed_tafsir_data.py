#!/usr/bin/env python3
"""
Tafsir Database Seeder Script.

Populates the ``tafsirs`` table with verse-keyed commentary for the three
sources declared in :class:`src.quran.tafsir_retrieval.TafsirRetrievalEngine`:

===============  =========================================  ======================
source_name      upstream                                   edition / id
===============  =========================================  ======================
al-jalalayn      api.alquran.cloud                          ar.jalalayn
al-qurtubi       api.alquran.cloud                          ar.qurtubi
ibn-kathir       api.quran.com/api/v4                       tafsir id 14
===============  =========================================  ======================

Rows are keyed by ``(ayah_id, source_name)`` and upserted, so re-running the
script updates text in place instead of duplicating rows. Ayahs must already
exist in the database; run ``seed_quran_data.py --source api`` first.

Usage:
    python scripts/data/seed_tafsir_data.py
    python scripts/data/seed_tafsir_data.py --source al-jalalayn
    python scripts/data/seed_tafsir_data.py --surah-start 1 --surah-end 10
    python scripts/data/seed_tafsir_data.py --dry-run
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger, setup_logging
from src.config.settings import settings
from src.data.models.quran import Ayah, Surah, Tafsir

setup_logging()
logger = get_logger()

USER_AGENT = "Burhan-Tafsir-Seeder/1.0"
REQUEST_PAUSE_SECONDS = 0.25
MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 2.0
QURANCOM_PER_PAGE = 50

_SUP_RE = re.compile(r"<sup[^>]*>.*?</sup>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_END_RE = re.compile(r"</(p|div|br)\s*>", re.IGNORECASE)
_SPACE_RE = re.compile(r"[ \t\u00a0]+")
_NEWLINE_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class TafsirSource:
    """One tafsir edition and where to fetch it from."""

    key: str
    provider: str
    edition: str
    author: str
    language: str = "ar"


SOURCES: dict[str, TafsirSource] = {
    "al-jalalayn": TafsirSource(
        key="al-jalalayn",
        provider="alquran.cloud",
        edition="ar.jalalayn",
        author="Jalal ad-Din al-Mahalli and Jalal ad-Din as-Suyuti",
    ),
    "al-qurtubi": TafsirSource(
        key="al-qurtubi",
        provider="alquran.cloud",
        edition="ar.qurtubi",
        author="Abu 'Abdullah Al-Qurtubi",
    ),
    "ibn-kathir": TafsirSource(
        key="ibn-kathir",
        provider="quran.com",
        edition="14",
        author="Ismail ibn Kathir",
    ),
}


# ── HTTP helpers ───────────────────────────────────────────────────────────────


def _fetch_json(url: str) -> dict[str, Any]:
    """Fetch JSON with bounded retries and a polite pause between attempts."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
            time.sleep(REQUEST_PAUSE_SECONDS)
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            wait = RETRY_BACKOFF_SECONDS * attempt
            logger.warning(
                "tafsir.fetch_retry",
                url=url,
                attempt=attempt,
                max_attempts=MAX_ATTEMPTS,
                wait_seconds=wait,
                error=str(exc),
            )
            time.sleep(wait)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def _clean_text(raw: str) -> str:
    """Turn upstream markup into readable plain text."""
    if not raw:
        return ""

    text = _SUP_RE.sub("", raw)
    text = _BLOCK_END_RE.sub("\n", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _SPACE_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _NEWLINE_RE.sub("\n\n", text)
    return text.strip()


# ── Per-source fetchers ────────────────────────────────────────────────────────


def _fetch_alquran_cloud(source: TafsirSource, surah: int) -> dict[int, str]:
    """Return ``{ayah_number: text}`` for one surah from api.alquran.cloud."""
    edition = urllib.parse.quote(source.edition)
    url = f"https://api.alquran.cloud/v1/surah/{surah}/{edition}"
    payload = _fetch_json(url)

    if payload.get("status") != "OK":
        raise RuntimeError(f"alquran.cloud returned status {payload.get('status')!r} for {url}")

    ayahs = payload.get("data", {}).get("ayahs", [])
    return {
        int(ayah["numberInSurah"]): _clean_text(ayah.get("text", ""))
        for ayah in ayahs
        if ayah.get("numberInSurah") is not None
    }


def _fetch_quran_com(source: TafsirSource, surah: int) -> dict[int, str]:
    """Return ``{ayah_number: text}`` for one surah from api.quran.com."""
    collected: dict[int, str] = {}
    page = 1

    while True:
        url = (
            f"https://api.quran.com/api/v4/tafsirs/{source.edition}/by_chapter/{surah}"
            f"?per_page={QURANCOM_PER_PAGE}&page={page}"
        )
        payload = _fetch_json(url)
        entries = payload.get("tafsirs", [])

        if not entries:
            break

        for entry in entries:
            verse_key = entry.get("verse_key", "")
            if ":" not in verse_key:
                continue
            try:
                ayah_number = int(verse_key.split(":", 1)[1])
            except ValueError:
                continue
            text = _clean_text(entry.get("text", ""))
            if text:
                collected[ayah_number] = text

        next_page = payload.get("pagination", {}).get("next_page")
        if not next_page:
            break
        page = int(next_page)

    return collected


def fetch_surah(source: TafsirSource, surah: int) -> dict[int, str]:
    """Dispatch to the provider that backs this tafsir source."""
    if source.provider == "alquran.cloud":
        return _fetch_alquran_cloud(source, surah)
    if source.provider == "quran.com":
        return _fetch_quran_com(source, surah)
    raise ValueError(f"Unknown provider {source.provider!r} for source {source.key!r}")


# ── Database helpers ──────────────────────────────────────────────────────────


def load_ayah_index(session: Session) -> dict[tuple[int, int], int]:
    """Map ``(surah_number, ayah_number) -> ayah_id`` from the database."""
    rows = session.execute(
        select(Surah.number, Ayah.number_in_surah, Ayah.id).join(Ayah, Ayah.surah_id == Surah.id)
    ).all()
    return {(int(surah), int(ayah)): int(ayah_id) for surah, ayah, ayah_id in rows}


def upsert_tafsirs(session: Session, source: TafsirSource, rows: list[dict[str, Any]]) -> int:
    """Insert or update tafsir rows, keyed by ``(ayah_id, source_name)``."""
    if not rows:
        return 0

    statement = pg_insert(Tafsir).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=["ayah_id", "source_name"],
        set_={
            "text": statement.excluded.text,
            "language": statement.excluded.language,
            "author": statement.excluded.author,
        },
    )
    session.execute(statement)
    return len(rows)


# ── Main flow ────────────────────────────────────────────────────────────────


def seed(
    session: Session,
    source_keys: list[str],
    surah_start: int,
    surah_end: int,
    dry_run: bool,
) -> dict[str, dict[str, int]]:
    """Seed the requested sources and return per-source counters."""
    ayah_index = load_ayah_index(session)
    if not ayah_index:
        raise SystemExit(
            "No ayahs found in the database. Run `python scripts/data/seed_quran_data.py --source api` first."
        )

    logger.info("tafsir.seed_start", ayahs_in_db=len(ayah_index), sources=source_keys)
    report: dict[str, dict[str, int]] = {}

    for key in source_keys:
        source = SOURCES[key]
        upserted = 0
        fetched = 0
        skipped_unmatched = 0
        skipped_empty = 0

        for surah in range(surah_start, surah_end + 1):
            entries = fetch_surah(source, surah)
            batch: list[dict[str, Any]] = []

            for ayah_number, text in sorted(entries.items()):
                if not text:
                    skipped_empty += 1
                    continue
                ayah_id = ayah_index.get((surah, ayah_number))
                if ayah_id is None:
                    skipped_unmatched += 1
                    continue
                batch.append(
                    {
                        "ayah_id": ayah_id,
                        "source_name": source.key,
                        "text": text,
                        "language": source.language,
                        "author": source.author,
                    }
                )

            fetched += len(entries)
            if not dry_run:
                upserted += upsert_tafsirs(session, source, batch)
                session.commit()

            logger.info(
                "tafsir.surah_done",
                source=source.key,
                surah=surah,
                entries=len(entries),
                written=len(batch),
            )

        report[source.key] = {
            "fetched": fetched,
            "written": upserted,
            "skipped_empty": skipped_empty,
            "skipped_unmatched": skipped_unmatched,
        }
        logger.info("tafsir.source_done", source=source.key, **report[source.key])

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed tafsir commentary into PostgreSQL")
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(SOURCES),
        help="Tafsir source to seed (repeatable). Default: all sources.",
    )
    parser.add_argument("--surah-start", type=int, default=1, help="First surah number (default: 1)")
    parser.add_argument("--surah-end", type=int, default=114, help="Last surah number (default: 114)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate without writing to the database.",
    )
    args = parser.parse_args()

    if not 1 <= args.surah_start <= args.surah_end <= 114:
        parser.error("surah range must satisfy 1 <= start <= end <= 114")

    source_keys = args.source or list(SOURCES)
    engine = create_engine(settings.database_url.replace("+asyncpg", ""), echo=settings.debug)

    with Session(engine) as session:
        report = seed(
            session,
            source_keys=source_keys,
            surah_start=args.surah_start,
            surah_end=args.surah_end,
            dry_run=args.dry_run,
        )

    logger.info("tafsir.seed_complete", report=report, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
