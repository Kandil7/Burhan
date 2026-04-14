@echo off
setlocal enabledelayedexpansion
REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  ATHAR - Download Embeddings from HuggingFace & Upload to Qdrant
REM ═══════════════════════════════════════════════════════════════════════
REM
REM This script downloads embeddings from HuggingFace and uploads to Qdrant.
REM Smart features:
REM   - Checks existing Qdrant data first
REM   - Only downloads what's missing (incremental sync)
REM   - Shows sync plan before execution
REM   - Supports --verify-only, --dry-run, --force options
REM
REM Prerequisites:
REM   - Qdrant running on localhost:6333
REM   - HF_TOKEN configured in .env
REM   - Poetry environment set up
REM
REM Usage:
REM   download-embeddings-to-qdrant.bat           (smart sync - only what's missing)
REM   download-embeddings-to-qdrant.bat --verify-only   (just check Qdrant)
REM   download-embeddings-to-qdrant.bat --force         (reupload everything)
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🕌  ATHAR - Smart Embeddings Sync
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Check Qdrant is running
echo [1/4] Checking Qdrant connection...
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
echo [2/4] Checking HuggingFace token...
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

REM Parse command line arguments
set "ARGS=%*"
if "%ARGS%"=="" (
    set "PYTHON_ARGS=--dry-run"
    set "MODE=Smart Sync (Dry Run)"
) else (
    set "PYTHON_ARGS=%ARGS%"
    set "MODE=Custom Mode"
)

REM Check the upload script exists
echo [3/4] Checking upload script...
if not exist "scripts\download_embeddings_and_upload_qdrant.py" (
    echo ❌ Upload script not found: scripts\download_embeddings_and_upload_qdrant.py
    echo.
    pause
    exit /b 1
)
echo ✅ Script found
echo.

REM Run the script
echo [4/4] Running sync...
echo ═══════════════════════════════════════════════════════════════════════
echo Mode: %MODE%
echo Arguments: %PYTHON_ARGS%
echo ═══════════════════════════════════════════════════════════════════════
echo.

poetry run python scripts/download_embeddings_and_upload_qdrant.py %PYTHON_ARGS%
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