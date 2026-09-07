import os
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest import mock

from config import SCHEMA_VERSION
from managers import BackupManager
import backup_restore_hardening as hardening


class BackupRestoreHardeningTests(unittest.TestCase):
    def setUp(self):
        hardening.install_backup_restore_hardening()
        self.td = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.td.name, "live.db")
        self.backup_dir = os.path.join(self.td.name, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self._init_db(self.db_path, value="LIVE")
        self.manager = BackupManager(self.db_path, self.backup_dir)

    def tearDown(self):
        hardening.uninstall_backup_restore_hardening_for_tests()
        self.td.cleanup()

    def _init_db(self, path, value="X", schema_version=SCHEMA_VERSION):
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE marker(value TEXT)")
        conn.execute("INSERT INTO marker(value) VALUES(?)", (value,))
        conn.execute(f"PRAGMA user_version = {int(schema_version)}")
        conn.commit()
        conn.close()

    def _read_marker(self, path=None):
        conn = sqlite3.connect(path or self.db_path)
        try:
            return conn.execute("SELECT value FROM marker").fetchone()[0]
        finally:
            conn.close()

    def test_create_backup_is_validated_and_metadata_is_published(self):
        path = self.manager.create_backup("manual")
        self.assertTrue(os.path.exists(path))
        self.assertEqual(hardening.validate_sqlite_backup(path), SCHEMA_VERSION)
        self.assertEqual(self._read_marker(path), "LIVE")
        meta = path[:-3] + ".json"
        self.assertTrue(os.path.exists(meta))
        with open(meta, "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('"validated": true', text)
        self.assertFalse(any(".tmp-" in name for name in os.listdir(self.backup_dir)))

    def test_corrupt_backup_is_rejected_before_live_database_changes(self):
        corrupt = os.path.join(self.td.name, "corrupt.db")
        with open(corrupt, "wb") as fh:
            fh.write(b"not sqlite")

        before_files = set(os.listdir(self.backup_dir))
        with self.assertRaisesRegex(Exception, "SQLite|Integrity|backup"):
            self.manager.restore_backup(corrupt)

        self.assertEqual(self._read_marker(), "LIVE")
        self.assertEqual(set(os.listdir(self.backup_dir)), before_files)

    def test_newer_schema_backup_is_rejected_before_restore(self):
        newer = os.path.join(self.td.name, "newer.db")
        self._init_db(newer, value="NEWER", schema_version=SCHEMA_VERSION + 1)
        with self.assertRaisesRegex(Exception, "mới hơn"):
            self.manager.restore_backup(newer)
        self.assertEqual(self._read_marker(), "LIVE")

    def test_valid_restore_uses_staging_and_replaces_live_database(self):
        source = os.path.join(self.td.name, "source.db")
        self._init_db(source, value="RESTORED")
        self.assertTrue(self.manager.restore_backup(source))
        self.assertEqual(self._read_marker(), "RESTORED")
        self.assertFalse(os.path.exists(self.db_path + "-wal"))
        self.assertFalse(os.path.exists(self.db_path + "-shm"))
        names = os.listdir(self.td.name)
        self.assertFalse(any(".restore-" in name or ".rollback-" in name for name in names))
        self.assertTrue(any(name.startswith("before_restore_") and name.endswith(".db") for name in os.listdir(self.backup_dir)))

    def test_failed_staging_copy_leaves_live_database_untouched_and_cleans_temp(self):
        source = os.path.join(self.td.name, "source.db")
        self._init_db(source, value="RESTORED")
        original_copy = hardening._copy_sqlite
        calls = {"n": 0}

        def fail_second_copy(src, dst):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("simulated stage failure")
            return original_copy(src, dst)

        with mock.patch.object(hardening, "_copy_sqlite", side_effect=fail_second_copy):
            with self.assertRaisesRegex(Exception, "simulated stage failure"):
                self.manager.restore_backup(source)

        self.assertEqual(self._read_marker(), "LIVE")
        self.assertFalse(any(".restore-" in name for name in os.listdir(self.td.name)))

    def test_concurrent_backup_calls_are_serialized_and_names_are_unique(self):
        active = 0
        max_active = 0
        gate = threading.Lock()
        original_copy = hardening._copy_sqlite

        def observed_copy(src, dst):
            nonlocal active, max_active
            with gate:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.03)
                return original_copy(src, dst)
            finally:
                with gate:
                    active -= 1

        paths = []
        errors = []

        def worker():
            try:
                paths.append(self.manager.create_backup("parallel"))
            except Exception as exc:
                errors.append(exc)

        with mock.patch.object(hardening, "_copy_sqlite", side_effect=observed_copy):
            threads = [threading.Thread(target=worker) for _ in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertFalse(errors)
        self.assertEqual(max_active, 1)
        self.assertEqual(len(paths), 4)
        self.assertEqual(len(set(paths)), 4)


if __name__ == "__main__":
    unittest.main()
