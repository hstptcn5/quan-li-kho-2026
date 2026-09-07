import datetime as dt
import unittest

from ui_catalog import build_catalog_rows, filter_catalog_rows


class CatalogModelTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date(2026, 9, 7)
        self.products = [
            {"id": 1, "name": "Cefotaxim 1g", "defaultUnit": "lọ", "barcode": "111", "productType": "thuoc", "registrationNumber": "VD-1"},
            {"id": 2, "name": "Vaccine B", "defaultUnit": "liều", "barcode": "222", "productType": "vaccine", "registrationNumber": "VX-2"},
            {"id": 3, "name": "Bơm kim", "defaultUnit": "cái", "barcode": "333", "productType": "vtyt", "registrationNumber": ""},
        ]
        self.inventory = [
            {"productId": 1, "batchId": 10, "expiryDate": "2026-10-01", "fundSource": "BHYT", "stockBase": 6},
            {"productId": 1, "batchId": 10, "expiryDate": "2026-10-01", "fundSource": "Ngân sách", "stockBase": 4},
            {"productId": 2, "batchId": 20, "expiryDate": "2026-08-01", "fundSource": "TCMR", "stockBase": 20},
        ]

    def test_aggregates_fund_splits_without_double_counting_physical_lot(self):
        rows = build_catalog_rows(self.products, self.inventory, today=self.today)
        cef = next(row for row in rows if row["id"] == 1)
        self.assertEqual(cef["totalStock"], 10)
        self.assertEqual(cef["lotCount"], 1)
        self.assertEqual(cef["fundSources"], ["BHYT", "Ngân sách"])
        self.assertEqual(cef["status"], "Cận hạn")
        self.assertEqual(cef["nearestExpiry"], "2026-10-01")

    def test_marks_expired_and_out_of_stock_from_real_balances(self):
        rows = build_catalog_rows(self.products, self.inventory, today=self.today)
        vaccine = next(row for row in rows if row["id"] == 2)
        supply = next(row for row in rows if row["id"] == 3)
        self.assertEqual(vaccine["status"], "Có lô hết hạn")
        self.assertEqual(supply["status"], "Hết tồn")
        self.assertEqual(supply["lotCount"], 0)

    def test_filters_by_name_barcode_registration_type_status_and_fund(self):
        rows = build_catalog_rows(self.products, self.inventory, today=self.today)
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, keyword="cefo")], [1])
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, keyword="222")], [2])
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, keyword="VD-1")], [1])
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, product_type="vtyt")], [3])
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, stock_status="Có lô hết hạn")], [2])
        self.assertEqual([r["id"] for r in filter_catalog_rows(rows, fund_source="BHYT")], [1])

    def test_negative_or_zero_net_stock_is_not_presented_as_available(self):
        inventory = [
            {"productId": 1, "batchId": 10, "expiryDate": "2027-01-01", "fundSource": "BHYT", "stockBase": -2},
        ]
        rows = build_catalog_rows(self.products[:1], inventory, today=self.today)
        self.assertEqual(rows[0]["status"], "Hết tồn")
        self.assertEqual(rows[0]["lotCount"], 0)
        self.assertEqual(rows[0]["nearestExpiry"], "")


if __name__ == "__main__":
    unittest.main()
