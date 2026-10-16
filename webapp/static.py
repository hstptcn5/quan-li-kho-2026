# -*- coding: utf-8 -*-
"""Phục vụ thư mục ``web/`` an toàn: không thoát khỏi thư mục gốc, không liệt kê thư mục."""

from __future__ import annotations

import urllib.parse
from pathlib import Path

from webapp.routing import Response

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


def resolve_static(web_root, url_path):
    """Trả về Path của file hợp lệ nằm trong ``web_root``, hoặc None."""
    rel = urllib.parse.unquote(url_path)
    if "\x00" in rel or "\\" in rel:
        return None
    rel = rel.lstrip("/")
    if rel == "":
        rel = "index.html"
    parts = rel.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.startswith(".") or ":" in part:
            return None

    root = Path(web_root).resolve()
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            return None
    try:
        resolved = current.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    if resolved.suffix.lower() not in CONTENT_TYPES or not resolved.is_file():
        return None
    return resolved


def _not_found() -> Response:
    return Response(
        status=404,
        body="Không tìm thấy".encode("utf-8"),
        content_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


def serve_static(web_root, url_path) -> Response:
    path = resolve_static(web_root, url_path)
    if path is None:
        return _not_found()
    try:
        body = path.read_bytes()
    except OSError:
        return _not_found()
    return Response(
        status=200,
        body=body,
        content_type=CONTENT_TYPES[path.suffix.lower()],
        headers={"Cache-Control": "no-cache"},
    )
