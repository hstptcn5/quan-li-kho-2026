# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as tb

from date_utils import format_date_display, format_datetime_display


class OperationsMixin:
    def build_operations_tab(self):
        container = tb.Frame(self.tab_operations, padding=10)
        container.pack(fill='both', expand=True)

        self.ops_nb = tb.Notebook(container)
        self.ops_nb.pack(fill='both', expand=True)

        self.ops_dashboard_tab = tb.Frame(self.ops_nb)
        self.ops_history_tab = tb.Frame(self.ops_nb)
        self.ops_inventory_tab = tb.Frame(self.ops_nb)
        self.ops_nb.add(self.ops_dashboard_tab, text='Tổng quan')
        self.ops_nb.add(self.ops_history_tab, text='Tra cứu lô/sản phẩm')
        self.ops_nb.add(self.ops_inventory_tab, text='Kiểm kê thực tế')

        self._build_dashboard_tab()
        self._build_history_tab()
        self._build_inventory_check_tab()

    def _build_dashboard_tab(self):
        root = self.ops_dashboard_tab
        header = tb.Frame(root)
        header.pack(fill='x', padx=8, pady=8)
        tb.Label(header, text='Tổng quan vận hành kho', font=('Segoe UI', 15, 'bold'), bootstyle='primary').pack(side='left')
        tb.Button(header, text='Tải lại', bootstyle='secondary', command=self.refresh_dashboard).pack(side='right')

        self.dashboard_cards = {}
        cards = tb.Frame(root)
        cards.pack(fill='x', padx=8, pady=(0, 8))
        for key, title, style in [
            ('product_count', 'Sản phẩm', 'info'),
            ('stock_lot_count', 'Lô còn tồn', 'success'),
            ('expiring_count', 'Sắp hết hạn', 'warning'),
            ('low_stock_count', 'Sắp hết tồn', 'secondary'),
            ('negative_count', 'Tồn âm', 'danger'),
        ]:
            frame = tb.Labelframe(cards, text=title, bootstyle=style, padding=10)
            frame.pack(side='left', fill='x', expand=True, padx=4)
            val = tb.Label(frame, text='0', font=('Segoe UI', 20, 'bold'), bootstyle=style)
            val.pack()
            self.dashboard_cards[key] = val

        self.dashboard_backup_label = tb.Label(root, text='Backup gần nhất: -', font=('Segoe UI', 10), bootstyle='secondary')
        self.dashboard_backup_label.pack(anchor='w', padx=12, pady=(0, 8))

        detail = tb.Frame(root)
        detail.pack(fill='both', expand=True, padx=8, pady=8)

        self.dashboard_expiring_tree = self._make_dashboard_tree(detail, 'Lô sắp hết hạn', 0)
        self.dashboard_low_tree = self._make_dashboard_tree(detail, 'Lô sắp hết tồn', 1)
        self.refresh_dashboard()

    def _make_dashboard_tree(self, parent, title, col):
        box = tb.Labelframe(parent, text=title, bootstyle='secondary', padding=8)
        box.grid(row=0, column=col, sticky='nsew', padx=4)
        parent.columnconfigure(col, weight=1)
        parent.rowconfigure(0, weight=1)
        columns = ('product', 'lot', 'exp', 'fund', 'qty')
        tree = tb.Treeview(box, columns=columns, show='headings', height=10)
        for c, w, t, anchor in [
            ('product', 220, 'Sản phẩm', 'w'),
            ('lot', 90, 'Số lô', 'center'),
            ('exp', 95, 'HSD', 'center'),
            ('fund', 120, 'Nguồn', 'w'),
            ('qty', 80, 'Tồn', 'e'),
        ]:
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=anchor)
        tree.tag_configure('odd', background='#f6f8fa')
        tree.pack(fill='both', expand=True)
        return tree

    def refresh_dashboard(self):
        try:
            data = self.db.dashboard_summary()
            for key, label in self.dashboard_cards.items():
                label.config(text=f"{data.get(key, 0):,}")
            backup = data.get('last_backup')
            if backup:
                self.dashboard_backup_label.config(text=f"Backup gần nhất: {backup['file']} ({format_datetime_display(backup['created'])})")
            else:
                self.dashboard_backup_label.config(text='Backup gần nhất: chưa có')
            self._fill_dashboard_rows(self.dashboard_expiring_tree, data.get('expiring_rows', []))
            self._fill_dashboard_rows(self.dashboard_low_tree, data.get('low_stock_rows', []), qty_key='stockBase')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể load dashboard: {e}')

    def _fill_dashboard_rows(self, tree, rows, qty_key='qtyBase'):
        for item in tree.get_children():
            tree.delete(item)
        for idx, r in enumerate(rows):
            tree.insert('', 'end', values=(
                r.get('productName') or '',
                r.get('lotNo') or '',
                format_date_display(r.get('expiryDate')),
                r.get('fundSource') or '',
                f"{float(r.get(qty_key) or 0):g}",
            ), tags=('odd',) if idx % 2 else ())

    def _build_history_tab(self):
        root = self.ops_history_tab
        filters = tb.Labelframe(root, text='Điều kiện tra cứu', bootstyle='secondary', padding=10)
        filters.pack(fill='x', padx=8, pady=8)

        tb.Label(filters, text='Sản phẩm:').pack(side='left', padx=(0, 6))
        self.history_product = tb.Combobox(filters, width=42, state='readonly')
        self.history_product.pack(side='left', padx=(0, 12))

        tb.Label(filters, text='Số lô:').pack(side='left', padx=(0, 6))
        self.history_lot = tb.Entry(filters, width=18)
        self.history_lot.pack(side='left', padx=(0, 12))
        self.history_lot.bind('<Return>', lambda e: self.search_product_lot_history())

        tb.Button(filters, text='Tra cứu', bootstyle='primary', command=self.search_product_lot_history).pack(side='left')
        tb.Button(filters, text='Làm mới danh mục', bootstyle='secondary', command=self.refresh_history_products).pack(side='left', padx=6)

        columns = ('time', 'type', 'product', 'lot', 'exp', 'fund', 'qty', 'unit', 'partner', 'reason')
        self.history_tree = tb.Treeview(root, columns=columns, show='headings')
        for c, w, t, anchor in [
            ('time', 135, 'Thời gian', 'center'),
            ('type', 95, 'Loại', 'center'),
            ('product', 230, 'Sản phẩm', 'w'),
            ('lot', 90, 'Lô', 'center'),
            ('exp', 95, 'HSD', 'center'),
            ('fund', 120, 'Nguồn', 'w'),
            ('qty', 80, 'SL quy đổi', 'e'),
            ('unit', 70, 'ĐVT gốc', 'center'),
            ('partner', 160, 'Đơn vị/NCC', 'w'),
            ('reason', 160, 'Lý do', 'w'),
        ]:
            self.history_tree.heading(c, text=t)
            self.history_tree.column(c, width=w, anchor=anchor)
        self.history_tree.tag_configure('odd', background='#f6f8fa')
        self.history_tree.pack(fill='both', expand=True, padx=8, pady=8)
        self.refresh_history_products()

    def refresh_history_products(self):
        try:
            rows = self.db.q("SELECT id, name FROM products ORDER BY LOWER(name)")
            vals = ['Tất cả'] + [f"{r['id']} — {r['name']}" for r in rows]
            self.history_product['values'] = vals
            self.history_product.current(0)
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể load sản phẩm: {e}')

    def search_product_lot_history(self):
        sel = self.history_product.get()
        product_id = None
        if sel and sel != 'Tất cả':
            product_id = int(sel.split(' — ')[0])
        lot = self.history_lot.get().strip()
        rows = self.db.product_lot_history(product_id, lot)
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for idx, r in enumerate(rows):
            qty = float(r.get('qtyBase') if r.get('qtyBase') is not None else r.get('qty') or 0)
            self.history_tree.insert('', 'end', values=(
                format_datetime_display(r.get('createdAt')),
                r.get('type') or '',
                r.get('productName') or '',
                r.get('lotNo') or '',
                format_date_display(r.get('expiryDate')),
                r.get('fundSource') or '',
                f"{qty:g}",
                r.get('originalUnit') or r.get('unitCode') or '',
                r.get('receivingUnit') or '',
                r.get('reason') or '',
            ), tags=('odd',) if idx % 2 else ())

    def _build_inventory_check_tab(self):
        root = self.ops_inventory_tab
        top = tb.Frame(root)
        top.pack(fill='x', padx=8, pady=8)
        tb.Label(top, text='Lọc sản phẩm/lô:').pack(side='left', padx=(0, 6))
        self.inventory_filter = tb.Entry(top, width=32)
        self.inventory_filter.pack(side='left', padx=(0, 8))
        self.inventory_filter.bind('<Return>', lambda e: self.refresh_inventory_check_rows())
        tb.Button(top, text='Tải tồn kho', bootstyle='primary', command=self.refresh_inventory_check_rows).pack(side='left')

        columns = ('pid', 'batch', 'product', 'lot', 'exp', 'fund', 'book')
        self.inventory_tree = tb.Treeview(
            root,
            columns=columns,
            displaycolumns=('product', 'lot', 'exp', 'fund', 'book'),
            show='headings',
            height=12
        )
        for c, w, t, anchor in [
            ('pid', 55, 'PID', 'center'),
            ('batch', 65, 'Batch', 'center'),
            ('product', 260, 'Sản phẩm', 'w'),
            ('lot', 95, 'Lô', 'center'),
            ('exp', 95, 'HSD', 'center'),
            ('fund', 140, 'Nguồn', 'w'),
            ('book', 90, 'Tồn sổ', 'e'),
        ]:
            self.inventory_tree.heading(c, text=t)
            self.inventory_tree.column(c, width=w, anchor=anchor)
        self.inventory_tree.tag_configure('odd', background='#f6f8fa')
        self.inventory_tree.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        editor = tb.Labelframe(root, text='Ghi nhận kiểm kê dòng đang chọn', bootstyle='info', padding=12)
        editor.pack(fill='x', padx=8, pady=8)
        tb.Label(editor, text='Tồn thực tế:').pack(side='left', padx=(0, 6))
        self.inventory_actual = tb.Entry(editor, width=14)
        self.inventory_actual.pack(side='left', padx=(0, 10))
        tb.Label(editor, text='Ghi chú:').pack(side='left', padx=(0, 6))
        self.inventory_note = tb.Entry(editor, width=42)
        self.inventory_note.pack(side='left', fill='x', expand=True, padx=(0, 10))
        tb.Button(editor, text='Thêm vào danh sách điều chỉnh', bootstyle='warning', command=self.add_inventory_adjustment).pack(side='left')

        pending_box = tb.Labelframe(root, text='Danh sách điều chỉnh chờ áp dụng', bootstyle='secondary', padding=8)
        pending_box.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        self.pending_adjustments = []
        self.pending_adjust_tree = tb.Treeview(pending_box, columns=('product', 'lot', 'fund', 'book', 'actual', 'diff'), show='headings', height=6)
        for c, w, t, anchor in [
            ('product', 260, 'Sản phẩm', 'w'),
            ('lot', 95, 'Lô', 'center'),
            ('fund', 140, 'Nguồn', 'w'),
            ('book', 90, 'Tồn sổ', 'e'),
            ('actual', 90, 'Tồn thực', 'e'),
            ('diff', 90, 'Chênh lệch', 'e'),
        ]:
            self.pending_adjust_tree.heading(c, text=t)
            self.pending_adjust_tree.column(c, width=w, anchor=anchor)
        self.pending_adjust_tree.tag_configure('odd', background='#f6f8fa')
        self.pending_adjust_tree.pack(fill='both', expand=True)

        actions = tb.Frame(pending_box)
        actions.pack(fill='x', pady=(8, 0))
        tb.Button(actions, text='Xóa dòng chờ', bootstyle='secondary', command=self.remove_pending_inventory_adjustment).pack(side='left')
        self.pending_adjust_summary = tb.Label(actions, text='0 dòng chờ', font=('Segoe UI', 10, 'bold'), bootstyle='secondary')
        self.pending_adjust_summary.pack(side='left', padx=12)
        tb.Button(actions, text='Áp dụng điều chỉnh', bootstyle='danger', command=self.apply_inventory_adjustments).pack(side='right')
        self.refresh_inventory_check_rows()

    def refresh_inventory_check_rows(self):
        keyword = (self.inventory_filter.get() or '').strip().lower() if hasattr(self, 'inventory_filter') else ''
        rows = self.db.get_inventory()
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for idx, r in enumerate(rows):
            haystack = f"{r.get('productName','')} {r.get('lotNo','')} {r.get('fundSource','')}".lower()
            if keyword and keyword not in haystack:
                continue
            stock = float(r.get('stockBase') or 0)
            if stock <= 0:
                continue
            self.inventory_tree.insert('', 'end', values=(
                r.get('productId'),
                r.get('batchId'),
                r.get('productName') or '',
                r.get('lotNo') or '',
                format_date_display(r.get('expiryDate')),
                r.get('fundSource') or '',
                f"{stock:g}",
            ), tags=('odd',) if idx % 2 else ())

    def add_inventory_adjustment(self):
        sel = self.inventory_tree.selection()
        if not sel:
            messagebox.showwarning('Chưa chọn dòng', 'Chọn một dòng tồn kho cần kiểm kê')
            return
        vals = self.inventory_tree.item(sel[0])['values']
        try:
            actual = float((self.inventory_actual.get() or '').replace(',', ''))
        except ValueError:
            messagebox.showerror('Lỗi', 'Tồn thực tế phải là số')
            return
        if actual < 0:
            messagebox.showerror('Lỗi', 'Tồn thực tế không được âm')
            return
        book = float(vals[6])
        adjustment = {
            'productId': int(vals[0]),
            'batchId': int(vals[1]),
            'productName': vals[2],
            'lotNo': vals[3],
            'fundSource': vals[5] or '',
            'bookQty': book,
            'actualQtyBase': actual,
            'note': self.inventory_note.get().strip() or 'Kiểm kê thực tế'
        }
        self.pending_adjustments.append(adjustment)
        self._refresh_pending_adjustments()
        self.inventory_actual.delete(0, tk.END)

    def _refresh_pending_adjustments(self):
        for item in self.pending_adjust_tree.get_children():
            self.pending_adjust_tree.delete(item)
        total_up = 0.0
        total_down = 0.0
        for idx, adj in enumerate(self.pending_adjustments):
            diff = float(adj['actualQtyBase']) - float(adj['bookQty'])
            if diff > 0:
                total_up += diff
            elif diff < 0:
                total_down += abs(diff)
            self.pending_adjust_tree.insert('', 'end', values=(
                adj['productName'],
                adj['lotNo'],
                adj['fundSource'],
                f"{float(adj['bookQty']):g}",
                f"{float(adj['actualQtyBase']):g}",
                f"{diff:g}",
            ), tags=('odd',) if idx % 2 else ())
        if hasattr(self, 'pending_adjust_summary'):
            self.pending_adjust_summary.config(
                text=f"{len(self.pending_adjustments)} dòng chờ | Tăng {total_up:g} | Giảm {total_down:g}"
            )

    def remove_pending_inventory_adjustment(self):
        sel = self.pending_adjust_tree.selection()
        if not sel:
            return
        idx = self.pending_adjust_tree.index(sel[0])
        if 0 <= idx < len(self.pending_adjustments):
            self.pending_adjustments.pop(idx)
            self._refresh_pending_adjustments()

    def apply_inventory_adjustments(self):
        if not self.pending_adjustments:
            messagebox.showwarning('Chưa có dữ liệu', 'Chưa có dòng điều chỉnh kiểm kê')
            return
        if hasattr(self, 'require_admin_action') and not self.require_admin_action('áp dụng điều chỉnh kiểm kê'):
            return
        if not messagebox.askyesno('Xác nhận', f'Áp dụng {len(self.pending_adjustments)} dòng điều chỉnh kiểm kê?'):
            return
        try:
            applied = self.db.record_inventory_adjustments(self.pending_adjustments, audit_ip='Local')
            self.pending_adjustments = []
            self._refresh_pending_adjustments()
            self.refresh_inventory_check_rows()
            self.refresh_stock()
            self.refresh_alerts()
            self.refresh_report()
            self.refresh_dashboard()
            messagebox.showinfo('Thành công', f'Đã áp dụng {len(applied)} dòng điều chỉnh')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể áp dụng kiểm kê: {e}')
