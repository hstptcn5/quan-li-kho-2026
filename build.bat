@echo off
echo ========================================
echo    BUILDING QUAN LY KHO APPLICATION
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo.
echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Locating pyzbar package...
set PYZBAR_DIR=
for /f "delims=" %%i in ('python -c "import os, pyzbar; print(os.path.dirname(pyzbar.__file__))" 2^>nul') do set PYZBAR_DIR=%%i

if "%PYZBAR_DIR%"=="" (
    echo ERROR: Could not locate pyzbar package directory.
    pause
    exit /b 1
)
echo PyZbar package located at: %PYZBAR_DIR%

echo.
echo Building main application...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="QuanLyKho" ^
    --add-data="thuoc.csv;." ^
    --add-data="%PYZBAR_DIR%;pyzbar" ^
    --hidden-import=pandas ^
    --hidden-import=matplotlib ^
    --hidden-import=cv2 ^
    --hidden-import=pyzbar ^
    --hidden-import=reportlab ^
    --hidden-import=ttkbootstrap ^
    --hidden-import=cryptography ^
    --hidden-import=schedule ^
    --hidden-import=PIL ^
    --hidden-import=openpyxl ^
    --hidden-import=qrcode ^
    --distpath="dist" ^
    --workpath="build" ^
    nhathuoc2.py

if errorlevel 1 (
    echo ERROR: Failed to build main application
    pause
    exit /b 1
)

echo.
echo Building License Generator...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="LicenseGenerator" ^
    --hidden-import=cryptography ^
    --distpath="dist" ^
    --workpath="build" ^
    license_generator.py

if errorlevel 1 (
    echo WARNING: Failed to build License Generator
)

echo.
echo Building Key Creator...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="KeyCreator" ^
    --hidden-import=cryptography ^
    --distpath="dist" ^
    --workpath="build" ^
    create_keys.py

if errorlevel 1 (
    echo WARNING: Failed to build Key Creator
)

echo.
echo Creating documentation folder...
if not exist "dist\docs" mkdir "dist\docs"
copy "HUONG_DAN_SU_DUNG.md" "dist\docs\"
copy "BARCODE_SETUP.md" "dist\docs\"
copy "EXPORT_REPORTS.md" "dist\docs\"
copy "README_LICENSE.md" "dist\docs\"

echo.
echo Creating README for distribution...
echo Quan Ly Kho - Pharmacy Management System > "dist\README.txt"
echo Version 1.0.0 >> "dist\README.txt"
echo. >> "dist\README.txt"
echo Installation: >> "dist\README.txt"
echo 1. Run QuanLyKho.exe to start the application >> "dist\README.txt"
echo 2. For license activation, contact: hstptcn5@gmail.com >> "dist\README.txt"
echo. >> "dist\README.txt"
echo Tools included: >> "dist\README.txt"
echo - LicenseGenerator.exe: Create licenses for customers >> "dist\README.txt"
echo - KeyCreator.exe: Generate key pairs >> "dist\README.txt"
echo. >> "dist\README.txt"
echo Documentation: See docs folder >> "dist\README.txt"

echo.
echo Cleaning up...
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo.
echo ========================================
echo    BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Output files in 'dist' folder:
dir /b dist
echo.
echo You can now distribute the 'dist' folder.
echo.
pause
