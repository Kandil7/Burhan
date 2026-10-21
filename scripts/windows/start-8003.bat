@echo off
cd /d K:\business\projects_v2\Burhan
poetry run python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8003