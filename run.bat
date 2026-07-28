@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call setup.bat
    if errorlevel 1 (
        exit /b 1
    )
)

if not exist ".venv\requirements.installed" (
    call setup.bat
    if errorlevel 1 exit /b 1
) else (
    fc /b "requirements.txt" ".venv\requirements.installed" >nul
    if errorlevel 1 (
        call setup.bat
        if errorlevel 1 exit /b 1
    )
)

echo Starting Quan Ly Kho...
".venv\Scripts\python.exe" quanly_xnt.py

endlocal
