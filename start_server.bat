@echo off
REM Start Burhan API server in background
cd /d K:\business\projects_v2\Burhan
call poetry run uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --log-level error