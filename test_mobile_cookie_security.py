import time
import unittest

import server
from mobile_templates import MOBILE_HTML
from mobile_cookie_security import (
    authenticate_mobile_pin,
    cookie_only_check_auth,
    harden_mobile_html,
)


class _FakeHandler:
    def __init__(self, path="/api/products", cookie="", authorization=""):
        self.path = path
        self.client_address = ("192.168.1.50", 12345)
        self._cookie = cookie
        self.headers = {"Authorization": authorization} if authorization else {}
        self.sent = []

    def get_cookie(self, name):
        return self._cookie if name == server.SESSION_COOKIE_NAME else ""

    def send_json(self, data, status_code=200, headers=None):
        self.sent.append((data, status_code, headers))


class MobileCookieSecurityTests(unittest.TestCase):
    def setUp(self):
        self.old_pin = server.SERVER_PIN
        self.old_tokens = dict(server.ACTIVE_TOKENS)
        self.old_attempts = dict(server.FAILED_ATTEMPTS)
        server.SERVER_PIN = "123456"
        server.ACTIVE_TOKENS.clear()
        server.FAILED_ATTEMPTS.clear()

    def tearDown(self):
        server.SERVER_PIN = self.old_pin
        server.ACTIVE_TOKENS.clear()
        server.ACTIVE_TOKENS.update(self.old_tokens)
        server.FAILED_ATTEMPTS.clear()
        server.FAILED_ATTEMPTS.update(self.old_attempts)

    def test_auth_success_returns_cookie_but_never_json_token(self):
        status, payload, cookie = authenticate_mobile_pin(
            "192.168.1.50", "123456", now=1000.0
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"success": True})
        self.assertNotIn("token", payload)
        self.assertIsNotNone(cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertIn("Path=/", cookie)
        self.assertEqual(len(server.ACTIVE_TOKENS), 1)

    def test_query_token_is_rejected_even_when_token_exists(self):
        token = "query-secret"
        server.ACTIVE_TOKENS[token] = {
            "ip": "192.168.1.50",
            "expiry": time.time() + 600,
        }
        handler = _FakeHandler(path=f"/api/print-dispatch?id=1&token={token}")
        self.assertFalse(cookie_only_check_auth(handler))
        self.assertEqual(handler.sent[-1][1], 401)

    def test_bearer_token_is_rejected_even_when_token_exists(self):
        token = "bearer-secret"
        server.ACTIVE_TOKENS[token] = {
            "ip": "192.168.1.50",
            "expiry": time.time() + 600,
        }
        handler = _FakeHandler(authorization=f"Bearer {token}")
        self.assertFalse(cookie_only_check_auth(handler))
        self.assertEqual(handler.sent[-1][1], 401)

    def test_valid_cookie_session_is_accepted(self):
        token = "cookie-secret"
        server.ACTIVE_TOKENS[token] = {
            "ip": "192.168.1.50",
            "expiry": time.time() + 600,
        }
        handler = _FakeHandler(cookie=token)
        self.assertTrue(cookie_only_check_auth(handler))
        self.assertEqual(handler.sent, [])

    def test_cookie_is_bound_to_client_ip(self):
        token = "cookie-secret"
        server.ACTIVE_TOKENS[token] = {
            "ip": "192.168.1.99",
            "expiry": time.time() + 600,
        }
        handler = _FakeHandler(cookie=token)
        self.assertFalse(cookie_only_check_auth(handler))
        self.assertNotIn(token, server.ACTIVE_TOKENS)
        self.assertEqual(handler.sent[-1][1], 401)

    def test_expired_cookie_session_is_removed(self):
        token = "expired-secret"
        server.ACTIVE_TOKENS[token] = {
            "ip": "192.168.1.50",
            "expiry": time.time() - 1,
        }
        handler = _FakeHandler(cookie=token)
        self.assertFalse(cookie_only_check_auth(handler))
        self.assertNotIn(token, server.ACTIVE_TOKENS)
        self.assertEqual(handler.sent[-1][1], 401)

    def test_runtime_html_contains_no_session_token_storage_or_bearer_header(self):
        hardened = harden_mobile_html(MOBILE_HTML)
        self.assertNotIn("localStorage.getItem('inventory_token')", hardened)
        self.assertNotIn("localStorage.setItem('inventory_token'", hardened)
        self.assertNotIn("options.headers['Authorization']", hardened)
        self.assertNotIn("token=${encodeURIComponent(token)}", hardened)
        self.assertIn("options.credentials = 'same-origin'", hardened)
        self.assertIn("window.open(printUrl, '_blank', 'noopener');", hardened)
        # Cart persistence remains intentionally local-only and is unrelated to auth.
        self.assertIn("mob_purchase_cart", hardened)
        self.assertIn("mob_dispatch_cart", hardened)

    def test_lockout_resets_after_window_expires(self):
        server.FAILED_ATTEMPTS["192.168.1.50"] = {
            "count": 5,
            "blocked_until": 900.0,
        }
        status, payload, cookie = authenticate_mobile_pin(
            "192.168.1.50", "000000", now=1000.0
        )
        self.assertEqual(status, 401)
        self.assertIsNone(cookie)
        self.assertEqual(server.FAILED_ATTEMPTS["192.168.1.50"]["count"], 1)
        self.assertIn("Còn 4 lần thử", payload["message"])


if __name__ == "__main__":
    unittest.main()
