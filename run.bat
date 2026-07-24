@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python 3.10 virtual environment...
    py -3.10 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python 3.10 is required. Install Python 3.10 or update this script.
        pause
        exit /b 1
    )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo Starting Quan Ly Kho...
".venv\Scripts\python.exe" quanly_xnt.py

endlocal
