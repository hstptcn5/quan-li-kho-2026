# -*- coding: utf-8 -*-
# quanly_xnt.py — Điểm khởi chạy chính của ứng dụng
import os
import sys


# =============================================================================
# QUAN TRỌNG: Đoạn code dưới đây PHẢI chạy TRƯỚC mọi lệnh import khác
# để đảm bảo Windows tìm thấy libzbar-64.dll và libiconv.dll khi
# ứng dụng được đóng gói bằng PyInstaller (--onefile).
# =============================================================================
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
from mobile_cookie_security import install_mobile_cookie_security


class App(
    AdminSecurityMixin,
    ClinicalShellMixin,
    DashboardUiMixin,
    CatalogUiMixin,
    TransactionUiMixin,
    StockHistoryUiMixin,
    AlertsReportsUiMixin,
    InventoryApp,
):
    """Inventory app with hardening and the Stitch-aligned desktop presentation."""

    def __init__(self, *args, **kwargs):
        install_mobile_cookie_security()
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    app = App()
    app.mainloop()
