# -*- coding: utf-8 -*-
"""Listener loopback: boot token -> cookie phiên, kiểm Host/Origin, router và file tĩnh."""

from __future__ import annotations

import http.server
import threading
import urllib.parse
from pathlib import Path

from http_limits import (
    REQUEST_QUEUE_SIZE,
    REQUEST_SOCKET_TIMEOUT_SECONDS,
    RequestBodyPolicyError,
    validate_request_body_headers,
)
from webapp.auth import LocalSession
from webapp.routing import SCOPE_LOCAL, Request, Response, Router, error_response
from webapp.security import SECURITY_HEADERS, host_allowed, origin_allowed
from webapp.static import serve_static

LOOPBACK_HOSTS = ("127.0.0.1",)
BODY_METHODS = ("POST", "PUT", "PATCH")


def _make_handler(router: Router, session: LocalSession, web_root: Path, scope: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "QuanLyKhoWeb"
        sys_version = ""
        timeout = REQUEST_SOCKET_TIMEOUT_SECONDS

        def log_message(self, format, *args):  # noqa: A002 - tên tham số do thư viện chuẩn quy định
            pass

        def _send(self, response: Response, close: bool = False):
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            for name, value in response.headers.items():
                self.send_header(name, value)
            if close:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            try:
                self.wfile.write(response.body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _boot(self, token: str) -> Response:
            if not session.redeem_boot_token(token):
                return error_response(401, "Token khởi động không hợp lệ hoặc đã dùng")
            return Response(
                status=302,
                body=b"",
                content_type="text/plain; charset=utf-8",
                headers={
                    "Location": "/",
                    "Set-Cookie": session.session_cookie_header(),
                    "Cache-Control": "no-store",
                },
            )

        def _handle(self):
            port = self.server.server_address[1]
            if not host_allowed(self.headers.get("Host"), port):
                self._send(error_response(403, "Host không hợp lệ"), close=True)
                return
            try:
                length = validate_request_body_headers(self.headers)
            except RequestBodyPolicyError as exc:
                self._send(error_response(exc.status_code, exc.message), close=True)
                return
            body = self.rfile.read(length) if length and self.command in BODY_METHODS else b""

            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            if self.command == "GET" and path.startswith("/boot/"):
                self._send(self._boot(urllib.parse.unquote(path[len("/boot/"):])))
                return

            if not session.is_authenticated(self.headers.get("Cookie", "")):
                if path.startswith("/api/"):
                    self._send(error_response(401, "Chưa xác thực", auth_required=True))
                else:
                    self._send(Response(
                        status=401, body=b"", content_type="text/html; charset=utf-8",
                        headers={"Cache-Control": "no-store"},
                    ))
                return

            if self.command not in ("GET", "HEAD") and not origin_allowed(self.headers, port):
                self._send(error_response(403, "Origin không hợp lệ"))
                return

            if path.startswith("/api/"):
                query = {
                    key: values[0]
                    for key, values in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items()
                }
                request = Request(
                    method=self.command, path=path, query=query,
                    headers=self.headers, body=body, scope=scope,
                )
                self._send(router.dispatch(request))
            elif self.command == "GET":
                self._send(serve_static(web_root, path))
            else:
                self._send(error_response(405, "Phương thức không được hỗ trợ", headers={"Allow": "GET"}))

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

    return Handler


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = REQUEST_QUEUE_SIZE


class LocalListener:
    """HTTP server loopback cho cửa sổ desktop (scope ``local``)."""

    def __init__(self, router: Router, session: LocalSession, web_root, host: str = "127.0.0.1"):
        if host not in LOOPBACK_HOSTS:
            raise ValueError("Listener cục bộ chỉ được bind vào địa chỉ loopback 127.0.0.1")
        self.session = session
        self._httpd = _Server((host, 0), _make_handler(router, session, Path(web_root), SCOPE_LOCAL))
        self._thread = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def boot_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/boot/{self.session.boot_token}"

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            kwargs={"poll_interval": 0.1},
            name="qlk-local-listener",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        thread, self._thread = self._thread, None
        if thread is not None:
            self._httpd.shutdown()
            thread.join(timeout=5)
        self._httpd.server_close()
