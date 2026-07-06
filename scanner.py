# scanner.py — Quét mã vạch từ webcam bằng OpenCV + pyzbar
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb

from config import BARCODE_AVAILABLE

# Import OpenCV and PIL if barcode scanner is available
if BARCODE_AVAILABLE:
    import cv2
    from pyzbar import pyzbar
    from PIL import Image, ImageTk


class BarcodeScanner:
    def __init__(self, parent_window, callback=None):
        self.parent = parent_window
        self.callback = callback
        self.cap = None
        self.scanning = False
        self.window = None
        
    def start_scan(self):
        """Bắt đầu quét barcode"""
        if not BARCODE_AVAILABLE:
            messagebox.showerror("Lỗi", 
                "Thư viện quét barcode chưa được cài đặt.\n"
                "Vui lòng chạy: pip install opencv-python pyzbar Pillow")
            return
            
        try:
            # Tạo window mới cho camera
            self.window = tk.Toplevel(self.parent)
            self.window.title("📷 Quét Barcode")
            self.window.geometry("640x480")
            self.window.resizable(False, False)
            
            # Tạo frame chính
            main_frame = tb.Frame(self.window)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Header
            header_frame = tb.Frame(main_frame)
            header_frame.pack(fill='x', pady=(0, 10))
            
            title_label = tb.Label(header_frame, text="📷 Quét Barcode", 
                                  font=('Segoe UI', 14, 'bold'), bootstyle='primary')
            title_label.pack()
            
            subtitle_label = tb.Label(header_frame, text="Đưa barcode vào khung hình để quét", 
                                     font=('Segoe UI', 10), bootstyle='secondary')
            subtitle_label.pack()
            
            # Video frame
            self.video_frame = tb.Frame(main_frame, relief='sunken', borderwidth=2)
            self.video_frame.pack(fill='both', expand=True, pady=(0, 10))
            
            self.video_label = tb.Label(self.video_frame, text="Đang khởi động camera...", 
                                       font=('Segoe UI', 12), bootstyle='info')
            self.video_label.pack(expand=True)
            
            # Control buttons
            button_frame = tb.Frame(main_frame)
            button_frame.pack(fill='x')
            
            self.start_btn = tb.Button(button_frame, text="▶️ Bắt đầu quét", 
                                      command=self.toggle_scan, bootstyle='success')
            self.start_btn.pack(side='left', padx=(0, 10))
            
            self.stop_btn = tb.Button(button_frame, text="⏹️ Dừng", 
                                     command=self.stop_scan, bootstyle='danger')
            self.stop_btn.pack(side='left', padx=(0, 10))
            
            tb.Button(button_frame, text="❌ Đóng", 
                     command=self.close_scanner, bootstyle='secondary').pack(side='right')
            
            # Status label
            self.status_label = tb.Label(main_frame, text="Sẵn sàng", 
                                        font=('Segoe UI', 10), bootstyle='info')
            self.status_label.pack(pady=(10, 0))
            
            # Khởi tạo camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Lỗi", "Không thể mở camera. Vui lòng kiểm tra kết nối.")
                self.close_scanner()
                return
                
            # Cấu hình camera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Bắt đầu quét
            self.toggle_scan()
            
            # Bind close event
            self.window.protocol("WM_DELETE_WINDOW", self.close_scanner)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động camera: {e}")
            
    def toggle_scan(self):
        """Bật/tắt quét"""
        if not self.scanning:
            self.start_scanning()
        else:
            self.stop_scanning()
            
    def start_scanning(self):
        """Bắt đầu quét"""
        self.scanning = True
        self.start_btn.config(text="⏸️ Tạm dừng", bootstyle='warning')
        self.status_label.config(text="Đang quét...", bootstyle='success')
        self.update_frame()
        
    def stop_scanning(self):
        """Tạm dừng quét"""
        self.scanning = False
        self.start_btn.config(text="▶️ Tiếp tục", bootstyle='success')
        self.status_label.config(text="Đã tạm dừng", bootstyle='warning')
        
    def update_frame(self):
        """Cập nhật frame camera"""
        if not self.scanning or not self.cap:
            return
            
        try:
            ret, frame = self.cap.read()
            if ret:
                # Lật frame để hiển thị đúng
                frame = cv2.flip(frame, 1)
                
                # Quét barcode nếu đang quét
                if self.scanning:
                    barcodes = pyzbar.decode(frame)
                    for barcode in barcodes:
                        # Lấy dữ liệu barcode
                        barcode_data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type
                        
                        # Vẽ khung quanh barcode
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        # Hiển thị thông tin
                        text = f"{barcode_type}: {barcode_data}"
                        cv2.putText(frame, text, (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # Gọi callback với dữ liệu barcode
                        if self.callback:
                            self.callback(barcode_data)
                            
                        # Dừng quét sau khi tìm thấy
                        self.stop_scanning()
                        self.status_label.config(text=f"Đã quét: {barcode_data}", bootstyle='success')
                        break
                
                # Chuyển đổi frame để hiển thị trong Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_tk = ImageTk.PhotoImage(frame_pil)
                
                # Cập nhật label
                self.video_label.config(image=frame_tk, text="")
                self.video_label.image = frame_tk
                
            # Lên lịch cập nhật tiếp theo
            if self.scanning:
                self.window.after(30, self.update_frame)
                
        except Exception as e:
            print(f"Lỗi cập nhật frame: {e}")
            self.stop_scanning()
            
    def stop_scan(self):
        """Dừng quét"""
        self.stop_scanning()
        
    def close_scanner(self):
        """Đóng scanner"""
        self.scanning = False
        if self.cap:
            self.cap.release()
        if self.window:
            self.window.destroy()
        self.window = None
        self.cap = None
