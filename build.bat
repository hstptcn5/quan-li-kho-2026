@echo off
echo ========================================
echo    BUILDING QUAN LY KHO APPLICATION
echo ========================================
echo.

REM Check if Python is installed
set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    echo Creating Python 3.10 virtual environment...
    py -3.10 -m venv .venv
)

"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 virtual environment is not available
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
"%PYTHON_EXE%" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    "%PYTHON_EXE%" -m pip install pyinstaller==6.6.0
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
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Locating pyzbar package...
set PYZBAR_DIR=
for /f "delims=" %%i in ('%PYTHON_EXE% -c "import os, pyzbar; print(os.path.dirname(pyzbar.__file__))" 2^>nul') do set PYZBAR_DIR=%%i

if "%PYZBAR_DIR%"=="" (
    echo ERROR: Could not locate pyzbar package directory.
    pause
    exit /b 1
)
echo PyZbar package located at: %PYZBAR_DIR%

echo.
echo Building main application...

REM Copy DLLs ra thu muc tam de add-binary vao root cua bundle
echo Copying pyzbar DLLs to temp directory...
if not exist "_pyzbar_dlls" mkdir "_pyzbar_dlls"
copy "%PYZBAR_DIR%\libzbar-64.dll" "_pyzbar_dlls\" >nul 2>&1
copy "%PYZBAR_DIR%\libiconv.dll" "_pyzbar_dlls\" >nul 2>&1
if not exist "_pyzbar_dlls\libzbar-64.dll" (
    echo WARNING: libzbar-64.dll was not found. App will still run, but camera barcode scanning may be disabled.
)
if not exist "_pyzbar_dlls\libiconv.dll" (
    echo WARNING: libiconv.dll was not found. App will still run, but camera barcode scanning may be disabled.
)

"%PYTHON_EXE%" -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name="QuanLyKho" ^
    --add-data="thuoc.csv;." ^
    --add-data="static;static" ^
    --add-data="docs;docs" ^
    --add-data="%PYZBAR_DIR%;pyzbar" ^
    --add-binary="_pyzbar_dlls\libzbar-64.dll;." ^
    --add-binary="_pyzbar_dlls\libiconv.dll;." ^
    --add-binary="_pyzbar_dlls\libzbar-64.dll;pyzbar" ^
    --add-binary="_pyzbar_dlls\libiconv.dll;pyzbar" ^
    --hidden-import=pandas ^
    --hidden-import=matplotlib ^
    --hidden-import=cv2 ^
    --hidden-import=pyzbar ^
    --hidden-import=reportlab ^
    --hidden-import=ttkbootstrap ^
    --hidden-import=schedule ^
    --hidden-import=PIL ^
    --hidden-import=openpyxl ^
    --hidden-import=qrcode ^
    --distpath="dist" ^
    --workpath="build" ^
    quanly_xnt.py

REM Cleanup temp DLL folder
if exist "_pyzbar_dlls" rmdir /s /q "_pyzbar_dlls"

if errorlevel 1 (
    echo ERROR: Failed to build main application
    pause
    exit /b 1
)

echo.
echo Creating documentation folder...
if not exist "dist\docs" mkdir "dist\docs"
if exist "docs" xcopy /E /I /Y "docs" "dist\docs" >nul
copy "HUONG_DAN_SU_DUNG.md" "dist\docs\"
copy "BARCODE_SETUP.md" "dist\docs\"
copy "EXPORT_REPORTS.md" "dist\docs\"

echo.
echo Creating README for distribution...
echo Quần lý XNT thuốc, vaccine và VTYT (CDC) > "dist\README.txt"
echo Phiên bản 2.0.0 >> "dist\README.txt"
echo. >> "dist\README.txt"
echo Cách khởi chạy: >> "dist\README.txt"
echo 1. Chạy file QuanLyKho.exe để khởi chạy phần mềm >> "dist\README.txt"
echo. >> "dist\README.txt"
echo Tài liệu hướng dẫn: Xem chi tiết trong thư mục docs >> "dist\README.txt"

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
