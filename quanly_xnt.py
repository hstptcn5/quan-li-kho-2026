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
        # 1. Đăng ký thư mục tìm DLL (Windows 10 1607+)
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(_meipass)
                os.add_dll_directory(os.path.join(_meipass, 'pyzbar'))
            except OSError:
                pass

        # 2. Thêm vào PATH hệ thống (fallback cho các bản Windows cũ hơn)
        pyzbar_dir = os.path.join(_meipass, 'pyzbar')
        os.environ['PATH'] = _meipass + os.pathsep + pyzbar_dir + os.pathsep + os.environ.get('PATH', '')

        # 3. Chủ động nạp trước libiconv.dll rồi mới nạp libzbar-64.dll
        #    để giải quyết triệt để lỗi dependency chain
        import ctypes
        for dll_dir in [_meipass, pyzbar_dir]:
            iconv_path = os.path.join(dll_dir, 'libiconv.dll')
            zbar_path = os.path.join(dll_dir, 'libzbar-64.dll')
            try:
                if os.path.isfile(iconv_path):
                    ctypes.cdll.LoadLibrary(iconv_path)
                if os.path.isfile(zbar_path):
                    ctypes.cdll.LoadLibrary(zbar_path)
                    break  # Đã nạp thành công, không cần thử thư mục tiếp theo
            except OSError:
                continue

# Bây giờ mới import ứng dụng chính (config.py -> ui.py -> pyzbar)
from ui import App as InventoryApp
from ui_security import AdminSecurityMixin
from mobile_cookie_security import install_mobile_cookie_security


class App(AdminSecurityMixin, InventoryApp):
    """Inventory desktop app with desktop and mobile security hardening."""

    def __init__(self, *args, **kwargs):
        # H1.1 is applied only when the real desktop application is instantiated,
        # keeping module-level server tests isolated from production runtime wiring.
        install_mobile_cookie_security()
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    app = App()
    app.mainloop()
