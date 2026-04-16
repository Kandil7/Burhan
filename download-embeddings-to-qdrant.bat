@echo off
setlocal enabledelayedexpansion

REM ═══════════════════════════════════════════════════════════════════════
REM 🕌  ATHAR - Download Embeddings from HuggingFace & Upload to Qdrant
REM ═══════════════════════════════════════════════════════════════════════
REM Usage:
REM   download-embeddings-to-qdrant.bat               (smart sync)
REM   download-embeddings-to-qdrant.bat --dry-run     (show plan, no upload)
REM   download-embeddings-to-qdrant.bat --verify-only (check Qdrant state)
REM   download-embeddings-to-qdrant.bat --force       (reupload everything)
REM   download-embeddings-to-qdrant.bat --help        (show this message)
REM ═══════════════════════════════════════════════════════════════════════

set "SCRIPT=scripts\download_embeddings_and_upload_qdrant.py"
set "QDRANT_URL=http://localhost:6333"
set "PYTHON_ARGS="
set "MODE=Smart Sync"

REM ─── Handle --help ──────────────────────────────────────────────────────
for %%A in (%*) do (
    if /I "%%A"=="--help" (
        type "%~f0" | findstr /R "^REM"
        exit /b 0
    )
)

REM ─── Collect arguments & set mode label ─────────────────────────────────
set "HAS_FORCE=0"
set "HAS_VERIFY=0"
set "HAS_DRY=0"

for %%A in (%*) do (
    if /I "%%A"=="--force"       set "HAS_FORCE=1"
    if /I "%%A"=="--verify-only" set "HAS_VERIFY=1"
    if /I "%%A"=="--dry-run"     set "HAS_DRY=1"
    set "PYTHON_ARGS=!PYTHON_ARGS! %%A"
)

REM Default: smart sync (no extra flags)
if "%PYTHON_ARGS%"=="" set "MODE=Smart Sync (incremental)"
if "!HAS_DRY!"==1      set "MODE=Dry Run (plan only)"
if "!HAS_VERIFY!"==1   set "MODE=Verify Only"
if "!HAS_FORCE!"==1    set "MODE=Force Re-upload"

REM ─── Header ─────────────────────────────────────────────────────────────
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo 🕌  ATHAR - Smart Embeddings Sync  ^|  %DATE% %TIME%
echo    Mode: %MODE%
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM ─── [1/4] Qdrant connectivity ──────────────────────────────────────────
echo [1/4] Checking Qdrant on %QDRANT_URL% ...
powershell -NoProfile -Command ^
  "try { $r=Invoke-WebRequest '%QDRANT_URL%/healthz' -UseBasicParsing -TimeoutSec 5 -EA Stop; exit 0 } catch { exit 1 }"
if !ERRORLEVEL! neq 0 (
    echo.
    echo  ❌  Qdrant is NOT reachable at %QDRANT_URL%
    echo.
    echo  Start it with:
    echo      docker compose -f docker/docker-compose.dev.yml up -d qdrant
    echo.
    pause & exit /b 1
)
echo  ✅  Qdrant is running
echo.

REM ─── [2/4] HF_TOKEN in .env ─────────────────────────────────────────────
echo [2/4] Checking HuggingFace token ...

if not exist ".env" (
    echo.
    echo  ❌  .env not found. Copy .env.example and set HF_TOKEN.
    echo.
    pause & exit /b 1
)

REM Extract the value of HF_TOKEN (strips quotes, ignores comments/blanks)
set "HF_TOKEN_VAL="
for /f "usebackq tokens=1,* delims==" %%K in (`findstr /B /I "HF_TOKEN=" .env`) do (
    set "_key=%%K"
    set "_val=%%L"
    REM Skip comment lines
    if "!_key:~0,1!" neq "#" (
        REM Strip surrounding quotes
        set "_val=!_val:"=!"
        if not "!_val!"=="" if not "!_val!"=="your_token_here" if not "!_val:~0,5!"=="hf_TO" (
            set "HF_TOKEN_VAL=!_val!"
        ) else if "!_val:~0,3!"=="hf_" (
            set "HF_TOKEN_VAL=!_val!"
        )
    )
)

if "!HF_TOKEN_VAL!"=="" (
    echo.
    echo  ❌  HF_TOKEN is missing or unconfigured in .env
    echo      Get a token at: https://huggingface.co/settings/tokens
    echo      Then set in .env: HF_TOKEN=hf_xxxxxxxxxxxx
    echo.
    pause & exit /b 1
)
echo  ✅  HF_TOKEN found ^(hf_****%HF_TOKEN_VAL:~-4%^)
echo.

REM ─── [3/4] Check Poetry and script ─────────────────────────────────────
echo [3/4] Checking environment ...

where poetry >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo.
    echo  ❌  Poetry not found in PATH.
    echo      Install from: https://python-poetry.org/docs/
    echo.
    pause & exit /b 1
)
echo  ✅  Poetry found

if not exist "%SCRIPT%" (
    echo.
    echo  ❌  Script not found: %SCRIPT%
    echo.
    pause & exit /b 1
)
echo  ✅  Script found: %SCRIPT%
echo.

REM ─── [4/4] Execute ──────────────────────────────────────────────────────
echo [4/4] Running sync ...
echo ═══════════════════════════════════════════════════════════════════════
echo.

poetry run python "%SCRIPT%" %PYTHON_ARGS%
set "RESULT=!ERRORLEVEL!"

echo.
echo ═══════════════════════════════════════════════════════════════════════
if !RESULT! equ 0 (
    echo  ✅  Sync complete  ^|  %TIME%
) else (
    echo  ❌  Failed with exit code !RESULT!
    echo      Check the output above for details.
)
echo ═══════════════════════════════════════════════════════════════════════
echo.
pause
exit /b !RESULT!