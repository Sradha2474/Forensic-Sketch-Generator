@echo off
cd /d "%~dp0"
echo Starting Python SD worker at http://127.0.0.1:8000
echo Health check: http://127.0.0.1:8000/health
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
