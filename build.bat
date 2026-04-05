@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM Athar Islamic QA System - Build System
REM ============================================================
REM Usage: build.bat [command] [options]
REM
REM Commands:
REM   setup          - Full initial setup (install + data + docker)
REM   start          - Start all services (API + Frontend)
REM   start:api      - Start API only
REM   start:frontend - Start Frontend only
REM   stop           - Stop all services
REM   restart        - Stop and start
REM   test           - Run test suite
REM   test:api       - Test API endpoints
REM   test:unit      - Run Python unit tests
REM   status         - Check service status
REM   logs [service] - View logs (all, api, postgres, redis, qdrant)
REM   clean          - Clean build artifacts
REM   reset          - Full reset (stop + clean volumes)
REM   data:ingest    - Process books and hadith
REM   data:embed     - Generate embeddings
REM   data:quran     - Seed Quran database
REM   data:status    - Show data statistics
REM   db:migrate     - Run database migrations
REM   db:shell       - Open PostgreSQL shell
REM   db:backup      - Backup database
REM   docker:prune   - Remove unused Docker resources
REM   help           - Show this help message
REM ============================================================

set COMMAND=%~1
set OPTION=%~2

if "%COMMAND%"=="" goto menu
if "%COMMAND%"=="help" goto help
if "%COMMAND%"=="setup" goto setup
if "%COMMAND%"=="start" goto start
if "%COMMAND%"=="start:api" goto start_api
if "%COMMAND%"=="start:frontend" goto start_frontend
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="restart" goto restart
if "%COMMAND%"=="test" goto test
if "%COMMAND%"=="test:api" goto test_api
if "%COMMAND%"=="test:unit" goto test_unit
if "%COMMAND%"=="status" goto status
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="clean" goto clean
if "%COMMAND%"=="reset" goto reset
if "%COMMAND%"=="data:ingest" goto data_ingest
if "%COMMAND%"=="data:embed" goto data_embed
if "%COMMAND%"=="data:quran" goto data_quran
if "%COMMAND%"=="data:status" goto data_status
if "%COMMAND%"=="db:migrate" goto db_migrate
if "%COMMAND%"=="db:shell" goto db_shell
if "%COMMAND%"=="db:backup" goto db_backup
if "%COMMAND%"=="docker:prune" goto docker_prune
if "%COMMAND%"=="menu" goto menu

echo [X] Unknown command: %COMMAND%
echo Type: build.bat help
goto :eof

:menu
cls
echo ============================================================
echo            🕌 Athar Islamic QA System
echo ============================================================
echo.
echo  Quick Actions:
echo    1. Setup & Install     (First time only)
echo    2. Start Application   (API + Frontend)
echo    3. Start API Only      (Backend only)
echo    4. Test Everything     (Run test suite)
echo    5. Check Status        (Service health)
echo.
echo  Data Management:
echo    6. Ingest More Data    (Books + Hadith)
echo    7. Generate Embeddings (For RAG)
echo    8. Seed Quran Database
echo    9. View Data Statistics
echo.
echo  Maintenance:
echo    10. View Logs
echo    11. Database Shell
echo    12. Stop All Services
echo    13. Clean & Reset
echo.
echo    0. Exit
echo.
echo ============================================================
echo.

set /p choice="Select option (0-13): "

if "!choice!"=="1" call build.bat setup & goto menu
if "!choice!"=="2" call build.bat start & goto menu
if "!choice!"=="3" call build.bat start:api & goto menu
if "!choice!"=="4" call build.bat test & goto menu
if "!choice!"=="5" call build.bat status & goto menu
if "!choice!"=="6" call build.bat data:ingest & goto menu
if "!choice!"=="7" call build.bat data:embed & goto menu
if "!choice!"=="8" call build.bat data:quran & goto menu
if "!choice!"=="9" call build.bat data:status & goto menu
if "!choice!"=="10" call build.bat logs & goto menu
if "!choice!"=="11" call build.bat db:shell & goto menu
if "!choice!"=="12" call build.bat stop & goto menu
if "!choice!"=="13" call build.bat reset & goto menu
if "!choice!"=="0" exit /b 0

echo [X] Invalid choice
timeout /t 2 >nul
goto menu

:setup
echo.
echo ============================================================
echo 🚀 Athar - Complete Setup
echo ============================================================
echo.

echo [1/5] Checking prerequisites...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [X] Python 3.12+ not found!
    echo     Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [✓] Python found

docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [X] Docker not found!
    echo     Install from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [✓] Docker found
echo.

echo [2/5] Installing Python dependencies...
pip install -e . --quiet
if !errorlevel! neq 0 (
    echo [X] Installation failed
    pause
    exit /b 1
)
echo [✓] Dependencies installed
echo.

echo [3/5] Starting Docker services...
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant
echo [✓] Services started
timeout /t 10 >nul
echo.

echo [4/5] Running database migrations...
docker exec -i athar-postgres psql -U athar -d athar_db < migrations/001_initial_schema.sql >nul 2>&1
echo [✓] Migrations complete
echo.

echo [5/5] Processing sample data...
python scripts/complete_ingestion.py --books 50 --hadith 500
echo.

echo ============================================================
echo ✓ Setup Complete!
echo ============================================================
echo.
echo Next: build.bat start
echo.
pause
goto :eof

:start
echo.
echo ============================================================
echo 🚀 Starting Athar Application
echo ============================================================
echo.

echo [1/3] Checking Docker services...
call :check_docker
echo.

echo [2/3] Starting Backend API...
start "Athar API" cmd /k "uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 >nul
echo [✓] API starting on port 8000
echo.

echo [3/3] Starting Frontend...
cd frontend
start "Athar Frontend" cmd /k "npm run dev"
cd ..
timeout /t 5 >nul
echo [✓] Frontend starting on port 3000
echo.

echo ============================================================
echo ✓ Application Starting!
echo ============================================================
echo.
echo Services:
echo   • API:        http://localhost:8000
echo   • API Docs:   http://localhost:8000/docs
echo   • Frontend:   http://localhost:3000
echo.
echo Opening API docs in 5 seconds...
timeout /t 5 >nul
start http://localhost:8000/docs
echo.
pause
goto :eof

:start_api
echo.
echo Starting Backend API only...
start "Athar API" cmd /k "uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
start http://localhost:8000/docs
goto :eof

:start_frontend
echo.
echo Starting Frontend only...
cd frontend
start "Athar Frontend" cmd /k "npm run dev"
cd ..
goto :eof

:stop
echo.
echo 🛑 Stopping all services...
docker compose -f docker/docker-compose.dev.yml down
echo ✓ Services stopped
pause
goto :eof

:restart
call :stop
call :start
goto :eof

:test
echo.
echo ============================================================
echo 🧪 Running Test Suite
echo ============================================================
echo.

echo [1/2] Testing API endpoints...
call build.bat test:api
echo.

echo [2/2] Running unit tests...
call build.bat test:unit
echo.

echo ✓ Tests complete
pause
goto :eof

:test_api
echo.
echo Testing API endpoints...
python scripts/test_api.py
pause
goto :eof

:test_unit
echo.
echo Running Python unit tests...
pytest tests/ -v --tb=short
pause
goto :eof

:status
echo.
echo ============================================================
echo 📊 Athar Service Status
echo ============================================================
echo.

echo Docker Services:
docker compose -f docker/docker-compose.dev.yml ps
echo.

echo Database:
docker exec athar-postgres psql -U athar -d athar_db -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';" 2>nul
echo.

call build.bat data:status
echo.
pause
goto :eof

:logs
echo.
echo Showing logs for: %OPTION%
echo (Press Ctrl+C to stop)
echo.

if "%OPTION%"=="" (
    docker compose -f docker/docker-compose.dev.yml logs -f
) else (
    docker compose -f docker/docker-compose.dev.yml logs -f %OPTION%
)
goto :eof

:clean
echo.
echo 🧹 Cleaning build artifacts...

if exist "__pycache__" rmdir /s /q "__pycache__"
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
if exist ".ruff_cache" rmdir /s /q ".ruff_cache"

echo ✓ Cleaned Python cache

if exist "frontend\.next" rmdir /s /q "frontend\.next"
if exist "frontend\node_modules" (
    echo [i] Frontend node_modules exists (skipping)
) else (
    echo ✓ Frontend clean
)

echo ✓ Clean complete
pause
goto :eof

:reset
echo.
echo ⚠️  WARNING: This will delete all data!
echo.
set /p confirm="Are you sure? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cancelled
    pause
    goto :eof
)

echo.
echo Stopping services...
docker compose -f docker/docker-compose.dev.yml down -v
echo.
echo Cleaning artifacts...
call :clean
echo.
echo ✓ Reset complete
echo.
echo To start fresh: build.bat setup
pause
goto :eof

:data_ingest
echo.
echo 📥 Data Ingestion
echo.
echo Options:
echo   1. Quick (50 books + 500 hadith) - 2 min
echo   2. Recommended (100 books + 1000 hadith) - 5 min
echo   3. Full (500 books + 5000 hadith) - 20 min
echo.
set /p opt="Select (1/2/3): "

if "!opt!"=="1" (
    python scripts/complete_ingestion.py --books 50 --hadith 500
) else if "!opt!"=="2" (
    python scripts/complete_ingestion.py --books 100 --hadith 1000
) else if "!opt!"=="3" (
    python scripts/complete_ingestion.py --books 500 --hadith 5000
) else (
    echo [X] Invalid option
)
pause
goto :eof

:data_embed
echo.
echo 🔢 Generating Embeddings
echo.
echo This requires Qwen3-Embedding model (~1GB download first time)
echo GPU recommended for fast processing
echo.
set /p count="Number of chunks to embed (default 1000): "
if "!count!"=="" set count=1000

python scripts/generate_embeddings.py --collection fiqh_passages --limit !count!
pause
goto :eof

:data_quran
echo.
echo 📖 Seeding Quran Database
echo.
python scripts/seed_quran_data.py --sample
pause
goto :eof

:data_status
echo.
echo 📊 Data Statistics
echo.

if exist "data\processed\all_chunks.json" (
    for %%F in ("data\processed\all_chunks.json") do (
        echo Processed chunks: %%~zF bytes
    )
) else (
    echo No processed data found
)
echo.
goto :eof

:db_migrate
echo.
echo 🗄️  Running Database Migrations
echo.

if exist "migrations\001_initial_schema.sql" (
    docker exec -i athar-postgres psql -U athar -d athar_db < migrations/001_initial_schema.sql
    echo [✓] Migration 001 complete
)

if exist "migrations\versions\002_quran_translations_tafsir.sql" (
    docker exec -i athar-postgres psql -U athar -d athar_db < migrations\versions\002_quran_translations_tafsir.sql
    echo [✓] Migration 002 complete
)
echo.
pause
goto :eof

:db_shell
echo.
echo 🗄️  Opening PostgreSQL Shell
echo.
docker exec -it athar-postgres psql -U athar -d athar_db
goto :eof

:db_backup
echo.
echo 💾 Backing up Database
echo.

set BACKUP_DIR=data\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set BACKUP_FILE=%BACKUP_DIR%\athar_backup_%date:~-4%%date:~3,2%%date:~0,2%.sql
docker exec athar-postgres pg_dump -U athar athar_db > "%BACKUP_FILE%"
echo [✓] Backup saved to: %BACKUP_FILE%
pause
goto :eof

:docker_prune
echo.
echo 🐳 Cleaning Docker Resources
echo.

echo Removing stopped containers...
docker container prune -f >nul

echo Removing unused images...
docker image prune -f >nul

echo Removing unused volumes...
docker volume prune -f >nul

echo ✓ Docker clean complete
pause
goto :eof

:check_docker
docker compose -f docker/docker-compose.dev.yml ps | findstr "healthy" >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Services not running. Starting...
    docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant
    timeout /t 10 >nul
    echo [✓] Services started
) else (
    echo [✓] Services running
)
goto :eof

:help
echo.
echo ============================================================
echo  Athar Islamic QA System - Build System
echo ============================================================
echo.
echo Usage: build.bat [command]
echo.
echo Commands:
echo   setup              Full initial setup
echo   start              Start all services
echo   start:api          Start API only
echo   start:frontend     Start Frontend only
echo   stop               Stop all services
echo   restart            Restart all services
echo   test               Run all tests
echo   test:api           Test API endpoints
echo   test:unit          Run unit tests
echo   status             Check service status
echo   logs [service]     View logs
echo   clean              Clean build artifacts
echo   reset              Full reset (WARNING: deletes data)
echo   data:ingest        Process books and hadith
echo   data:embed         Generate embeddings
echo   data:quran         Seed Quran database
echo   data:status        Show data statistics
echo   db:migrate         Run database migrations
echo   db:shell           Open PostgreSQL shell
echo   db:backup          Backup database
echo   docker:prune       Remove unused Docker resources
echo   help               Show this help
echo   menu               Interactive menu
echo.
echo Examples:
echo   build.bat setup            # First time setup
echo   build.bat start            # Start application
echo   build.bat logs api         # View API logs
echo   build.bat data:ingest      # Process more data
echo.
goto :eof
