# -*- coding: utf-8 -*-
"""Cookie-only authentication hardening for the mobile LAN UI.

This module deliberately applies as a small runtime patch so H1.1 can remove
session credentials from browser-accessible storage without mixing that change
with the larger HTTP server resilience refactor planned for H1.2.
"""

import json
import secrets
import time
import urllib.parse

import server as _server


SESSION_SECONDS = 8 * 3600
_INSTALLED = False
_ORIGINAL_CHECK_AUTH = None
_ORIGINAL_DO_POST = None
_ORIGINAL_MOBILE_HTML = None


def authenticate_mobile_pin(client_ip, pin, now=None):
    """Validate the LAN PIN and return an HttpOnly cookie response tuple.

    Returns ``(status_code, payload, set_cookie_or_none)``.  The session token
    is intentionally never returned in the JSON payload.
    """
    if now is None:
        now = time.time()

    client_ip = str(client_ip or "")
    pin = str(pin or "").strip()
    block_info = _server.FAILED_ATTEMPTS.get(client_ip)

    if block_info and now < float(block_info.get("blocked_until") or 0):
        secs_left = max(1, int(float(block_info["blocked_until"]) - now))
        return 429, {
            "success": False,
            "message": f"IP bị tạm khóa. Vui lòng thử lại sau {secs_left} giây",
        }, None

    # Once a lockout window has expired, start a fresh attempt window instead
    # of immediately re-locking the client after one more typo.
    if block_info and float(block_info.get("blocked_until") or 0) <= now and int(block_info.get("count") or 0) >= 5:
        block_info = {"count": 0, "blocked_until": 0}
        _server.FAILED_ATTEMPTS[client_ip] = block_info

    if not pin:
        return 400, {"success": False, "message": "Mã PIN không được để trống"}, None

    if pin == _server.SERVER_PIN and bool(_server.SERVER_PIN):
        _server.FAILED_ATTEMPTS.pop(client_ip, None)
        token = secrets.token_urlsafe(32)
        _server.ACTIVE_TOKENS[token] = {
            "ip": client_ip,
            "expiry": now + SESSION_SECONDS,
        }
        cookie = (
            f"{_server.SESSION_COOKIE_NAME}={urllib.parse.quote(token)}; "
            f"Max-Age={SESSION_SECONDS}; Path=/; SameSite=Strict; HttpOnly"
        )
        return 200, {"success": True}, cookie

    if not block_info:
        block_info = {"count": 0, "blocked_until": 0}
        _server.FAILED_ATTEMPTS[client_ip] = block_info

    block_info["count"] = int(block_info.get("count") or 0) + 1
    if block_info["count"] >= 5:
        block_info["blocked_until"] = now + 5 * 60

    attempts_left = max(0, 5 - int(block_info["count"]))
    return 401, {
        "success": False,
        "message": f"Mã PIN sai. Còn {attempts_left} lần thử",
    }, None


def cookie_only_check_auth(handler):
    """Accept protected requests only through the HttpOnly session cookie."""
    parsed_url = urllib.parse.urlparse(handler.path)
    path = parsed_url.path

    if path in ["/", "/index.html", "/api/auth"] or path.startswith("/static/"):
        return True

    token = handler.get_cookie(_server.SESSION_COOKIE_NAME)
    if not token:
        handler.send_json(
            {"success": False, "message": "Yêu cầu xác thực PIN", "auth_required": True},
            401,
        )
        return False

    token_info = _server.ACTIVE_TOKENS.get(token)
    if not token_info:
        handler.send_json(
            {"success": False, "message": "Phiên làm việc không hợp lệ hoặc đã hết hạn", "auth_required": True},
            401,
        )
        return False

    if token_info.get("ip") != handler.client_address[0]:
        _server.ACTIVE_TOKENS.pop(token, None)
        handler.send_json(
            {"success": False, "message": "Phiên không hợp lệ", "auth_required": True},
            401,
        )
        return False

    if time.time() > float(token_info.get("expiry") or 0):
        _server.ACTIVE_TOKENS.pop(token, None)
        handler.send_json(
            {"success": False, "message": "Phiên làm việc đã hết hạn", "auth_required": True},
            401,
        )
        return False

    return True


def _cookie_only_do_post(handler):
    parsed_url = urllib.parse.urlparse(handler.path)
    if parsed_url.path != "/api/auth":
        return _ORIGINAL_DO_POST(handler)

    try:
        content_length = int(handler.headers.get("Content-Length", 0))
    except (TypeError, ValueError):
        handler.send_json({"success": False, "message": "Content-Length không hợp lệ"}, 400)
        return

    post_data = handler.rfile.read(content_length)
    try:
        data = json.loads(post_data.decode("utf-8")) if post_data else {}
    except Exception:
        handler.send_json({"success": False, "message": "Dữ liệu JSON không hợp lệ"}, 400)
        return

    client_ip = handler.client_address[0]
    status, payload, cookie = authenticate_mobile_pin(client_ip, data.get("pin", ""))

    try:
        if payload.get("success"):
            _server.write_audit_log("LOGIN", "Đăng nhập thành công di động", ip=client_ip)
        elif status == 401:
            _server.write_audit_log("LOGIN_FAILED", "Đăng nhập thất bại (Mã PIN sai)", ip=client_ip)
    except Exception:
        pass

    headers = {"Set-Cookie": cookie, "Cache-Control": "no-store"} if cookie else {"Cache-Control": "no-store"}
    handler.send_json(payload, status, headers=headers)


def harden_mobile_html(html):
    """Remove browser-accessible session credentials from the mobile page."""
    hardened = str(html)

    old_fetch_prefix = """        // Override fetch to include token and handle 401 (Lỗi 3)\n        const originalFetch = window.fetch;\n        window.fetch = function(url, options = {}) {\n            const token = localStorage.getItem('inventory_token') || '';\n            options.headers = options.headers || {};\n            if (token) {\n                options.headers['Authorization'] = `Bearer ${token}`;\n            }\n"""
    new_fetch_prefix = """        // Cookie-only session: credentials stay in an HttpOnly same-origin cookie.\n        const originalFetch = window.fetch;\n        window.fetch = function(url, options = {}) {\n            options.headers = options.headers || {};\n            options.credentials = 'same-origin';\n"""
    hardened = hardened.replace(old_fetch_prefix, new_fetch_prefix)

    hardened = hardened.replace(
        "                    localStorage.removeItem('inventory_token');\n                    showAuthModal();",
        "                    showAuthModal();",
    )
    hardened = hardened.replace(
        "                    localStorage.setItem('inventory_token', data.token);",
        "                    try { localStorage.removeItem(['inventory', 'token'].join('_')); } catch (e) {}",
    )

    old_dom_auth = """            const token = localStorage.getItem('inventory_token');\n            if (!token) {\n                showAuthModal();\n            } else {\n                hideAuthModal();\n            }\n"""
    new_dom_auth = """            showAuthModal();\n            originalFetch('/api/dashboard-stats', { credentials: 'same-origin', cache: 'no-store' })\n                .then(response => {\n                    if (response.status === 401) showAuthModal();\n                    else hideAuthModal();\n                })\n                .catch(() => showAuthModal());\n"""
    hardened = hardened.replace(old_dom_auth, new_dom_auth)

    old_helper = """        function withAuthToken(url) {\n            const token = localStorage.getItem('inventory_token') || '';\n            if (!token) return url;\n            const sep = url.includes('?') ? '&' : '?';\n            return `${url}${sep}token=${encodeURIComponent(token)}`;\n        }\n"""
    hardened = hardened.replace(old_helper, """        function withAuthToken(url) {\n            return url;\n        }\n""")

    hardened = hardened.replace(
        "window.open(withAuthToken(`/api/print-purchase?id=${encodeURIComponent(noteId)}`), '_blank');",
        "window.open(`/api/print-purchase?id=${encodeURIComponent(noteId)}`, '_blank', 'noopener');",
    )
    hardened = hardened.replace(
        "window.open(withAuthToken(`/api/print-dispatch?id=${encodeURIComponent(noteId)}`), '_blank');",
        "window.open(`/api/print-dispatch?id=${encodeURIComponent(noteId)}`, '_blank', 'noopener');",
    )
    hardened = hardened.replace(
        "window.open(withAuthToken(printUrl), '_blank');",
        "window.open(printUrl, '_blank', 'noopener');",
    )
    hardened = hardened.replace(
        "window.open(withAuthToken(url), '_blank');",
        "window.open(url, '_blank', 'noopener');",
    )

    forbidden = [
        "localStorage.getItem('inventory_token')",
        "localStorage.setItem('inventory_token'",
        "options.headers['Authorization']",
        "token=${encodeURIComponent(token)}",
    ]
    leftovers = [marker for marker in forbidden if marker in hardened]
    if leftovers:
        raise RuntimeError("Mobile auth template hardening incomplete: " + ", ".join(leftovers))

    return hardened


def install_mobile_cookie_security():
    """Apply H1.1 once to the server class and the HTML served at runtime."""
    global _INSTALLED, _ORIGINAL_CHECK_AUTH, _ORIGINAL_DO_POST, _ORIGINAL_MOBILE_HTML
    if _INSTALLED:
        return

    handler_cls = _server.MobileInventoryRequestHandler
    _ORIGINAL_CHECK_AUTH = handler_cls.check_auth
    _ORIGINAL_DO_POST = handler_cls.do_POST
    _ORIGINAL_MOBILE_HTML = _server.MOBILE_HTML

    handler_cls.check_auth = cookie_only_check_auth
    handler_cls.do_POST = _cookie_only_do_post
    _server.MOBILE_HTML = harden_mobile_html(_server.MOBILE_HTML)
    _INSTALLED = True


def uninstall_mobile_cookie_security_for_tests():
    """Restore the imported server module; intended only for isolated tests."""
    global _INSTALLED, _ORIGINAL_CHECK_AUTH, _ORIGINAL_DO_POST, _ORIGINAL_MOBILE_HTML
    if not _INSTALLED:
        return
    handler_cls = _server.MobileInventoryRequestHandler
    handler_cls.check_auth = _ORIGINAL_CHECK_AUTH
    handler_cls.do_POST = _ORIGINAL_DO_POST
    _server.MOBILE_HTML = _ORIGINAL_MOBILE_HTML
    _ORIGINAL_CHECK_AUTH = None
    _ORIGINAL_DO_POST = None
    _ORIGINAL_MOBILE_HTML = None
    _INSTALLED = False
