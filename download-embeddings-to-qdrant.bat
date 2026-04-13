@echo off
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
REM
REM Usage: Double-click or run: download-embeddings-to-qdrant.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🕌  ATHAR - Download Embeddings & Upload to Qdrant
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Check Qdrant is running
echo [1/2] Checking Qdrant connection...
curl -s http://localhost:6333/collections >nul 2>&1
if %ERRORLEVEL% neq 0 (
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

REM Check HF_TOKEN
echo [2/2] Checking HuggingFace token...
findstr "HF_TOKEN=" .env | findstr "your-hf-token-here" >nul
if %ERRORLEVEL% equ 0 (
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

REM Run the download and upload script
echo ═══════════════════════════════════════════════════════════════════════
echo 🚀  Starting download and upload...
echo.
echo This will:
echo   1. Download 685 embedding files from HuggingFace (~20-30 GB)
echo   2. Upload 5.7M vectors to Qdrant
echo   3. Verify all collections
echo.
echo Estimated time: 30-60 minutes (depends on internet speed)
echo ═══════════════════════════════════════════════════════════════════════
echo.

poetry run python scripts/download_embeddings_and_upload_qdrant.py

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo ✅ Complete!
echo ═══════════════════════════════════════════════════════════════════════
echo.
pause
