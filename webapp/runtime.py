# -*- coding: utf-8 -*-
"""Tiện ích môi trường chạy: thư mục gốc ứng dụng và phát hiện WebView2 Runtime."""

from __future__ import annotations

import sys
from pathlib import Path

WEBVIEW2_CLIENT_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_REGISTRY_LOCATIONS = (
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
    ("HKEY_CURRENT_USER", r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
)


def app_root() -> Path:
    """Thư mục chứa ``web/``: gốc repo khi chạy mã nguồn, bundle PyInstaller khi đã đóng gói."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def webview2_runtime_version(winreg_module=None):
    """Trả về chuỗi phiên bản WebView2 Runtime đã cài, hoặc None nếu chưa có."""
    if winreg_module is None:
        try:
            import winreg as winreg_module
        except ImportError:  # không phải Windows
            return None
    for hive_name, path in _REGISTRY_LOCATIONS:
        hive = getattr(winreg_module, hive_name)
        try:
            with winreg_module.OpenKey(hive, path) as key:
                value, _ = winreg_module.QueryValueEx(key, "pv")
        except OSError:
            continue
        if value and value != "0.0.0.0":
            return str(value)
    return None
