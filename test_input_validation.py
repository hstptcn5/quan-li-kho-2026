# -*- coding: utf-8 -*-
"""Regression gate: NaN / Infinity must never reach stock or cost columns.

Python's ``json`` accepts the literals ``NaN`` and ``Infinity`` and ``float()``
accepts the strings "nan" / "inf" / "1e309". Because ``nan <= 0`` is False, a
plain ``<= 0`` check lets them through. A purchase of ``qty=Infinity`` with an
explicit ``totalAmount`` used to be stored as ``inf`` stock, which poisons every
SUM over that product permanently.
"""

import http.client
import json
import math
import os
import tempfile
import threading
import time
import unittest

import mobile_cookie_security
import mobile_http_hardening as hardening
import server
from database import DB

NON_FINITE = (float("inf"), float("-inf"), float("nan"), "inf", "nan", "1e309")


class _TempDbCase(unittest.TestCase):
    PRODUCT_ID = 901

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = os.path.join(self.temp_dir.name, "input-validation.db")
        self.db = DB(self.db_path)
        self.addCleanup(self._close_db)
        self.db.conn.execute(
            "INSERT INTO products(id, name, defaultUnit) VALUES(?, 'Thuốc kiểm tra', 'Viên')",
            (self.PRODUCT_ID,),
        )
        self.db.conn.execute(
            "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
            (self.PRODUCT_ID,),
        )
        self.db.conn.commit()

    def _close_db(self):
        try:
            self.db.conn.close()
        except Exception:
            pass

    def purchase_item(self, **overrides):
        item = {
            "productId": self.PRODUCT_ID,
            "qty": 10,
            "unitCode": "Viên",
            "lotNo": "LOT-1",
            "expiryDate": "2030-12-31",
            "cost": 1000,
            "fundSource": "",
        }
        item.update(overrides)
        return item

    def count(self, table):
        return self.db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def stock_total(self):
        return self.db.conn.execute(
            "SELECT COALESCE(SUM(qtyBase), 0) FROM stock_movements WHERE productId=?",
            (self.PRODUCT_ID,),
        ).fetchone()[0]


class DatabaseNonFiniteNumberTests(_TempDbCase):
    def assert_purchase_rejected(self, **overrides):
        tables = ("purchase_notes", "purchase_items", "stock_movements")
        before = {table: self.count(table) for table in tables}
        with self.assertRaises(ValueError):
            self.db.record_purchase([self.purchase_item(**overrides)], "NCC", "Nhập kho", "")
        self.assertEqual({table: self.count(table) for table in tables}, before)

    def test_purchase_rejects_non_finite_quantity_even_with_explicit_total_amount(self):
        for qty in NON_FINITE:
            with self.subTest(qty=qty):
                self.assert_purchase_rejected(qty=qty, totalAmount=100)

    def test_purchase_rejects_non_finite_total_amount(self):
        for total in NON_FINITE:
            with self.subTest(totalAmount=total):
                self.assert_purchase_rejected(qty=5, totalAmount=total)

    def test_purchase_rejects_non_finite_cost(self):
        for cost in NON_FINITE:
            with self.subTest(cost=cost):
                self.assert_purchase_rejected(qty=5, cost=cost)

    def test_purchase_still_accepts_normal_values(self):
        self.db.record_purchase(
            [self.purchase_item(qty=12.5, totalAmount=2500)], "NCC", "Nhập kho", ""
        )
        self.assertEqual(self.stock_total(), 12.5)
        self.assertTrue(math.isfinite(self.stock_total()))

    def test_dispatch_rejects_non_finite_quantity_and_leaves_stock_untouched(self):
        self.db.record_purchase([self.purchase_item(qty=10)], "NCC", "Nhập kho", "")
        for qty in NON_FINITE:
            with self.subTest(qty=qty):
                with self.assertRaises(ValueError):
                    self.db.dispatch(
                        [{"productId": self.PRODUCT_ID, "qty": qty, "unitCode": "Viên"}],
                        "Khoa A", "Cấp phát", "",
                    )
                self.assertEqual(self.count("dispatch_notes"), 0)
                self.assertEqual(self.stock_total(), 10)


class MobileApiNonFiniteNumberTests(_TempDbCase):
    def setUp(self):
        super().setUp()
        # Start from the unpatched module, then install the production
        # cookie-only + hardened-server stack exactly as quanly_xnt.App does.
        hardening.uninstall_mobile_http_hardening_for_tests()
        mobile_cookie_security.uninstall_mobile_cookie_security_for_tests()
        hardening.install_mobile_http_hardening()
        self.addCleanup(self._uninstall_mobile_stack)

        self.old_db_path = server.DB_PATH
        server.DB_PATH = self.db_path
        self.token = "test-session-token"
        server.ACTIVE_TOKENS.clear()
        server.ACTIVE_TOKENS[self.token] = {"ip": "127.0.0.1", "expiry": time.time() + 3600}

        self.httpd = hardening.HardenedThreadingHTTPServer(
            ("127.0.0.1", 0), server.MobileInventoryRequestHandler
        )
        self.port = int(self.httpd.server_address[1])
        thread = threading.Thread(
            target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        thread.start()
        self.addCleanup(self._stop_http, thread)

    def _uninstall_mobile_stack(self):
        server.ACTIVE_TOKENS.clear()
        server.FAILED_ATTEMPTS.clear()
        server.DB_PATH = self.old_db_path
        hardening.uninstall_mobile_http_hardening_for_tests()
        mobile_cookie_security.uninstall_mobile_cookie_security_for_tests()

    def _stop_http(self, thread):
        self.httpd.shutdown()
        self.httpd.server_close()
        thread.join(timeout=5)

    def post(self, path, payload):
        # json.dumps emits the literal Infinity / NaN, exactly what a hostile or
        # buggy client can send and Python's json.loads will accept.
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(
                "POST", path, body=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Cookie": f"{server.SESSION_COOKIE_NAME}={self.token}",
                    "Connection": "close",
                },
            )
            response = conn.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            conn.close()

    def test_api_purchase_rejects_infinite_quantity_with_total_amount(self):
        status, body = self.post("/api/purchase", {
            "productId": self.PRODUCT_ID, "qty": float("inf"), "totalAmount": 100,
            "lotNo": "LOT-INF", "expiryDate": "2030-12-31",
        })
        self.assertEqual(status, 400, body)
        self.assertFalse(body["success"])
        self.assertEqual(self.count("stock_movements"), 0)
        self.assertEqual(self.count("purchase_notes"), 0)

    def test_api_purchase_rejects_nan_total_amount(self):
        status, body = self.post("/api/purchase", {
            "productId": self.PRODUCT_ID, "qty": 5, "totalAmount": float("nan"),
            "lotNo": "LOT-NAN", "expiryDate": "2030-12-31",
        })
        self.assertEqual(status, 400, body)
        self.assertEqual(self.count("stock_movements"), 0)

    def test_api_dispatch_rejects_non_finite_quantity(self):
        self.db.record_purchase([self.purchase_item(qty=10)], "NCC", "Nhập kho", "")
        for qty in (float("inf"), float("nan")):
            with self.subTest(qty=qty):
                status, body = self.post("/api/dispatch", {
                    "productId": self.PRODUCT_ID, "qty": qty,
                })
                self.assertEqual(status, 400, body)
                self.assertEqual(self.count("dispatch_notes"), 0)
                self.assertEqual(self.stock_total(), 10)

    def test_api_purchase_still_accepts_normal_request(self):
        status, body = self.post("/api/purchase", {
            "productId": self.PRODUCT_ID, "qty": 4, "totalAmount": 400,
            "lotNo": "LOT-OK", "expiryDate": "2030-12-31",
        })
        self.assertEqual(status, 200, body)
        self.assertTrue(body["success"])
        self.assertEqual(self.stock_total(), 4)


if __name__ == "__main__":
    unittest.main()
