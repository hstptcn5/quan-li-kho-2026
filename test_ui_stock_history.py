# -*- coding: utf-8 -*-
import datetime as dt
import unittest

from ui_stock_history import StockHistoryUiMixin, build_stock_snapshot


class StockSnapshotTests(unittest.TestCase):
    def test_counts_physical_lots_once_across_fund_splits(self):
        rows = [
            {
                "productId": 1,
                "batchId": 10,
                "productName": "Vaccine A",
                "lotNo": "L1",
                "expiryDate": "2026-09-20",
                "fundSource": "Ngân sách",
                "stockBase": 5,
            },
            {
                "productId": 1,
                "batchId": 10,
                "productName": "Vaccine A",
                "lotNo": "L1",
                "expiryDate": "2026-09-20",
                "fundSource": "TCMR",
                "stockBase": 7,
            },
            {
                "productId": 2,
                "batchId": 20,
                "productName": "VTYT B",
                "lotNo": "L2",
                "expiryDate": "2027-12-31",
                "fundSource": "Ngân sách",
                "stockBase": 3,
            },
        ]
        snap = build_stock_snapshot(rows, today=dt.date(2026, 9, 7))
        self.assertEqual(snap["product_count"], 2)
        self.assertEqual(snap["physical_lot_count"], 2)
        self.assertEqual(snap["fund_balance_count"], 3)
        self.assertEqual(snap["near_lot_count"], 1)
        self.assertEqual(snap["expired_lot_count"], 0)

    def test_expired_and_near_expiry_are_classified_from_real_expiry_dates(self):
        rows = [
            {"productId": 1, "batchId": 1, "productName": "A", "lotNo": "OLD", "expiryDate": "2026-09-01", "fundSource": "", "stockBase": 1},
            {"productId": 2, "batchId": 2, "productName": "B", "lotNo": "NEAR", "expiryDate": "2026-10-01", "fundSource": "", "stockBase": 1},
            {"productId": 3, "batchId": 3, "productName": "C", "lotNo": "OK", "expiryDate": "2027-10-01", "fundSource": "", "stockBase": 1},
            {"productId": 4, "batchId": 4, "productName": "D", "lotNo": "ZERO", "expiryDate": "2026-09-01", "fundSource": "", "stockBase": 0},
        ]
        snap = build_stock_snapshot(rows, today=dt.date(2026, 9, 7))
        self.assertEqual([row["statusKey"] for row in snap["rows"]], ["expired", "near", "ok"])
        self.assertEqual(snap["expired_lot_count"], 1)
        self.assertEqual(snap["near_lot_count"], 1)

    def test_ui_mixin_does_not_override_document_mutation_or_print_implementation(self):
        owned = set(StockHistoryUiMixin.__dict__)
        forbidden = {
            "delete_purchase_note",
            "delete_dispatch_note",
            "reprint_selected_purchase",
            "reprint_selected_dispatch",
            "print_purchase_note",
            "print_dispatch_note",
            "record_purchase",
            "dispatch",
        }
        self.assertTrue(forbidden.isdisjoint(owned))
        self.assertIn("build_stock_tab", owned)
        self.assertIn("refresh_stock", owned)


if __name__ == "__main__":
    unittest.main()
