# -*- coding: utf-8 -*-
import datetime as dt
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry

from config import BARCODE_AVAILABLE
from date_utils import format_date_display, parse_date_to_iso
from scanner import BarcodeScanner


class DispatchMixin:
    # -------- Xuất kho / Cấp phát (Dispatch) --------
    def build_dispatch_tab(self):
        frm = self.tab_dispatch

        # Header với title đẹp
        header_frame = tb.Frame(frm)
        header_frame.pack(fill='x', padx=8, pady=(8,4))
        
        title_label = tb.Label(header_frame, text='📤 Xuất kho / Cấp phát', 
                              font=('Segoe UI', 14, 'bold'), bootstyle='warning')
        title_label.pack(anchor='w')
        
        subtitle_label = tb.Label(header_frame, text='Cấp phát thuốc, vaccine và vật tư y tế cho các đơn vị tuyến dưới theo nguyên tắc FEFO', 
                                 font=('Segoe UI', 9), bootstyle='secondary')
        subtitle_label.pack(anchor='w')

        # --- Khung thông tin phiếu xuất
        info_note = tb.Labelframe(frm, text='📝 Thông tin phiếu xuất kho', bootstyle='light')
        info_note.pack(fill='x', padx=8, pady=8)

        # Đơn vị nhận
        tb.Label(info_note, text='Đơn vị nhận:').grid(row=0, column=0, padx=6, pady=6, sticky='w')
        self.cmb_receiving_unit = tb.Combobox(info_note, width=25)
        self.cmb_receiving_unit.grid(row=0, column=1, padx=6, pady=6, sticky='w')
        self.refresh_receiving_units_combo()

        # Ngày xuất
        tb.Label(info_note, text='Ngày xuất:').grid(row=0, column=2, padx=6, pady=6, sticky='w')
        self.ent_dispatch_date = DateEntry(
            info_note,
            dateformat="%d-%m-%Y",
            firstweekday=0,
            bootstyle='info',
            width=12
        )
        self.ent_dispatch_date.grid(row=0, column=3, padx=6, pady=6, sticky='w')

        # Lý do xuất
        tb.Label(info_note, text='Lý do xuất:').grid(row=0, column=4, padx=6, pady=6, sticky='w')
        self.cmb_reason = tb.Combobox(info_note, values=['Cấp phát', 'Hủy kho', 'Chuyển kho', 'Khác'], width=15, state='readonly')
        self.cmb_reason.set('Cấp phát')
        self.cmb_reason.grid(row=0, column=5, padx=6, pady=6, sticky='w')

        # Ghi chú (đặt xuống hàng 1 để rộng rãi hơn)
        tb.Label(info_note, text='Ghi chú:').grid(row=1, column=0, padx=6, pady=6, sticky='w')
        self.ent_dispatch_note = tb.Entry(info_note)
        self.ent_dispatch_note.grid(row=1, column=1, columnspan=5, padx=6, pady=6, sticky='ew')
        info_note.columnconfigure(1, weight=1)

        # --- Khung thao tác chọn hàng xuất
        op_frame = tb.Labelframe(frm, text='🛒 Thao tác chọn hàng xuất', bootstyle='light')
        op_frame.pack(fill='x', padx=8, pady=4)

        # Hàng 0: Barcode & Quét, Tìm nhanh, Chọn sản phẩm
        tb.Label(op_frame, text='Barcode:').grid(row=0, column=0, padx=6, pady=6, sticky='w')
        barcode_inner = tb.Frame(op_frame)
        barcode_inner.grid(row=0, column=1, padx=6, pady=6, sticky='ew')
        
        self.ent_barcode = tb.Entry(barcode_inner, width=12)
        self.ent_barcode.pack(side='left', fill='x', expand=True, padx=(0, 4))
        self.ent_barcode.bind('<Return>', lambda e: self.scan_and_add_dispatch())
        self.ent_barcode.bind('<KP_Enter>', lambda e: self.scan_and_add_dispatch())
        
        if BARCODE_AVAILABLE:
            btn_scan = tb.Button(barcode_inner, text='📷 Quét', command=self.open_barcode_scanner_dispatch, 
                                 bootstyle='info', width=6)
        else:
            btn_scan = tb.Button(barcode_inner, text='📷 Quét', command=self.show_barcode_install_info, 
                                 bootstyle='secondary', width=6)
        btn_scan.pack(side='right')

        tb.Label(op_frame, text='Tìm nhanh:').grid(row=0, column=2, padx=6, pady=6, sticky='w')
        self.search_pos = tb.Entry(op_frame, width=15)
        self.search_pos.grid(row=0, column=3, padx=6, pady=6, sticky='ew')

        tb.Label(op_frame, text='Chọn sản phẩm:').grid(row=0, column=4, padx=6, pady=6, sticky='w')
        self.cmb_prod_pos = tb.Combobox(op_frame, state='readonly', width=35)
        self.cmb_prod_pos.grid(row=0, column=5, padx=6, pady=6, sticky='ew')

        # Hàng 1: Chọn lô, Nguồn xuất, SL xuất
        tb.Label(op_frame, text='Chọn lô:').grid(row=1, column=0, padx=6, pady=6, sticky='w')
        self.cmb_lot_pos = tb.Combobox(op_frame, state='readonly', width=20)
        self.cmb_lot_pos.grid(row=1, column=1, padx=6, pady=6, sticky='ew')

        tb.Label(op_frame, text='Nguồn xuất:').grid(row=1, column=2, padx=6, pady=6, sticky='w')
        self.cmb_fund_pos = tb.Combobox(op_frame, state='readonly', width=20)
        self.cmb_fund_pos.grid(row=1, column=3, padx=6, pady=6, sticky='ew')

        tb.Label(op_frame, text='SL xuất:').grid(row=1, column=4, padx=6, pady=6, sticky='w')
        qty_inner = tb.Frame(op_frame)
        qty_inner.grid(row=1, column=5, padx=6, pady=6, sticky='w')
        
        self.ent_qty_pos = tb.Entry(qty_inner, width=10)
        self.ent_qty_pos.insert(0, '1')
        self.ent_qty_pos.pack(side='left', padx=(0, 10))
        self._numberize(self.ent_qty_pos)

        # Cấu hình co giãn các cột trong op_frame
        op_frame.columnconfigure(1, weight=1)
        op_frame.columnconfigure(3, weight=1)
        op_frame.columnconfigure(5, weight=2)

        # --- Bind sự kiện
        self.search_pos.bind('<KeyRelease>', lambda e: self.filter_product_list_dispatch())
        self.search_pos.bind('<Down>', lambda e: (self.cmb_prod_pos.focus_set(),
                                                   self.cmb_prod_pos.event_generate('<Alt-Down>')))

        self.cmb_prod_pos.bind('<<ComboboxSelected>>', lambda e: self.update_dispatch_unit_label())
        self.cmb_prod_pos.bind('<Escape>', lambda e: self.search_pos.focus_set())
        self.cmb_prod_pos.bind('<Return>', lambda e: (self.cmb_lot_pos.focus_set(),
                                                      self.cmb_lot_pos.event_generate('<Alt-Down>')))
        self.cmb_lot_pos.bind('<<ComboboxSelected>>', lambda e: self.update_dispatch_funds())
        self.cmb_lot_pos.bind('<Return>', lambda e: (self.cmb_fund_pos.focus_set(),
                                                      self.cmb_fund_pos.event_generate('<Alt-Down>')))
        self.cmb_fund_pos.bind('<Return>', lambda e: self.ent_qty_pos.focus_set())

        # --- Nút tác vụ
        btns = tb.Frame(frm)
        btns.pack(fill='x', padx=8, pady=8)
        
        # Nhóm chính bên trái
        tb.Button(btns, text='+ Thêm vào giỏ hàng', bootstyle='primary', command=self.add_to_dispatch_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Xác nhận xuất kho', bootstyle='success', command=self.confirm_dispatch).pack(side='left', padx=4)
        tb.Button(btns, text='In phiếu xuất kho', bootstyle='info', command=self.print_dispatch_note).pack(side='left', padx=4)
        
        # Nhóm xóa hủy bên phải (phòng tránh bấm nhầm)
        tb.Button(btns, text='Xóa danh sách', bootstyle='danger-outline', command=self.clear_dispatch_cart).pack(side='right', padx=4)
        tb.Button(btns, text='Xóa dòng', bootstyle='warning', command=self.remove_selected_dispatch_item).pack(side='right', padx=4)

        # --- Info tổng quan đơn vị
        info = tb.Frame(frm)
        info.pack(fill='x', padx=8, pady=(0, 4))
        self.lbl_unit_pos = tb.Label(info, text='Đơn vị tính: -', font=('Segoe UI', 10))
        self.lbl_unit_pos.pack(side='left', padx=(8, 12))

        # Báº£ng giÃ³ hÃ ng xuáº¥t
        cols = ('productId', 'productName', 'lotNo', 'expiryDate', 'fundSource', 'unitCode', 'price', 'qty', 'amount')
        self.tree_cart = tb.Treeview(frm, columns=cols, show='headings', height=10)
        for c, w, t, anchor in [
            ('productId', 60, 'PID', 'center'),
            ('productName', 220, 'Tên hàng hóa', 'w'),
            ('lotNo', 100, 'Số lô', 'center'),
            ('expiryDate', 100, 'Hạn dùng', 'center'),
            ('fundSource', 120, 'Nguồn kinh phí', 'w'),
            ('unitCode', 60, 'ĐVT', 'center'),
            ('price', 80, 'Đơn giá', 'e'),
            ('qty', 80, 'SL xuất', 'e'),
            ('amount', 100, 'Thành tiền', 'e')
        ]:
            self.tree_cart.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_cart, col)))
            self.tree_cart.column(c, width=w, anchor=anchor)
        self.tree_cart.tag_configure('odd', background='#f6f8fa')
        self.tree_cart.pack(fill='both', expand=True, padx=8, pady=8)

        self.ent_qty_pos.bind('<Return>', lambda e: self.add_to_dispatch_cart())
        self.cart_dispatch = []
        self.last_dispatch_items = []
        self.last_dispatch_info = {}

    def refresh_receiving_units_combo(self):
        """Cập nhật danh sách đơn vị nhận vào combobox"""
        try:
            units = self.db.get_receiving_units()
            self.cmb_receiving_unit['values'] = units
        except Exception as e:
            print(f"Lỗi refresh đơn vị nhận: {e}")

    def _parse_date_entry(self, date_entry):
        """Return YYYY-MM-DD for SQLite queries while accepting DD-MM-YYYY UI input."""
        return parse_date_to_iso(date_entry.entry.get(), default_today=True)

    def _date_range_from_entries(self, from_entry, to_entry):
        start_date = parse_date_to_iso(from_entry.entry.get())
        end_date = parse_date_to_iso(to_entry.entry.get())
        return start_date, end_date

    def _date_range_label(self, start_date, end_date):
        return f"{format_date_display(start_date)} -> {format_date_display(end_date)}"

    def update_dispatch_unit_label(self):
        sel = self.cmb_prod_pos.get()
        if not sel:
            self.lbl_unit_pos.config(text='Đơn vị tính: -')
            self.cmb_lot_pos['values'] = []
            self.cmb_lot_pos.set('')
            return
        pid = int(sel.split(' — ')[0])
        du = self.db.default_unit_of(pid) or '-'
        
        ref_date = self._parse_date_entry(self.ent_dispatch_date)

        # Lấy các lô hàng khả dụng theo FEFO
        lots = self.db.q('''
          SELECT b.lotNo, b.expiryDate, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
          FROM stock_movements sm
          JOIN batches b ON b.id = sm.batchId
          WHERE sm.productId=?
          GROUP BY sm.batchId
          HAVING qtyBase > 0 AND DATE(b.expiryDate) >= DATE(?)
          ORDER BY DATE(b.expiryDate)
        ''', (pid, ref_date))
        
        lot_info_strs = []
        for lot in lots[:3]:
            lot_info_strs.append(f"{lot['lotNo']} (HSD: {format_date_display(lot['expiryDate'])}) - Còn: {lot['qtyBase']:g}")
        if len(lots) > 3:
            lot_info_strs.append("...")
            
        if lot_info_strs:
            lots_str = "  |  Lô khả dụng trong kho (FEFO): " + ", ".join(lot_info_strs)
        else:
            lots_str = "  |  HẾT HÀNG TRONG KHO"
            
        self.lbl_unit_pos.config(text=f'Đơn vị tính: {du}{lots_str}')
        
        # Cập nhật danh sách chọn lô thủ công
        lot_options = ["[Tự động - FEFO]"]
        for lot in lots:
            lot_options.append(f"{lot['lotNo']} (HSD: {format_date_display(lot['expiryDate'])}) - Tồn: {lot['qtyBase']:g}")
        self.cmb_lot_pos['values'] = lot_options
        self.cmb_lot_pos.current(0)
        self.update_dispatch_funds()

    def update_dispatch_funds(self):
        sel = self.cmb_prod_pos.get()
        if not sel:
            self.cmb_fund_pos['values'] = []
            self.cmb_fund_pos.set('')
            return
        pid = int(sel.split(' — ')[0])
        
        ref_date = self._parse_date_entry(self.ent_dispatch_date)

        # Lấy lô được chọn
        chosen_val = self.cmb_lot_pos.get()
        chosen_lot = None
        if chosen_val and chosen_val != "[Tự động - FEFO]":
            chosen_lot = chosen_val.split(" (HSD:")[0].strip()
            
        if chosen_lot:
            # Lọc nguồn theo lô cụ thể
            funds = self.db.q('''
                SELECT sm.fundSource, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                FROM stock_movements sm
                JOIN batches b ON b.id = sm.batchId
                WHERE sm.productId=? AND b.lotNo=?
                GROUP BY sm.fundSource
                HAVING qtyBase > 0
            ''', (pid, chosen_lot))
        else:
            # Lọc nguồn theo sản phẩm nói chung (tổng tất cả các lô chưa hết hạn tại ref_date)
            funds = self.db.q('''
                SELECT sm.fundSource, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                FROM stock_movements sm
                JOIN batches b ON b.id = sm.batchId
                WHERE sm.productId=? AND DATE(b.expiryDate) >= DATE(?)
                GROUP BY sm.fundSource
                HAVING qtyBase > 0
            ''', (pid, ref_date))
            
        fund_options = ["[Tự động trừ kho]"]
        for f in funds:
            f_name = f['fundSource'] or 'Không rõ nguồn'
            fund_options.append(f"{f_name} - Tồn: {f['qtyBase']:g}")
            
        self.cmb_fund_pos['values'] = fund_options
        self.cmb_fund_pos.current(0)

    def fill_product_by_barcode_dispatch(self, only_select=False):
        bc = self.ent_barcode.get().strip()
        if not bc:
            return False
        row = self.db.q("SELECT id, name FROM products WHERE barcode=?", (bc,))
        if not row:
            if not only_select:
                messagebox.showwarning('Không tìm thấy', 'Barcode không khớp sản phẩm nào')
            return False
        target = f"{row[0]['id']} — {row[0]['name']}"
        if target not in self.cmb_prod_pos['values']:
            self.cmb_prod_pos['values'] = list(self.cmb_prod_pos['values']) + [target]
        self.cmb_prod_pos.set(target)
        self.update_dispatch_unit_label()
        return True

    def scan_and_add_dispatch(self):
        ok = self.fill_product_by_barcode_dispatch(only_select=True)
        if ok:
            self.ent_qty_pos.delete(0, tk.END)
            self.ent_qty_pos.insert(0, '1')
            self.add_to_dispatch_cart()
            self.ent_barcode.delete(0, tk.END)
        self.after(50, lambda: self.ent_barcode.focus_set())

    def open_barcode_scanner_dispatch(self):
        if not BARCODE_AVAILABLE:
            self.show_barcode_install_info()
            return
        try:
            def on_barcode_scanned(barcode_data):
                self.ent_barcode.delete(0, tk.END)
                self.ent_barcode.insert(0, barcode_data)
                self.after(100, self.scan_and_add_dispatch)
            self.barcode_scanner = BarcodeScanner(self, callback=on_barcode_scanned)
            self.barcode_scanner.start_scan()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở barcode scanner: {e}")

    def filter_product_list_dispatch(self):
        kw = (self.search_pos.get() or '').strip().lower()
        opts = [f"{p['id']} — {p['name']}" for p in self._products if kw in p['name'].lower()]
        self.cmb_prod_pos['values'] = opts
        if opts:
            self.cmb_prod_pos.current(0)
            self.update_dispatch_unit_label()

    def add_to_dispatch_cart(self):
        sel = self.cmb_prod_pos.get()
        if not sel:
            messagebox.showerror('Lỗi', 'Chọn sản phẩm để xuất'); return
        pid = int(sel.split(' — ')[0])
        unit = self.db.default_unit_of(pid) or 'vien'
        try:
            qty = float(self.ent_qty_pos.get())
        except:
            qty = 0
        if qty <= 0:
            messagebox.showerror('Lỗi', 'Số lượng xuất phải > 0'); return
        
        name = self.name_by_id(pid)
        
        # Lấy thông tin lô hàng chọn thủ công
        chosen_val = self.cmb_lot_pos.get()
        chosen_lot = None
        if chosen_val and chosen_val != "[Tự động - FEFO]":
            chosen_lot = chosen_val.split(" (HSD:")[0].strip()
            
        # Kiểm tra xem có lô hàng nào cận hạn hơn lô được chọn hay không
        if chosen_lot:
            ref_date = self._parse_date_entry(self.ent_dispatch_date)

            lots = self.db.q('''
              SELECT b.lotNo, b.expiryDate, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
              FROM stock_movements sm
              JOIN batches b ON b.id = sm.batchId
              WHERE sm.productId=?
              GROUP BY sm.batchId
              HAVING qtyBase > 0 AND DATE(b.expiryDate) >= DATE(?)
              ORDER BY DATE(b.expiryDate)
            ''', (pid, ref_date))
            
            chosen_expiry = None
            for lot in lots:
                if lot['lotNo'] == chosen_lot:
                    chosen_expiry = lot['expiryDate']
                    break
                    
            if chosen_expiry:
                earlier_lots = []
                for lot in lots:
                    if lot['lotNo'] != chosen_lot and lot['expiryDate'] < chosen_expiry:
                        earlier_lots.append(f"Lô {lot['lotNo']} (HSD: {format_date_display(lot['expiryDate'])}) - Còn: {lot['qtyBase']:g}")
                
                if earlier_lots:
                    warning_msg = f"Cảnh báo: Có lô hàng cận hạn dùng hơn so với lô bạn chọn:\n\n"
                    warning_msg += "\n".join(earlier_lots[:3])
                    if len(earlier_lots) > 3:
                        warning_msg += "\n..."
                    warning_msg += "\n\nHãy cân nhắc kỹ càng! Bạn có chắc chắn muốn tiếp tục chọn lô đã chọn?"
                    if not messagebox.askyesno("Cảnh báo cận hạn", warning_msg):
                        return
                        
        # Lấy nguồn kinh phí chọn thủ công
        chosen_fund_val = self.cmb_fund_pos.get()
        chosen_fund = None
        if chosen_fund_val and chosen_fund_val != "[Tự động trừ kho]":
            chosen_fund = chosen_fund_val.split(" - Tồn:")[0].strip()
            if chosen_fund == "Không rõ nguồn":
                chosen_fund = ""
                         
        merged = False
        for it in self.cart_dispatch:
            if (it['productId'] == pid 
                and it['unitCode'] == unit 
                and it.get('lotNo') == chosen_lot 
                and it.get('fundSource') == chosen_fund):
                it['qty'] = round(it['qty'] + qty, 4)
                merged = True
                break
        if not merged:
            self.cart_dispatch.append({
                'productId': pid,
                'productName': name,
                'unitCode': unit,
                'qty': qty,
                'lotNo': chosen_lot,
                'fundSource': chosen_fund
            })

        self.refresh_dispatch_cart_view()
        self.ent_qty_pos.delete(0, tk.END)
        self.ent_qty_pos.insert(0, '1')
        self.ent_qty_pos.focus_set()

    def remove_selected_dispatch_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            return
        item_vals = self.tree_cart.item(sel[0])['values']
        if not item_vals:
            return
        pid = int(item_vals[0])
        lot = item_vals[2]   # Cột Số lô có chỉ số là 2
        fund = item_vals[4]  # Cột Nguồn kinh phí có chỉ số là 4
        unit = item_vals[5]  # Cột ĐVT có chỉ số là 5
        
        if fund == '[Tự động]':
            fund = None
            
        # Tìm xem sản phẩm có trong giỏ hàng xuất không
        exact_exists = any(it['productId'] == pid and it['unitCode'] == unit and it.get('lotNo') == lot and it.get('fundSource') == fund for it in self.cart_dispatch)
        
        if exact_exists:
            self.cart_dispatch = [it for it in self.cart_dispatch if not (it['productId'] == pid and it['unitCode'] == unit and it.get('lotNo') == lot and it.get('fundSource') == fund)]
        else:
            # Nếu không tìm thấy trùng khớp Số lô chính xác (có thể do xuất tự động FEFO nên trong cart lotNo=None), xóa cả sản phẩm với ĐVT đó
            self.cart_dispatch = [it for it in self.cart_dispatch if not (it['productId'] == pid and it['unitCode'] == unit)]
            
        self.refresh_dispatch_cart_view()

    def clear_dispatch_cart(self):
        if self.cart_dispatch and messagebox.askyesno('Xác nhận', 'Xóa toàn bộ danh sách xuất kho?'):
            self.cart_dispatch = []
            self.refresh_dispatch_cart_view()

    def refresh_dispatch_cart_view(self):
        for i in self.tree_cart.get_children():
            self.tree_cart.delete(i)
        
        ref_date = self._parse_date_entry(self.ent_dispatch_date)

        idx = 0
        for it in self.cart_dispatch:
            pid = it['productId']
            name = it['productName']
            unitCode = it['unitCode']
            qty = it['qty']
            fund_source_val = it.get('fundSource')
            
            # Lấy thông tin tồn kho của các lô sắp xếp theo HSD (FEFO) hoặc theo lô được chọn
            to_base, _ = self.db.unit_info(pid, unitCode)
            if to_base is None:
                to_base = 1.0
            need_base = qty * to_base
            
            if it.get('lotNo'):
                if fund_source_val is not None:
                    lots = self.db.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                        FROM stock_movements sm 
                        WHERE sm.productId=? AND sm.batchId=(
                            SELECT id FROM batches WHERE productId=? AND lotNo=? LIMIT 1
                        ) AND COALESCE(sm.fundSource, '')=?
                        GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                    ''', (pid, pid, it['lotNo'], fund_source_val))
                else:
                    lots = self.db.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                        FROM stock_movements sm 
                        WHERE sm.productId=? AND sm.batchId=(
                            SELECT id FROM batches WHERE productId=? AND lotNo=? LIMIT 1
                        )
                        GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                    ''', (pid, pid, it['lotNo']))
            else:
                if fund_source_val is not None:
                    lots = self.db.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                        FROM stock_movements sm 
                        WHERE sm.productId=? AND COALESCE(sm.fundSource, '')=?
                        GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                      WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE(?)
                      ORDER BY DATE(b.expiryDate)
                    ''', (pid, fund_source_val, ref_date))
                else:
                    lots = self.db.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                        FROM stock_movements sm WHERE sm.productId=? GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                      WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE(?)
                      ORDER BY DATE(b.expiryDate)
                    ''', (pid, ref_date))
            
            allocated = []
            for lot in lots:
                if need_base <= 0:
                    break
                take_base = min(need_base, float(lot['qtyBase']))
                take_in_unit = take_base / to_base
                cost_in_unit = float(lot['costBase']) * to_base
                sub_total = take_in_unit * cost_in_unit
                allocated.append({
                    'lotNo': lot['lotNo'],
                    'expiryDate': lot['expiryDate'],
                    'cost': cost_in_unit,
                    'qty': take_in_unit,
                    'total': sub_total
                })
                need_base -= take_base
                
            if need_base > 0:
                # Trường hợp không đủ tồn kho
                price = self.db.unit_price(pid, unitCode)
                allocated.append({
                    'lotNo': 'KHÔNG ĐỦ KHO',
                    'expiryDate': '-',
                    'cost': price,
                    'qty': need_base / to_base,
                    'total': (need_base / to_base) * price
                })
                
            for alloc in allocated:
                self.tree_cart.insert('', 'end',
                    values=(
                        pid,
                        name,
                        alloc['lotNo'],
                        format_date_display(alloc['expiryDate']),
                        it.get('fundSource') or '[Tự động]',
                        unitCode,
                        f"{alloc['cost']:,.0f}",
                        f"{alloc['qty']:g}",
                        f"{alloc['total']:,.0f}"
                    ),
                    tags=('odd',) if idx % 2 else ())
                idx += 1

    def confirm_dispatch(self):
        if not self.cart_dispatch:
            messagebox.showwarning('Chưa có dữ liệu', 'Danh sách xuất kho trống'); return
        
        receiving_unit = self.cmb_receiving_unit.get().strip()
        if not receiving_unit:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập Đơn vị nhận'); return
        
        date_str = self._parse_date_entry(self.ent_dispatch_date)

                
        reason = self.cmb_reason.get().strip()
        note = self.ent_dispatch_note.get().strip()

        if not messagebox.askyesno('Xác nhận', f'Bạn có chắc chắn muốn xuất kho cho:\nĐơn vị: {receiving_unit}\nNgày xuất: {date_str or "Hôm nay"}\nLý do: {reason}?'):
            return

        try:
            dispatch_id, note_number, details = self.db.dispatch(self.cart_dispatch, receiving_unit, reason, note, date_str)
            self.last_dispatch_items = details
            
            created_at_str = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}" if date_str else dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_dispatch_info = {
                'id': dispatch_id,
                'noteNumber': note_number,
                'receivingUnit': receiving_unit,
                'reason': reason,
                'note': note,
                'createdAt': created_at_str
            }
            self.cart_dispatch = []
            self.refresh_dispatch_cart_view()
            self.refresh_stock()
            self.refresh_receiving_units_combo()
            messagebox.showinfo('Thành công', f'Đã xuất kho thành công!\nSố phiếu: {note_number}')
            
            # Tự động hỏi in phiếu xuất kho
            if messagebox.askyesno('In phiếu', 'Bạn có muốn in phiếu xuất kho ngay bây giờ?'):
                self.print_dispatch_note()
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Lỗi xuất kho: {str(e)}')

    def name_by_id(self, pid):
        for p in self._products:
            if p['id'] == pid:
                return p['name']
        return f'#{pid}'

    def print_dispatch_note(self):
        if not self.last_dispatch_items:
            messagebox.showwarning('Chưa có dữ liệu', 'Hãy thực hiện xuất kho trước khi in phiếu'); return
        
        # Kiểm tra và tự động cài đặt reportlab nếu thiếu
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
                    # Chạy lệnh pip install reportlab bằng python hiện tại
                    subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
                    self.toast("Đã cài đặt reportlab thành công!")
                except Exception as ex:
                    messagebox.showerror("Lỗi cài đặt", f"Không thể tự động cài đặt reportlab: {str(ex)}\nHãy chạy lệnh 'pip install reportlab' trong terminal."); return
            else:
                return
        
        info = self.last_dispatch_info
        
        # Cho phép người dùng chọn vị trí lưu file PDF
        initial_filename = f"Phieu_Xuat_Kho_{info['noteNumber']}.pdf"
        pdf_path = filedialog.asksaveasfilename(
            title="Chọn vị trí lưu phiếu xuất kho PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=initial_filename
        )
        if not pdf_path:
            return  # Người dùng hủy bỏ lưu file

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Đăng ký font Times New Roman trên Windows hỗ trợ tiếng Việt
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
            
            # Styles
            styles = getSampleStyleSheet()
            
            style_header_left = ParagraphStyle(
                'HeaderLeft',
                parent=styles['Normal'],
                fontName=font_bold,
                fontSize=10,
                leading=14,
                alignment=0 # Left
            )
            
            style_header_right = ParagraphStyle(
                'HeaderRight',
                parent=styles['Normal'],
                fontName=font_normal,
                fontSize=10,
                leading=14,
                alignment=2 # Right
            )
            
            style_title = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontName=font_bold,
                fontSize=16,
                leading=20,
                alignment=1, # Center
                spaceAfter=5
            )
            
            style_subtitle = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontName=font_bold,
                fontSize=11,
                leading=14,
                alignment=1, # Center
                spaceAfter=15
            )
            
            style_info = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontName=font_normal,
                fontSize=11,
                leading=16,
                alignment=0
            )
            
            style_table_header = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontName=font_bold,
                fontSize=10,
                leading=12,
                alignment=1, # Center
                textColor=colors.black
            )
            
            style_cell = ParagraphStyle(
                'Cell',
                parent=styles['Normal'],
                fontName=font_normal,
                fontSize=10,
                leading=12,
                alignment=0
            )
            
            style_cell_center = ParagraphStyle(
                'CellCenter',
                parent=styles['Normal'],
                fontName=font_normal,
                fontSize=10,
                leading=12,
                alignment=1
            )
            
            style_cell_right = ParagraphStyle(
                'CellRight',
                parent=styles['Normal'],
                fontName=font_normal,
                fontSize=10,
                leading=12,
                alignment=2
            )
            
            # Header
            header_data = [
                [
                    Paragraph("SỞ Y TẾ THÀNH PHỐ CẦN THƠ<br/>TRUNG TÂM KIỂM SOÁT BỆNH TẬT (CDC)", style_header_left),
                    Paragraph("<b>Mẫu số: C31-HD</b><br/><i>(Ban hành theo Thông tư số 107/2017/TT-BTC)</i>", style_header_right)
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
            story.append(Paragraph("PHIẾU XUẤT KHO", style_title))
            story.append(Paragraph(f"Số: {info['noteNumber']}", style_subtitle))
            
            # Parse createdAt
            created_str = info['createdAt']
            try:
                created_at_dt = dt.datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    created_at_dt = dt.datetime.strptime(created_str.split(' ')[0], '%Y-%m-%d')
                except Exception:
                    created_at_dt = dt.datetime.now()
            
            info_lines = [
                f"<b>Đơn vị nhận:</b> {info['receivingUnit']}",
                f"<b>Lý do xuất:</b> {info['reason']}",
                f"<b>Kho xuất:</b> Kho Dược CDC Cần Thơ",
                f"<b>Ngày xuất:</b> {created_at_dt.strftime('%d-%m-%Y')}",
                f"<b>Ghi chú:</b> {info['note'] or 'Không'}"
            ]
            for line in info_lines:
                story.append(Paragraph(line, style_info))
                story.append(Spacer(1, 4))
                
            story.append(Spacer(1, 10))
            
            # Table of items
            table_data = [
                [
                    Paragraph("STT", style_table_header),
                    Paragraph("Tên thuốc, vaccine, VTYT", style_table_header),
                    Paragraph("ĐVT", style_table_header),
                    Paragraph("Số lượng", style_table_header),
                    Paragraph("Đơn giá", style_table_header),
                    Paragraph("Thành tiền", style_table_header),
                    Paragraph("Số lô", style_table_header),
                    Paragraph("Hạn dùng", style_table_header),
                    Paragraph("Nguồn", style_table_header)
                ]
            ]
            
            total_sum = 0.0
            for idx, it in enumerate(self.last_dispatch_items, 1):
                qty = it['qty']
                cost = it.get('cost') or 0.0
                sub_total = float(it.get('totalAmount') if it.get('totalAmount') is not None else qty * cost)
                total_sum += sub_total
                
                table_data.append([
                    Paragraph(str(idx), style_cell_center),
                    Paragraph(it['productName'], style_cell),
                    Paragraph(it['unitCode'], style_cell_center),
                    Paragraph(f"{qty:g}", style_cell_right),
                    Paragraph(f"{cost:,.0f}" if cost > 0 else "0", style_cell_right),
                    Paragraph(f"{sub_total:,.0f}" if sub_total > 0 else "0", style_cell_right),
                    Paragraph(it['lotNo'] or '', style_cell_center),
                    Paragraph(format_date_display(it['expiryDate']), style_cell_center),
                    Paragraph(it.get('fundSource') or '', style_cell)
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
                Paragraph("", style_cell_center),
                Paragraph("", style_cell)
            ])
                
            col_widths = [20, 130, 30, 40, 50, 60, 50, 50, 80]
            items_table = Table(table_data, colWidths=col_widths)
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('SPAN', (0, -1), (4, -1)),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 15))
            
            # Date & Signatures
            date_right_style = ParagraphStyle(
                'DateRight',
                parent=styles['Normal'],
                fontName=font_italic,
                fontSize=11,
                alignment=2,
                spaceAfter=10
            )
            
            sig_title_style = ParagraphStyle(
                'SigTitle',
                parent=styles['Normal'],
                fontName=font_bold,
                fontSize=11,
                alignment=1
            )
            
            sig_sub_style = ParagraphStyle(
                'SigSub',
                parent=styles['Normal'],
                fontName=font_italic,
                fontSize=9,
                alignment=1
            )
            
            story.append(Paragraph(f"Cần Thơ, ngày {created_at_dt.strftime('%d')} tháng {created_at_dt.strftime('%m')} năm {created_at_dt.strftime('%Y')}", date_right_style))
            
            sig_headers = [
                [
                    Paragraph("<b>Người lập phiếu</b>", sig_title_style),
                    Paragraph("<b>Người nhận hàng</b>", sig_title_style),
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
            story.append(Spacer(1, 60)) # Chừa khoảng trống để ký và ghi tên
            
            doc.build(story)
            
            # Mở file PDF kết quả
            os.startfile(pdf_path)
            self.toast("Đã in phiếu xuất ra PDF và mở file thành công")
            
        except Exception as e:
            messagebox.showerror("Lỗi in PDF", f"Không thể xuất file PDF: {str(e)}")

    # -------- Stock --------

