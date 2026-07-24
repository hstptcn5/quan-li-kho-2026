# -*- coding: utf-8 -*-
import datetime as dt
import os
from tkinter import messagebox, filedialog

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry
from ttkbootstrap.constants import *

from date_utils import format_date_display, parse_date_to_iso


class TempLogMixin:
    def build_temp_log_tab(self):
        """Tạo giao diện Nhật ký nhiệt độ"""
        container = tb.Frame(self.tab_temp_log, padding=10)
        container.pack(fill=BOTH, expand=True)

        # Tiêu đề phân hệ
        title_frame = tb.Frame(container)
        title_frame.pack(fill='x', pady=(0, 10))
        tb.Label(title_frame, text="🌡️ NHẬT KÝ THEO DÕI NHIỆT ĐỘ - ĐỘ ẨM (GSP)", 
                 font=('Segoe UI', 14, 'bold'), bootstyle='primary').pack(side='left')

        # Split layout: Form (Trái) & Bảng lịch sử (Phải)
        main_layout = tb.Frame(container)
        main_layout.pack(fill=BOTH, expand=True)

        left_panel = tb.LabelFrame(main_layout, text=" Nhập chỉ số hàng ngày ", padding=15, width=320)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        right_panel = tb.LabelFrame(main_layout, text=" Lịch sử theo dõi ", padding=15)
        right_panel.pack(side='right', fill=BOTH, expand=True)

        # --- Form nhập liệu (left_panel) ---
        # 1. Ngày ghi
        tb.Label(left_panel, text="Ngày theo dõi:").pack(anchor='w', pady=(5, 2))
        self.temp_date = DateEntry(left_panel, dateformat='%d-%m-%Y', bootstyle='primary')
        self.temp_date.pack(fill='x', pady=(0, 10))

        # 2. Buổi
        tb.Label(left_panel, text="Buổi:").pack(anchor='w', pady=(0, 2))
        self.temp_session = tb.Combobox(left_panel, values=['Sáng', 'Chiều'], state='readonly')
        self.temp_session.pack(fill='x', pady=(0, 10))
        self.temp_session.current(0)

        # 3. Vị trí thiết bị
        tb.Label(left_panel, text="Tủ lạnh / Kho bảo quản:").pack(anchor='w', pady=(0, 2))
        self.temp_location = tb.Combobox(left_panel, values=[
            'Tủ vaccine 1 (2-8°C)', 
            'Tủ vaccine 2 (2-8°C)', 
            'Kho lạnh 1 (2-8°C)', 
            'Kho mát VTYT (15-25°C)'
        ])
        self.temp_location.pack(fill='x', pady=(0, 10))
        self.temp_location.current(0)

        # 4. Nhiệt độ
        tb.Label(left_panel, text="Nhiệt độ (°C):").pack(anchor='w', pady=(0, 2))
        self.temp_val = tb.Entry(left_panel)
        self.temp_val.pack(fill='x', pady=(0, 10))
        self.temp_val.insert(0, "5.0")

        # 5. Độ ẩm
        tb.Label(left_panel, text="Độ ẩm (% RH - không bắt buộc):").pack(anchor='w', pady=(0, 2))
        self.temp_humidity = tb.Entry(left_panel)
        self.temp_humidity.pack(fill='x', pady=(0, 10))

        # 6. Người ghi nhận
        tb.Label(left_panel, text="Người ghi nhận:").pack(anchor='w', pady=(0, 2))
        self.temp_recorded_by = tb.Entry(left_panel)
        self.temp_recorded_by.pack(fill='x', pady=(0, 15))
        
        # Load tên thủ kho mặc định nếu có
        self.temp_recorded_by.insert(0, "Thủ kho CDC")

        # Nút Lưu
        btn_save = tb.Button(left_panel, text="💾 Lưu chỉ số", bootstyle='success', command=self.save_temp_log)
        btn_save.pack(fill='x')

        # --- Bảng lịch sử & bộ lọc (right_panel) ---
        # Bộ lọc
        filter_frame = tb.Frame(right_panel)
        filter_frame.pack(fill='x', pady=(0, 10))

        tb.Label(filter_frame, text="Tháng lọc:").pack(side='left', padx=(0, 5))
        
        # List các tháng của năm hiện tại và trước đó
        now = dt.datetime.now()
        months_list = []
        for i in range(12):
            m = now - dt.timedelta(days=30 * i)
            months_list.append(m.strftime('%Y-%m'))
        months_list = sorted(list(set(months_list)), reverse=True)
        
        self.temp_filter_month = tb.Combobox(filter_frame, values=months_list, state='readonly', width=10)
        self.temp_filter_month.pack(side='left', padx=(0, 15))
        if months_list:
            self.temp_filter_month.current(0)
        self.temp_filter_month.bind('<<ComboboxSelected>>', lambda e: self.load_temp_logs_tree())

        tb.Label(filter_frame, text="Tủ/Kho:").pack(side='left', padx=(0, 5))
        self.temp_filter_loc = tb.Combobox(filter_frame, values=['Tất cả'], state='readonly', width=20)
        self.temp_filter_loc.pack(side='left', padx=(0, 10))
        self.temp_filter_loc.current(0)
        self.temp_filter_loc.bind('<<ComboboxSelected>>', lambda e: self.load_temp_logs_tree())

        btn_refresh = tb.Button(filter_frame, text="🔄 Tải lại", bootstyle='secondary-outline', 
                                command=self.refresh_temp_tab_data, padding=(10, 5))
        btn_refresh.pack(side='left')

        # Treeview bảng dữ liệu
        tree_frame = tb.Frame(right_panel)
        tree_frame.pack(fill=BOTH, expand=True)

        self.temp_tree = tb.Treeview(
            tree_frame, 
            columns=('id', 'date', 'session', 'location', 'temp', 'humidity', 'recorded_by', 'status'),
            show='headings',
            bootstyle='primary'
        )
        self.temp_tree.pack(side='left', fill=BOTH, expand=True)

        scrollbar = tb.Scrollbar(tree_frame, orient="vertical", command=self.temp_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.temp_tree.configure(yscrollcommand=scrollbar.set)

        self.temp_tree.heading('id', text='ID')
        self.temp_tree.heading('date', text='Ngày ghi')
        self.temp_tree.heading('session', text='Buổi')
        self.temp_tree.heading('location', text='Vị trí tủ/kho')
        self.temp_tree.heading('temp', text='Nhiệt độ (°C)')
        self.temp_tree.heading('humidity', text='Độ ẩm (%)')
        self.temp_tree.heading('recorded_by', text='Người ghi')
        self.temp_tree.heading('status', text='Trạng thái')

        self.temp_tree.column('id', width=40, anchor='center')
        self.temp_tree.column('date', width=90, anchor='center')
        self.temp_tree.column('session', width=70, anchor='center')
        self.temp_tree.column('location', width=180, anchor='w')
        self.temp_tree.column('temp', width=95, anchor='center')
        self.temp_tree.column('humidity', width=95, anchor='center')
        self.temp_tree.column('recorded_by', width=110, anchor='w')
        self.temp_tree.column('status', width=120, anchor='center')

        # Thiết lập tag cảnh báo màu sắc
        self.temp_tree.tag_configure('warning', foreground='orange', font=('Segoe UI', 10, 'bold'))
        self.temp_tree.tag_configure('danger', foreground='red', font=('Segoe UI', 10, 'bold'))

        # Khu vực các nút chức năng (phía dưới bảng)
        action_frame = tb.Frame(right_panel)
        action_frame.pack(fill='x', pady=(10, 0))

        btn_delete = tb.Button(action_frame, text="❌ Xóa dòng chọn", bootstyle='danger-outline', 
                               command=self.delete_selected_temp_log)
        btn_delete.pack(side='left', padx=(0, 10))

        self.btn_export_pdf = tb.Button(action_frame, text="📄 Xuất PDF Sổ nhật ký", bootstyle='info', 
                                        command=self.export_temp_log_pdf)
        self.btn_export_pdf.pack(side='right', padx=(10, 0))

        self.btn_plot = tb.Button(action_frame, text="📈 Vẽ biểu đồ xu hướng", bootstyle='primary-outline', 
                                  command=self.plot_temp_chart)
        self.btn_plot.pack(side='right')

        # Tải dữ liệu ban đầu
        self.refresh_temp_tab_data()

    def refresh_temp_tab_data(self):
        """Cập nhật bộ lọc vị trí tủ và tải danh sách nhật ký"""
        try:
            locations = self.db.get_temperature_locations()
            current_filter = self.temp_filter_loc.get()
            
            # Giữ nguyên danh sách cố định và thêm các vị trí trong DB
            fixed_locations = ['Tủ vaccine 1 (2-8°C)', 'Tủ vaccine 2 (2-8°C)', 'Kho lạnh 1 (2-8°C)', 'Kho mát VTYT (15-25°C)']
            all_locs = sorted(list(set(fixed_locations + locations)))
            
            self.temp_filter_loc.config(values=['Tất cả'] + all_locs)
            self.temp_location.config(values=all_locs)
            
            if current_filter in all_locs:
                self.temp_filter_loc.set(current_filter)
            else:
                self.temp_filter_loc.current(0)
                
            self.load_temp_logs_tree()
        except Exception as e:
            print(f"Lỗi refresh danh sách tủ: {e}")

    def load_temp_logs_tree(self):
        """Đọc và điền dữ liệu nhật ký nhiệt độ lên bảng"""
        # Xóa bảng cũ
        for item in self.temp_tree.get_children():
            self.temp_tree.delete(item)

        month = self.temp_filter_month.get()
        loc = self.temp_filter_loc.get()

        try:
            logs = self.db.get_temperature_logs(month, loc)
            for r in logs:
                t = float(r['temperature'])
                h = r['humidity']
                h_str = f"{h}%" if h is not None and h != "" else "-"
                
                # Xác định trạng thái vượt ngưỡng
                loc_lower = r['locationName'].lower()
                status = "Bình thường"
                tag = ""
                
                if "2-8" in loc_lower or "vaccine" in loc_lower or "lạnh" in loc_lower:
                    if t < 2.0 or t > 8.0:
                        status = "Vượt ngưỡng (2-8°C)"
                        tag = "danger"
                elif "15-25" in loc_lower or "mát" in loc_lower:
                    if t < 15.0 or t > 25.0:
                        status = "Vượt ngưỡng (15-25°C)"
                        tag = "warning"
                else:
                    # Mặc định kho thường
                    if t > 30.0:
                        status = "Nhiệt độ cao (>30°C)"
                        tag = "warning"
                    if h is not None and h != "" and float(h) > 75.0:
                        status = "Độ ẩm cao (>75%)"
                        tag = "warning"
                
                self.temp_tree.insert('', 'end', values=(
                    r['id'],
                    format_date_display(r['logDate']),
                    r['session'],
                    r['locationName'],
                    f"{t} °C",
                    h_str,
                    r['recordedBy'] or "-",
                    status
                ), tags=(tag,) if tag else ())
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải nhật ký nhiệt độ: {str(e)}")

    def save_temp_log(self):
        """Lưu chỉ số nhiệt độ/độ ẩm mới nhập vào DB"""
        log_date = parse_date_to_iso(self.temp_date.entry.get())
        session = self.temp_session.get()
        location = self.temp_location.get().strip()
        temp_s = self.temp_val.get().strip()
        humidity_s = self.temp_humidity.get().strip()
        recorded_by = self.temp_recorded_by.get().strip()

        if not location:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập tên tủ lạnh hoặc kho bảo quản."); return
        if not temp_s:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập chỉ số nhiệt độ."); return

        try:
            temp = float(temp_s)
        except ValueError:
            messagebox.showerror("Sai định dạng", "Chỉ số nhiệt độ phải là số thực (ví dụ: 5.5)."); return

        humidity = None
        if humidity_s:
            try:
                humidity = float(humidity_s)
            except ValueError:
                messagebox.showerror("Sai định dạng", "Chỉ số độ ẩm phải là số thực (ví dụ: 65)."); return

        # Kiểm tra nhanh ngưỡng để đưa cảnh báo ngay khi nhập
        loc_lower = location.lower()
        is_alert = False
        limit_desc = ""
        if "2-8" in loc_lower or "vaccine" in loc_lower or "lạnh" in loc_lower:
            if temp < 2.0 or temp > 8.0:
                is_alert = True
                limit_desc = "2-8°C"
        elif "15-25" in loc_lower or "mát" in loc_lower:
            if temp < 15.0 or temp > 25.0:
                is_alert = True
                limit_desc = "15-25°C"
        else:
            if temp > 30.0:
                is_alert = True
                limit_desc = "dưới 30°C"

        if is_alert:
            self.toast(f"⚠️ Cảnh báo: Nhiệt độ {temp}°C vượt ngưỡng an toàn ({limit_desc})!", ms=3000)

        try:
            self.db.add_temperature_log(log_date, session, location, temp, humidity, recorded_by)
            self.toast("Đã lưu chỉ số nhiệt độ thành công!")
            
            # Reset ô nhập nhiệt độ/độ ẩm để nhập tiếp buổi khác
            self.temp_val.delete(0, 'end')
            self.temp_val.insert(0, "5.0")
            self.temp_humidity.delete(0, 'end')
            
            self.refresh_temp_tab_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {str(e)}")

    def delete_selected_temp_log(self):
        """Xóa dòng nhật ký đang được chọn"""
        selected = self.temp_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn dòng cần xóa trong bảng."); return

        values = self.temp_tree.item(selected[0])['values']
        log_id = values[0]
        date_str = values[1]
        session = values[2]
        loc = values[3]

        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa bản ghi ngày {date_str} ({session}) của {loc} không?")
        if confirm:
            try:
                self.db.delete_temperature_log(log_id)
                self.toast("Đã xóa dòng nhật ký thành công!")
                self.refresh_temp_tab_data()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa bản ghi: {str(e)}")

    def plot_temp_chart(self):
        """Vẽ biểu đồ dao động nhiệt độ trong tháng sử dụng matplotlib"""
        # Kiểm tra thư viện matplotlib
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            messagebox.showerror("Thiếu thư viện", "Bạn cần cài đặt matplotlib để sử dụng chức năng vẽ biểu đồ.\nHãy chạy lệnh 'pip install matplotlib' trong terminal."); return

        month = self.temp_filter_month.get()
        loc = self.temp_filter_loc.get()

        if loc == "Tất cả":
            messagebox.showwarning("Chọn vị trí", "Vui lòng chọn một tủ bảo quản hoặc kho lạnh cụ thể để vẽ biểu đồ."); return

        try:
            logs = self.db.get_temperature_logs(month, loc)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu: {str(e)}"); return

        if not logs:
            messagebox.showwarning("Không có dữ liệu", f"Không tìm thấy bản ghi nhiệt độ nào cho {loc} trong tháng {month} để vẽ biểu đồ."); return

        # Đảo ngược danh sách để vẽ từ ngày 1 đến cuối tháng
        logs = list(reversed(logs))

        # Chuẩn bị dữ liệu
        dates_session = []
        temps = []
        
        for r in logs:
            day_str = r['logDate'].split('-')[-1]
            dates_session.append(f"{day_str} ({r['session']})")
            temps.append(float(r['temperature']))

        # Tạo cửa sổ hiển thị biểu đồ
        chart_win = tb.Toplevel(self)
        chart_win.title(f"Biểu đồ nhiệt độ - {loc} - Tháng {month}")
        chart_win.geometry("900x550")
        chart_win.transient(self)
        
        # Center cửa sổ
        chart_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (900 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (550 // 2)
        chart_win.geometry(f"900x550+{x}+{y}")

        # Thêm tiêu đề text ở trên
        tb.Label(chart_win, text=f"BIỂU ĐỒ BIẾN THIÊN NHIỆT ĐỘ - THÁNG {month}", 
                 font=('Segoe UI', 12, 'bold'), bootstyle='primary').pack(pady=(10, 5))
        tb.Label(chart_win, text=f"Thiết bị: {loc}", font=('Segoe UI', 10)).pack(pady=(0, 10))

        # Thiết lập figure matplotlib
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Vẽ đường nhiệt độ
        ax.plot(dates_session, temps, marker='o', color='#0275d8', linewidth=2, label='Nhiệt độ thực tế (°C)')
        
        # Thêm nhãn giá trị nhiệt độ tại các điểm
        for idx, temp in enumerate(temps):
            ax.annotate(f"{temp}°", (dates_session[idx], temps[idx]), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=8, fontweight='bold', color='#111')

        # Thêm đường giới hạn cảnh báo dựa trên loại tủ
        loc_lower = loc.lower()
        if "2-8" in loc_lower or "vaccine" in loc_lower or "lạnh" in loc_lower:
            ax.axhline(y=2.0, color='red', linestyle='--', linewidth=1.5, label='Giới hạn dưới (2°C)')
            ax.axhline(y=8.0, color='red', linestyle='--', linewidth=1.5, label='Giới hạn trên (8°C)')
            ax.set_ylim(0, 12)
        elif "15-25" in loc_lower or "mát" in loc_lower:
            ax.axhline(y=15.0, color='orange', linestyle='--', linewidth=1.5, label='Giới hạn dưới (15°C)')
            ax.axhline(y=25.0, color='orange', linestyle='--', linewidth=1.5, label='Giới hạn trên (25°C)')
            ax.set_ylim(10, 30)
        else:
            ax.axhline(y=30.0, color='red', linestyle='--', linewidth=1.5, label='Giới hạn nhiệt độ thường (30°C)')
            ax.set_ylim(15, 35)

        ax.set_ylabel("Nhiệt độ (°C)", fontsize=10, fontweight='bold')
        ax.set_xlabel("Ngày & Buổi kiểm tra", fontsize=10, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right')
        
        # Xoay label x để đỡ bị dính chữ
        fig.autofmt_xdate(rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=15, pady=10)

        tb.Button(chart_win, text="Đóng biểu đồ", bootstyle='secondary', command=chart_win.destroy).pack(pady=(0, 15))

    def export_temp_log_pdf(self):
        """Xuất PDF Sổ nhật ký nhiệt độ tháng chuyên nghiệp theo quy định GSP"""
        # Kiểm tra reportlab
        try:
            import reportlab
        except ImportError:
            response = messagebox.askyesno(
                "Thiếu thư viện", 
                "Hệ thống thiếu thư viện 'reportlab' để xuất PDF.\nBạn có muốn tự động cài đặt không? (Quá trình này mất khoảng vài giây)"
            )
            if response:
                import subprocess
                import sys
                try:
                    self.toast("Đang cài đặt thư viện reportlab, vui lòng đợi...")
                    subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
                    self.toast("Đã cài đặt reportlab thành công!")
                except Exception as ex:
                    messagebox.showerror("Lỗi cài đặt", f"Không thể tự động cài đặt reportlab: {str(ex)}\nHãy chạy lệnh 'pip install reportlab' trong terminal."); return
            else:
                return

        month = self.temp_filter_month.get()
        loc = self.temp_filter_loc.get()

        if loc == "Tất cả":
            messagebox.showwarning("Chọn thiết bị", "Vui lòng chọn cụ thể một tủ lạnh hoặc kho bảo quản cần xuất nhật ký."); return

        try:
            logs = self.db.get_temperature_logs(month, loc)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy dữ liệu: {str(e)}"); return

        if not logs:
            messagebox.showwarning("Không có dữ liệu", f"Không có dữ liệu ghi chép nào của {loc} trong tháng {month} để xuất báo cáo."); return

        # Cho phép chọn vị trí lưu file PDF
        month_file_str = month.replace('-', '_')
        loc_file_str = "".join([c if c.isalnum() else "_" for c in loc])
        initial_filename = f"Nhat_Ky_Nhiet_Do_{loc_file_str}_{month_file_str}.pdf"
        
        pdf_path = filedialog.asksaveasfilename(
            title="Chọn vị trí lưu Sổ nhật ký nhiệt độ PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=initial_filename
        )
        if not pdf_path:
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Đăng ký font hỗ trợ tiếng Việt
            try:
                pdfmetrics.registerFont(TTFont('TimesNewRoman', "C:\\Windows\\Fonts\\times.ttf"))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', "C:\\Windows\\Fonts\\timesbd.ttf"))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', "C:\\Windows\\Fonts\\timesi.ttf"))
                font_normal = 'TimesNewRoman'
                font_bold = 'TimesNewRoman-Bold'
                font_italic = 'TimesNewRoman-Italic'
            except Exception:
                font_normal = 'Helvetica'
                font_bold = 'Helvetica-Bold'
                font_italic = 'Helvetica-Oblique'

            # Trang nằm ngang (A4 Landscape)
            from reportlab.lib.pagesizes import landscape
            doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []

            styles = getSampleStyleSheet()

            style_header_left = ParagraphStyle(
                'HLeft', parent=styles['Normal'], fontName=font_bold, fontSize=10, leading=13, alignment=0
            )
            style_header_right = ParagraphStyle(
                'HRight', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=12, alignment=2
            )
            style_title = ParagraphStyle(
                'TitleTemp', parent=styles['Heading1'], fontName=font_bold, fontSize=15, leading=18, alignment=1, spaceAfter=5
            )
            style_subtitle = ParagraphStyle(
                'SubTemp', parent=styles['Normal'], fontName=font_italic, fontSize=10, leading=13, alignment=1, spaceAfter=15
            )
            style_tbl_hdr = ParagraphStyle(
                'TblHdr', parent=styles['Normal'], fontName=font_bold, fontSize=9, leading=11, alignment=1
            )
            style_cell = ParagraphStyle(
                'CVal', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=1
            )
            style_cell_left = ParagraphStyle(
                'CValL', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=0
            )

            # Header hai bên
            header_data = [
                [
                    Paragraph("SỞ Y TẾ THÀNH PHỐ CẦN THƠ<br/>TRUNG TÂM KIỂM SOÁT BỆNH TẬT (CDC)", style_header_left),
                    Paragraph("<b>BIỂU MẪU THEO DÕI GSP</b><br/><i>(Quy định theo Thông tư số 36/2018/TT-BYT)</i>", style_header_right)
                ]
            ]
            header_table = Table(header_data, colWidths=[380, 400])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            
            # Tiêu đề báo cáo
            story.append(Paragraph("NHẬT KÝ THEO DÕI NHIỆT ĐỘ, ĐỘ ẨM TỦ BẢO QUẢN / KHO LẠNH", style_title))
            
            # Lấy thông tin tháng
            parts = month.split('-')
            month_text = f"Tháng {parts[1]} năm {parts[0]}"
            story.append(Paragraph(f"Thiết bị/Vị trí theo dõi: {loc} • Thời gian: {month_text}", style_subtitle))

            # Xây dựng bảng nhật ký (bố cục ngang, chia cột rõ ràng)
            # Cột: STT | Ngày | Buổi | Chỉ số nhiệt độ | Chỉ số độ ẩm | Trạng thái | Người ký xác nhận | Ghi chú/Biện pháp khắc phục
            table_data = [
                [
                    Paragraph("<b>STT</b>", style_tbl_hdr),
                    Paragraph("<b>Ngày ghi</b>", style_tbl_hdr),
                    Paragraph("<b>Buổi</b>", style_tbl_hdr),
                    Paragraph("<b>Nhiệt độ (°C)</b>", style_tbl_hdr),
                    Paragraph("<b>Độ ẩm (% RH)</b>", style_tbl_hdr),
                    Paragraph("<b>Đánh giá GSP</b>", style_tbl_hdr),
                    Paragraph("<b>Người ký ghi tên</b>", style_tbl_hdr),
                    Paragraph("<b>Biện pháp khắc phục khi vượt ngưỡng</b>", style_tbl_hdr)
                ]
            ]

            # Sắp xếp từ ngày đầu đến cuối tháng
            logs = list(reversed(logs))
            
            for idx, r in enumerate(logs):
                t = float(r['temperature'])
                h = r['humidity']
                h_str = f"{h}%" if h is not None and h != "" else "-"
                
                # Trạng thái
                loc_lower = r['locationName'].lower()
                status = "Đạt tiêu chuẩn"
                if "2-8" in loc_lower or "vaccine" in loc_lower or "lạnh" in loc_lower:
                    if t < 2.0 or t > 8.0:
                        status = "⚠️ VƯỢT NGƯỠNG"
                elif "15-25" in loc_lower or "mát" in loc_lower:
                    if t < 15.0 or t > 25.0:
                        status = "⚠️ VƯỢT NGƯỠNG"
                else:
                    if t > 30.0 or (h is not None and h != "" and float(h) > 75.0):
                        status = "⚠️ VƯỢT NGƯỠNG"
                
                table_data.append([
                    Paragraph(str(idx + 1), style_cell),
                    Paragraph(format_date_display(r['logDate']), style_cell),
                    Paragraph(r['session'], style_cell),
                    Paragraph(f"<b>{t} °C</b>" if "VƯỢT" in status else f"{t} °C", style_cell),
                    Paragraph(h_str, style_cell),
                    Paragraph(f"<font color='red'><b>{status}</b></font>" if "VƯỢT" in status else status, style_cell),
                    Paragraph(r['recordedBy'] or "-", style_cell),
                    Paragraph("" if "Đạt" in status else "Đã chuyển vaccine sang tủ dự phòng / Báo cáo kỹ thuật", style_cell_left)
                ])

            # Rộng cột
            col_widths = [35, 75, 55, 90, 80, 110, 110, 225]
            t_style = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ])
            
            # Tạo bảng
            temp_table = Table(table_data, colWidths=col_widths)
            temp_table.setStyle(t_style)
            story.append(temp_table)
            story.append(Spacer(1, 20))

            # Chữ ký phê duyệt
            now_dt = dt.datetime.now()
            date_sign_str = f"Ngày {now_dt.strftime('%d')} tháng {now_dt.strftime('%m')} năm {now_dt.strftime('%Y')}"
            
            sig_data = [
                [
                    "",
                    Paragraph(f"<i>Cần Thơ, {date_sign_str}</i>", style_cell)
                ],
                [
                    Paragraph("<b>THỦ KHO CDC</b><br/><i>(Ký và ghi rõ họ tên)</i>", style_cell),
                    Paragraph("<b>LÃNH ĐẠO TRUNG TÂM PHÊ DUYỆT</b><br/><i>(Ký tên và đóng dấu)</i>", style_cell)
                ],
                [
                    Spacer(1, 40),
                    Spacer(1, 40)
                ]
            ]
            sig_table = Table(sig_data, colWidths=[390, 390])
            sig_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(sig_table)

            # Build PDF
            doc.build(story)
            self.toast("Đã xuất bản Sổ nhật ký nhiệt độ thành công!")
            
            # Mở file PDF ngay sau khi lưu
            try:
                os.startfile(pdf_path)
            except:
                pass
        except Exception as ex:
            messagebox.showerror("Lỗi xuất PDF", f"Lỗi không thể tạo file PDF: {str(ex)}")
