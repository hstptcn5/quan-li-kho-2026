# -*- coding: utf-8 -*-
import unittest

from webapp.auth import COOKIE_NAME, LocalSession
from webapp.security import SECURITY_HEADERS, host_allowed, origin_allowed


class HostAndOriginTests(unittest.TestCase):
    def test_host_must_be_loopback_with_the_listener_port(self):
        for host in ("127.0.0.1:5000", "localhost:5000", "LOCALHOST:5000"):
            with self.subTest(host=host):
                self.assertTrue(host_allowed(host, 5000))
        for host in (
            None, "", "127.0.0.1", "127.0.0.1:5001", "evil.example", "evil.example:5000",
            "127.0.0.1:5000.evil.example", "0.0.0.0:5000", "[::1]:5000",
        ):
            with self.subTest(host=host):
                self.assertFalse(host_allowed(host, 5000))

    def test_origin_must_be_same_origin(self):
        self.assertTrue(origin_allowed({"Origin": "http://127.0.0.1:5000"}, 5000))
        self.assertTrue(origin_allowed({"Origin": "http://localhost:5000"}, 5000))
        self.assertTrue(origin_allowed({"Sec-Fetch-Site": "same-origin"}, 5000))
        self.assertFalse(origin_allowed({}, 5000))
        self.assertFalse(origin_allowed({"Origin": "http://evil.example"}, 5000))
        self.assertFalse(origin_allowed({"Origin": "http://127.0.0.1:5001"}, 5000))
        self.assertFalse(origin_allowed({"Origin": "null"}, 5000))
        self.assertFalse(origin_allowed({"Sec-Fetch-Site": "cross-site"}, 5000))
        # Origin hợp lệ không cứu được Sec-Fetch-Site sai, nhưng Origin sai thì luôn bị chặn.
        self.assertFalse(origin_allowed({"Origin": "http://evil.example", "Sec-Fetch-Site": "same-origin"}, 5000))

    def test_security_headers_are_the_specified_policy(self):
        self.assertEqual(
            SECURITY_HEADERS["Content-Security-Policy"],
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'",
        )
        self.assertEqual(SECURITY_HEADERS["X-Content-Type-Options"], "nosniff")
        self.assertEqual(SECURITY_HEADERS["Referrer-Policy"], "no-referrer")


class LocalSessionTests(unittest.TestCase):
    def test_boot_token_is_single_use_and_returns_the_session_token(self):
        session = LocalSession()
        first = session.redeem_boot_token(session.boot_token)
        self.assertTrue(first)
        self.assertIsNone(session.redeem_boot_token(session.boot_token))

    def test_wrong_token_does_not_consume_the_real_one(self):
        session = LocalSession()
        for wrong in ("", "x", session.boot_token[:-1], session.boot_token + "a", "Ư" * 20):
            with self.subTest(wrong=wrong):
                self.assertIsNone(session.redeem_boot_token(wrong))
        self.assertTrue(session.redeem_boot_token(session.boot_token))

    def test_cookie_header_has_the_required_attributes(self):
        header = LocalSession().session_cookie_header()
        self.assertTrue(header.startswith(COOKIE_NAME + "="))
        for attribute in ("Path=/", "HttpOnly", "SameSite=Strict"):
            self.assertIn(attribute, header)
        self.assertNotIn("Max-Age", header)
        self.assertNotIn("Expires", header)

    def test_cookie_authentication(self):
        session = LocalSession()
        cookie = session.session_cookie_header().split(";", 1)[0]
        self.assertTrue(session.is_authenticated(cookie))
        self.assertTrue(session.is_authenticated("other=1; " + cookie))
        for bad in ("", None, COOKIE_NAME + "=", COOKIE_NAME + "=wrong", cookie + "x", "garbage;;;", "=="):
            with self.subTest(bad=bad):
                self.assertFalse(session.is_authenticated(bad))

    def test_two_sessions_do_not_accept_each_others_cookies(self):
        a, b = LocalSession(), LocalSession()
        self.assertNotEqual(a.boot_token, b.boot_token)
        self.assertFalse(b.is_authenticated(a.session_cookie_header().split(";", 1)[0]))


if __name__ == "__main__":
    unittest.main()
