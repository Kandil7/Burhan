@echo off
setlocal enabledelayedexpansion
REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  Burhan - Stop All Services
REM ═══════════════════════════════════════════════════════════════════════
REM
REM This script stops all Docker services (PostgreSQL, Qdrant, Redis).
REM Data is preserved - volumes are NOT deleted.
REM
REM Usage: Double-click or run: stop-Burhan.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🛑  Burhan - Stopping All Services
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Check Docker is running
docker info >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo ❌ Docker Desktop is NOT running!
    echo    Services may already be stopped.
    echo.
    pause
    goto :eof
)

echo Stopping Docker services (PostgreSQL, Qdrant, Redis)...
docker compose -f docker/docker-compose.dev.yml down

echo.
if !ERRORLEVEL! equ 0 (
    echo ✅ All services stopped successfully
    echo.
    echo Data is preserved. To start again: start-Burhan.bat
) else (
    echo ⚠️  Some services may not have stopped cleanly
    echo    Check with: docker compose -f docker/docker-compose.dev.yml ps
)
echo.
pause
