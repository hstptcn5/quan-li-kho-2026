# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import tempfile
import threading
import unittest

from database import DB


class ReliabilityConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "reliability.db")
        self.db = DB(self.db_path)

    def tearDown(self):
        try:
            if self.db and self.db.conn:
                self.db.conn.close()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def add_product(self, pid, name):
        self.db.conn.execute("INSERT INTO products(id,name,defaultUnit) VALUES(?,?,'Viên')", (pid, name))
        self.db.conn.execute("INSERT INTO product_units(productId,unitCode,toBaseQty,price) VALUES(?,'Viên',1,0)", (pid,))
        self.db.conn.commit()

    @staticmethod
    def purchase(pid, qty, lot):
        return {"productId": pid, "productName": f"SP {pid}", "qty": qty, "unitCode": "Viên", "lotNo": lot,
                "expiryDate": "2030-12-31", "cost": 1000.0, "fundSource": "Nguồn A"}

    @staticmethod
    def dispatch_item(pid, qty):
        return {"productId": pid, "productName": f"SP {pid}", "qty": qty, "unitCode": "Viên", "fundSource": "Nguồn A"}

    def test_two_concurrent_dispatches_cannot_oversell_same_stock(self):
        self.add_product(701, "Thuốc concurrency")
        self.db.record_purchase([self.purchase(701, 10, "LOT-C")], "NCC", date_str="2026-09-01")

        ready = threading.Barrier(3)
        successes, failures = [], []
        lock = threading.Lock()

        def worker(receiver):
            db = None
            try:
                # SQLite connections are intentionally created and used in the same
                # worker thread, matching the threaded mobile request lifecycle.
                db = DB(self.db_path)
                ready.wait(timeout=10)
                result = db.dispatch([self.dispatch_item(701, 7)], receiver, date_str="2026-09-02")
                with lock:
                    successes.append(result)
            except Exception as exc:
                with lock:
                    failures.append(exc)
            finally:
                if db is not None:
                    try:
                        db.conn.close()
                    except Exception:
                        pass

        threads = [threading.Thread(target=worker, args=(name,)) for name in ("Đơn vị A", "Đơn vị B")]
        for t in threads:
            t.start()
        ready.wait(timeout=15)
        for t in threads:
            t.join(timeout=20)

        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertEqual(len(successes), 1, successes)
        self.assertEqual(len(failures), 1, failures)

        check = DB(self.db_path)
        try:
            balance = float(check.conn.execute("SELECT COALESCE(SUM(qtyBase),0) FROM stock_movements WHERE productId=701").fetchone()[0])
            notes = check.conn.execute("SELECT COUNT(*) FROM dispatch_notes").fetchone()[0]
            negative = check.conn.execute("""
                SELECT COUNT(*) FROM (
                  SELECT productId,batchId,COALESCE(fundSource,'') fundSource,SUM(COALESCE(qtyBase,qty)) balance
                  FROM stock_movements GROUP BY productId,batchId,COALESCE(fundSource,'') HAVING balance < -0.0001
                )
            """).fetchone()[0]
            self.assertAlmostEqual(balance, 3.0, places=4)
            self.assertEqual(notes, 1)
            self.assertEqual(negative, 0)
        finally:
            check.conn.close()

    def test_concurrent_purchase_note_numbers_remain_unique(self):
        self.add_product(702, "Thuốc note number")
        count = 5
        ready = threading.Barrier(count + 1)
        results, errors = [], []
        lock = threading.Lock()

        def worker(i):
            db = None
            try:
                db = DB(self.db_path)
                ready.wait(timeout=10)
                _, note, _ = db.record_purchase([self.purchase(702, 1, f"LOT-{i}")], f"NCC {i}", date_str="2026-09-03")
                with lock:
                    results.append(note)
            except Exception as exc:
                with lock:
                    errors.append(exc)
            finally:
                if db is not None:
                    try: db.conn.close()
                    except Exception: pass

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
        for t in threads: t.start()
        ready.wait(timeout=15)
        for t in threads: t.join(timeout=20)

        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(sorted(results), [f"PN-030926-{i:03d}" for i in range(1, count + 1)])

    def test_purchase_failure_on_later_line_rolls_back_everything(self):
        self.add_product(703, "A")
        self.add_product(704, "B")
        with self.assertRaises(ValueError):
            self.db.record_purchase([self.purchase(703, 5, "LOT-A"), self.purchase(704, 0, "LOT-B")], "NCC", date_str="2026-09-04")
        for table in ("purchase_notes", "purchase_items", "stock_movements", "batches"):
            self.assertEqual(self.db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0, table)

    def test_dispatch_failure_on_later_line_rolls_back_first_line(self):
        self.add_product(705, "A")
        self.add_product(706, "B")
        self.db.record_purchase([self.purchase(705, 10, "LOT-A"), self.purchase(706, 10, "LOT-B")], "NCC", date_str="2026-09-01")
        with self.assertRaises(Exception):
            self.db.dispatch([self.dispatch_item(705, 5), self.dispatch_item(706, 20)], "Đơn vị", date_str="2026-09-05")
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM dispatch_notes").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM dispatch_items").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM stock_movements WHERE type='DISPATCH'").fetchone()[0], 0)

    def test_parallel_database_open_and_read_is_stable(self):
        self.add_product(707, "Parallel")
        self.db.record_purchase([self.purchase(707, 2, "LOT-P")], "NCC", date_str="2026-09-01")
        count = 4
        ready = threading.Barrier(count + 1)
        errors, results = [], []
        lock = threading.Lock()

        def worker():
            db = None
            try:
                ready.wait(timeout=5)
                db = DB(self.db_path)
                value = (db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0], len(db.get_inventory()))
                with lock: results.append(value)
            except Exception as exc:
                with lock: errors.append(exc)
            finally:
                if db is not None:
                    try: db.conn.close()
                    except Exception: pass

        threads = [threading.Thread(target=worker) for _ in range(count)]
        for t in threads: t.start()
        ready.wait(timeout=5)
        for t in threads: t.join(timeout=20)
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(results, [(1, 1)] * count)


if __name__ == "__main__":
    unittest.main()
