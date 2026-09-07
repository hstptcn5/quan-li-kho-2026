# -*- coding: utf-8 -*-
"""H2.2 crash-safe backup/restore hardening for the desktop runtime.

This layer intentionally leaves inventory/query/transaction semantics untouched.  It
only replaces BackupManager.create_backup/restore_backup with staged, validated
filesystem operations and serializes destructive backup I/O.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import threading
import uuid

import managers as _managers
from config import APP_VERSION, SCHEMA_VERSION

_BACKUP_IO_LOCK = threading.RLock()
_INSTALLED = False
_ORIGINAL_CREATE_BACKUP = None
_ORIGINAL_RESTORE_BACKUP = None


def _connect(path: str, *, read_only: bool = False):
    if read_only:
        uri = "file:" + os.path.abspath(path).replace("\\", "/") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30)
    else:
        conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _fsync_file(path: str) -> None:
    with open(path, "rb") as fh:
        os.fsync(fh.fileno())


def _safe_unlink(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def validate_sqlite_backup(path: str) -> int:
    """Validate a candidate backup before it can replace the live database.

    Returns the candidate PRAGMA user_version.  Backups created by a newer schema
    are rejected so an older executable cannot silently downgrade/partially read it.
    """
    if not path or not os.path.isfile(path):
        raise ValueError("File backup không tồn tại")
    if os.path.getsize(path) <= 0:
        raise ValueError("File backup rỗng")

    conn = None
    try:
        conn = _connect(path, read_only=True)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or str(integrity[0]).lower() != "ok":
            raise ValueError("Integrity check database thất bại")
        fk_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_rows:
            raise ValueError(f"Foreign key check thất bại: {fk_rows[:5]}")
        schema_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if schema_version > SCHEMA_VERSION:
            raise ValueError(
                f"Backup schema_version {schema_version} mới hơn ứng dụng hiện tại {SCHEMA_VERSION}"
            )
        return schema_version
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"File backup không phải SQLite hợp lệ: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def _copy_sqlite(source_path: str, destination_path: str) -> None:
    src = dst = None
    try:
        src = _connect(source_path, read_only=True)
        dst = _connect(destination_path)
        with dst:
            src.backup(dst)
    finally:
        if dst is not None:
            dst.close()
        if src is not None:
            src.close()


def _checkpoint_live_database(db_path: str) -> None:
    """Checkpoint WAL before an atomic file replacement.

    The UI restore flow closes the primary DB first.  This extra checkpoint makes
    stale WAL state explicit and prevents an old sidecar being replayed against the
    newly restored main database file.
    """
    if not os.path.exists(db_path):
        return
    conn = None
    try:
        conn = _connect(db_path)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        if conn is not None:
            conn.close()

    # After a successful checkpoint and close there is no uncheckpointed content in
    # these sidecars.  Remove them before publishing a different main DB image.
    _safe_unlink(db_path + "-wal")
    _safe_unlink(db_path + "-shm")


def _atomic_metadata_write(path: str, metadata: dict) -> None:
    temp = path + ".tmp-" + uuid.uuid4().hex
    try:
        with open(temp, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, path)
    finally:
        _safe_unlink(temp)


def _hardened_create_backup(self, custom_name: str = None) -> str:
    with _BACKUP_IO_LOCK:
        os.makedirs(self.backup_dir, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        prefix = custom_name or "backup"
        backup_name = f"{prefix}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        stage_path = backup_path + ".tmp-" + uuid.uuid4().hex
        metadata_path = backup_path[:-3] + ".json"

        try:
            _copy_sqlite(self.db_path, stage_path)
            schema_version = validate_sqlite_backup(stage_path)
            _fsync_file(stage_path)
            os.replace(stage_path, backup_path)

            metadata = {
                "created_at": dt.datetime.now().isoformat(),
                "db_size": os.path.getsize(self.db_path),
                "backup_size": os.path.getsize(backup_path),
                "version": APP_VERSION,
                "schema_version": schema_version,
                "validated": True,
            }
            _atomic_metadata_write(metadata_path, metadata)
            self._cleanup_old_backups()
            return backup_path
        except Exception as exc:
            # Never leave a partial .db that list_backups() could later offer for
            # restore.  If metadata publication failed after the DB rename, remove
            # the orphan pair as one failed backup operation.
            _safe_unlink(stage_path)
            _safe_unlink(backup_path)
            _safe_unlink(metadata_path)
            raise Exception(f"Lỗi tạo backup: {exc}") from exc


def _publish_staged_restore(stage_path: str, db_path: str) -> None:
    _checkpoint_live_database(db_path)
    _fsync_file(stage_path)
    os.replace(stage_path, db_path)
    # Validate the published image too; the stage was already validated, so this is
    # primarily a guard against unexpected filesystem/replace failures.
    validate_sqlite_backup(db_path)


def _hardened_restore_backup(self, backup_path: str) -> bool:
    with _BACKUP_IO_LOCK:
        # Critical ordering: reject corrupt/newer backup BEFORE touching the live DB
        # or creating a misleading "before_restore" snapshot.
        validate_sqlite_backup(backup_path)

        current_backup = self.create_backup("before_restore")
        stage_path = self.db_path + ".restore-" + uuid.uuid4().hex + ".tmp"
        rollback_stage = None
        try:
            _copy_sqlite(backup_path, stage_path)
            validate_sqlite_backup(stage_path)
            _publish_staged_restore(stage_path, self.db_path)
            return True
        except Exception as exc:
            _safe_unlink(stage_path)
            # A failure before os.replace leaves the live DB untouched.  A rare
            # failure after publication is recovered from the already-validated
            # before_restore image via another staged atomic publication.
            try:
                validate_sqlite_backup(self.db_path)
            except Exception:
                try:
                    rollback_stage = self.db_path + ".rollback-" + uuid.uuid4().hex + ".tmp"
                    _copy_sqlite(current_backup, rollback_stage)
                    validate_sqlite_backup(rollback_stage)
                    _publish_staged_restore(rollback_stage, self.db_path)
                except Exception as rollback_exc:
                    raise Exception(
                        "Lỗi khôi phục backup và rollback tự động cũng thất bại: "
                        f"{rollback_exc}; lỗi ban đầu: {exc}"
                    ) from rollback_exc
                finally:
                    _safe_unlink(rollback_stage)
            raise Exception(f"Lỗi khôi phục backup (database hiện tại được giữ/phục hồi): {exc}") from exc
        finally:
            _safe_unlink(stage_path)


def install_backup_restore_hardening() -> None:
    global _INSTALLED, _ORIGINAL_CREATE_BACKUP, _ORIGINAL_RESTORE_BACKUP
    if _INSTALLED:
        return
    _ORIGINAL_CREATE_BACKUP = _managers.BackupManager.create_backup
    _ORIGINAL_RESTORE_BACKUP = _managers.BackupManager.restore_backup
    _managers.BackupManager.create_backup = _hardened_create_backup
    _managers.BackupManager.restore_backup = _hardened_restore_backup
    _INSTALLED = True


def uninstall_backup_restore_hardening_for_tests() -> None:
    global _INSTALLED, _ORIGINAL_CREATE_BACKUP, _ORIGINAL_RESTORE_BACKUP
    if not _INSTALLED:
        return
    _managers.BackupManager.create_backup = _ORIGINAL_CREATE_BACKUP
    _managers.BackupManager.restore_backup = _ORIGINAL_RESTORE_BACKUP
    _ORIGINAL_CREATE_BACKUP = None
    _ORIGINAL_RESTORE_BACKUP = None
    _INSTALLED = False
