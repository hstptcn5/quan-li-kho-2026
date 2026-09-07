# -*- coding: utf-8 -*-
"""H3.1 end-to-end mobile threading / SQLite ownership regression gate."""

from __future__ import annotations

import http.client
import inspect
import json
import os
import tempfile
import threading
import unittest

from database import DB
import mobile_cookie_security
import mobile_http_hardening as hardening
import server


class _FakeDesktopApp:
    """Minimal Tk-like owner that deliberately keeps a desktop DB connection."""

    def __init__(self, db):
        self.db = db
        self.refresh_requests = 0

    def after(self, _delay_ms, _callback):
        # The integration gate only verifies that workers schedule a refresh;
        # running Tk callbacks is outside this HTTP/SQLite ownership test.
        self.refresh_requests += 1

    def refresh_all_data(self):
        pass


class _LegacyServerHolder:
    def __init__(self, db):
        self.db_instance = db


class MobileThreadDatabaseIntegrationTests(unittest.TestCase):
    PIN = "246810"
    EXPECTED_CONNECTIONS = 3  # login + two concurrent dispatch requests

    def setUp(self):
        # Start from the unpatched legacy module, independent of test order.
        hardening.uninstall_mobile_http_hardening_for_tests()
        mobile_cookie_security.uninstall_mobile_cookie_security_for_tests()
        server.ACTIVE_TOKENS.clear()
        server.FAILED_ATTEMPTS.clear()
        server.SERVER_PIN = ""

        self.old_db_path = server.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "mobile-thread.db")
        server.DB_PATH = self.db_path

        # Intentionally leave this DB open on the main test thread. If a mobile
        # worker ever reuses it, sqlite3's default check_same_thread protection
        # will fail the request immediately.
        self.desktop_db = DB(self.db_path)
        self.desktop_db.conn.execute(
            "INSERT INTO products(id, name, defaultUnit) VALUES(901, 'Thuốc HTTP concurrent', 'Viên')"
        )
        self.desktop_db.conn.execute(
            "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(901, 'Viên', 1, 0)"
        )
        self.desktop_db.conn.commit()
        self.desktop_db.record_purchase(
            [{
                "productId": 901,
                "productName": "Thuốc HTTP concurrent",
                "qty": 10,
                "unitCode": "Viên",
                "lotNo": "LOT-HTTP",
                "expiryDate": "2030-12-31",
                "cost": 1000,
                "fundSource": "Nguồn A",
            }],
            "NCC seed",
            date_str="2026-09-01",
        )

        self.app = _FakeDesktopApp(self.desktop_db)
        hardening.install_mobile_http_hardening()
        server.SERVER_PIN = self.PIN

        # Use the production threaded HTTP class, but make the listener finite:
        # exactly three accepted connections are enough for this test. This
        # avoids a serve_forever/shutdown lifecycle inside unittest while still
        # exercising real BaseHTTPRequestHandler worker threads and sockets.
        self.httpd = hardening.HardenedThreadingHTTPServer(
            ("127.0.0.1", 0),
            server.MobileInventoryRequestHandler,
        )
        self.httpd.app_instance = self.app
        self.httpd.timeout = 10
        self.port = int(self.httpd.server_address[1])

        def serve_expected_connections():
            for _ in range(self.EXPECTED_CONNECTIONS):
                self.httpd.handle_request()

        self.listener_thread = threading.Thread(
            target=serve_expected_connections,
            name="h3.1-finite-http-listener",
            daemon=True,
        )
        self.listener_thread.start()

    def tearDown(self):
        try:
            if getattr(self, "listener_thread", None) is not None:
                self.listener_thread.join(timeout=15)
            if getattr(self, "httpd", None) is not None:
                self.httpd.server_close()
        finally:
            hardening.uninstall_mobile_http_hardening_for_tests()
            mobile_cookie_security.uninstall_mobile_cookie_security_for_tests()
            server.ACTIVE_TOKENS.clear()
            server.FAILED_ATTEMPTS.clear()
            server.SERVER_PIN = ""
            server.DB_PATH = self.old_db_path
            if getattr(self, "desktop_db", None) is not None:
                try:
                    self.desktop_db.conn.close()
                except Exception:
                    pass
            self.temp_dir.cleanup()

    def _post_json(self, path, payload, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
        }
        if cookie:
            headers["Cookie"] = cookie
        try:
            conn.request("POST", path, body=body, headers=headers)
            response = conn.getresponse()
            raw = response.read()
            data = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, data, response.getheader("Set-Cookie")
        finally:
            conn.close()

    def _login_cookie(self):
        status, payload, set_cookie = self._post_json("/api/auth", {"pin": self.PIN})
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload.get("success"), payload)
        self.assertNotIn("token", payload)
        self.assertIsNotNone(set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        return set_cookie.split(";", 1)[0]

    def test_threaded_http_dispatch_never_reuses_desktop_connection(self):
        """Two real HTTP workers race stock without sharing Tk's DB connection."""
        cookie = self._login_cookie()

        # H3.1 production contract: the legacy copied DB reference is actively
        # detached before MobileInventoryServer starts workers, and neither the
        # handler nor the hardened HTTP server carries that connection.
        legacy_holder = _LegacyServerHolder(self.desktop_db)
        self.assertIs(hardening.detach_legacy_desktop_db_reference(legacy_holder), legacy_holder)
        self.assertIsNone(legacy_holder.db_instance)
        self.assertFalse(hasattr(self.httpd, "db_instance"))

        run_source = inspect.getsource(hardening._hardened_server_run)
        self.assertIn("detach_legacy_desktop_db_reference(server_thread)", run_source)
        self.assertNotIn("server_thread.server.db_instance", run_source)

        handler_source = inspect.getsource(server.MobileInventoryRequestHandler)
        self.assertNotIn("self.server.db_instance", handler_source)
        self.assertNotIn("self.server.app_instance.db", handler_source)

        barrier = threading.Barrier(3)
        results = []
        results_lock = threading.Lock()

        def dispatch_worker(receiver):
            try:
                barrier.wait(timeout=5)
                result = self._post_json(
                    "/api/dispatch",
                    {
                        "items": [{
                            "productId": 901,
                            "qty": 7,
                            "unitCode": "Viên",
                            "fundSource": "Nguồn A",
                            "lotNo": "[Tự động - FEFO]",
                        }],
                        "receivingUnit": receiver,
                        "reason": "H3.1 concurrent HTTP",
                        "note": "integration gate",
                        "dispatchDate": "2026-09-02",
                    },
                    cookie=cookie,
                )
            except Exception as exc:
                result = (None, {"success": False, "exception": repr(exc)}, None)
            with results_lock:
                results.append(result)

        threads = [
            threading.Thread(target=dispatch_worker, args=("Đơn vị HTTP A",)),
            threading.Thread(target=dispatch_worker, args=("Đơn vị HTTP B",)),
        ]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=20)
            self.assertFalse(thread.is_alive())

        self.listener_thread.join(timeout=10)
        self.assertFalse(self.listener_thread.is_alive(), "Finite HTTP listener did not consume all expected requests")

        self.assertEqual(len(results), 2, results)
        successes = [r for r in results if r[0] == 200 and r[1].get("success") is True]
        rejections = [r for r in results if not (r[0] == 200 and r[1].get("success") is True)]
        self.assertEqual(len(successes), 1, results)
        self.assertEqual(len(rejections), 1, results)
        self.assertIsNotNone(rejections[0][0], rejections[0])

        # The original desktop-owned connection is still alive and usable only
        # from its owner thread, and sees the committed worker transaction.
        self.assertEqual(self.desktop_db.conn.execute("SELECT 1").fetchone()[0], 1)
        balance = self.desktop_db.conn.execute(
            "SELECT COALESCE(SUM(qtyBase), 0) FROM stock_movements WHERE productId=901"
        ).fetchone()[0]
        dispatch_notes = self.desktop_db.conn.execute(
            "SELECT COUNT(*) FROM dispatch_notes"
        ).fetchone()[0]
        negative = self.desktop_db.conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT productId, batchId, COALESCE(fundSource, '') AS fundSource,
                       SUM(COALESCE(qtyBase, qty)) AS balance
                FROM stock_movements
                GROUP BY productId, batchId, COALESCE(fundSource, '')
                HAVING balance < -0.0001
            )
            """
        ).fetchone()[0]

        self.assertAlmostEqual(float(balance), 3.0, places=4)
        self.assertEqual(dispatch_notes, 1)
        self.assertEqual(negative, 0)
        self.assertGreaterEqual(self.app.refresh_requests, 1)


if __name__ == "__main__":
    unittest.main()
