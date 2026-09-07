# -*- coding: utf-8 -*-
"""H1.2 mobile HTTP resilience hardening.

This module composes after H1.1 cookie-only authentication.  It intentionally
patches only the runtime mobile server so the large legacy ``server.py`` stays
unchanged while request handling gains bounded bodies, socket timeouts,
threaded concurrency and serialized access to the in-memory auth state.
"""

from __future__ import annotations

import http.server
import os
import secrets
import sys
import threading

import mobile_cookie_security as _cookie_security
import server as _server


MAX_REQUEST_BODY_BYTES = 1024 * 1024
REQUEST_SOCKET_TIMEOUT_SECONDS = 15.0
REQUEST_QUEUE_SIZE = 32

_AUTH_STATE_LOCK = threading.RLock()
_INSTALLED = False
_ORIGINAL_DO_POST = None
_ORIGINAL_CHECK_AUTH = None
_ORIGINAL_SERVER_RUN = None
_ORIGINAL_SERVER_STOP = None
_ORIGINAL_AUTHENTICATE_PIN = None


class RequestBodyPolicyError(ValueError):
    """Raised when request framing violates the bounded POST-body policy."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = str(message)


def validate_request_body_headers(headers) -> int:
    """Return a safe Content-Length or raise ``RequestBodyPolicyError``.

    The legacy request handlers understand fixed-length JSON bodies only.  An
    unsupported Transfer-Encoding is therefore rejected instead of being
    ambiguously interpreted as an empty or partial request.
    """
    transfer_encoding = str(headers.get("Transfer-Encoding", "") or "").strip().lower()
    if transfer_encoding and transfer_encoding != "identity":
        raise RequestBodyPolicyError(
            400,
            "Transfer-Encoding không được hỗ trợ; vui lòng gửi Content-Length cố định",
        )

    raw_length = headers.get("Content-Length")
    if raw_length in (None, ""):
        return 0

    try:
        content_length = int(str(raw_length).strip())
    except (TypeError, ValueError):
        raise RequestBodyPolicyError(400, "Content-Length không hợp lệ")

    if content_length < 0:
        raise RequestBodyPolicyError(400, "Content-Length không được âm")
    if content_length > MAX_REQUEST_BODY_BYTES:
        raise RequestBodyPolicyError(
            413,
            f"Dữ liệu gửi lên vượt quá giới hạn {MAX_REQUEST_BODY_BYTES // (1024 * 1024)} MiB",
        )
    return content_length


def configure_client_socket(client_socket):
    """Apply the per-connection read/write timeout used by the LAN server."""
    client_socket.settimeout(REQUEST_SOCKET_TIMEOUT_SECONDS)
    return client_socket


class HardenedThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Small bounded ThreadingHTTPServer suitable for the trusted LAN UI."""

    daemon_threads = True
    block_on_close = False
    allow_reuse_address = True
    request_queue_size = REQUEST_QUEUE_SIZE

    def get_request(self):
        client_socket, client_address = super().get_request()
        configure_client_socket(client_socket)
        return client_socket, client_address


def _reject_request(handler, status_code: int, message: str):
    handler.close_connection = True
    handler.send_json(
        {"success": False, "message": message},
        status_code,
        headers={"Connection": "close", "Cache-Control": "no-store"},
    )


def _guarded_do_post(handler):
    try:
        validate_request_body_headers(handler.headers)
    except RequestBodyPolicyError as exc:
        _reject_request(handler, exc.status_code, exc.message)
        return

    if _ORIGINAL_DO_POST is None:
        raise RuntimeError("Mobile HTTP hardening is not initialized")
    return _ORIGINAL_DO_POST(handler)


def _locked_check_auth(handler):
    if _ORIGINAL_CHECK_AUTH is None:
        raise RuntimeError("Mobile HTTP hardening is not initialized")
    with _AUTH_STATE_LOCK:
        return _ORIGINAL_CHECK_AUTH(handler)


def _locked_authenticate_mobile_pin(*args, **kwargs):
    if _ORIGINAL_AUTHENTICATE_PIN is None:
        raise RuntimeError("Mobile HTTP hardening is not initialized")
    with _AUTH_STATE_LOCK:
        return _ORIGINAL_AUTHENTICATE_PIN(*args, **kwargs)


def _hardened_server_run(server_thread):
    """Preserve the legacy lifecycle while using the hardened server class."""
    with _AUTH_STATE_LOCK:
        _server.SERVER_PIN = "".join(secrets.choice("0123456789") for _ in range(6))
        _server.ACTIVE_TOKENS.clear()
        _server.FAILED_ATTEMPTS.clear()

    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(_server.__file__)))
    else:
        base_dir = os.path.dirname(os.path.abspath(_server.__file__))

    static_dir = os.path.join(base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    js_path = os.path.join(static_dir, "html5-qrcode.min.js")
    if not os.path.exists(js_path):
        print(f"Cảnh báo: Tệp tin thư viện QR ngoại tuyến không tồn tại tại: {js_path}")

    attempts = 0
    while attempts < 10:
        try:
            server_thread.server = HardenedThreadingHTTPServer(
                (server_thread.host, server_thread.port),
                _server.MobileInventoryRequestHandler,
            )
            server_thread.server.db_instance = server_thread.db_instance
            server_thread.server.app_instance = server_thread.app_instance
            server_thread.is_running = True
            print(f"Mobile inventory server started on http://{server_thread.host}:{server_thread.port}")
            print(f"Xác thực PIN di động: {_server.SERVER_PIN}")
            _server.write_audit_log(
                action="BAT_SERVER",
                details=f"Mobile server started on port {server_thread.port}",
            )
            server_thread.server.serve_forever()
            break
        except Exception as exc:
            print(f"Failed to start mobile server on port {server_thread.port}: {exc}")
            server_thread.port += 1
            attempts += 1


def _hardened_server_stop(server_thread):
    with _AUTH_STATE_LOCK:
        _server.ACTIVE_TOKENS.clear()
        _server.FAILED_ATTEMPTS.clear()

    if server_thread.server:
        _server.write_audit_log(
            action="TAT_SERVER",
            details="Mobile server stopped",
        )
        server_thread.server.shutdown()
        server_thread.server.server_close()
        server_thread.is_running = False
        print("Mobile inventory server stopped")


def install_mobile_http_hardening():
    """Install H1.2 once, always after H1.1 cookie authentication."""
    global _INSTALLED
    global _ORIGINAL_DO_POST, _ORIGINAL_CHECK_AUTH
    global _ORIGINAL_SERVER_RUN, _ORIGINAL_SERVER_STOP
    global _ORIGINAL_AUTHENTICATE_PIN

    if _INSTALLED:
        return

    # H1.2 must capture the H1.1 cookie-only handlers, not the legacy bearer /
    # query-token handlers.  H1.1 is idempotent, so enforcing the order here is
    # safe both in production and isolated tests.
    _cookie_security.install_mobile_cookie_security()

    handler_cls = _server.MobileInventoryRequestHandler
    _ORIGINAL_DO_POST = handler_cls.do_POST
    _ORIGINAL_CHECK_AUTH = handler_cls.check_auth
    _ORIGINAL_SERVER_RUN = _server.MobileInventoryServer.run
    _ORIGINAL_SERVER_STOP = _server.MobileInventoryServer.stop
    _ORIGINAL_AUTHENTICATE_PIN = _cookie_security.authenticate_mobile_pin

    handler_cls.do_POST = _guarded_do_post
    handler_cls.check_auth = _locked_check_auth
    _cookie_security.authenticate_mobile_pin = _locked_authenticate_mobile_pin
    _server.MobileInventoryServer.run = _hardened_server_run
    _server.MobileInventoryServer.stop = _hardened_server_stop
    _INSTALLED = True


def uninstall_mobile_http_hardening_for_tests():
    """Restore the H1.1 runtime state; intended only for isolated tests."""
    global _INSTALLED
    global _ORIGINAL_DO_POST, _ORIGINAL_CHECK_AUTH
    global _ORIGINAL_SERVER_RUN, _ORIGINAL_SERVER_STOP
    global _ORIGINAL_AUTHENTICATE_PIN

    if not _INSTALLED:
        return

    handler_cls = _server.MobileInventoryRequestHandler
    handler_cls.do_POST = _ORIGINAL_DO_POST
    handler_cls.check_auth = _ORIGINAL_CHECK_AUTH
    _server.MobileInventoryServer.run = _ORIGINAL_SERVER_RUN
    _server.MobileInventoryServer.stop = _ORIGINAL_SERVER_STOP
    _cookie_security.authenticate_mobile_pin = _ORIGINAL_AUTHENTICATE_PIN

    _ORIGINAL_DO_POST = None
    _ORIGINAL_CHECK_AUTH = None
    _ORIGINAL_SERVER_RUN = None
    _ORIGINAL_SERVER_STOP = None
    _ORIGINAL_AUTHENTICATE_PIN = None
    _INSTALLED = False
