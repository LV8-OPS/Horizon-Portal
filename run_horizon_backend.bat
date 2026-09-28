@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "PY=%VENV%\Scripts\python.exe"
set "REQ=%ROOT%requirements.txt"

cd /d "%ROOT%"

if not exist "%PY%" (
    py -m venv "%VENV%"
)

"%PY%" -m pip install --upgrade pip
if exist "%REQ%" (
    "%PY%" -m pip install -r "%REQ%"
) else (
    "%PY%" -m pip install fastapi uvicorn sqlalchemy pytest httpx
)

"%PY%" -m pytest
"%PY%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause
endlocal