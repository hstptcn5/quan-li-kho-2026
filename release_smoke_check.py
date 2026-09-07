# -*- coding: utf-8 -*-
"""Smoke-test the packaged Windows release candidate, not the source tree."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
APP_DIST = ROOT / "dist" / "QuanLyKho"
EXE = APP_DIST / "QuanLyKho.exe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest() -> None:
    manifest = APP_DIST / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise RuntimeError("Thiếu SHA256SUMS.txt")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = APP_DIST / Path(rel)
        if not path.is_file():
            raise RuntimeError(f"Manifest trỏ tới file bị thiếu: {rel}")
        actual = sha256(path)
        if actual.lower() != expected.lower():
            raise RuntimeError(f"SHA-256 mismatch: {rel}")


def find_dll_pair() -> tuple[Path, Path]:
    directories = [
        APP_DIST,
        APP_DIST / "_internal",
        APP_DIST / "pyzbar",
        APP_DIST / "_internal" / "pyzbar",
    ]
    for directory in directories:
        zbar = directory / "libzbar-64.dll"
        iconv = directory / "libiconv.dll"
        if zbar.is_file() and iconv.is_file():
            return zbar, iconv
    raise RuntimeError("Không tìm thấy cặp libzbar-64.dll/libiconv.dll trong cùng thư mục bundle")


def verify_barcode_dll_loads() -> None:
    if os.name != "nt":
        return
    zbar, iconv = find_dll_pair()
    handle = None
    try:
        if hasattr(os, "add_dll_directory"):
            handle = os.add_dll_directory(str(zbar.parent))
        ctypes.WinDLL(str(iconv))
        ctypes.WinDLL(str(zbar))
    finally:
        if handle is not None:
            handle.close()


def check_database(db_path: Path, schema_version: int) -> None:
    if not db_path.is_file():
        raise RuntimeError(f"Packaged app chưa tạo database: {db_path}")
    conn = sqlite3.connect(db_path, timeout=10)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError(f"Packaged DB integrity_check failed: {integrity}")
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if version != schema_version:
            raise RuntimeError(f"Schema packaged DB={version}, expected={schema_version}")
        required = {"products", "batches", "stock_movements", "purchase_notes", "dispatch_notes"}
        actual = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing = sorted(required - actual)
        if missing:
            raise RuntimeError(f"Packaged DB thiếu bảng: {missing}")
    finally:
        conn.close()


def launch_until_db(local_appdata: Path, db_path: Path, timeout: float = 20.0) -> subprocess.Popen:
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_appdata)
    env["PYTHONUTF8"] = "1"
    log_path = local_appdata / "packaged-startup.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = log_path.open("ab")
    try:
        proc = subprocess.Popen(
            [str(EXE)],
            cwd=APP_DIST,
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
        )
    finally:
        log_fh.close()

    deadline = time.time() + timeout
    while time.time() < deadline:
        code = proc.poll()
        if code is not None:
            output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            raise RuntimeError(f"QuanLyKho.exe thoát sớm với code {code}:\n{output[-4000:]}")
        if db_path.is_file():
            time.sleep(2.0)
            if proc.poll() is None:
                return proc
        time.sleep(0.25)

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    raise RuntimeError("QuanLyKho.exe không đạt trạng thái startup trong thời gian cho phép")


def stop_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main() -> int:
    if os.name != "nt":
        print("Packaged release smoke is Windows-only")
        return 0
    if not EXE.is_file():
        raise RuntimeError(f"Thiếu packaged executable: {EXE}")

    info_path = APP_DIST / "RELEASE_INFO.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    schema_version = int(info["schema_version"])

    verify_manifest()
    verify_barcode_dll_loads()

    with tempfile.TemporaryDirectory(prefix="quanlykho-rc-") as td:
        local_appdata = Path(td)
        db_path = local_appdata / "QuanLyXNT" / "pharm.db"

        # First clean-machine boot.
        first = launch_until_db(local_appdata, db_path)
        try:
            check_database(db_path, schema_version)
        finally:
            stop_process(first)
        check_database(db_path, schema_version)

        # Reopen the same per-user data after process termination.  This catches
        # packaging/startup regressions around WAL/schema initialization/restart.
        second = launch_until_db(local_appdata, db_path)
        try:
            check_database(db_path, schema_version)
        finally:
            stop_process(second)
        check_database(db_path, schema_version)

    print("Packaged release smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
