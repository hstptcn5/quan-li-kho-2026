import glob
import os
import sqlite3
import tempfile
import unittest

import database as database_module
from database import DB


class TestMigrationBackupHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "legacy.db")
        self.backup_dir = os.path.join(self.temp_dir.name, "backups")
        self.old_backup_dir = database_module.BACKUP_DIR
        database_module.BACKUP_DIR = self.backup_dir

    def tearDown(self):
        database_module.BACKUP_DIR = self.old_backup_dir
        self.temp_dir.cleanup()

    def _create_legacy_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE products ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "defaultUnit TEXT NOT NULL, "
            "createdAt TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "INSERT INTO products(name, defaultUnit) VALUES (?, ?)",
            ("Thuoc legacy", "Vien"),
        )
        conn.execute("PRAGMA user_version = 0")
        conn.commit()
        conn.close()

    def _migration_backups(self):
        return glob.glob(os.path.join(self.backup_dir, "legacy_pre_migration_*.db"))

    def test_backup_is_taken_before_any_schema_mutation(self):
        self._create_legacy_database()

        db = DB(self.db_path)
        db.conn.close()

        backups = self._migration_backups()
        self.assertEqual(len(backups), 1)

        backup = sqlite3.connect(backups[0])
        try:
            columns = [row[1] for row in backup.execute("PRAGMA table_info(products)")]
            self.assertNotIn("barcode", columns)
            self.assertNotIn("productType", columns)
            self.assertNotIn("registrationNumber", columns)
            row = backup.execute(
                "SELECT name, defaultUnit FROM products WHERE id=1"
            ).fetchone()
            self.assertEqual(row, ("Thuoc legacy", "Vien"))
            self.assertEqual(backup.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            backup.close()

        current = sqlite3.connect(self.db_path)
        try:
            columns = [row[1] for row in current.execute("PRAGMA table_info(products)")]
            self.assertIn("barcode", columns)
            self.assertIn("productType", columns)
            self.assertIn("registrationNumber", columns)
            self.assertEqual(
                current.execute("PRAGMA user_version").fetchone()[0],
                database_module.SCHEMA_VERSION,
            )
        finally:
            current.close()

    def test_current_schema_reopen_does_not_create_migration_backup(self):
        db = DB(self.db_path)
        db.conn.close()
        self.assertEqual(self._migration_backups(), [])

        db = DB(self.db_path)
        db.conn.close()
        self.assertEqual(self._migration_backups(), [])


if __name__ == "__main__":
    unittest.main()
