import datetime as dt
import unittest

from ui_dashboard import LOW_STOCK_THRESHOLD, build_dashboard_snapshot


class DashboardSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date(2026, 9, 7)

    def test_classifies_expired_near_expiry_and_low_stock_without_fake_thresholds(self):
        rows = [
            {
                "productId": 1,
                "productName": "Thuốc A",
                "batchId": 11,
                "lotNo": "A-OLD",
                "expiryDate": "2026-09-01",
                "fundSource": "BHYT",
                "stockBase": 20,
            },
            {
                "productId": 2,
                "productName": "Thuốc B",
                "batchId": 22,
                "lotNo": "B-NEAR",
                "expiryDate": "2026-10-01",
                "fundSource": "TCMR",
                "stockBase": 50,
            },
            {
                "productId": 3,
                "productName": "Vật tư C",
                "batchId": 33,
                "lotNo": "C-LOW",
                "expiryDate": "2028-01-01",
                "fundSource": "Ngân sách",
                "stockBase": LOW_STOCK_THRESHOLD,
            },
        ]

        snapshot = build_dashboard_snapshot(rows, today=self.today)

        self.assertEqual(snapshot["active_lot_count"], 3)
        self.assertEqual(snapshot["expired_count"], 1)
        self.assertEqual(snapshot["near_expiry_count"], 1)
        self.assertEqual(snapshot["low_stock_count"], 1)
        self.assertEqual(
            [row["status"] for row in snapshot["warning_rows"]],
            ["Đã hết hạn", "Cận hạn 24 ngày", "Tồn thấp ≤10"],
        )

    def test_same_physical_lot_split_by_fund_counts_as_one_active_lot(self):
        rows = [
            {
                "productId": 7,
                "productName": "Vaccine X",
                "batchId": 70,
                "lotNo": "VX70",
                "expiryDate": "2027-01-01",
                "fundSource": "A",
                "stockBase": 5,
            },
            {
                "productId": 7,
                "productName": "Vaccine X",
                "batchId": 70,
                "lotNo": "VX70",
                "expiryDate": "2027-01-01",
                "fundSource": "B",
                "stockBase": 8,
            },
        ]

        snapshot = build_dashboard_snapshot(rows, today=self.today)

        self.assertEqual(snapshot["active_lot_count"], 1)
        self.assertEqual(snapshot["low_stock_count"], 2)

    def test_non_positive_balances_do_not_appear_as_available_stock(self):
        rows = [
            {
                "productId": 9,
                "productName": "Không tồn",
                "batchId": 90,
                "lotNo": "ZERO",
                "expiryDate": "2026-09-08",
                "fundSource": "",
                "stockBase": 0,
            },
            {
                "productId": 10,
                "productName": "Âm",
                "batchId": 100,
                "lotNo": "NEG",
                "expiryDate": "2026-09-08",
                "fundSource": "",
                "stockBase": -1,
            },
        ]

        snapshot = build_dashboard_snapshot(rows, today=self.today)
        self.assertEqual(snapshot["active_lot_count"], 0)
        self.assertEqual(snapshot["warning_rows"], [])

    def test_expiring_and_low_stock_uses_expiry_as_higher_priority_status(self):
        rows = [
            {
                "productId": 12,
                "productName": "Thuốc D",
                "batchId": 120,
                "lotNo": "D1",
                "expiryDate": "2026-09-20",
                "fundSource": "BHYT",
                "stockBase": 2,
            }
        ]

        snapshot = build_dashboard_snapshot(rows, today=self.today)
        self.assertEqual(snapshot["near_expiry_count"], 1)
        self.assertEqual(snapshot["low_stock_count"], 1)
        self.assertEqual(snapshot["warning_rows"][0]["status"], "Cận hạn 13 ngày")


if __name__ == "__main__":
    unittest.main()
