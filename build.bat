@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   BUILDING QUAN LY KHO RELEASE CANDIDATE
echo ========================================
echo.

set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    call setup.bat
    if errorlevel 1 exit /b 1
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

echo.
echo Building deterministic Windows release candidate...
"%PYTHON_EXE%" build_release.py
if errorlevel 1 (
    echo.
    echo ERROR: Release candidate build failed.
    echo See the error above. No release should be distributed from this build.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   RELEASE CANDIDATE BUILD COMPLETED
 echo ========================================
echo.
echo Output: dist\QuanLyKho
echo SHA-256 manifest: dist\QuanLyKho\SHA256SUMS.txt
echo.
dir /b "dist\QuanLyKho"
echo.
echo Before distribution, complete docs\RELEASE_CANDIDATE.md.
echo.
pause
endlocal
