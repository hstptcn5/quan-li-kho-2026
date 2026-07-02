#!/bin/bash

echo "========================================"
echo "   BUILDING QUAN LY KHO APPLICATION"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed"
    exit 1
fi

# Check if PyInstaller is installed
if ! pip3 show pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
fi

echo
echo "Cleaning previous builds..."
rm -rf dist build *.spec

echo
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo
echo "Locating pyzbar package..."
PYZBAR_DIR=$(python3 -c "import os, pyzbar; print(os.path.dirname(pyzbar.__file__))" 2>/dev/null)
if [ -z "$PYZBAR_DIR" ]; then
    echo "ERROR: Could not locate pyzbar package directory."
    exit 1
fi
echo "PyZbar package located at: $PYZBAR_DIR"

echo
echo "Building main application..."
pyinstaller \
    --onefile \
    --windowed \
    --name="QuanLyKho" \
    --add-data="thuoc.csv:." \
    --add-data="${PYZBAR_DIR}:pyzbar" \
    --hidden-import=pandas \
    --hidden-import=matplotlib \
    --hidden-import=cv2 \
    --hidden-import=pyzbar \
    --hidden-import=reportlab \
    --hidden-import=ttkbootstrap \
    --hidden-import=cryptography \
    --hidden-import=schedule \
    --hidden-import=PIL \
    --hidden-import=openpyxl \
    --hidden-import=qrcode \
    --distpath="dist" \
    --workpath="build" \
    nhathuoc2.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build main application"
    exit 1
fi

echo
echo "Creating documentation folder..."
mkdir -p dist/docs
cp HUONG_DAN_SU_DUNG.md dist/docs/
cp BARCODE_SETUP.md dist/docs/
cp EXPORT_REPORTS.md dist/docs/

echo
echo "Creating README for distribution..."
cat > dist/README.txt << EOF
Quan Ly Kho - CDC Management System
Version 2.0.0

Installation:
1. Run QuanLyKho to start the application

Documentation: See docs folder
EOF

echo
echo "Setting executable permissions..."
chmod +x dist/QuanLyKho

echo
echo "Cleaning up..."
rm -rf build *.spec

echo
echo "========================================"
echo "   BUILD COMPLETED SUCCESSFULLY!"
echo "========================================"
echo
echo "Output files in 'dist' folder:"
ls -la dist/
echo
echo "You can now distribute the 'dist' folder."
echo
