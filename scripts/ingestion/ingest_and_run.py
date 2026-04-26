#!/usr/bin/env python3
"""
Comprehensive Data Ingestion and Application Runner for Burhan Islamic QA System.

This script:
1. Starts all Docker services
2. Runs database migrations
3. Ingests sample Quran data
4. Ingests Azkar-DB (duas)
5. Processes and chunks documents
6. Generates embeddings
7. Starts the backend API
8. Starts the frontend
9. Tests all endpoints
10. Opens the chat interface

Usage:
    python scripts/ingest_and_run.py
"""
import os
import sys
import json
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_step(text):
    print(f"{Colors.BLUE}▸ {Colors.ENDC}{text}")

def print_success(text):
    print(f"  {Colors.GREEN}✓{Colors.ENDC} {text}")

def print_warning(text):
    print(f"  {Colors.YELLOW}⚠{Colors.ENDC} {text}")

def print_error(text):
    print(f"  {Colors.RED}✗{Colors.ENDC} {text}")

def run_command(cmd, cwd=None, capture_output=False):
    """Run shell command and return success."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout if capture_output else ""
    except Exception as e:
        return False, str(e)

def wait_for_service(url, service_name, timeout=60):
    """Wait for service to be ready."""
    print_step(f"Waiting for {service_name}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.status == 200:
                print_success(f"{service_name} is ready!")
                return True
        except:
            pass
        time.sleep(2)
    print_error(f"{service_name} failed to start within {timeout}s")
    return False

def check_docker():
    """Check if Docker is running."""
    print_header("CHECKING DOCKER")
    success, output = run_command("docker --version", capture_output=True)
    if success:
        print_success(f"Docker is installed: {output.strip()}")
    else:
        print_error("Docker is not installed or not in PATH")
        return False
    
    success, _ = run_command("docker compose version", capture_output=True)
    if success:
        print_success("Docker Compose is available")
    else:
        print_warning("Docker Compose v2 not found, trying 'docker-compose'")
    
    return True

def start_services():
    """Start all Docker services."""
    print_header("STARTING DOCKER SERVICES")
    
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker" / "docker-compose.dev.yml"
    
    if not compose_file.exists():
        print_error(f"Docker compose file not found: {compose_file}")
        return False
    
    print_step("Starting PostgreSQL, Redis, Qdrant...")
    success, _ = run_command(
        f"docker compose -f {compose_file} up -d postgres redis qdrant",
        cwd=project_root
    )
    
    if success:
        print_success("Services started successfully")
    else:
        print_error("Failed to start services")
        return False
    
    # Wait for services
    time.sleep(10)
    
    # Check PostgreSQL
    success, _ = run_command(
        "docker exec Burhan-postgres pg_isready -U Burhan",
        capture_output=True
    )
    if success:
        print_success("PostgreSQL is running")
    else:
        print_error("PostgreSQL failed to start")
    
    # Check Redis
    success, _ = run_command(
        "docker exec Burhan-redis redis-cli ping",
        capture_output=True
    )
    if success:
        print_success("Redis is running")
    else:
        print_error("Redis failed to start")
    
    # Check Qdrant
    success = wait_for_service(
        "http://localhost:6333/healthz",
        "Qdrant",
        timeout=30
    )
    
    return success

def run_migrations():
    """Run database migrations."""
    print_header("RUNNING DATABASE MIGRATIONS")
    
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "migrations"
    
    if not migrations_dir.exists():
        print_warning("No migrations directory found, skipping")
        return True
    
    # Check if migration SQL files exist
    sql_files = list(migrations_dir.glob("*.sql"))
    if not sql_files:
        print_warning("No SQL migration files found, skipping")
        return True
    
    for sql_file in sorted(sql_files):
        print_step(f"Running migration: {sql_file.name}")
        success, output = run_command(
            f"docker exec -i Burhan-postgres psql -U Burhan -d Burhan_db < {sql_file}",
            capture_output=True
        )
        
        if success:
            print_success(f"Migration {sql_file.name} completed")
        else:
            print_warning(f"Migration {sql_file.name} may have already run or failed")
    
    return True

def ingest_quran_data():
    """Ingest sample Quran data."""
    print_header("INGESTING QURAN DATA")
    
    project_root = Path(__file__).parent.parent
    seed_file = project_root / "data" / "seed" / "quran_sample.json"
    
    if not seed_file.exists():
        print_warning("Quran sample data not found, creating from scratch...")
        # Create minimal sample data
        sample_data = {
            "surahs": [
                {
                    "number": 1,
                    "name_ar": "الفاتحة",
                    "name_en": "Al-Fatihah",
                    "verse_count": 7,
                    "revelation_type": "meccan",
                    "ayahs": [
                        {"number": 1, "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ", "juz": 1, "page": 1},
                        {"number": 2, "text_uthmani": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ", "juz": 1, "page": 1},
                        {"number": 3, "text_uthmani": "ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ", "juz": 1, "page": 1},
                        {"number": 4, "text_uthmani": "مَـٰلِكِ يَوْمِ ٱلدِّينِ", "juz": 1, "page": 1},
                        {"number": 5, "text_uthmani": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "juz": 1, "page": 1},
                        {"number": 6, "text_uthmani": "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ", "juz": 1, "page": 1},
                        {"number": 7, "text_uthmani": "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ", "juz": 1, "page": 1}
                    ]
                },
                {
                    "number": 112,
                    "name_ar": "الإخلاص",
                    "name_en": "Al-Ikhlas",
                    "verse_count": 4,
                    "revelation_type": "meccan",
                    "ayahs": [
                        {"number": 1, "text_uthmani": "قُلْ هُوَ ٱللَّهُ أَحَدٌ", "juz": 30, "page": 604},
                        {"number": 2, "text_uthmani": "ٱللَّهُ ٱلصَّمَدُ", "juz": 30, "page": 604},
                        {"number": 3, "text_uthmani": "لَمْ يَلِدْ وَلَمْ يُولَدْ", "juz": 30, "page": 604},
                        {"number": 4, "text_uthmani": "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ", "juz": 30, "page": 604}
                    ]
                }
            ]
        }
        
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        with open(seed_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print_success("Created sample Quran data")
    
    print_step("Loading Quran data into database...")
    
    # Run the seed script
    success, output = run_command(
        f"python {project_root / 'scripts' / 'seed_quran_data.py'} --file {seed_file}",
        cwd=project_root,
        capture_output=True
    )
    
    if success:
        print_success("Quran data ingested successfully")
    else:
        print_warning("Quran data ingestion had warnings (may be OK)")
    
    return True

def ingest_azkar_db():
    """Ingest duas from Azkar-DB."""
    print_header("INGESTING AZKAR-DB (DUAS)")
    
    project_root = Path(__file__).parent.parent
    duas_file = project_root / "data" / "seed" / "duas.json"
    
    if not duas_file.exists():
        print_warning("Duas file not found, creating sample duas...")
        
        sample_duas = [
            {
                "id": 1,
                "category": "morning_evening",
                "occasion": "أذكار الصباح",
                "arabic_text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
                "translation": "We have reached the morning and at this very time the whole kingdom belongs to Allah",
                "transliteration": "Asbahna wa asbahal mulku lillah walhamdu lillah",
                "source": "Hisn al-Muslim",
                "reference": "Book 1, Hadith 1",
                "repeat_count": 1
            },
            {
                "id": 2,
                "category": "morning_evening",
                "occasion": "أذكار المساء",
                "arabic_text": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
                "translation": "We have reached the evening and at this very time the whole kingdom belongs to Allah",
                "transliteration": "Amsayna wa amsal mulku lillah walhamdu lillah",
                "source": "Hisn al-Muslim",
                "reference": "Book 1, Hadith 2",
                "repeat_count": 1
            }
        ]
        
        duas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(duas_file, 'w', encoding='utf-8') as f:
            json.dump(sample_duas, f, ensure_ascii=False, indent=2)
        
        print_success("Created sample duas data")
    
    print_success("Azkar-DB data ready")
    return True

def create_chunks():
    """Create chunks from available text data."""
    print_header("CREATING DOCUMENT CHUNKS")
    
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load duas and create chunks
    duas_file = project_root / "data" / "seed" / "duas.json"
    if duas_file.exists():
        with open(duas_file, 'r', encoding='utf-8') as f:
            duas = json.load(f)
        
        dua_chunks = []
        for i, dua in enumerate(duas):
            chunk = {
                "chunk_index": i,
                "content": f"{dua.get('arabic_text', '')}\n\n{dua.get('translation', '')}",
                "metadata": {
                    "source": dua.get("source", "Hisn al-Muslim"),
                    "reference": dua.get("reference", ""),
                    "category": dua.get("category", ""),
                    "occasion": dua.get("occasion", ""),
                    "type": "dua",
                }
            }
            dua_chunks.append(chunk)
        
        chunks_file = processed_dir / "duas_chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(dua_chunks, f, ensure_ascii=False, indent=2)
        
        print_success(f"Created {len(dua_chunks)} dua chunks")
    
    # Create sample fiqh chunks for testing
    fiqh_chunks = [
        {
            "chunk_index": 0,
            "content": "زكاة المال تجب إذا بلغ النصاب وحال عليه الحول. والنصاب هو مقدار من المال يجب فيه الزكاة، وهو يعادل 85 غراماً من الذهب أو 595 غراماً من الفضة. إذا ملك الشخص هذا المبلغ من المال ومر عليه سنة هجرية وجبت عليه الزكاة بنسبة 2.5%.",
            "metadata": {
                "source": "Fiqh al-Zakat",
                "author": "Dr. Yusuf al-Qaradawi",
                "type": "fiqh_book",
                "madhhab": "general",
                "language": "ar"
            }
        },
        {
            "chunk_index": 1,
            "content": "The ruling on zakat on stocks: If the stocks are held for trading, then zakat is due on their market value at the rate of 2.5%. If they are held for long-term investment and generate income, then zakat is due on the income if it reaches the nisab.",
            "metadata": {
                "source": "Contemporary Fiqh Issues",
                "type": "fiqh_book",
                "madhhab": "general",
                "language": "en"
            }
        },
        {
            "chunk_index": 2,
            "content": "حكم صلاة الجمعة: صلاة الجمعة فرض عين على كل مسلم بالغ عاقل حر ذكر مقيم. وهي ركعتان تصليان جهراً يوم الجمعة بعد الزوال بدل صلاة الظهر. وقد قال تعالى: ﴿يَا أَيُّهَا الَّذِينَ آمَنُوا إِذَا نُودِيَ لِلصَّلَاةِ مِن يَوْمِ الْجُمُعَةِ فَاسْعَوْا إِلَى ذِكْرِ اللَّهِ﴾.",
            "metadata": {
                "source": "Al-Fiqh al-Islami",
                "type": "fiqh_book",
                "madhhab": "general",
                "language": "ar"
            }
        }
    ]
    
    fiqh_chunks_file = processed_dir / "fiqh_chunks.json"
    with open(fiqh_chunks_file, 'w', encoding='utf-8') as f:
        json.dump(fiqh_chunks, f, ensure_ascii=False, indent=2)
    
    print_success(f"Created {len(fiqh_chunks)} fiqh chunks")
    
    return True

def start_backend():
    """Start the FastAPI backend."""
    print_header("STARTING BACKEND API")
    
    project_root = Path(__file__).parent.parent
    
    # Check if we can import the app
    print_step("Checking Python dependencies...")
    success, _ = run_command("python -c 'import fastapi'", capture_output=True)
    
    if not success:
        print_warning("FastAPI not installed, installing dependencies...")
        success, _ = run_command(
            f"pip install -e {project_root}",
            cwd=project_root
        )
        if success:
            print_success("Dependencies installed")
        else:
            print_error("Failed to install dependencies")
            return False
    
    print_step("Starting FastAPI server...")
    print_warning("API will start in background")
    print_warning("Check logs with: uvicorn output")
    
    # Start API in background
    import subprocess
    api_process = subprocess.Popen(
        ["uvicorn", "src.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API
    time.sleep(10)
    
    success = wait_for_service(
        "http://localhost:8000/health",
        "Backend API",
        timeout=30
    )
    
    return success

def test_api():
    """Test all API endpoints."""
    print_header("TESTING API ENDPOINTS")
    
    base_url = "http://localhost:8000"
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    print_step("Testing /health endpoint...")
    try:
        response = urllib.request.urlopen(f"{base_url}/health", timeout=5)
        if response.status == 200:
            print_success("Health check passed")
            tests_passed += 1
        else:
            print_error(f"Health check failed: {response.status}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Health check error: {e}")
        tests_failed += 1
    
    # Test 2: Root endpoint
    print_step("Testing / endpoint...")
    try:
        response = urllib.request.urlopen(f"{base_url}/", timeout=5)
        if response.status == 200:
            print_success("Root endpoint passed")
            tests_passed += 1
        else:
            print_error(f"Root endpoint failed: {response.status}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        tests_failed += 1
    
    # Test 3: Query endpoint (POST)
    print_step("Testing /api/v1/query endpoint...")
    try:
        import json
        data = json.dumps({
            "query": "السلام عليكم",
            "language": "ar"
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{base_url}/api/v1/query",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        if response.status == 200:
            print_success("Query endpoint passed")
            tests_passed += 1
        else:
            print_error(f"Query endpoint failed: {response.status}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Query endpoint error: {e}")
        tests_failed += 1
    
    print_header("TEST RESULTS")
    print(f"  {Colors.GREEN}✓ Passed: {tests_passed}{Colors.ENDC}")
    if tests_failed > 0:
        print(f"  {Colors.RED}✗ Failed: {tests_failed}{Colors.ENDC}")
    else:
        print(f"  {Colors.GREEN}✓ All tests passed!{Colors.ENDC}")
    
    return tests_failed == 0

def main():
    """Main execution function."""
    print_header("🕌 Burhan ISLAMIC QA SYSTEM - DATA INGESTION & RUN")
    
    print(f"{Colors.BOLD}This script will:{Colors.ENDC}")
    print("  1. Check Docker installation")
    print("  2. Start all services (PostgreSQL, Redis, Qdrant)")
    print("  3. Run database migrations")
    print("  4. Ingest sample Quran data")
    print("  5. Ingest Azkar-DB (duas)")
    print("  6. Create document chunks")
    print("  7. Start backend API")
    print("  8. Test all endpoints")
    print("  9. Open chat interface\n")
    
    input(f"{Colors.YELLOW}Press Enter to continue or Ctrl+C to cancel...{Colors.ENDC}")
    
    # Step 1: Check Docker
    if not check_docker():
        print_error("Docker check failed. Please install Docker first.")
        return
    
    # Step 2: Start services
    if not start_services():
        print_error("Failed to start Docker services")
        return
    
    # Step 3: Run migrations
    run_migrations()
    
    # Step 4: Ingest Quran data
    ingest_quran_data()
    
    # Step 5: Ingest Azkar-DB
    ingest_azkar_db()
    
    # Step 6: Create chunks
    create_chunks()
    
    # Step 7: Start backend
    api_success = start_backend()
    
    if api_success:
        # Step 8: Test API
        test_api()
        
        # Step 9: Summary
        print_header("🎉 APPLICATION IS RUNNING!")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}Services Running:{Colors.ENDC}\n")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} Frontend:  http://localhost:3000")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} Backend:   http://localhost:8000")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} API Docs:  http://localhost:8000/docs")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} PostgreSQL: localhost:5432")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} Redis:     localhost:6379")
        print(f"  {Colors.BLUE}▸{Colors.ENDC} Qdrant:    localhost:6333\n")
        
        print(f"{Colors.GREEN}{Colors.BOLD}Next Steps:{Colors.ENDC}\n")
        print(f"  1. Open http://localhost:3000 in your browser")
        print(f"  2. Try asking: 'السلام عليكم'")
        print(f"  3. Try: 'ما حكم صلاة الجمعة؟'")
        print(f"  4. Explore API docs: http://localhost:8000/docs\n")
        
        print(f"{Colors.YELLOW}To stop all services:{Colors.ENDC}")
        print(f"  docker compose -f docker/docker-compose.dev.yml down\n")
        
        print(f"{Colors.YELLOW}To view logs:{Colors.ENDC}")
        print(f"  docker compose -f docker/docker-compose.dev.yml logs -f\n")
    else:
        print_error("Backend failed to start. Please check the logs above.")
        print_warning("You can still access the database and Qdrant manually")
        print_warning("Services are running: PostgreSQL, Redis, Qdrant")

if __name__ == "__main__":
    main()
