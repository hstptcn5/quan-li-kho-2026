# -*- coding: utf-8 -*-
import datetime as dt
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry

from date_utils import format_date_display, parse_date_to_iso


class PurchaseMixin:
    # -------- Purchase --------
    def build_purchase_tab(self):
        frm = self.tab_purchase
        self.cart_purchase = []
        self.last_purchase_items = []
        self.last_purchase_info = {}

        # Header với title đẹp
        header_frame = tb.Frame(frm)
        header_frame.pack(fill='x', padx=8, pady=(8,4))
        
        title_label = tb.Label(header_frame, text='📦 Nhập kho / Lập phiếu nhập', 
                              font=('Segoe UI', 14, 'bold'), bootstyle='success')
        title_label.pack(anchor='w')
        
        subtitle_label = tb.Label(header_frame, text='Lập phiếu nhập kho thuốc, vaccine và vật tư y tế', 
                                 font=('Segoe UI', 9), bootstyle='secondary')
        subtitle_label.pack(anchor='w')

        # --- Khung thông tin phiếu nhập
        info_note = tb.Labelframe(frm, text='📝 Thông tin phiếu nhập kho', bootstyle='secondary')
        info_note.pack(fill='x', padx=8, pady=8)

        # Nhà cung cấp / Nguồn cấp
        tb.Label(info_note, text='Nguồn cấp/Nhà CC:').grid(row=0, column=0, padx=6, pady=6, sticky='w')
        self.cmb_supplier = tb.Combobox(info_note, width=25)
        self.cmb_supplier.grid(row=0, column=1, padx=6, pady=6, sticky='w')
        self.refresh_suppliers_combo()

        # Ngày nhập
        tb.Label(info_note, text='Ngày nhập:').grid(row=0, column=2, padx=6, pady=6, sticky='w')
        self.ent_purchase_date = DateEntry(
            info_note,
            dateformat="%d-%m-%Y",
            firstweekday=0,
            bootstyle='info',
            width=12
        )
        self.ent_purchase_date.grid(row=0, column=3, padx=6, pady=6, sticky='w')

        # Lý do nhập
        tb.Label(info_note, text='Lý do nhập:').grid(row=0, column=4, padx=6, pady=6, sticky='w')
        self.cmb_purchase_reason = tb.Combobox(info_note, values=['Nhận cấp phát tuyến trên', 'Mua sắm đấu thầu', 'Viện trợ - Tài trợ', 'Khác'], width=22, state='readonly')
        self.cmb_purchase_reason.set('Nhận cấp phát tuyến trên')
        self.cmb_purchase_reason.grid(row=0, column=5, padx=6, pady=6, sticky='w')

        # Ghi chú
        tb.Label(info_note, text='Ghi chú:').grid(row=1, column=0, padx=6, pady=6, sticky='w')
        self.ent_purchase_note = tb.Entry(info_note)
        self.ent_purchase_note.grid(row=1, column=1, columnspan=5, padx=6, pady=6, sticky='ew')
        info_note.columnconfigure(1, weight=1)

        # --- Khung nhập sản phẩm
        box = tb.Labelframe(frm, text='➕ Thêm sản phẩm vào phiếu nhập', bootstyle='secondary')
        box.pack(fill='x', padx=8, pady=4)

        # Cho các cột có thể giãn đều khi thay đổi kích thước cửa sổ
        for i in range(12):
            box.grid_columnconfigure(i, weight=1)

        # ── Hàng 0: Tìm kiếm + Combobox chọn sản phẩm
        tb.Label(box, text='Tìm sản phẩm:').grid(row=0, column=0, sticky='w', padx=6, pady=6)
        self.search_purchase = tb.Entry(box)
        self.search_purchase.grid(row=0, column=1, columnspan=4, sticky='ew', padx=6, pady=6)
        self.search_purchase.bind('<KeyRelease>', lambda e: self.filter_product_list())
        self.search_purchase.bind('<Down>', lambda e: self.open_combo(self.cmb_prod)) 

        tb.Label(box, text='Chọn:').grid(row=0, column=5, sticky='e', padx=6, pady=6)
        self.cmb_prod = tb.Combobox(box, state='readonly')
        self.cmb_prod.grid(row=0, column=6, columnspan=5, sticky='ew', padx=6, pady=6)
        self.cmb_prod.bind('<<ComboboxSelected>>', lambda e: self.update_purchase_unit_and_price())
        self.cmb_prod.bind('<Escape>', lambda e: self.search_purchase.focus_set())  # ESC quay lại ô tìm
        self.cmb_prod.bind('<Return>', lambda e: self.ent_qty.focus_set())

        # ── Hàng 1: Đơn vị, Số lượng, Số lô, HSD
        tb.Label(box, text='Đơn vị tính:').grid(row=1, column=0, sticky='w', padx=6, pady=6)
        self.lbl_unit_purchase = tb.Label(box, text='-')
        self.lbl_unit_purchase.grid(row=1, column=1, sticky='w', padx=6, pady=6)

        tb.Label(box, text='Số lượng:').grid(row=1, column=2, sticky='e', padx=6, pady=6)
        self.ent_qty = tb.Entry(box, width=10)
        self.ent_qty.insert(0, '1')
        self.ent_qty.grid(row=1, column=3, sticky='w', padx=6, pady=6)
        self._numberize(self.ent_qty)

        tb.Label(box, text='Số lô:').grid(row=1, column=4, sticky='e', padx=6, pady=6)
        self.ent_lot = tb.Entry(box, width=14)
        self.ent_lot.insert(0, 'LOT001')
        self.ent_lot.grid(row=1, column=5, sticky='w', padx=6, pady=6)

        tb.Label(box, text='HSD (DD-MM-YYYY):').grid(row=1, column=6, sticky='e', padx=6, pady=6)
        self.ent_exp = DateEntry(
            box,
            dateformat="%d-%m-%Y",
            firstweekday=0,     # Monday
            bootstyle='info'
        )
        self.ent_exp.grid(row=1, column=7, sticky='w', padx=6, pady=6)

        # ── Hàng 2: Đơn giá nhập hoặc tổng tiền dòng
        tb.Label(box, text='Đơn giá nhập:').grid(row=2, column=0, sticky='w', padx=6, pady=(6,8))
        self.ent_cost = tb.Entry(box, width=12)
        self.ent_cost.insert(0, '0')
        self.ent_cost.grid(row=2, column=1, sticky='w', padx=6, pady=(6,8))
        self._numberize(self.ent_cost)

        tb.Label(box, text='Tổng tiền dòng:').grid(row=2, column=2, sticky='e', padx=6, pady=(6,8))
        self.ent_line_total = tb.Entry(box, width=14)
        self.ent_line_total.grid(row=2, column=3, sticky='w', padx=6, pady=(6,8))
        self._numberize(self.ent_line_total)

        tb.Label(box, text='Nguồn kinh phí:').grid(row=2, column=4, sticky='e', padx=6, pady=(6,8))
        self.cmb_item_fund = tb.Combobox(
            box,
            values=[
                'TCMR (Tiêm chủng mở rộng)',
                'Ngân sách địa phương',
                'Dự án viện trợ',
                'Mua sắm đấu thầu',
                'Nguồn khác'
            ],
            width=25
        )
        self.cmb_item_fund.set('TCMR (Tiêm chủng mở rộng)')
        self.cmb_item_fund.grid(row=2, column=5, columnspan=3, sticky='w', padx=6, pady=(6,8))

        # --- Nút tác vụ
        btns = tb.Frame(frm)
        btns.pack(fill='x', padx=8, pady=8)
        
        # Nhóm chính bên trái
        tb.Button(btns, text='+ Thêm vào giỏ hàng', bootstyle='primary', command=self.add_to_purchase_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Xác nhận nhập kho', bootstyle='success', command=self.confirm_purchase).pack(side='left', padx=4)
        tb.Button(btns, text='In phiếu nhập kho', bootstyle='info', command=self.print_purchase_note).pack(side='left', padx=4)
        
        # Nhóm xóa hủy bên phải (phòng tránh bấm nhầm)
        tb.Button(btns, text='Xóa danh sách', bootstyle='danger-outline', command=self.clear_purchase_cart).pack(side='right', padx=4)
        tb.Button(btns, text='Xóa dòng', bootstyle='warning', command=self.remove_selected_purchase_item).pack(side='right', padx=4)

        # --- Bảng danh sách hàng nhập tạm thời
        cols = ('product','productName','unit','qty','lot','exp','cost','fundSource','total')
        self.tree_purchase_cart = tb.Treeview(frm, columns=cols, show='headings')
        for c, w, t, anchor in [
            ('product',50,'PID','center'),('productName',220,'Tên thuốc/vaccine/VTYT','w'),
            ('unit',60,'ĐVT','center'),('qty',60,'SL','e'),('lot',80,'Số lô','w'),
            ('exp',80,'HSD','center'),('cost',95,'Đơn giá nhập','e'),
            ('fundSource',135,'Nguồn kinh phí','w'),('total',105,'Thành tiền','e')
        ]:
            self.tree_purchase_cart.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_purchase_cart, col)))
            self.tree_purchase_cart.column(c, width=w, anchor=anchor)
        self.tree_purchase_cart.tag_configure('odd', background='#f6f8fa')
        self.tree_purchase_cart.pack(fill='both', expand=True, padx=8, pady=8)
        summary_frame = tb.Frame(frm)
        summary_frame.pack(fill='x', padx=8, pady=(0, 8))
        self.lbl_purchase_cart_total = tb.Label(
            summary_frame,
            text='Tổng tiền tạm tính: 0 VNĐ',
            font=('Segoe UI', 12, 'bold'),
            bootstyle='success'
        )
        self.lbl_purchase_cart_total.pack(side='right')

    def update_purchase_unit_and_price(self):
        sel = self.cmb_prod.get()
        if not sel: self.lbl_unit_purchase.config(text='-'); return
        pid = int(sel.split(' — ')[0])
        du = self.db.default_unit_of(pid) or '-'
        self.lbl_unit_purchase.config(text=du)

    def filter_product_list(self):
        kw = (self.search_purchase.get() or '').strip().lower()
        opts = [f"{p['id']} — {p['name']}" for p in self._products if kw in p['name'].lower()]
        self.cmb_prod['values'] = opts
        if opts:
            self.cmb_prod.current(0)
            self.update_purchase_unit_and_price()

    def refresh_suppliers_combo(self):
        try:
            suppliers = self.db.get_suppliers()
            self.cmb_supplier['values'] = suppliers
        except Exception as e:
            print(f"Lỗi tải nhà cung cấp: {e}")

    def add_to_purchase_cart(self):
        sel = self.cmb_prod.get()
        if not sel:
            messagebox.showerror('Lỗi', 'Chọn sản phẩm để nhập'); return
        pid = int(sel.split(' — ')[0])
        unit = self.db.default_unit_of(pid) or 'vien'
        try:
            qty = float(self.ent_qty.get())
        except:
            qty = 0
        if qty <= 0:
            messagebox.showerror('Lỗi', 'Số lượng nhập phải > 0'); return
        
        lot = self.ent_lot.get().strip()
        if not lot:
            messagebox.showerror('Lỗi', 'Vui lòng nhập số lô'); return
            
        exp = parse_date_to_iso(self.ent_exp.entry.get())
        try:
            dt.datetime.strptime(exp, '%Y-%m-%d')
        except:
            messagebox.showerror('Lỗi', 'Hạn sử dụng không hợp lệ (DD-MM-YYYY)'); return
            
        try:
            cost = float((self.ent_cost.get() or '0').replace(',', ''))
        except:
            cost = 0.0
        if cost < 0:
            messagebox.showerror('Lỗi', 'Đơn giá nhập không được âm'); return

        total_raw = (self.ent_line_total.get() or '').strip().replace(',', '')
        if total_raw:
            try:
                line_total = float(total_raw)
            except:
                messagebox.showerror('Lỗi', 'Tổng tiền dòng không hợp lệ'); return
            if line_total < 0:
                messagebox.showerror('Lỗi', 'Tổng tiền dòng không được âm'); return
            cost = line_total / qty if qty else 0.0
        else:
            line_total = qty * cost

        name = self.name_by_id(pid)
        fund_source = self.cmb_item_fund.get().strip()
        
        merged = False
        for it in self.cart_purchase:
            if it['productId'] == pid and it['lotNo'] == lot and it.get('fundSource') == fund_source:
                it['qty'] = round(it['qty'] + qty, 4)
                it['totalAmount'] = float(it.get('totalAmount') or 0) + line_total
                it['cost'] = it['totalAmount'] / it['qty'] if it['qty'] else 0.0
                merged = True
                break
        if not merged:
            self.cart_purchase.append({
                'productId': pid,
                'productName': name,
                'unitCode': unit,
                'qty': qty,
                'lotNo': lot,
                'expiryDate': exp,
                'cost': cost,
                'totalAmount': line_total,
                'fundSource': fund_source
            })

        self.refresh_purchase_cart_view()
        self.ent_qty.delete(0, tk.END)
        self.ent_qty.insert(0, '1')
        self.ent_line_total.delete(0, tk.END)
        self.search_purchase.focus_set()

    def remove_selected_purchase_item(self):
        sel = self.tree_purchase_cart.selection()
        if not sel:
            return
        idx = self.tree_purchase_cart.index(sel[0])
        if 0 <= idx < len(self.cart_purchase):
            self.cart_purchase.pop(idx)
            self.refresh_purchase_cart_view()

    def clear_purchase_cart(self):
        if self.cart_purchase and messagebox.askyesno('Xác nhận', 'Xóa toàn bộ danh sách hàng nhập kho?'):
            self.cart_purchase = []
            self.refresh_purchase_cart_view()

    def refresh_purchase_cart_view(self):
        for i in self.tree_purchase_cart.get_children():
            self.tree_purchase_cart.delete(i)
        for idx, it in enumerate(self.cart_purchase):
            total_val = float(it.get('totalAmount') if it.get('totalAmount') is not None else it['qty'] * it['cost'])
            self.tree_purchase_cart.insert('', 'end',
                values=(
                    it['productId'], 
                    it['productName'], 
                    it['unitCode'], 
                    f"{it['qty']:g}", 
                    it['lotNo'], 
                    format_date_display(it['expiryDate']),
                    f"{it['cost']:,.0f}", 
                    it.get('fundSource', ''),
                    f"{total_val:,.0f}"
                ),
                tags=('odd',) if idx % 2 else ())
        total_sum = sum(float(it.get('totalAmount') if it.get('totalAmount') is not None else float(it.get('qty') or 0) * float(it.get('cost') or 0)) for it in self.cart_purchase)
        if hasattr(self, 'lbl_purchase_cart_total'):
            self.lbl_purchase_cart_total.config(text=f'Tổng tiền tạm tính: {total_sum:,.0f} VNĐ')

    def confirm_purchase(self):
        if not self.cart_purchase:
            messagebox.showwarning('Chưa có dữ liệu', 'Danh sách nhập kho trống'); return
        
        supplier = self.cmb_supplier.get().strip()
        if not supplier:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập/chọn Nguồn cấp/Nhà cung cấp'); return
        
        date_str = self._parse_date_entry(self.ent_purchase_date)
                
        reason = self.cmb_purchase_reason.get().strip()
        note = self.ent_purchase_note.get().strip()

        if not messagebox.askyesno('Xác nhận', f'Bạn có chắc chắn muốn nhập kho từ:\nNguồn cấp: {supplier}\nNgày nhập: {date_str or "Hôm nay"}\nLý do: {reason}?'):
            return

        try:
            purchase_id, note_number, details = self.db.record_purchase(self.cart_purchase, supplier, reason, note, date_str)
            self.last_purchase_items = details
            
            created_at_str = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}" if date_str else dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_purchase_info = {
                'id': purchase_id,
                'noteNumber': note_number,
                'supplier': supplier,
                'reason': reason,
                'note': note,
                'createdAt': created_at_str
            }
            self.cart_purchase = []
            self.refresh_purchase_cart_view()
            self.refresh_stock()
            self.refresh_suppliers_combo()
            if hasattr(self, 'refresh_report_funds_combo'):
                self.refresh_report_funds_combo()
            messagebox.showinfo('Thành công', f'Đã nhập kho thành công!\nSố phiếu: {note_number}')
            
            # Tự động hỏi in phiếu nhập kho
            if messagebox.askyesno('In phiếu', 'Bạn có muốn in phiếu nhập kho ngay bây giờ?'):
                self.print_purchase_note()
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Lỗi nhập kho: {str(e)}')

    def print_purchase_note(self):
        if not self.last_purchase_items:
            messagebox.showwarning('Chưa có dữ liệu', 'Hãy thực hiện nhập kho trước khi in phiếu'); return
        
        info = self.last_purchase_info
        
        # Cho phép người dùng chọn vị trí lưu file PDF
        initial_filename = f"Phieu_Nhap_Kho_{info['noteNumber']}.pdf"
        pdf_path = filedialog.asksaveasfilename(
            title="Chọn vị trí lưu phiếu nhập kho PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=initial_filename
        )
        if not pdf_path:
            return

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

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
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
                
            doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            
            styles = getSampleStyleSheet()
            
            style_header_left = ParagraphStyle(
                'HeaderLeft', parent=styles['Normal'], fontName=font_bold, fontSize=10, leading=14, alignment=0
            )
            style_header_right = ParagraphStyle(
                'HeaderRight', parent=styles['Normal'], fontName=font_normal, fontSize=10, leading=14, alignment=2
            )
            style_title = ParagraphStyle(
                'Title', parent=styles['Heading1'], fontName=font_bold, fontSize=16, leading=20, alignment=1, spaceAfter=5
            )
            style_subtitle = ParagraphStyle(
                'Subtitle', parent=styles['Normal'], fontName=font_bold, fontSize=11, leading=14, alignment=1, spaceAfter=15
            )
            style_info = ParagraphStyle(
                'Info', parent=styles['Normal'], fontName=font_normal, fontSize=11, leading=16, alignment=0
            )
            style_table_header = ParagraphStyle(
                'TableHeader', parent=styles['Normal'], fontName=font_bold, fontSize=9, leading=11, alignment=1, textColor=colors.black
            )
            style_cell = ParagraphStyle(
                'Cell', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=0
            )
            style_cell_center = ParagraphStyle(
                'CellCenter', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=1
            )
            style_cell_right = ParagraphStyle(
                'CellRight', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=2
            )
            
            # Header
            header_data = [
                [
                    Paragraph("SỞ Y TẾ THÀNH PHỐ CẦN THƠ<br/>TRUNG TÂM KIỂM SOÁT BỆNH TẬT (CDC)", style_header_left),
                    Paragraph("<b>Mẫu số: C30-HD</b><br/><i>(Ban hành theo Thông tư số 107/2017/TT-BTC)</i>", style_header_right)
                ]
            ]
            header_table = Table(header_data, colWidths=[280, 230])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 10))
            
            # Title
            story.append(Paragraph("PHIẾU NHẬP KHO", style_title))
            story.append(Paragraph(f"Số: {info['noteNumber']}", style_subtitle))
            
            # Parse Date
            created_str = info['createdAt']
            try:
                created_at_dt = dt.datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    created_at_dt = dt.datetime.strptime(created_str.split(' ')[0], '%Y-%m-%d')
                except Exception:
                    created_at_dt = dt.datetime.now()
            
            info_lines = [
                f"<b>Nguồn cấp / Nhà CC:</b> {info['supplier']}",
                f"<b>Lý do nhập:</b> {info['reason']}",
                f"<b>Kho nhập:</b> Kho Dược CDC Cần Thơ",
                f"<b>Ngày nhập:</b> {created_at_dt.strftime('%d-%m-%Y')}",
                f"<b>Ghi chú:</b> {info['note'] or 'Không'}"
            ]
            for line in info_lines:
                story.append(Paragraph(line, style_info))
                story.append(Spacer(1, 4))
                
            story.append(Spacer(1, 10))
            
            # Table items
            table_data = [
                [
                    Paragraph("STT", style_table_header),
                    Paragraph("Tên thuốc, vaccine, VTYT", style_table_header),
                    Paragraph("ĐVT", style_table_header),
                    Paragraph("Số lượng", style_table_header),
                    Paragraph("Đơn giá", style_table_header),
                    Paragraph("Thành tiền", style_table_header),
                    Paragraph("Số lô", style_table_header),
                    Paragraph("Hạn dùng", style_table_header)
                ]
            ]
            
            total_sum = 0.0
            for idx, it in enumerate(self.last_purchase_items, 1):
                qty = it['qty']
                cost = it['cost']
                sub_total = float(it.get('totalAmount') if it.get('totalAmount') is not None else qty * cost)
                total_sum += sub_total
                
                table_data.append([
                    Paragraph(str(idx), style_cell_center),
                    Paragraph(it['productName'], style_cell),
                    Paragraph(it['unitCode'], style_cell_center),
                    Paragraph(f"{qty:g}", style_cell_right),
                    Paragraph(f"{cost:,.0f}", style_cell_right),
                    Paragraph(f"{sub_total:,.0f}", style_cell_right),
                    Paragraph(it['lotNo'] or '', style_cell_center),
                    Paragraph(format_date_display(it['expiryDate']), style_cell_center)
                ])
            
            # Thêm dòng tổng cộng
            table_data.append([
                Paragraph("<b>Tổng cộng</b>", style_cell_center),
                Paragraph("", style_cell),
                Paragraph("", style_cell_center),
                Paragraph("", style_cell_right),
                Paragraph("", style_cell_right),
                Paragraph(f"<b>{total_sum:,.0f}</b>", style_cell_right),
                Paragraph("", style_cell_center),
                Paragraph("", style_cell_center)
            ])
                
            col_widths = [25, 160, 45, 55, 65, 75, 55, 50]
            items_table = Table(table_data, colWidths=col_widths)
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('SPAN', (0, -1), (4, -1)),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 15))
            
            # Signatures
            date_right_style = ParagraphStyle(
                'DateRight', parent=styles['Normal'], fontName=font_italic, fontSize=11, alignment=2, spaceAfter=10
            )
            sig_title_style = ParagraphStyle(
                'SigTitle', parent=styles['Normal'], fontName=font_bold, fontSize=11, alignment=1
            )
            sig_sub_style = ParagraphStyle(
                'SigSub', parent=styles['Normal'], fontName=font_italic, fontSize=9, alignment=1
            )
            
            story.append(Paragraph(f"Cần Thơ, ngày {created_at_dt.strftime('%d')} tháng {created_at_dt.strftime('%m')} năm {created_at_dt.strftime('%Y')}", date_right_style))
            
            sig_headers = [
                [
                    Paragraph("<b>Người lập phiếu</b>", sig_title_style),
                    Paragraph("<b>Người giao hàng</b>", sig_title_style),
                    Paragraph("<b>Thủ kho</b>", sig_title_style),
                    Paragraph("<b>Kế toán trưởng</b>", sig_title_style),
                    Paragraph("<b>Lãnh đạo đơn vị</b>", sig_title_style)
                ],
                [
                    Paragraph("(Ký, họ tên)", sig_sub_style),
                    Paragraph("(Ký, họ tên)", sig_sub_style),
                    Paragraph("(Ký, họ tên)", sig_sub_style),
                    Paragraph("(Ký, họ tên)", sig_sub_style),
                    Paragraph("(Ký, đóng dấu)", sig_sub_style)
                ]
            ]
            sig_table = Table(sig_headers, colWidths=[102, 102, 102, 102, 102])
            sig_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(sig_table)
            story.append(Spacer(1, 60))
            
            doc.build(story)
            os.startfile(pdf_path)
            self.toast("Đã in phiếu nhập ra PDF và mở file thành công")
        except Exception as e:
            messagebox.showerror("Lỗi in PDF", f"Không thể xuất file PDF: {str(e)}")


