import http.server
import threading
import time
import unittest

import mobile_cookie_security
import mobile_http_hardening as hardening
import server


class _FakeSocket:
    def __init__(self):
        self.timeout = None

    def settimeout(self, value):
        self.timeout = value


class _FakeHandler:
    def __init__(self, headers=None):
        self.headers = headers or {}
        self.close_connection = False
        self.sent = []
        self.delegated = 0

    def send_json(self, data, status_code=200, headers=None):
        self.sent.append((data, status_code, headers or {}))


class MobileHttpHardeningTests(unittest.TestCase):
    def test_threading_server_contract_and_socket_timeout(self):
        self.assertTrue(issubclass(hardening.HardenedThreadingHTTPServer, http.server.ThreadingHTTPServer))
        self.assertTrue(hardening.HardenedThreadingHTTPServer.daemon_threads)
        self.assertFalse(hardening.HardenedThreadingHTTPServer.block_on_close)
        self.assertTrue(hardening.HardenedThreadingHTTPServer.allow_reuse_address)
        self.assertEqual(
            hardening.HardenedThreadingHTTPServer.request_queue_size,
            hardening.REQUEST_QUEUE_SIZE,
        )

        fake_socket = _FakeSocket()
        returned = hardening.configure_client_socket(fake_socket)
        self.assertIs(returned, fake_socket)
        self.assertEqual(fake_socket.timeout, hardening.REQUEST_SOCKET_TIMEOUT_SECONDS)

    def test_request_body_header_policy_accepts_bounded_fixed_length(self):
        self.assertEqual(hardening.validate_request_body_headers({}), 0)
        self.assertEqual(
            hardening.validate_request_body_headers({"Content-Length": " 128 "}),
            128,
        )
        self.assertEqual(
            hardening.validate_request_body_headers(
                {
                    "Transfer-Encoding": "identity",
                    "Content-Length": str(hardening.MAX_REQUEST_BODY_BYTES),
                }
            ),
            hardening.MAX_REQUEST_BODY_BYTES,
        )

    def test_request_body_header_policy_rejects_bad_or_oversized_framing(self):
        cases = [
            ({"Content-Length": "not-a-number"}, 400),
            ({"Content-Length": "-1"}, 400),
            ({"Content-Length": str(hardening.MAX_REQUEST_BODY_BYTES + 1)}, 413),
            ({"Transfer-Encoding": "chunked"}, 400),
            ({"Transfer-Encoding": "gzip", "Content-Length": "10"}, 400),
        ]
        for headers, expected_status in cases:
            with self.subTest(headers=headers):
                with self.assertRaises(hardening.RequestBodyPolicyError) as ctx:
                    hardening.validate_request_body_headers(headers)
                self.assertEqual(ctx.exception.status_code, expected_status)

    def test_guarded_post_rejects_before_delegating_and_closes_connection(self):
        old_delegate = hardening._ORIGINAL_DO_POST
        try:
            hardening._ORIGINAL_DO_POST = lambda handler: setattr(
                handler, "delegated", handler.delegated + 1
            )
            handler = _FakeHandler(
                {"Content-Length": str(hardening.MAX_REQUEST_BODY_BYTES + 1)}
            )
            hardening._guarded_do_post(handler)

            self.assertEqual(handler.delegated, 0)
            self.assertTrue(handler.close_connection)
            self.assertEqual(handler.sent[-1][1], 413)
            self.assertEqual(handler.sent[-1][2]["Connection"], "close")
        finally:
            hardening._ORIGINAL_DO_POST = old_delegate

    def test_guarded_post_delegates_normal_small_request_once(self):
        old_delegate = hardening._ORIGINAL_DO_POST
        try:
            hardening._ORIGINAL_DO_POST = lambda handler: setattr(
                handler, "delegated", handler.delegated + 1
            )
            handler = _FakeHandler({"Content-Length": "256"})
            hardening._guarded_do_post(handler)
            self.assertEqual(handler.delegated, 1)
            self.assertFalse(handler.close_connection)
            self.assertEqual(handler.sent, [])
        finally:
            hardening._ORIGINAL_DO_POST = old_delegate

    def test_authentication_mutation_wrapper_is_serialized(self):
        old_authenticate = hardening._ORIGINAL_AUTHENTICATE_PIN
        counter_lock = threading.Lock()
        active = 0
        max_active = 0

        def slow_authenticate(*args, **kwargs):
            nonlocal active, max_active
            with counter_lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.02)
            with counter_lock:
                active -= 1
            return 200, {"success": True}, None

        try:
            hardening._ORIGINAL_AUTHENTICATE_PIN = slow_authenticate
            threads = [
                threading.Thread(
                    target=hardening._locked_authenticate_mobile_pin,
                    args=("192.168.1.10", "123456"),
                )
                for _ in range(5)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=2)
                self.assertFalse(thread.is_alive())
            self.assertEqual(max_active, 1)
        finally:
            hardening._ORIGINAL_AUTHENTICATE_PIN = old_authenticate

    def test_install_composes_after_cookie_only_security_and_restores_cleanly(self):
        hardening.uninstall_mobile_http_hardening_for_tests()
        cookie_was_installed = mobile_cookie_security._INSTALLED
        if cookie_was_installed:
            original_cookie_do_post = server.MobileInventoryRequestHandler.do_POST
            original_cookie_check_auth = server.MobileInventoryRequestHandler.check_auth
        else:
            original_cookie_do_post = None
            original_cookie_check_auth = None

        try:
            hardening.install_mobile_http_hardening()
            self.assertIs(server.MobileInventoryRequestHandler.do_POST, hardening._guarded_do_post)
            self.assertIs(server.MobileInventoryRequestHandler.check_auth, hardening._locked_check_auth)
            self.assertIs(server.MobileInventoryServer.run, hardening._hardened_server_run)
            self.assertIs(server.MobileInventoryServer.stop, hardening._hardened_server_stop)
            self.assertIs(
                mobile_cookie_security.authenticate_mobile_pin,
                hardening._locked_authenticate_mobile_pin,
            )
            self.assertEqual(hardening._ORIGINAL_DO_POST.__module__, "mobile_cookie_security")
            self.assertEqual(hardening._ORIGINAL_CHECK_AUTH.__module__, "mobile_cookie_security")
        finally:
            hardening.uninstall_mobile_http_hardening_for_tests()
            if cookie_was_installed:
                self.assertIs(server.MobileInventoryRequestHandler.do_POST, original_cookie_do_post)
                self.assertIs(server.MobileInventoryRequestHandler.check_auth, original_cookie_check_auth)
            else:
                mobile_cookie_security.uninstall_mobile_cookie_security_for_tests()


if __name__ == "__main__":
    unittest.main()
