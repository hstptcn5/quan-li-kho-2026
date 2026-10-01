# -*- coding: utf-8 -*-
"""Build bản phát hành giao diện web: dist/QuanLyKhoWeb/ (PyInstaller onedir).

Tách khỏi build_release.py (bản Tkinter) để hai bản độc lập, dùng chung DB.
Thư viện chỉ dùng cho bản Tkinter (OpenCV, pandas, matplotlib, ...) bị loại khỏi bản web:
``config.py`` đã bọc việc import chúng trong try/except nên thiếu chúng vẫn chạy được.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
APP_DIST = DIST_ROOT / "QuanLyKhoWeb"
WORK_ROOT = ROOT / "build_web"
EXCLUDED_MODULES = (
    "cv2", "pyzbar", "matplotlib", "pandas", "numpy", "PIL", "reportlab",
    "openpyxl", "qrcode", "schedule", "ttkbootstrap", "tkinter",
)
REQUIRED_WEB_FILES = (
    "index.html",
    "css/tokens.css",
    "css/base.css",
    "css/components.css",
    "js/app.js",
    "js/vendor/htm-preact.js",
)


def _require(path: Path, label: str) -> Path:
    if not path.exists():
        raise RuntimeError(f"Thiếu {label}: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_command(python=None) -> list:
    command = [
        python or sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--console", "--noupx",
        "--name=QuanLyKhoWeb",
        f"--add-data={ROOT / 'web'}{os.pathsep}web",
    ]
    command += [f"--exclude-module={module}" for module in EXCLUDED_MODULES]
    command += [
        f"--distpath={DIST_ROOT}",
        f"--workpath={WORK_ROOT}",
        f"--specpath={WORK_ROOT}",
        str(ROOT / "quanly_web.py"),
    ]
    return command


def _validate_distribution() -> None:
    exe = _require(APP_DIST / "QuanLyKhoWeb.exe", "executable")
    if exe.stat().st_size < 1024 * 1024:
        raise RuntimeError(f"{exe} nhỏ bất thường")
    web_dir = APP_DIST / "_internal" / "web"
    for rel in REQUIRED_WEB_FILES:
        _require(web_dir / rel, f"web asset {rel}")


def _write_hash_manifest() -> None:
    manifest = APP_DIST / "SHA256SUMS.txt"
    lines = []
    for path in sorted(APP_DIST.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file() or path == manifest:
            continue
        lines.append(f"{_sha256(path)}  {path.relative_to(APP_DIST).as_posix()}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_release() -> Path:
    if os.name != "nt":
        raise RuntimeError("Release QuanLyKhoWeb hiện chỉ hỗ trợ build trên Windows")
    _require(ROOT / "quanly_web.py", "entrypoint")
    _require(ROOT / "web" / "index.html", "web UI")
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("PyInstaller chưa được cài đặt trong môi trường build") from exc
    try:
        import webview  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("pywebview chưa được cài đặt: chạy pip install -r requirements.txt") from exc

    shutil.rmtree(APP_DIST, ignore_errors=True)
    shutil.rmtree(WORK_ROOT, ignore_errors=True)
    print("Building web release candidate with:", sys.executable)
    subprocess.run(build_command(), cwd=ROOT, check=True)
    _validate_distribution()
    _write_hash_manifest()
    print(f"Web release candidate ready: {APP_DIST}")
    return APP_DIST


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="CI marker; behavior remains deterministic")
    parser.parse_args()
    try:
        build_release()
        return 0
    except Exception as exc:
        print(f"WEB RELEASE BUILD FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
