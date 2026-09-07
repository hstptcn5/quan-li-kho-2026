# -*- coding: utf-8 -*-
"""H2.3 reliability/concurrency tests using real SQLite connections.

These tests intentionally avoid mocks for the core transaction races.  They exercise
multiple DB instances against the same WAL database so the same lock/transaction
behavior used by the desktop and threaded mobile server is covered on Windows CI.
"""

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
            if getattr(self, "db", None) is not None and getattr(self.db, "conn", None) is not None:
                self.db.conn.close()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def _add_product(self, product_id: int, name: str):
        self.db.conn.execute(
            "INSERT INTO products(id, name, defaultUnit) VALUES(?, ?, 'Viên')",
            (product_id, name),
        )
        self.db.conn.execute(
            "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
            (product_id,),
        )
        self.db.conn.commit()

    @staticmethod
    def _purchase_item(product_id: int, qty: float, lot: str, fund: str = "Nguồn A"):
        return {
            "productId": product_id,
            "productName": f"SP {product_id}",
            "qty": qty,
            "unitCode": "Viên",
            "lotNo": lot,
            "expiryDate": "2030-12-31",
            "cost": 1000.0,
            "fundSource": fund,
        }

    @staticmethod
    def _dispatch_item(product_id: int, qty: float, fund: str = "Nguồn A"):
        return {
            "productId": product_id,
            "productName": f"SP {product_id}",
            "qty": qty,
            "unitCode": "Viên",
            "fundSource": fund,
        }

    def test_two_concurrent_dispatches_cannot_oversell_same_stock(self):
        """Two independent writers requesting 7/10 stock: exactly one may commit."""
        self._add_product(701, "Thuốc concurrency")
        self.db.record_purchase(
            [self._purchase_item(701, 10, "LOT-C")],
            "NCC",
            date_str="2026-09-01",
        )

        # Open both DB connections before releasing the workers so the race is only
        # over the transaction, not Python object construction.
        db_a = DB(self.db_path)
        db_b = DB(self.db_path)
        barrier = threading.Barrier(3)
        successes = []
        failures = []
        result_lock = threading.Lock()

        def worker(db, receiver):
            try:
                barrier.wait(timeout=5)
                result = db.dispatch(
                    [self._dispatch_item(701, 7)],
                    receiver,
                    date_str="2026-09-02",
                )
                with result_lock:
                    successes.append(result)
            except Exception as exc:
                with result_lock:
                    failures.append(exc)
            finally:
                try:
                    db.conn.close()
                except Exception:
                    pass

        t1 = threading.Thread(target=worker, args=(db_a, "Đơn vị A"))
        t2 = threading.Thread(target=worker, args=(db_b, "Đơn vị B"))
        t1.start()
        t2.start()
        barrier.wait(timeout=5)
        t1.join(timeout=15)
        t2.join(timeout=15)

        self.assertFalse(t1.is_alive())
        self.assertFalse(t2.is_alive())
        self.assertEqual(len(successes), 1, successes)
        self.assertEqual(len(failures), 1, failures)

        check = DB(self.db_path)
        try:
            balance = check.conn.execute(
                "SELECT COALESCE(SUM(qtyBase), 0) FROM stock_movements WHERE productId=701"
            ).fetchone()[0]
            dispatch_notes = check.conn.execute("SELECT COUNT(*) FROM dispatch_notes").fetchone()[0]
            negative = check.conn.execute(
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
        finally:
            check.conn.close()

    def test_concurrent_purchase_note_numbers_remain_unique(self):
        """Concurrent writers must serialize note-number allocation and commits."""
        self._add_product(702, "Thuốc note number")
        worker_count = 5
        barrier = threading.Barrier(worker_count + 1)
        results = []
        errors = []
        result_lock = threading.Lock()

        def worker(index: int):
            db = None
            try:
                db = DB(self.db_path)
                barrier.wait(timeout=10)
                _, note_number, _ = db.record_purchase(
                    [self._purchase_item(702, 1, f"LOT-{index}")],
                    f"NCC {index}",
                    date_str="2026-09-03",
                )
                with result_lock:
                    results.append(note_number)
            except Exception as exc:
                with result_lock:
                    errors.append(exc)
            finally:
                if db is not None:
                    try:
                        db.conn.close()
                    except Exception:
                        pass

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(worker_count)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=15)
        for thread in threads:
            thread.join(timeout=20)

        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(len(results), worker_count)
        self.assertEqual(len(set(results)), worker_count)
        self.assertEqual(
            sorted(results),
            [f"PN-030926-{i:03d}" for i in range(1, worker_count + 1)],
        )

        check = DB(self.db_path)
        try:
            notes = check.conn.execute("SELECT COUNT(*) FROM purchase_notes").fetchone()[0]
            movements = check.conn.execute(
                "SELECT COUNT(*) FROM stock_movements WHERE productId=702 AND type='PURCHASE'"
            ).fetchone()[0]
            balance = check.conn.execute(
                "SELECT COALESCE(SUM(qtyBase), 0) FROM stock_movements WHERE productId=702"
            ).fetchone()[0]
            self.assertEqual(notes, worker_count)
            self.assertEqual(movements, worker_count)
            self.assertAlmostEqual(float(balance), float(worker_count), places=4)
        finally:
            check.conn.close()

    def test_purchase_failure_on_later_line_rolls_back_everything(self):
        """A late validation failure cannot leave note, batch or movement fragments."""
        self._add_product(703, "Thuốc rollback A")
        self._add_product(704, "Thuốc rollback B")

        with self.assertRaises(ValueError):
            self.db.record_purchase(
                [
                    self._purchase_item(703, 5, "LOT-VALID"),
                    self._purchase_item(704, 0, "LOT-INVALID"),
                ],
                "NCC rollback",
                date_str="2026-09-04",
            )

        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM purchase_notes").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM purchase_items").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0], 0)

    def test_dispatch_failure_on_later_line_rolls_back_first_line(self):
        """If a later product cannot be fulfilled, earlier dispatch writes disappear."""
        self._add_product(705, "Thuốc dispatch rollback A")
        self._add_product(706, "Thuốc dispatch rollback B")
        self.db.record_purchase(
            [
                self._purchase_item(705, 10, "LOT-A"),
                self._purchase_item(706, 10, "LOT-B"),
            ],
            "NCC seed",
            date_str="2026-09-01",
        )

        with self.assertRaises(Exception):
            self.db.dispatch(
                [
                    self._dispatch_item(705, 5),
                    self._dispatch_item(706, 20),
                ],
                "Đơn vị rollback",
                date_str="2026-09-05",
            )

        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM dispatch_notes").fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM dispatch_items").fetchone()[0], 0)
        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) FROM stock_movements WHERE type='DISPATCH'").fetchone()[0],
            0,
        )
        balances = {
            row[0]: float(row[1])
            for row in self.db.conn.execute(
                "SELECT productId, SUM(qtyBase) FROM stock_movements GROUP BY productId"
            ).fetchall()
        }
        self.assertAlmostEqual(balances[705], 10.0, places=4)
        self.assertAlmostEqual(balances[706], 10.0, places=4)

    def test_parallel_database_open_and_read_is_stable(self):
        """Threaded mobile-style independent DB instances can open/read in parallel."""
        self._add_product(707, "Thuốc parallel open")
        self.db.record_purchase(
            [self._purchase_item(707, 2, "LOT-P")],
            "NCC",
            date_str="2026-09-01",
        )

        worker_count = 4
        barrier = threading.Barrier(worker_count + 1)
        errors = []
        counts = []
        result_lock = threading.Lock()

        def worker():
            db = None
            try:
                barrier.wait(timeout=5)
                db = DB(self.db_path)
                count = db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                inventory = db.get_inventory()
                with result_lock:
                    counts.append((count, len(inventory)))
            except Exception as exc:
                with result_lock:
                    errors.append(exc)
            finally:
                if db is not None:
                    try:
                        db.conn.close()
                    except Exception:
                        pass

        threads = [threading.Thread(target=worker) for _ in range(worker_count)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=20)

        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(len(counts), worker_count)
        self.assertTrue(all(product_count == 1 and inventory_count == 1 for product_count, inventory_count in counts))


if __name__ == "__main__":
    unittest.main()
