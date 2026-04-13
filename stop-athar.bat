@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  ATHAR - Stop All Services
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🛑  ATHAR - Stopping All Services
echo ═══════════════════════════════════════════════════════════════════════
echo.

echo Stopping Docker services...
docker compose -f docker/docker-compose.dev.yml down

echo.
echo ✅ All services stopped
echo.
pause
