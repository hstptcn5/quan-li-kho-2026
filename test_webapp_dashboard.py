import datetime as dt
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import DB
from webapp.app import build_router
from webapp.services import dashboard as service
from webapp_testkit import Harness

HOSTILE_NAME = "<img src=x onerror=alert(1)> \"quote\" & 'apos' " + "Ư" * 300


class SeededDatabaseCase(unittest.TestCase):
    """Bốn sản phẩm: hết hạn, cận hạn, tồn thấp, bình thường (ngày tính theo hôm nay)."""

    def setUp(self):
        self.today = dt.date.today()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = os.path.join(self.tmp.name, "dashboard.db")
        self.db = DB(self.db_path)
        self.addCleanup(self.db.conn.close)
        self.add_product(1, "Thuốc hết hạn", "L-EXP", -10, 20)
        self.add_product(2, "Thuốc cận hạn", "L-NEAR", 30, 50)
        self.add_product(3, "Vật tư tồn thấp", "L-LOW", 800, 5)
        self.add_product(4, "Thuốc bình thường", "L-OK", 900, 100)

    def iso(self, days_from_today):
        return (self.today + dt.timedelta(days=days_from_today)).isoformat()

    def add_product(self, product_id, name, lot, expiry_offset_days, qty, fund="BHYT"):
        self.db.conn.execute(
            "INSERT INTO products(id, name, defaultUnit) VALUES(?, ?, 'Viên')", (product_id, name)
        )
        self.db.conn.execute(
            "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
            (product_id,),
        )
        self.db.conn.commit()
        self.db.record_purchase(
            [{
                "productId": product_id, "productName": name, "qty": qty, "unitCode": "Viên",
                "lotNo": lot, "expiryDate": self.iso(expiry_offset_days), "cost": 1000,
                "fundSource": fund,
            }],
            "NCC", "Nhập kho", "",
        )


class DashboardServiceTests(SeededDatabaseCase):
    def test_cards_match_the_tkinter_dashboard_logic(self):
        summary = self.db.dashboard_summary(service.WARNING_DAYS)
        snapshot = service.build_dashboard_snapshot(self.db.get_inventory(), warning_days=service.WARNING_DAYS)
        payload = service.build_dashboard_payload(self.db)
        self.assertEqual(payload["cards"], {
            "productCount": int(summary["product_count"]),
            "activeLotCount": snapshot["active_lot_count"],
            "nearExpiryCount": snapshot["near_expiry_count"],
            "expiredCount": snapshot["expired_count"],
            "lowStockCount": snapshot["low_stock_count"],
        })
        self.assertEqual(
            payload["cards"],
            {"productCount": 4, "activeLotCount": 4, "nearExpiryCount": 1, "expiredCount": 1, "lowStockCount": 1},
        )

    def test_counts_cover_the_whole_warning_set(self):
        payload = service.build_dashboard_payload(self.db)
        self.assertEqual(payload["warnings"]["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})
        self.assertEqual(payload["warningDays"], 90)
        self.assertEqual(payload["lowStockThreshold"], 10)

    def test_rows_follow_the_contract_and_severity_order(self):
        rows = service.build_dashboard_payload(self.db)["warnings"]["rows"]
        self.assertEqual([r["severity"] for r in rows], [0, 2, 3])
        self.assertEqual(
            set(rows[0]),
            {"productId", "batchId", "productName", "lotNo", "expiryDate", "fundSource",
             "stockBase", "status", "severity", "daysLeft"},
        )
        self.assertEqual(rows[0]["productName"], "Thuốc hết hạn")
        self.assertEqual(rows[0]["status"], "Đã hết hạn")

    def test_filter_selects_one_group_and_leaves_counts_unchanged(self):
        for flt, severity in (("expired", 0), ("near", 2), ("low", 3)):
            with self.subTest(flt=flt):
                warnings = service.build_dashboard_payload(self.db, flt=flt)["warnings"]
                self.assertEqual([r["severity"] for r in warnings["rows"]], [severity])
                self.assertEqual(warnings["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})

    def test_limit_is_applied_after_the_filter(self):
        # Nếu cắt trước rồi mới lọc, dòng "low" (xếp sau cùng) sẽ biến mất.
        warnings = service.build_dashboard_payload(self.db, flt="low", limit=1)["warnings"]
        self.assertEqual([r["productName"] for r in warnings["rows"]], ["Vật tư tồn thấp"])
        all_rows = service.build_dashboard_payload(self.db, limit=1)["warnings"]["rows"]
        self.assertEqual(len(all_rows), 1)

    def test_invalid_parameters_are_rejected(self):
        for kwargs in (
            {"flt": "bogus"}, {"flt": ""}, {"flt": None},
            {"limit": 0}, {"limit": -1}, {"limit": service.MAX_LIMIT + 1},
            {"limit": True}, {"limit": "5"}, {"limit": 2.5},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    service.build_dashboard_payload(self.db, **kwargs)

    def test_limit_boundaries_are_accepted(self):
        service.build_dashboard_payload(self.db, limit=1)
        service.build_dashboard_payload(self.db, limit=service.MAX_LIMIT)

    def test_hostile_text_is_returned_verbatim(self):
        self.add_product(5, HOSTILE_NAME, "L-<b>", -5, 7, fund="Quỹ <i>x</i>")
        rows = service.build_dashboard_payload(self.db)["warnings"]["rows"]
        hostile = [r for r in rows if r["productId"] == 5][0]
        self.assertEqual(hostile["productName"], HOSTILE_NAME)
        self.assertEqual(hostile["lotNo"], "L-<b>")
        self.assertEqual(hostile["fundSource"], "Quỹ <i>x</i>")

    def test_activities_are_the_ten_newest_audit_rows(self):
        for i in range(12):
            self.db.conn.execute(
                "INSERT INTO audit_logs(timestamp, action, details) VALUES(?, ?, ?)",
                (f"2099-01-{i + 1:02d} 08:00:00", f"ACT{i}", f"chi tiết {i}"),  # tương lai: luôn mới hơn các dòng NHAP_KHO lúc dựng dữ liệu
            )
        self.db.conn.commit()
        activities = service.build_dashboard_payload(self.db)["activities"]
        self.assertEqual(len(activities), 10)
        self.assertEqual([a["action"] for a in activities][:3], ["ACT11", "ACT10", "ACT9"])
        self.assertEqual(set(activities[0]), {"timestamp", "action", "details"})

    def test_runtime_reports_backup_temperature_and_negative_stock(self):
        runtime = service.build_dashboard_payload(self.db)["runtime"]
        self.assertEqual(set(runtime), {"lastBackup", "latestTemperature", "negativeStockRows"})
        self.assertIsNone(runtime["latestTemperature"])
        self.assertEqual(runtime["negativeStockRows"], 0)

        self.db.add_temperature_log("2026-09-30", "Sáng", "Kho lạnh 1", 24.5, 55.0, "Thủ kho")
        # Bỏ qua bất biến tồn không âm bằng SQL trực tiếp để kiểm tra đếm thật.
        self.db.conn.execute(
            "INSERT INTO stock_movements(productId, batchId, unitCode, qty, qtyBase, type) "
            "SELECT productId, id, 'Viên', -500, -500, 'ADJUST' FROM batches WHERE lotNo='L-OK'"
        )
        self.db.conn.commit()
        runtime = service.build_dashboard_payload(self.db)["runtime"]
        self.assertEqual(
            runtime["latestTemperature"],
            {"logDate": "2026-09-30", "session": "Sáng", "locationName": "Kho lạnh 1",
             "temperature": 24.5, "humidity": 55.0, "recordedBy": "Thủ kho"},
        )
        self.assertEqual(runtime["negativeStockRows"], 1)
        last_backup = runtime["lastBackup"]
        self.assertTrue(last_backup is None or set(last_backup) == {"file", "created"})


class EmptyDatabaseTests(unittest.TestCase):
    def test_empty_database_gives_zero_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DB(os.path.join(tmp, "empty.db"))
            try:
                payload = service.build_dashboard_payload(db)
            finally:
                db.conn.close()
        self.assertEqual(
            payload["cards"],
            {"productCount": 0, "activeLotCount": 0, "nearExpiryCount": 0, "expiredCount": 0, "lowStockCount": 0},
        )
        self.assertEqual(payload["warnings"], {"counts": {"all": 0, "expired": 0, "near": 0, "low": 0}, "rows": []})
        self.assertEqual(payload["activities"], [])
        self.assertIsNone(payload["runtime"]["latestTemperature"])


class WarningCategoryTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(service.warning_category(0), "expired")
        self.assertEqual(service.warning_category(1), "expired")
        self.assertEqual(service.warning_category(2), "near")
        self.assertEqual(service.warning_category(3), "low")


class DashboardApiTests(SeededDatabaseCase):
    def setUp(self):
        super().setUp()
        self.web_root = Path(self.tmp.name) / "web"
        self.web_root.mkdir()
        self.harness = Harness(self, build_router(lambda: DB(self.db_path)), self.web_root)
        self.harness.login()

    def get(self, query=""):
        return self.harness.json("GET", "/api/dashboard" + query)

    def test_requires_authentication(self):
        status, _, payload = self.harness.json("GET", "/api/dashboard", cookie="")
        self.assertEqual(status, 401)
        self.assertTrue(payload["auth_required"])

    def test_returns_the_documented_contract(self):
        status, headers, payload = self.get()
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(
            set(payload),
            {"success", "warningDays", "lowStockThreshold", "cards", "warnings", "activities", "runtime"},
        )
        self.assertEqual(set(payload["warnings"]), {"counts", "rows"})
        self.assertEqual(payload["warnings"]["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertIn("default-src 'self'", headers["content-security-policy"])

    def test_filter_and_limit_query_parameters(self):
        _, _, payload = self.get("?filter=near&limit=5")
        self.assertEqual([r["severity"] for r in payload["warnings"]["rows"]], [2])
        _, _, payload = self.get("?filter=low&limit=1")
        self.assertEqual([r["productName"] for r in payload["warnings"]["rows"]], ["Vật tư tồn thấp"])
        _, _, payload = self.get("?limit=500")
        self.assertEqual(len(payload["warnings"]["rows"]), 3)

    def test_invalid_query_parameters_are_400(self):
        for query in (
            "?filter=bogus", "?filter=", "?limit=0", "?limit=501", "?limit=abc",
            "?limit=", "?limit=2.5", "?limit=-3",
        ):
            with self.subTest(query=query):
                status, _, payload = self.get(query)
                self.assertEqual(status, 400)
                self.assertFalse(payload["success"])
                self.assertTrue(payload["message"])

    def test_database_error_is_reported_without_internal_details(self):
        def broken_factory():
            raise sqlite3.OperationalError(r"database is locked: C:\Users\secret\pharm.db")

        harness = Harness(self, build_router(broken_factory), self.web_root)
        harness.login()
        with self.assertLogs("webapp.routing", level="ERROR"):
            status, _, payload = harness.json("GET", "/api/dashboard")
        self.assertEqual(status, 500)
        self.assertEqual(payload, {"success": False, "message": "Lỗi hệ thống"})

    def test_hostile_text_survives_the_json_round_trip(self):
        self.add_product(5, HOSTILE_NAME, "L-<b>", -5, 7)
        _, _, payload = self.get("?filter=expired&limit=500")
        names = [row["productName"] for row in payload["warnings"]["rows"]]
        self.assertIn(HOSTILE_NAME, names)

    def test_database_connection_is_closed_after_each_request(self):
        opened = []

        def tracking_factory():
            db = DB(self.db_path)
            opened.append(db)
            return db

        harness = Harness(self, build_router(tracking_factory), self.web_root)
        harness.login()
        self.assertEqual(harness.json("GET", "/api/dashboard")[0], 200)
        self.assertEqual(len(opened), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].conn.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
