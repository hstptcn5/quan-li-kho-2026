# -*- coding: utf-8 -*-
"""Điểm vào giao diện web: cổng cục bộ + cửa sổ pywebview (Edge WebView2).

Bản Tkinter vẫn là ``quanly_xnt.py``; hai bản dùng chung ``pharm.db``.
"""

from __future__ import annotations

import argparse
import sys
import time

from webapp.runtime import app_root, webview2_runtime_version

WINDOW_TITLE = "Quản lý kho 2026"
WEBVIEW2_HELP = (
    "Không tìm thấy Microsoft Edge WebView2 Runtime, cần có để hiển thị giao diện.\n"
    "Hãy cài bản 'Evergreen Bootstrapper' tại https://go.microsoft.com/fwlink/p/?LinkId=2124703 "
    "rồi chạy lại ứng dụng."
)


def create_listener(db_path=None):
    """Dựng router + phiên + listener; mỗi request mở một kết nối SQLite riêng."""
    from config import DB_PATH
    from database import DB
    from webapp.app import build_router
    from webapp.auth import LocalSession
    from webapp.listener import LocalListener

    path = db_path or DB_PATH
    router = build_router(lambda: DB(path))
    return LocalListener(router, LocalSession(), app_root() / "web")


def run_serve_only(listener) -> int:
    """Chế độ phát triển: chỉ mở cổng cục bộ, in địa chỉ boot dùng một lần."""
    listener.start()
    print("Giao diện web đang chạy ở chế độ phát triển (không mở cửa sổ).", flush=True)
    print("Mở địa chỉ sau trong trình duyệt (chỉ dùng được một lần):", flush=True)
    print(listener.boot_url(), flush=True)
    print("Nhấn Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
    return 0


def run_window(listener, on_ready=None) -> int:
    """Mở cửa sổ pywebview. ``on_ready(window)`` (tùy chọn) chạy sau khi cửa sổ sẵn sàng;
    giá trị trả về là mã thoát và cửa sổ được đóng ngay sau đó."""
    if webview2_runtime_version() is None:
        print(WEBVIEW2_HELP, file=sys.stderr)
        return 1
    try:
        import webview
    except ImportError:
        print("Thiếu thư viện pywebview. Hãy chạy: pip install -r requirements.txt", file=sys.stderr)
        return 1

    listener.start()
    window = webview.create_window(
        WINDOW_TITLE, listener.boot_url(), width=1366, height=800, min_size=(1024, 640)
    )
    outcome = {"code": 0}
    callback = None
    if on_ready is not None:
        def callback(win):
            try:
                outcome["code"] = int(on_ready(win) or 0)
            finally:
                win.destroy()
    try:
        webview.start(callback, window if callback else None, gui="edgechromium", private_mode=True, debug=False)
    except Exception as exc:
        print(f"Không mở được cửa sổ giao diện: {exc}\n{WEBVIEW2_HELP}", file=sys.stderr)
        return 1
    return outcome["code"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quản lý kho 2026 (giao diện web)")
    parser.add_argument(
        "--serve", action="store_true",
        help="chỉ mở cổng cục bộ và in địa chỉ boot một lần (phát triển/kiểm thử), không mở cửa sổ",
    )
    return parser


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    listener = create_listener()
    try:
        if args.serve:
            return run_serve_only(listener)
        return run_window(listener)
    finally:
        listener.stop()


if __name__ == "__main__":
    sys.exit(main())
