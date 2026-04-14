@echo off
setlocal enabledelayedexpansion
REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  ATHAR - Download Embeddings from HuggingFace & Upload to Qdrant
REM ═══════════════════════════════════════════════════════════════════════
REM
REM This script downloads 5.7M embeddings from HuggingFace and uploads
REM them to your local Qdrant instance.
REM
REM Prerequisites:
REM   - Qdrant running on localhost:6333
REM   - HF_TOKEN configured in .env
REM   - Poetry environment set up
REM
REM Usage: Double-click or run: download-embeddings-to-qdrant.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🕌  ATHAR - Download Embeddings & Upload to Qdrant
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Check Qdrant is running using PowerShell
echo [1/3] Checking Qdrant connection...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:6333/collections' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if !ERRORLEVEL! neq 0 (
    echo ❌ Qdrant is NOT running on localhost:6333
    echo.
    echo Start Qdrant first:
    echo   docker compose -f docker/docker-compose.dev.yml up -d qdrant
    echo.
    pause
    exit /b 1
)
echo ✅ Qdrant is running
echo.

REM Check HF_TOKEN exists in .env
echo [2/3] Checking HuggingFace token...
if not exist ".env" (
    echo ❌ .env file not found!
    echo    Copy .env.example to .env and configure HF_TOKEN
    echo.
    pause
    exit /b 1
)

findstr "HF_TOKEN=" .env | findstr /V "HF_TOKEN=$" | findstr /V "HF_TOKEN=your" >nul
if !ERRORLEVEL! neq 0 (
    echo ❌ HF_TOKEN not configured in .env
    echo.
    echo Get token from: https://huggingface.co/settings/tokens
    echo Then add to .env: HF_TOKEN=hf_your_token_here
    echo.
    pause
    exit /b 1
)
echo ✅ HF_TOKEN configured
echo.

REM Check the upload script exists
if not exist "scripts\download_embeddings_and_upload_qdrant.py" (
    echo ❌ Upload script not found: scripts\download_embeddings_and_upload_qdrant.py
    echo.
    pause
    exit /b 1
)

REM Run the download and upload script
echo [3/3] Starting download and upload...
echo ═══════════════════════════════════════════════════════════════════════
echo 🚀  This will:
echo   1. Download embedding files from HuggingFace (~20-30 GB)
echo   2. Upload vectors to Qdrant
echo   3. Verify all collections
echo.
echo Estimated time: 30-60 minutes (depends on internet speed)
echo ═══════════════════════════════════════════════════════════════════════
echo.

poetry run python scripts/download_embeddings_and_upload_qdrant.py
set RESULT=!ERRORLEVEL!

echo.
echo ═══════════════════════════════════════════════════════════════════════
if !RESULT! equ 0 (
    echo ✅ Complete!
) else (
    echo ❌ Failed with error code !RESULT!
)
echo ═══════════════════════════════════════════════════════════════════════
echo.
pause
