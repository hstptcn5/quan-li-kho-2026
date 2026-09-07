import os
import tempfile
import unittest

from database import DB
import db_lifecycle_hardening as hardening


class _FakeMobileServer:
    def __init__(self, fail=False):
        self.fail = fail
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1
        if self.fail:
            raise RuntimeError("stop failed")


class _FakeDb:
    def __init__(self, fail=False):
        self.fail = fail
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        if self.fail:
            raise RuntimeError("close failed")


class _FakeApp:
    def __init__(self, mobile_server=None, db=None):
        self.mobile_server = mobile_server
        self.db = db
        self.destroy_calls = 0

    def destroy(self):
        self.destroy_calls += 1


class DatabaseLifecycleHardeningTests(unittest.TestCase):
    def tearDown(self):
        hardening.uninstall_database_lifecycle_hardening_for_tests()

    def test_db_close_is_idempotent_and_context_manager_closes(self):
        hardening.install_database_lifecycle_hardening()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "lifecycle.db")
            db = DB(path)
            self.assertIsNotNone(db.conn)
            db.conn.execute("CREATE TABLE IF NOT EXISTS lifecycle_test (id INTEGER)")
            db.close()
            self.assertIsNone(db.conn)
            db.close()
            self.assertIsNone(db.conn)

            with DB(path) as scoped:
                self.assertIsNotNone(scoped.conn)
                scoped.conn.execute("INSERT INTO lifecycle_test(id) VALUES(1)")
                scoped.conn.commit()
            self.assertIsNone(scoped.conn)

    def test_context_manager_does_not_swallow_exceptions(self):
        hardening.install_database_lifecycle_hardening()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "lifecycle.db")
            db = None
            with self.assertRaisesRegex(RuntimeError, "boom"):
                with DB(path) as db:
                    raise RuntimeError("boom")
            self.assertIsNotNone(db)
            self.assertIsNone(db.conn)

    def test_enter_rejects_already_closed_database(self):
        hardening.install_database_lifecycle_hardening()
        with tempfile.TemporaryDirectory() as td:
            db = DB(os.path.join(td, "lifecycle.db"))
            db.close()
            with self.assertRaisesRegex(RuntimeError, "already closed"):
                db.__enter__()

    def test_app_shutdown_stops_mobile_then_closes_db_then_destroys(self):
        hardening.install_database_lifecycle_hardening()
        mobile = _FakeMobileServer()
        db = _FakeDb()
        app = _FakeApp(mobile, db)

        hardening.DatabaseLifecycleMixin.on_close(app)

        self.assertEqual(mobile.stop_calls, 1)
        self.assertEqual(db.close_calls, 1)
        self.assertEqual(app.destroy_calls, 1)

    def test_app_shutdown_continues_when_cleanup_steps_fail(self):
        hardening.install_database_lifecycle_hardening()
        mobile = _FakeMobileServer(fail=True)
        db = _FakeDb(fail=True)
        app = _FakeApp(mobile, db)

        hardening.DatabaseLifecycleMixin.on_close(app)

        self.assertEqual(mobile.stop_calls, 1)
        self.assertEqual(db.close_calls, 1)
        self.assertEqual(app.destroy_calls, 1)


if __name__ == "__main__":
    unittest.main()
