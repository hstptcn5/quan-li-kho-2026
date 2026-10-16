# -*- coding: utf-8 -*-
"""Giới hạn framing HTTP dùng chung cho server di động (LAN) và backend web cục bộ.

Module này cố ý không import code ứng dụng, để backend mới dùng được mà không
phải nạp ``server.py`` cũ.
"""

from __future__ import annotations


MAX_REQUEST_BODY_BYTES = 1024 * 1024
REQUEST_SOCKET_TIMEOUT_SECONDS = 15.0
REQUEST_QUEUE_SIZE = 32


class RequestBodyPolicyError(ValueError):
    """Raised when request framing violates the bounded POST-body policy."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = str(message)


def validate_request_body_headers(headers) -> int:
    """Return a safe Content-Length or raise ``RequestBodyPolicyError``.

    The legacy request handlers understand fixed-length JSON bodies only. An
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
