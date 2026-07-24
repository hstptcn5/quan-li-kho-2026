# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as tb

from server import MobileInventoryServer, get_local_ip


QR_CODE_AVAILABLE = False
try:
    import qrcode
    QR_CODE_AVAILABLE = True
except ImportError:
    pass


class MobileMixin:
    def build_mobile_tab(self):
        """Xây dựng giao diện cho Tab Kiểm kho di động"""
        # Xóa các widget cũ
        for widget in self.tab_mobile.winfo_children():
            widget.destroy()
            
        main_frame = tb.Frame(self.tab_mobile)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # --- CỘT TRÁI: ĐIỀU KHIỂN & TRẠNG THÁI ---
        left_frame = tb.LabelFrame(main_frame, text="⚙️ Cấu hình máy chủ di động", padding=15)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Trạng thái máy chủ
        status_lbl_frame = tb.Frame(left_frame)
        status_lbl_frame.pack(fill='x', pady=10)
        
        tb.Label(status_lbl_frame, text="Trạng thái máy chủ:", font=('Segoe UI', 11, 'bold')).pack(side='left')
        
        self.mobile_status_val = tb.Label(status_lbl_frame, font=('Segoe UI', 11, 'bold'))
        self.mobile_status_val.pack(side='left', padx=10)
        
        # Điều khiển nút
        self.btn_toggle_server = tb.Button(left_frame, command=self.toggle_mobile_server, bootstyle='success')
        self.btn_toggle_server.pack(fill='x', pady=10)
        
        # Đường link kết nối
        link_frame = tb.Frame(left_frame)
        link_frame.pack(fill='x', pady=10)
        
        tb.Label(link_frame, text="Địa chỉ kết nối LAN:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        self.mobile_url_val = tb.Entry(link_frame, font=('Segoe UI', 10), state='readonly')
        self.mobile_url_val.pack(fill='x', pady=5)
        
        def copy_url():
            url = self.mobile_url_val.get()
            if url:
                self.clipboard_clear()
                self.clipboard_append(url)
                self.toast("Đã copy đường dẫn kết nối vào clipboard!")
                
        def open_browser():
            url = self.mobile_url_val.get()
            if url:
                import webbrowser
                webbrowser.open(url)
                
        btn_copy = tb.Button(link_frame, text="📋 Sao chép liên kết", command=copy_url, bootstyle='outline-info')
        btn_copy.pack(side='left', padx=2)
        
        btn_open = tb.Button(link_frame, text="🌐 Mở trên PC (Test)", command=open_browser, bootstyle='outline-secondary')
        btn_open.pack(side='left', padx=2)
        
        # Hướng dẫn chi tiết
        help_text = (
            "💡 Hướng dẫn sử dụng:\n"
            "1. Đảm bảo máy tính và điện thoại di động cùng kết nối chung một mạng Wi-Fi cục bộ.\n"
            "2. Khởi động máy chủ bằng nút phía trên (nếu đang dừng).\n"
            "3. Lấy điện thoại di động quét mã QR ở ô bên phải để mở liên kết.\n"
            "4. Cấp quyền truy cập Camera cho trình duyệt trên điện thoại nếu được hỏi.\n"
            "5. Đưa camera điện thoại quét mã vạch sản phẩm để kiểm tra số tồn tức thì."
        )
        tb.Label(left_frame, text=help_text, font=('Segoe UI', 9), justify='left', 
                 wraplength=450, bootstyle='secondary').pack(anchor='w', pady=15)
                 
        # --- CỘT PHẢI: MÃ QR ---
        right_frame = tb.LabelFrame(main_frame, text="📱 Quét mã QR để kết nối", padding=15)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # Canvas vẽ QR Code
        self.qr_canvas = tk.Canvas(right_frame, width=260, height=260, bg='white', relief='ridge', borderwidth=1)
        self.qr_canvas.pack(pady=10)
        
        self.qr_help_lbl = tb.Label(right_frame, text="Đang tạo mã QR kết nối...", font=('Segoe UI', 10), justify='center')
        self.qr_help_lbl.pack(pady=5)
        
        # Cập nhật UI ban đầu
        self.update_mobile_server_ui()

    def toggle_mobile_server(self):
        """Khởi động hoặc dừng máy chủ di động"""
        if self.mobile_server and self.mobile_server.is_running:
            try:
                self.mobile_server.stop()
                self.toast("Đã dừng máy chủ di động")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể dừng máy chủ: {e}")
        else:
            try:
                self.mobile_server = MobileInventoryServer(self, host="0.0.0.0", port=5000)
                self.mobile_server.start()
                self.toast("Đã khởi động máy chủ di động")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khởi động máy chủ: {e}")
        
        self.update_mobile_server_ui()

    def refresh_all_data(self):
        """Làm mới tất cả bảng dữ liệu trên giao diện máy tính"""
        try:
            self.refresh_products()
            self.refresh_stock()
            self.refresh_alerts()
            self.refresh_report()
            # Làm mới lịch sử nếu giao diện lịch sử đang mở
            if hasattr(self, 'show_purchase_history'):
                try: self.show_purchase_history()
                except: pass
            if hasattr(self, 'show_dispatch_history'):
                try: self.show_dispatch_history()
                except: pass
        except Exception as e:
            print(f"Lỗi refresh_all_data: {e}")

    def update_mobile_server_ui(self):
        """Cập nhật trạng thái giao diện và vẽ lại mã QR kết nối"""
        if not hasattr(self, 'mobile_status_val') or not self.mobile_status_val:
            return
        if not hasattr(self, 'mobile_url_val') or not self.mobile_url_val:
            return
        if not hasattr(self, 'btn_toggle_server') or not self.btn_toggle_server:
            return
        if not hasattr(self, 'qr_help_lbl') or not self.qr_help_lbl:
            return
        if not hasattr(self, 'qr_canvas') or not self.qr_canvas:
            return
            
        ip = get_local_ip()
        port = 5000
        if self.mobile_server:
            port = self.mobile_server.port
            
        url = f"http://{ip}:{port}"
        
        self.mobile_url_val.config(state='normal')
        self.mobile_url_val.delete(0, 'end')
        self.mobile_url_val.insert(0, url)
        self.mobile_url_val.config(state='readonly')
        
        if self.mobile_server and self.mobile_server.is_running:
            import server
            self.mobile_status_val.config(text=f"ĐANG CHẠY | PIN: {server.SERVER_PIN}", bootstyle='success')
            self.btn_toggle_server.config(text="⏹️ Dừng máy chủ di động", bootstyle='danger')
            self.qr_help_lbl.config(text=f"PIN: {server.SERVER_PIN}\nMở Zalo hoặc quét QR để truy cập", bootstyle='success')
            self.draw_qr_code(url)
        else:
            self.mobile_status_val.config(text="ĐÃ DỪNG", bootstyle='danger')
            self.btn_toggle_server.config(text="▶️ Khởi động máy chủ di động", bootstyle='success')
            self.qr_help_lbl.config(text="Vui lòng khởi động máy chủ để hiển thị mã QR", bootstyle='warning')
            self.qr_canvas.delete("all")
            self.qr_canvas.create_text(130, 130, text="MÁY CHỦ\nĐANG DỪNG", fill='gray', font=('Segoe UI', 14, 'bold'), justify='center')

    def draw_qr_code(self, url):
        """Vẽ mã QR lên Canvas"""
        global QR_CODE_AVAILABLE, qrcode
        self.qr_canvas.delete("all")
        
        if not QR_CODE_AVAILABLE:
            try:
                import qrcode
                QR_CODE_AVAILABLE = True
            except ImportError:
                pass
                
        if not QR_CODE_AVAILABLE:
            self.qr_canvas.create_text(130, 100, text="Thiếu thư viện 'qrcode'\nđể hiển thị mã QR", 
                                       fill='red', font=('Segoe UI', 10, 'bold'), justify='center')
                                       
            def auto_install_qr():
                import subprocess, sys
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "qrcode"], check=True)
                    global QR_CODE_AVAILABLE
                    QR_CODE_AVAILABLE = True
                    self.toast("Đã cài đặt thành công thư viện qrcode!")
                    self.update_mobile_server_ui()
                except Exception as ex:
                    messagebox.showerror("Lỗi cài đặt", f"Không thể tự động cài đặt: {str(ex)}")
            
            btn_install = tb.Button(self.qr_canvas, text="🔧 Cài đặt qrcode", command=auto_install_qr, bootstyle='warning-outline')
            self.qr_canvas.create_window(130, 160, window=btn_install)
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(url)
            qr.make(fit=True)
            matrix = qr.get_matrix()
            
            num_rows = len(matrix)
            block_size = min(220 // num_rows, 10)
            offset_x = (260 - num_rows * block_size) // 2
            offset_y = (260 - num_rows * block_size) // 2
            
            for r in range(num_rows):
                for c in range(num_rows):
                    if matrix[r][c]:
                        x1 = offset_x + c * block_size
                        y1 = offset_y + r * block_size
                        x2 = x1 + block_size
                        y2 = y1 + block_size
                        self.qr_canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
        except Exception as e:
            self.qr_canvas.create_text(130, 130, text=f"Lỗi vẽ QR:\n{str(e)}", fill='red', font=('Segoe UI', 10), justify='center')


