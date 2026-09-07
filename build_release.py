# -*- coding: utf-8 -*-
"""Deterministic Windows release builder for QuanLyKho.

Used by both build.bat and GitHub Actions so local and CI packaging follow the
same fail-closed checks for required assets and barcode DLLs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from config import APP_VERSION, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
APP_DIST = DIST_ROOT / "QuanLyKho"
WORK_ROOT = ROOT / "build"
TEMP_DLL_DIR = ROOT / "_pyzbar_dlls"
REQUIRED_DLLS = ("libzbar-64.dll", "libiconv.dll")


def _require(path: Path, label: str) -> Path:
    if not path.exists():
        raise RuntimeError(f"Thiếu {label}: {path}")
    return path


def _find_pyzbar_dir() -> Path:
    import pyzbar

    package_dir = Path(pyzbar.__file__).resolve().parent
    for name in REQUIRED_DLLS:
        _require(package_dir / name, f"barcode DLL {name}")
    return package_dir


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _find_bundled_file(name: str) -> Path | None:
    candidates = [
        APP_DIST / name,
        APP_DIST / "_internal" / name,
        APP_DIST / "pyzbar" / name,
        APP_DIST / "_internal" / "pyzbar" / name,
    ]
    return next((path for path in candidates if path.is_file()), None)


def _write_distribution_files() -> None:
    docs_target = APP_DIST / "docs"
    static_target = APP_DIST / "static"
    shutil.copytree(ROOT / "docs", docs_target, dirs_exist_ok=True)
    shutil.copytree(ROOT / "static", static_target, dirs_exist_ok=True)

    for name in ("HUONG_DAN_SU_DUNG.md", "BARCODE_SETUP.md", "EXPORT_REPORTS.md", "UAT_CHECKLIST.md"):
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, docs_target / name)

    readme = (
        "Quan ly XNT thuoc, vaccine va VTYT (CDC)\n"
        f"Phien ban {APP_VERSION}\n\n"
        "Khoi chay: QuanLyKho.exe\n"
        "Khi chuyen sang may khac, sao chep NGUYEN thu muc QuanLyKho.\n"
        "Du lieu nguoi dung duoc luu trong LOCALAPPDATA\\QuanLyXNT.\n"
        "Tai lieu: thu muc docs.\n"
    )
    (APP_DIST / "README.txt").write_text(readme, encoding="utf-8")

    release_info = {
        "app": "QuanLyKho",
        "app_version": APP_VERSION,
        "schema_version": SCHEMA_VERSION,
        "python": sys.version.split()[0],
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": os.environ.get("GITHUB_SHA", "local"),
    }
    (APP_DIST / "RELEASE_INFO.json").write_text(
        json.dumps(release_info, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _validate_distribution() -> None:
    _require(APP_DIST / "QuanLyKho.exe", "executable")
    _require(APP_DIST / "docs" / "index.html", "offline documentation")
    _require(APP_DIST / "static" / "html5-qrcode.min.js", "offline QR asset")

    internal_qr = APP_DIST / "_internal" / "static" / "html5-qrcode.min.js"
    _require(internal_qr, "bundled runtime QR asset")

    for name in REQUIRED_DLLS:
        found = _find_bundled_file(name)
        if found is None:
            raise RuntimeError(f"Barcode DLL không có trong release bundle: {name}")


def _write_hash_manifest() -> None:
    manifest = APP_DIST / "SHA256SUMS.txt"
    lines = []
    for path in sorted(APP_DIST.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file() or path == manifest:
            continue
        rel = path.relative_to(APP_DIST).as_posix()
        lines.append(f"{_sha256(path)}  {rel}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_release() -> Path:
    if os.name != "nt":
        raise RuntimeError("Release QuanLyKho hiện chỉ hỗ trợ build trên Windows")

    _require(ROOT / "quanly_xnt.py", "entrypoint")
    _require(ROOT / "thuoc.csv", "medicine catalog")
    _require(ROOT / "static" / "html5-qrcode.min.js", "offline QR asset")
    _require(ROOT / "docs" / "index.html", "offline documentation")

    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("PyInstaller chưa được cài đặt trong môi trường build") from exc

    pyzbar_dir = _find_pyzbar_dir()

    shutil.rmtree(DIST_ROOT, ignore_errors=True)
    shutil.rmtree(WORK_ROOT, ignore_errors=True)
    shutil.rmtree(TEMP_DLL_DIR, ignore_errors=True)
    TEMP_DLL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        for name in REQUIRED_DLLS:
            shutil.copy2(pyzbar_dir / name, TEMP_DLL_DIR / name)

        sep = ";" if os.name == "nt" else ":"
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--console",
            "--noupx",
            "--name=QuanLyKho",
            f"--add-data={ROOT / 'thuoc.csv'}{sep}.",
            f"--add-data={ROOT / 'static'}{sep}static",
            f"--add-data={ROOT / 'docs'}{sep}docs",
            f"--add-data={pyzbar_dir}{sep}pyzbar",
        ]
        for name in REQUIRED_DLLS:
            command.extend(
                [
                    f"--add-binary={TEMP_DLL_DIR / name}{sep}.",
                    f"--add-binary={TEMP_DLL_DIR / name}{sep}pyzbar",
                ]
            )
        for hidden in (
            "pandas", "matplotlib", "cv2", "pyzbar", "reportlab", "ttkbootstrap",
            "schedule", "PIL", "openpyxl", "qrcode",
        ):
            command.append(f"--hidden-import={hidden}")
        command.extend(
            [
                f"--distpath={DIST_ROOT}",
                f"--workpath={WORK_ROOT}",
                str(ROOT / "quanly_xnt.py"),
            ]
        )

        print("Building release candidate with:", sys.executable)
        subprocess.run(command, cwd=ROOT, check=True)
        _write_distribution_files()
        _validate_distribution()
        _write_hash_manifest()
        print(f"Release candidate ready: {APP_DIST}")
        return APP_DIST
    finally:
        shutil.rmtree(TEMP_DLL_DIR, ignore_errors=True)
        # PyInstaller writes the .spec next to the entrypoint unless --specpath is set.
        spec = ROOT / "QuanLyKho.spec"
        if spec.exists():
            spec.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="CI marker; behavior remains deterministic")
    parser.parse_args()
    try:
        build_release()
        return 0
    except Exception as exc:
        print(f"RELEASE BUILD FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
