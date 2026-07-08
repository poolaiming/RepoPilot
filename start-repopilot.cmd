@echo off
setlocal

cd /d "%~dp0"

if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv || exit /b 1
)

if not exist ".venv\.deps-installed" (
  echo Installing dependencies...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
  type nul > ".venv\.deps-installed"
)

echo.
echo RepoPilot: http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env
