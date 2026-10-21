#!/usr/bin/env python3
"""
Quran Database Seeder Script.

Seeds Quran data into PostgreSQL database from:
- Sample JSON (for testing)
- Quran.com API (for production)

Usage:
    python scripts/data/seed_quran_data.py --sample
    python scripts/data/seed_quran_data.py --source api
    python scripts/data/seed_quran_data.py --source json --file data/seed/quran_sample.json
"""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.data.models.quran import Base
from src.data.ingestion.quran_loader import QuranLoader
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

SAMPLE_PATH = PROJECT_ROOT / "data" / "seed" / "quran_sample.json"


def create_tables(engine):
    """Create all Quran database tables."""
    logger.info("db.creating_tables")
    Base.metadata.create_all(engine)
    logger.info("db.tables_created")


def seed_sample(session):
    """Seed sample Quran data from JSON file."""
    logger.info("quran.seeding_sample")

    if not SAMPLE_PATH.exists():
        logger.error("quran.sample_not_found", path=str(SAMPLE_PATH))
        return

    stats = QuranLoader(session).load_from_json(str(SAMPLE_PATH))
    logger.info("quran.seed_complete", **stats)


def seed_from_json(session, path: str):
    """Seed Quran data from an arbitrary JSON file."""
    logger.info("quran.seeding_from_json", path=path)
    stats = QuranLoader(session).load_from_json(path)
    logger.info("quran.seed_complete", **stats)


async def seed_from_api(session, language: str = "en"):
    """Seed complete Quran data from API."""
    logger.info("quran.seeding_from_api", language=language)

    loader = QuranLoader(session)
    stats = await loader.load_from_api(language=language)

    logger.info("quran.api_seed_complete", **stats)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed Quran Database")
    parser.add_argument(
        "--source", choices=["api", "json"], default="sample", help="Data source (api, json, or sample)"
    )
    parser.add_argument("--sample", action="store_true", help="Load sample data for testing")
    parser.add_argument("--file", help="JSON file to load when --source json is used")
    parser.add_argument("--language", default="en", help="Translation language (default: en)")

    args = parser.parse_args()

    # Create database engine
    engine = create_engine(settings.database_url.replace("+asyncpg", ""), echo=settings.debug)

    # Create tables
    create_tables(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        if args.sample:
            seed_sample(session)
        elif args.source == "api":
            asyncio.run(seed_from_api(session, args.language))
        elif args.source == "json":
            if not args.file:
                parser.error("--source json requires --file PATH")
            seed_from_json(session, args.file)
        else:
            seed_sample(session)

        logger.info("db.seed_complete")

    except Exception as e:
        logger.error("db.seed_error", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
