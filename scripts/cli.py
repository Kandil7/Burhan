#!/usr/bin/env python3
"""
Burhan CLI - Command-line interface for managing the application.

Provides convenient commands for:
- Setup and installation
- Starting/stopping services
- Data ingestion and embedding
- Testing and status checks
- Database management

Usage:
    python scripts/cli.py setup
    python scripts/cli.py start
    python scripts/cli.py stop
    python scripts/cli.py test
    python scripts/cli.py status
    python scripts/cli.py ingest --books 100 --hadith 1000
    python scripts/cli.py embed --limit 1000
    python scripts/cli.py db migrate
    python scripts/cli.py help

Author: Burhan Engineering Team
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from scripts.utils import (
    get_project_root,
    get_data_dir,
    setup_script_logger,
    format_size,
)

logger = setup_script_logger("cli")

PROJECT_ROOT = get_project_root()


# ── Terminal Helpers ─────────────────────────────────────────────────────


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_step(text: str) -> None:
    """Print a step indicator."""
    print(f"  ▸ {text}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"  ✓ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"  ✗ {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"  ⚠ {text}")


# ── Command Runner ───────────────────────────────────────────────────────


def run_command(cmd: str, capture: bool = False, cwd: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run shell command and return success status and output.

    Args:
        cmd: Shell command to run.
        capture: Whether to capture stdout.
        cwd: Working directory.

    Returns:
        Tuple of (success, output).
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=120,
            cwd=cwd or PROJECT_ROOT,
        )
        return result.returncode == 0, result.stdout if capture else ""
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 120s"
    except Exception as e:
        return False, str(e)


# ── Commands ─────────────────────────────────────────────────────────────


def cmd_setup() -> bool:
    """Full initial setup."""
    print_header("🚀 Burhan - Complete Setup")

    # Check Python
    print_step("Checking Python...")
    success, output = run_command("python --version", capture=True)
    if not success:
        print_error("Python not found!")
        return False
    print_success(f"Python found: {output.strip()}")

    # Install dependencies
    print_step("Installing dependencies...")
    success, _ = run_command("pip install -e . --quiet")
    if not success:
        print_error("Installation failed!")
        return False
    print_success("Dependencies installed")

    # Start Docker
    print_step("Starting Docker services...")
    run_command("docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant")
    time.sleep(10)
    print_success("Services started")

    # Run migrations
    print_step("Running migrations...")
    run_command(
        "docker exec -i Burhan-postgres psql -U Burhan -d Burhan_db < migrations/001_initial_schema.sql"
    )
    print_success("Migrations complete")

    print_header("✓ Setup Complete! Next: python scripts/cli.py start")
    return True


def cmd_start(api_only: bool = False) -> None:
    """Start application."""
    print_header("🚀 Starting Burhan")

    # Check Docker
    print_step("Checking Docker services...")
    success, _ = run_command("docker compose -f docker/docker-compose.dev.yml ps", capture=True)
    if not success:
        print_step("Starting services...")
        run_command("docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant")
        time.sleep(10)
    print_success("Services running")

    # Start API
    print_step("Starting Backend API...")
    print_warning("API will start in a new window")
    run_command(
        'start "Burhan API" cmd /k "uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"'
    )
    time.sleep(3)
    print_success("API starting on port 8000")

    if not api_only:
        print_step("Starting Frontend...")
        run_command('cd frontend && start "Burhan Frontend" cmd /k "npm run dev" && cd ..')
        time.sleep(3)
        print_success("Frontend starting on port 3000")

    print_header(
        "✓ Application Starting!\n"
        "  API: http://localhost:8000\n"
        "  Docs: http://localhost:8000/docs"
    )

    # Open browser
    time.sleep(3)
    run_command("start http://localhost:8000/docs")


def cmd_stop() -> None:
    """Stop all services."""
    print_header("🛑 Stopping Services")
    run_command("docker compose -f docker/docker-compose.dev.yml down")
    print_success("Services stopped")


def cmd_test() -> None:
    """Run tests."""
    print_header("🧪 Running Tests")

    print_step("Testing API...")
    run_command("python scripts/tests/test_api.py")

    print_step("Running unit tests...")
    run_command("pytest tests/ -v --tb=short")

    print_header("✓ Tests Complete")


def cmd_status() -> None:
    """Check service status."""
    print_header("📊 Burhan Status")

    print("Docker Services:")
    success, output = run_command(
        "docker compose -f docker/docker-compose.dev.yml ps", capture=True
    )
    if output:
        print(output)
    else:
        print_warning("Could not get Docker status")

    print("\nData Files:")
    processed_dir = get_data_dir("processed")
    if processed_dir.exists():
        for f in processed_dir.glob("*.json"):
            size = format_size(f.stat().st_size)
            print(f"  • {f.name}: {size}")
    else:
        print_warning("No processed data found")

    print()


def cmd_ingest(books: int = 100, hadith: int = 1000) -> None:
    """Ingest data."""
    print_header(f"📥 Data Ingestion ({books} books, {hadith} hadith)")
    run_command(
        f"python scripts/ingestion/complete_ingestion.py --books {books} --hadith {hadith}"
    )


def cmd_embed(limit: int = 1000) -> None:
    """Generate embeddings."""
    print_header(f"🔢 Generating Embeddings (limit: {limit})")
    run_command(
        f"python scripts/data/generate_embeddings.py --collection fiqh_passages --limit {limit}"
    )


def cmd_db_migrate() -> None:
    """Run database migrations."""
    print_header("🗄️  Database Migrations")

    migrations = [
        "migrations/001_initial_schema.sql",
    ]

    for migration in migrations:
        migration_path = PROJECT_ROOT / migration
        if migration_path.exists():
            print_step(f"Running {migration_path.name}...")
            run_command(
                f"docker exec -i Burhan-postgres psql -U Burhan -d Burhan_db < {migration_path}"
            )
            print_success(f"{migration_path.name} complete")
        else:
            print_warning(f"Migration not found: {migration}")


def cmd_db_shell() -> None:
    """Open database shell."""
    print_header("🗄️  PostgreSQL Shell")
    run_command("docker exec -it Burhan-postgres psql -U Burhan -d Burhan_db")


def cmd_data_status() -> None:
    """Show data statistics."""
    print_header("📊 Data Statistics")

    processed_dir = get_data_dir("processed")

    if not processed_dir.exists():
        print_error("No processed data found")
        return

    total_chunks = 0
    total_size = 0

    for f in processed_dir.glob("*.json"):
        size = f.stat().st_size
        total_size += size

        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    total_chunks += len(data)
        except Exception:
            pass

    print(f"  Total chunks: {total_chunks:,}")
    print(f"  Total size:   {format_size(total_size)}")
    print(f"  Files:        {len(list(processed_dir.glob('*.json')))}")
    print()


def cmd_check_datasets() -> None:
    """Run dataset integrity check."""
    print_header("🔍 Dataset Integrity Check")
    run_command("python scripts/check_datasets.py")


def cmd_quick_test() -> None:
    """Run quick smoke test."""
    print_header("🧪 Quick Smoke Test")
    run_command("python scripts/quick_test.py")


def print_help() -> None:
    """Print help message."""
    print("""
Burhan CLI - Command-line interface

Usage:
    python scripts/cli.py <command> [options]

Commands:
    setup                   Full initial setup
    start                   Start application (API + Frontend)
    start:api               Start API only
    stop                    Stop all services
    test                    Run tests
    status                  Check service status
    ingest                  Process books and hadith
    embed                   Generate embeddings
    data                    Show data statistics
    check                   Check dataset integrity
    quick-test              Run quick smoke test
    db migrate              Run database migrations
    db shell                Open PostgreSQL shell
    help                    Show this help

Examples:
    python scripts/cli.py setup
    python scripts/cli.py start
    python scripts/cli.py ingest --books 100 --hadith 1000
    python scripts/cli.py embed --limit 5000
    python scripts/cli.py db migrate
    python scripts/cli.py check
    """)


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "setup":
        cmd_setup()
    elif command == "start":
        cmd_start()
    elif command == "start:api":
        cmd_start(api_only=True)
    elif command == "stop":
        cmd_stop()
    elif command == "test":
        cmd_test()
    elif command == "status":
        cmd_status()
    elif command == "ingest":
        books = 100
        hadith = 1000
        if "--books" in sys.argv:
            idx = sys.argv.index("--books")
            books = int(sys.argv[idx + 1])
        if "--hadith" in sys.argv:
            idx = sys.argv.index("--hadith")
            hadith = int(sys.argv[idx + 1])
        cmd_ingest(books, hadith)
    elif command == "embed":
        limit = 1000
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        cmd_embed(limit)
    elif command == "data":
        cmd_data_status()
    elif command == "check":
        cmd_check_datasets()
    elif command == "quick-test":
        cmd_quick_test()
    elif command == "db":
        if len(sys.argv) > 2:
            subcmd = sys.argv[2]
            if subcmd == "migrate":
                cmd_db_migrate()
            elif subcmd == "shell":
                cmd_db_shell()
    elif command == "help":
        print_help()
    else:
        print(f"Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
