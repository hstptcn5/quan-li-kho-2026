# -*- coding: utf-8 -*-
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "dist" / "QuanLyKho"

REQUIRED_PATHS = [
    RELEASE_DIR / "QuanLyKho.exe",
    RELEASE_DIR / "README.txt",
    RELEASE_DIR / "docs" / "index.html",
    RELEASE_DIR / "static" / "html5-qrcode.min.js",
    RELEASE_DIR / "_internal" / "pyzbar" / "libzbar-64.dll",
    RELEASE_DIR / "_internal" / "pyzbar" / "libiconv.dll",
]


def main():
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        for path in missing:
            print(f"MISSING: {path}")
        return 1

    exe = RELEASE_DIR / "QuanLyKho.exe"
    if exe.stat().st_size < 1024 * 1024:
        print(f"INVALID: {exe} is unexpectedly small")
        return 1

    qr = RELEASE_DIR / "static" / "html5-qrcode.min.js"
    if qr.stat().st_size < 100_000:
        print(f"INVALID: {qr} is unexpectedly small")
        return 1

    print("Release artifact check passed")
    print(f"Release directory: {RELEASE_DIR}")
    print(f"Executable size: {exe.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
