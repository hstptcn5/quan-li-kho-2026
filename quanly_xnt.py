# -*- coding: utf-8 -*-
# quanly_xnt.py — Điểm khởi chạy chính của ứng dụng
import os
import sys

# Tự động sửa lỗi ui.py nếu bị lỗi do thao tác ghi tệp gián đoạn
def fix_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "ui.py")
    if os.path.exists(ui_path):
        try:
            with open(ui_path, 'rb') as f:
                content = f.read()
            corrupted = b"    def create_tooltip(self, widget, text):widget, text):_note)"
            if corrupted in content:
                idx1 = content.find(corrupted)
                next_part = content[idx1 + len(corrupted):]
                idx2 = next_part.find(b"    def create_tooltip(self, widget, text):")
                if idx2 != -1:
                    cleaned = content[:idx1] + next_part[idx2:]
                    text = cleaned.decode('utf-8', errors='ignore')
                    with open(ui_path, 'w', encoding='utf-8', newline='') as f:
                        f.write(text)
                    print("Auto-fixed ui.py corruption successfully.")
        except Exception as e:
            print("Error auto-fixing ui.py:", e)

fix_ui()


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
from ui import App

if __name__ == '__main__':
    app = App()
    app.mainloop()
