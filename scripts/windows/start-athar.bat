@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  Burhan - Start Everything Automatically
REM ═══════════════════════════════════════════════════════════════════════
REM
REM This script:
REM 1. Checks Docker Desktop is running
REM 2. Starts PostgreSQL, Qdrant, Redis
REM 3. Waits for services to be healthy
REM 4. Runs database migrations
REM 5. Starts API server on port 8002
REM
REM Usage: Double-click or run: start-Burhan.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🕌  Burhan - Islamic QA System
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Check Docker Desktop is running
echo [1/5] Checking Docker Desktop...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Docker Desktop is NOT running!
    echo.
    echo Please start Docker Desktop and try again.
    echo   - Press Windows key
    echo   - Type "Docker Desktop"
    echo   - Click to launch
    echo   - Wait for green whale icon
    echo.
    pause
    exit /b 1
)
echo ✅ Docker Desktop is running
echo.

REM Start infrastructure services
echo [2/5] Starting PostgreSQL, Qdrant, Redis...
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Failed to start Docker services
    pause
    exit /b 1
)
echo ✅ Services started
echo.

REM Wait for services to be healthy
echo [3/5] Waiting for services to initialize (30 seconds)...
timeout /t 30 /nobreak >nul

REM Verify services
echo Checking service health...
docker compose -f docker/docker-compose.dev.yml ps
echo.

REM Run database migrations
echo [4/5] Running database migrations...
poetry run alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo ⚠️  Migration failed (may be already up to date)
) else (
    echo ✅ Migrations complete
)
echo.

REM Check if GROQ_API_KEY is set
echo Checking configuration...
findstr "GROQ_API_KEY=" .env | findstr "your-groq-key-here" >nul
if %ERRORLEVEL% equ 0 (
    echo ⚠️  WARNING: GROQ_API_KEY not configured in .env
    echo    Get free key from: https://console.groq.com/
    echo    Then add to .env: GROQ_API_KEY=gsk_your_key_here
    echo.
)

REM Start API server
echo [5/5] Starting API server on port 8002...
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🚀  Burhan is starting!
echo.
echo 📖 API Docs: http://localhost:8002/docs
echo 💚 Health:    http://localhost:8002/health
echo.
echo Press Ctrl+C to stop the server
echo ═══════════════════════════════════════════════════════════════════════
echo.

poetry run python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload
