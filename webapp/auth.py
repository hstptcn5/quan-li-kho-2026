# -*- coding: utf-8 -*-
"""Phiên cục bộ: boot token dùng một lần đổi lấy cookie phiên HttpOnly."""

from __future__ import annotations

import hmac
import secrets
import threading
from http.cookies import CookieError, SimpleCookie

COOKIE_NAME = "qlk_session"


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))


class LocalSession:
    """Một phiên cho một lần chạy ứng dụng.

    ``boot_token`` chỉ đổi được một lần (cửa sổ pywebview mở ``/boot/<token>``);
    token sai không làm mất token đúng, vì token có 256 bit và việc tiêu hủy khi
    đoán sai chỉ giúp kẻ khác phá được lần khởi động hợp lệ.
    """

    def __init__(self):
        self.boot_token = secrets.token_urlsafe(32)
        self._session_token = secrets.token_urlsafe(32)
        self._boot_available = True
        self._lock = threading.Lock()

    def redeem_boot_token(self, candidate):
        with self._lock:
            if not self._boot_available or not _same(candidate, self.boot_token):
                return None
            self._boot_available = False
            return self._session_token

    def session_cookie_header(self) -> str:
        # Cookie phiên (không Max-Age/Expires): hết hạn khi đóng ứng dụng.
        return f"{COOKIE_NAME}={self._session_token}; Path=/; HttpOnly; SameSite=Strict"

    def is_authenticated(self, cookie_header) -> bool:
        jar = SimpleCookie()
        try:
            jar.load(cookie_header or "")
        except CookieError:
            return False
        morsel = jar.get(COOKIE_NAME)
        return morsel is not None and bool(morsel.value) and _same(morsel.value, self._session_token)
