@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo    SETUP DEVELOPMENT ENVIRONMENT
echo ========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python Launcher ^(py.exe^) was not found.
    echo Install Python 3.10 from https://www.python.org/downloads/ and enable "py launcher".
    pause
    exit /b 1
)

py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 was not found.
    echo Install Python 3.10, then run setup.bat again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python 3.10 virtual environment...
    if exist ".venv" rmdir /s /q ".venv"
    py -3.10 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        if exist ".venv" rmdir /s /q ".venv"
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

copy /y "requirements.txt" ".venv\requirements.installed" >nul

echo.
echo Setup completed.
endlocal
