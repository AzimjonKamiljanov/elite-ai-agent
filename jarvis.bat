@echo off
REM JARVIS Prime — Windows launcher
cd /d "%~dp0"

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python not found. Install Python 3.11+: https://www.python.org/downloads/
    exit /b 1
)

IF EXIST ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
) ELSE IF EXIST "runtime\venv\Scripts\python.exe" (
    call runtime\venv\Scripts\activate.bat
)

python -m apps.cli %*
