# -*- coding: utf-8 -*-
"""Router nhỏ cho backend web: mỗi route khai báo scope (local | lan)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Tuple

SCOPE_LOCAL = "local"
SCOPE_LAN = "lan"

log = logging.getLogger(__name__)


class HttpError(Exception):
    """Handler ném lỗi này để trả JSON lỗi với mã HTTP tương ứng."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = int(status)
        self.message = str(message)


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: Mapping[str, str]
    headers: Mapping[str, str]
    body: bytes
    scope: str


@dataclass
class Response:
    status: int = 200
    body: bytes = b""
    content_type: str = "application/json; charset=utf-8"
    headers: Dict[str, str] = field(default_factory=dict)


def json_response(payload, status: int = 200, headers=None) -> Response:
    merged = {"Cache-Control": "no-store"}
    merged.update(headers or {})
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return Response(status=status, body=body, headers=merged)


def error_response(status: int, message: str, headers=None, **extra) -> Response:
    payload = {"success": False, "message": message}
    payload.update(extra)
    return json_response(payload, status, headers)


class Router:
    def __init__(self):
        self._routes: Dict[str, Dict[str, Tuple[Callable[[Request], Response], frozenset]]] = {}

    def add(self, method, path, handler, scopes=(SCOPE_LOCAL,)):
        self._routes.setdefault(path, {})[method.upper()] = (handler, frozenset(scopes))

    def dispatch(self, request: Request) -> Response:
        by_method = self._routes.get(request.path)
        if by_method is None:
            return error_response(404, "Không tìm thấy")
        entry = by_method.get(request.method.upper())
        if entry is None:
            return error_response(
                405, "Phương thức không được hỗ trợ", headers={"Allow": ", ".join(sorted(by_method))}
            )
        handler, scopes = entry
        if request.scope not in scopes:
            return error_response(403, "Không được phép truy cập")
        try:
            return handler(request)
        except HttpError as exc:
            return error_response(exc.status, exc.message)
        except Exception:
            log.exception("Lỗi không xử lý được ở %s %s", request.method, request.path)
            return error_response(500, "Lỗi hệ thống")
