# -*- coding: utf-8 -*-
"""Header bảo mật cố định và kiểm Host/Origin cho listener cục bộ."""

from __future__ import annotations

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'"
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _allowed_hosts(port: int):
    return {f"127.0.0.1:{port}", f"localhost:{port}"}


def host_allowed(host_header, port: int) -> bool:
    """Chống DNS rebinding: chỉ nhận đúng host loopback kèm cổng của listener."""
    return str(host_header or "").lower() in _allowed_hosts(port)


def origin_allowed(headers, port: int) -> bool:
    """Request ghi dữ liệu phải cùng origin: Origin hợp lệ, hoặc không có Origin
    nhưng trình duyệt báo ``Sec-Fetch-Site: same-origin``."""
    origin = headers.get("Origin")
    if origin is not None:
        return str(origin).lower() in {f"http://{host}" for host in _allowed_hosts(port)}
    return str(headers.get("Sec-Fetch-Site") or "").lower() == "same-origin"
