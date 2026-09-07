# -*- coding: utf-8 -*-
"""H2.1 database lifecycle hardening.

Adds an explicit, idempotent ``DB.close()`` / context-manager contract without
rewriting the large legacy database module, and ensures the desktop runtime
closes its primary SQLite connection during application shutdown.
"""

from __future__ import annotations

from database import DB


_INSTALLED = False
_ORIGINAL_CLOSE = None
_ORIGINAL_ENTER = None
_ORIGINAL_EXIT = None
_MISSING = object()


def _db_close(db):
    """Close a DB connection exactly once and make later use fail clearly."""
    conn = getattr(db, "conn", None)
    if conn is None:
        return
    try:
        conn.close()
    finally:
        db.conn = None


def _db_enter(db):
    if getattr(db, "conn", None) is None:
        raise RuntimeError("Database connection is already closed")
    return db


def _db_exit(db, exc_type, exc_value, traceback):
    _db_close(db)
    return False


def install_database_lifecycle_hardening():
    """Install the H2.1 DB lifecycle contract once."""
    global _INSTALLED, _ORIGINAL_CLOSE, _ORIGINAL_ENTER, _ORIGINAL_EXIT
    if _INSTALLED:
        return

    _ORIGINAL_CLOSE = getattr(DB, "close", _MISSING)
    _ORIGINAL_ENTER = getattr(DB, "__enter__", _MISSING)
    _ORIGINAL_EXIT = getattr(DB, "__exit__", _MISSING)

    DB.close = _db_close
    DB.__enter__ = _db_enter
    DB.__exit__ = _db_exit
    _INSTALLED = True


def uninstall_database_lifecycle_hardening_for_tests():
    """Restore the DB class to its state before H2.1 installation."""
    global _INSTALLED, _ORIGINAL_CLOSE, _ORIGINAL_ENTER, _ORIGINAL_EXIT
    if not _INSTALLED:
        return

    for name, original in (
        ("close", _ORIGINAL_CLOSE),
        ("__enter__", _ORIGINAL_ENTER),
        ("__exit__", _ORIGINAL_EXIT),
    ):
        if original is _MISSING:
            try:
                delattr(DB, name)
            except AttributeError:
                pass
        else:
            setattr(DB, name, original)

    _ORIGINAL_CLOSE = None
    _ORIGINAL_ENTER = None
    _ORIGINAL_EXIT = None
    _INSTALLED = False


class DatabaseLifecycleMixin:
    """Own the desktop application's shutdown order for DB/server resources."""

    def on_close(self):
        # Stop request workers before closing the primary DB they reference via
        # the desktop app instance. Shutdown must continue even if one cleanup
        # operation reports an error.
        mobile_server = getattr(self, "mobile_server", None)
        if mobile_server is not None:
            try:
                mobile_server.stop()
            except Exception as exc:
                print(f"Lỗi khi dừng mobile server lúc thoát: {exc}")

        db = getattr(self, "db", None)
        if db is not None:
            try:
                close = getattr(db, "close", None)
                if callable(close):
                    close()
                else:
                    conn = getattr(db, "conn", None)
                    if conn is not None:
                        conn.close()
                        db.conn = None
            except Exception as exc:
                print(f"Lỗi khi đóng database lúc thoát: {exc}")

        self.destroy()
