#!/usr/bin/env python3
"""
Athar CLI - Command-line interface for managing the application.

Usage:
    python scripts/cli.py setup
    python scripts/cli.py start
    python scripts/cli.py stop
    python scripts/cli.py test
    python scripts/cli.py status
    python scripts/cli.py ingest --books 100 --hadith 1000
    python scripts/cli.py embed --limit 1000
    python scripts/cli.py db migrate
    python scripts/cli.py db shell
"""
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: str, capture: bool = False) -> tuple[bool, str]:
    """Run shell command and return success + output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout if capture else ""
    except Exception as e:
        return False, str(e)


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_step(text: str):
    print(f"  ▸ {text}")


def print_success(text: str):
    print(f"  ✓ {text}")


def print_error(text: str):
    print(f"  ✗ {text}")


def cmd_setup():
    """Full initial setup."""
    print_header("🚀 Athar - Complete Setup")
    
    # Check Python
    print_step("Checking Python...")
    success, _ = run_command("python --version")
    if not success:
        print_error("Python 3.12+ not found!")
        return False
    print_success("Python found")
    
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
    run_command("docker exec -i athar-postgres psql -U athar -d athar_db < migrations/001_initial_schema.sql")
    print_success("Migrations complete")
    
    # Ingest sample data
    print_step("Processing sample data...")
    run_command("python scripts/complete_ingestion.py --books 50 --hadith 500")
    
    print_header("✓ Setup Complete! Next: build.bat start")
    return True


def cmd_start(api_only: bool = False):
    """Start application."""
    print_header("🚀 Starting Athar")
    
    # Check Docker
    print_step("Checking Docker services...")
    success, _ = run_command("docker compose -f docker/docker-compose.dev.yml ps | findstr healthy")
    if not success:
        print_step("Starting services...")
        run_command("docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant")
        time.sleep(10)
    print_success("Services running")
    
    # Start API
    print_step("Starting Backend API...")
    run_command('start "Athar API" cmd /k "uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"')
    time.sleep(3)
    print_success("API starting on port 8000")
    
    if not api_only:
        print_step("Starting Frontend...")
        run_command('cd frontend && start "Athar Frontend" cmd /k "npm run dev" && cd ..')
        time.sleep(3)
        print_success("Frontend starting on port 3000")
    
    print_header("✓ Application Starting!\nAPI: http://localhost:8000\nDocs: http://localhost:8000/docs")
    
    # Open browser
    time.sleep(3)
    run_command("start http://localhost:8000/docs")


def cmd_stop():
    """Stop all services."""
    print_header("🛑 Stopping Services")
    run_command("docker compose -f docker/docker-compose.dev.yml down")
    print_success("Services stopped")


def cmd_test():
    """Run tests."""
    print_header("🧪 Running Tests")
    
    print_step("Testing API...")
    run_command("python scripts/test_api.py")
    
    print_step("Running unit tests...")
    run_command("pytest tests/ -v --tb=short")
    
    print_header("✓ Tests Complete")


def cmd_status():
    """Check service status."""
    print_header("📊 Athar Status")
    
    print("Docker Services:")
    success, output = run_command("docker compose -f docker/docker-compose.dev.yml ps", capture=True)
    print(output)
    
    print("\nData Files:")
    processed_dir = PROJECT_ROOT / "data" / "processed"
    if processed_dir.exists():
        for f in processed_dir.glob("*.json"):
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"  • {f.name}: {size_mb:.2f} MB")
    
    print()


def cmd_ingest(books: int = 100, hadith: int = 1000):
    """Ingest data."""
    print_header(f"📥 Data Ingestion ({books} books, {hadith} hadith)")
    
    run_command(f"python scripts/complete_ingestion.py --books {books} --hadith {hadith}")


def cmd_embed(limit: int = 1000):
    """Generate embeddings."""
    print_header(f"🔢 Generating Embeddings (limit: {limit})")
    
    run_command(f"python scripts/generate_embeddings.py --collection fiqh_passages --limit {limit}")


def cmd_db_migrate():
    """Run database migrations."""
    print_header("🗄️  Database Migrations")
    
    migrations = [
        "migrations/001_initial_schema.sql",
        "migrations/versions/002_quran_translations_tafsir.sql"
    ]
    
    for migration in migrations:
        migration_path = PROJECT_ROOT / migration
        if migration_path.exists():
            print_step(f"Running {migration_path.name}...")
            run_command(f"docker exec -i athar-postgres psql -U athar -d athar_db < {migration}")
            print_success(f"{migration_path.name} complete")


def cmd_db_shell():
    """Open database shell."""
    print_header("🗄️  PostgreSQL Shell")
    run_command("docker exec -it athar-postgres psql -U athar -d athar_db")


def cmd_data_status():
    """Show data statistics."""
    print_header("📊 Data Statistics")
    
    processed_dir = PROJECT_ROOT / "data" / "processed"
    
    if not processed_dir.exists():
        print_error("No processed data found")
        return
    
    total_chunks = 0
    total_size = 0
    
    for f in processed_dir.glob("*.json"):
        size = f.stat().st_size
        total_size += size
        
        # Count chunks
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    total_chunks += len(data)
        except:
            pass
    
    print(f"  Total chunks: {total_chunks:,}")
    print(f"  Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"  Files: {len(list(processed_dir.glob('*.json')))}")
    print()


def print_help():
    """Print help message."""
    print("""
Athar CLI - Command-line interface

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
    db migrate              Run database migrations
    db shell                Open PostgreSQL shell
    help                    Show this help

Examples:
    python scripts/cli.py setup
    python scripts/cli.py start
    python scripts/cli.py ingest --books 100 --hadith 1000
    python scripts/cli.py embed --limit 5000
    python scripts/cli.py db migrate
    """)


def main():
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
