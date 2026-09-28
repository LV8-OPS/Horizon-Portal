@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [1/5] Checking project folders...
if not exist app mkdir app
if not exist templates mkdir templates
if not exist static mkdir static
if not exist static\img mkdir static\img

if not exist requirements.txt (
  echo requirements.txt not found.
  pause
  exit /b 1
)

if not exist venv (
  echo [2/5] Creating virtual environment...
  py -m venv venv
)

echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
  echo Failed to activate venv.
  pause
  exit /b 1
)

echo [4/5] Installing/updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo [5/5] Starting Horizon Portal server...
start "Horizon Portal" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo Server started on http://127.0.0.1:8000
endlocal
