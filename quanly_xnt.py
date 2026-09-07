# -*- coding: utf-8 -*-
# quanly_xnt.py — Điểm khởi chạy chính của ứng dụng
import os
import sys


if sys.platform == 'win32':
    _meipass = getattr(sys, '_MEIPASS', None)
    if _meipass:
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(_meipass)
                os.add_dll_directory(os.path.join(_meipass, 'pyzbar'))
            except OSError:
                pass

        pyzbar_dir = os.path.join(_meipass, 'pyzbar')
        os.environ['PATH'] = _meipass + os.pathsep + pyzbar_dir + os.pathsep + os.environ.get('PATH', '')

        import ctypes
        for dll_dir in [_meipass, pyzbar_dir]:
            iconv_path = os.path.join(dll_dir, 'libiconv.dll')
            zbar_path = os.path.join(dll_dir, 'libzbar-64.dll')
            try:
                if os.path.isfile(iconv_path):
                    ctypes.cdll.LoadLibrary(iconv_path)
                if os.path.isfile(zbar_path):
                    ctypes.cdll.LoadLibrary(zbar_path)
                    break
            except OSError:
                continue

from ui import App as InventoryApp
from ui_security import AdminSecurityMixin
from ui_shell import ClinicalShellMixin
from ui_dashboard import DashboardUiMixin
from ui_catalog import CatalogUiMixin
from ui_transactions import TransactionUiMixin
from ui_stock_history import StockHistoryUiMixin
from ui_alerts_reports import AlertsReportsUiMixin
from ui_support_final import SupportFinalUiMixin
from xnt_excel_export import XntExcelExportMixin
from mobile_cookie_security import install_mobile_cookie_security
from mobile_http_hardening import install_mobile_http_hardening
from db_lifecycle_hardening import DatabaseLifecycleMixin, install_database_lifecycle_hardening
from backup_restore_hardening import install_backup_restore_hardening


class App(
    AdminSecurityMixin,
    DatabaseLifecycleMixin,
    ClinicalShellMixin,
    DashboardUiMixin,
    CatalogUiMixin,
    TransactionUiMixin,
    StockHistoryUiMixin,
    AlertsReportsUiMixin,
    SupportFinalUiMixin,
    XntExcelExportMixin,
    InventoryApp,
):
    """Inventory app with hardening and the Stitch-aligned desktop presentation."""

    def __init__(self, *args, **kwargs):
        install_database_lifecycle_hardening()
        install_backup_restore_hardening()
        install_mobile_cookie_security()
        install_mobile_http_hardening()
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    app = App()
    app.mainloop()
