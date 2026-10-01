# -*- coding: utf-8 -*-
"""Smoke test giao diện web trong cửa sổ pywebview thật.

Mặc định chạy bản đóng gói ``dist/QuanLyKhoWeb``; ``--source`` chạy ``quanly_web.py`` từ mã nguồn.
Mỗi kịch bản dùng ``LOCALAPPDATA`` tạm nên không bao giờ chạm DB thật:
  * empty : cài mới, DB trống (Tổng quan hiện số 0, không báo lỗi)
  * seeded: DB mẫu (chip lọc, hiển thị an toàn, bấm nhanh, địa chỉ chưa có bản web)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
APP_DIST = ROOT / "dist" / "QuanLyKhoWeb"
EXE = APP_DIST / "QuanLyKhoWeb.exe"
SCENARIO_TIMEOUT_SECONDS = 180
EMPTY_EXPECTATION = {"counts": {"all": 0, "expired": 0, "near": 0, "low": 0}, "literal": None}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_package() -> None:
    if not EXE.is_file():
        raise RuntimeError(f"Thiếu packaged executable: {EXE}")
    if EXE.stat().st_size < 1024 * 1024:
        raise RuntimeError(f"{EXE} nhỏ bất thường")
    manifest = APP_DIST / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise RuntimeError("Thiếu SHA256SUMS.txt")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = APP_DIST / Path(rel)
        if not path.is_file():
            raise RuntimeError(f"Manifest trỏ tới file bị thiếu: {rel}")
        if _sha256(path).lower() != expected.lower():
            raise RuntimeError(f"SHA-256 mismatch: {rel}")


def _env(local_appdata: Path, expectation=None) -> dict:
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_appdata)
    env["PYTHONUTF8"] = "1"
    env.pop("QLK_SMOKE_EXPECT", None)
    if expectation is not None:
        env["QLK_SMOKE_EXPECT"] = json.dumps(expectation)
    return env


def seed_database(local_appdata: Path) -> dict:
    """Tạo DB mẫu ở LOCALAPPDATA tạm (trong tiến trình con để config.py đọc đúng thư mục)."""
    code = (
        "import json, config, webapp_testkit; "
        "print('SEED:' + json.dumps(webapp_testkit.seed_demo_database(config.DB_PATH)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=_env(local_appdata),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    for line in result.stdout.splitlines():
        if line.startswith("SEED:"):
            return json.loads(line[5:])
    raise RuntimeError("Không tạo được DB mẫu:\n" + (result.stdout + result.stderr)[-2000:])


def run_scenario(name: str, command: list, cwd: Path, local_appdata: Path, expectation: dict) -> bool:
    result = subprocess.run(
        command, cwd=cwd, env=_env(local_appdata, expectation),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=SCENARIO_TIMEOUT_SECONDS,
    )
    output = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0 and "WEB_SMOKE_OK" in output
    print(f"[{name}] {'OK' if ok else 'FAIL'} (exit={result.returncode})")
    if not ok:
        print(output[-4000:])
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="store_true", help="chạy quanly_web.py từ mã nguồn thay vì bản đóng gói")
    args = parser.parse_args()

    if os.name != "nt":
        print("Smoke test giao diện web chỉ hỗ trợ Windows")
        return 0

    if args.source:
        command, cwd = [sys.executable, "quanly_web.py", "--smoke"], ROOT
    else:
        verify_package()
        command, cwd = [str(EXE), "--smoke"], APP_DIST

    results = []
    with tempfile.TemporaryDirectory(prefix="quanlykho-web-empty-") as empty_dir:
        results.append(run_scenario("empty", command, cwd, Path(empty_dir), EMPTY_EXPECTATION))
    with tempfile.TemporaryDirectory(prefix="quanlykho-web-seeded-") as seeded_dir:
        expectation = seed_database(Path(seeded_dir))
        results.append(run_scenario("seeded", command, cwd, Path(seeded_dir), expectation))
    return 0 if all(results) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"WEB RELEASE SMOKE FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
