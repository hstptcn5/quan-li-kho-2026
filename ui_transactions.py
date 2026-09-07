# -*- coding: utf-8 -*-
"""Stitch-aligned receive and dispatch workspaces.

The legacy PurchaseMixin and DispatchMixin continue to own all validation,
transaction, FEFO, printing and audit behaviour.  UI-3 only recreates their
widget contracts in the approved clinical operations layout.
"""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry

from config import BARCODE_AVAILABLE
from ui_design import COLORS, TYPOGRAPHY


PURCHASE_WIDGET_CONTRACT = (
    "cmb_supplier", "ent_purchase_date", "cmb_purchase_reason", "ent_purchase_note",
    "search_purchase", "cmb_prod", "lbl_unit_purchase", "ent_qty", "ent_lot",
    "ent_exp", "ent_cost", "ent_line_total", "cmb_item_fund", "tree_purchase_cart",
    "lbl_purchase_cart_total",
)

DISPATCH_WIDGET_CONTRACT = (
    "cmb_receiving_unit", "ent_dispatch_date", "cmb_reason", "ent_dispatch_note",
    "ent_barcode", "search_pos", "cmb_prod_pos", "cmb_lot_pos", "cmb_fund_pos",
    "ent_qty_pos", "lbl_unit_pos", "tree_cart",
)


class TransactionUiMixin:
    """Override only the two transaction page builders."""

    def build_purchase_tab(self):
        root = self.tab_purchase
        self.cart_purchase = []
        self.last_purchase_items = []
        self.last_purchase_info = {}

        self._transaction_page_header(
            root,
            "Nhập kho",
            "Lập phiếu nhập thuốc, vaccine và vật tư y tế",
            "Nhập đúng lô, HSD và nguồn kinh phí để bảo toàn truy vết tồn kho.",
        )

        info = self._transaction_panel(root, "THÔNG TIN PHIẾU NHẬP")
        info.pack(fill="x", padx=8, pady=(0, 7))
        form = info.content
        for col in range(6):
            form.grid_columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        self._field_label(form, "Nhà cung cấp / Nguồn cấp").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(8, 3))
        self.cmb_supplier = tb.Combobox(form, width=28)
        self.cmb_supplier.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 8))

        self._field_label(form, "Ngày nhập").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(8, 3))
        self.ent_purchase_date = DateEntry(form, dateformat="%d-%m-%Y", firstweekday=0, bootstyle="info", width=13)
        self.ent_purchase_date.grid(row=1, column=2, sticky="w", padx=(0, 8), pady=(0, 8))

        self._field_label(form, "Lý do nhập").grid(row=0, column=3, sticky="w", padx=(0, 5), pady=(8, 3))
        self.cmb_purchase_reason = tb.Combobox(
            form,
            values=["Nhận cấp phát tuyến trên", "Mua sắm đấu thầu", "Viện trợ - Tài trợ", "Khác"],
            state="readonly",
            width=24,
        )
        self.cmb_purchase_reason.set("Nhận cấp phát tuyến trên")
        self.cmb_purchase_reason.grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=(0, 8))

        self._field_label(form, "Ghi chú").grid(row=0, column=4, sticky="w", padx=(0, 5), pady=(8, 3))
        self.ent_purchase_note = tb.Entry(form)
        self.ent_purchase_note.grid(row=1, column=4, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 8))
        self.refresh_suppliers_combo()

        editor = self._transaction_panel(root, "THÊM HÀNG VÀO PHIẾU NHẬP")
        editor.pack(fill="x", padx=8, pady=(0, 7))
        box = editor.content
        for col in range(8):
            box.grid_columnconfigure(col, weight=1 if col in {1, 3, 5, 7} else 0)

        self._field_label(box, "Tìm sản phẩm").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(8, 3))
        self.search_purchase = tb.Entry(box)
        self.search_purchase.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 6))
        self.search_purchase.bind("<KeyRelease>", lambda event: self.filter_product_list())
        self.search_purchase.bind("<Down>", lambda event: self.open_combo(self.cmb_prod))

        self._field_label(box, "Sản phẩm").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(8, 3))
        self.cmb_prod = tb.Combobox(box, state="readonly")
        self.cmb_prod.grid(row=1, column=2, columnspan=3, sticky="ew", padx=(0, 8), pady=(0, 6))
        self.cmb_prod.bind("<<ComboboxSelected>>", lambda event: self.update_purchase_unit_and_price())
        self.cmb_prod.bind("<Escape>", lambda event: self.search_purchase.focus_set())
        self.cmb_prod.bind("<Return>", lambda event: self.ent_qty.focus_set())

        self._field_label(box, "Đơn vị cơ sở").grid(row=0, column=5, sticky="w", padx=(0, 5), pady=(8, 3))
        self.lbl_unit_purchase = tk.Label(box, text="-", bg=COLORS["surface"], fg=COLORS["text"], font=TYPOGRAPHY["body_medium"], anchor="w")
        self.lbl_unit_purchase.grid(row=1, column=5, sticky="ew", padx=(0, 8), pady=(0, 6))

        self._field_label(box, "Số lượng").grid(row=0, column=6, sticky="w", padx=(0, 5), pady=(8, 3))
        self.ent_qty = tb.Entry(box, width=10)
        self.ent_qty.insert(0, "1")
        self.ent_qty.grid(row=1, column=6, sticky="ew", padx=(0, 8), pady=(0, 6))
        self._numberize(self.ent_qty)

        tb.Button(box, text="+ Thêm dòng", style="Shell.Primary.TButton", command=self.add_to_purchase_cart).grid(row=1, column=7, sticky="e", padx=(0, 10), pady=(0, 6))

        self._field_label(box, "Số lô").grid(row=2, column=0, sticky="w", padx=(10, 5), pady=(5, 3))
        self.ent_lot = tb.Entry(box)
        self.ent_lot.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 8))

        self._field_label(box, "Hạn sử dụng").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=(5, 3))
        self.ent_exp = DateEntry(box, dateformat="%d-%m-%Y", firstweekday=0, bootstyle="info")
        self.ent_exp.grid(row=3, column=2, sticky="ew", padx=(0, 8), pady=(0, 8))

        self._field_label(box, "Đơn giá nhập").grid(row=2, column=3, sticky="w", padx=(0, 5), pady=(5, 3))
        self.ent_cost = tb.Entry(box)
        self.ent_cost.insert(0, "0")
        self.ent_cost.grid(row=3, column=3, sticky="ew", padx=(0, 8), pady=(0, 8))
        self._numberize(self.ent_cost)

        self._field_label(box, "Tổng tiền dòng").grid(row=2, column=4, sticky="w", padx=(0, 5), pady=(5, 3))
        self.ent_line_total = tb.Entry(box)
        self.ent_line_total.grid(row=3, column=4, sticky="ew", padx=(0, 8), pady=(0, 8))
        self._numberize(self.ent_line_total)

        self._field_label(box, "Nguồn kinh phí").grid(row=2, column=5, sticky="w", padx=(0, 5), pady=(5, 3))
        self.cmb_item_fund = tb.Combobox(
            box,
            values=[
                "TCMR (Tiêm chủng mở rộng)", "Ngân sách địa phương", "Dự án viện trợ",
                "Mua sắm đấu thầu", "Nguồn khác",
            ],
        )
        self.cmb_item_fund.set("TCMR (Tiêm chủng mở rộng)")
        self.cmb_item_fund.grid(row=3, column=5, columnspan=3, sticky="ew", padx=(0, 10), pady=(0, 8))

        table = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        table.pack(fill="both", expand=True, padx=8, pady=(0, 58))
        cols = ("product", "productName", "unit", "qty", "lot", "exp", "cost", "fundSource", "total")
        self.tree_purchase_cart = tb.Treeview(table, columns=cols, show="headings")
        for key, width, label, anchor in (
            ("product", 55, "PID", "center"),
            ("productName", 255, "TÊN THUỐC / VACCINE / VTYT", "w"),
            ("unit", 60, "ĐVT", "center"),
            ("qty", 65, "SL", "e"),
            ("lot", 90, "SỐ LÔ", "center"),
            ("exp", 95, "HSD", "center"),
            ("cost", 100, "ĐƠN GIÁ", "e"),
            ("fundSource", 160, "NGUỒN KINH PHÍ", "w"),
            ("total", 110, "THÀNH TIỀN", "e"),
        ):
            self.tree_purchase_cart.heading(key, text=label, command=lambda col=key: self.sort_tree(self.tree_purchase_cart, col))
            self.tree_purchase_cart.column(key, width=width, anchor=anchor, stretch=(key in {"productName", "fundSource"}))
        self.tree_purchase_cart.pack(fill="both", expand=True, padx=1, pady=1)

        footer = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1, height=52)
        footer.place(relx=0, rely=1, relwidth=1, height=52, anchor="sw")
        self.lbl_purchase_cart_total = tk.Label(footer, text="Tổng tiền tạm tính: 0 VNĐ", bg=COLORS["surface"], fg=COLORS["text"], font=TYPOGRAPHY["body_medium"])
        self.lbl_purchase_cart_total.pack(side="left", padx=12, pady=12)
        tb.Button(footer, text="Xóa dòng", style="Shell.Secondary.TButton", command=self.remove_selected_purchase_item).pack(side="left", padx=3, pady=8)
        tb.Button(footer, text="Xóa danh sách", style="Shell.Secondary.TButton", command=self.clear_purchase_cart).pack(side="left", padx=3, pady=8)
        tb.Button(footer, text="Tạo phiếu nhập", style="Shell.Primary.TButton", command=self.confirm_purchase).pack(side="right", padx=(3, 10), pady=8)
        tb.Button(footer, text="In phiếu gần nhất", style="Shell.Secondary.TButton", command=self.print_purchase_note).pack(side="right", padx=3, pady=8)

    def build_dispatch_tab(self):
        root = self.tab_dispatch
        self.cart_dispatch = []
        self.last_dispatch_items = []
        self.last_dispatch_info = {}

        self._transaction_page_header(
            root,
            "Xuất kho (FEFO)",
            "Cấp phát thuốc, vaccine và vật tư y tế theo lô khả dụng",
            "Hệ thống ưu tiên lô có hạn sử dụng gần nhất; vẫn cho phép chọn lô/nguồn khi nghiệp vụ yêu cầu.",
        )

        info = self._transaction_panel(root, "THÔNG TIN PHIẾU XUẤT")
        info.pack(fill="x", padx=8, pady=(0, 7))
        form = info.content
        for col in range(6):
            form.grid_columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        self._field_label(form, "Đơn vị nhận").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(8, 3))
        self.cmb_receiving_unit = tb.Combobox(form, width=28)
        self.cmb_receiving_unit.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 8))

        self._field_label(form, "Ngày xuất").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(8, 3))
        self.ent_dispatch_date = DateEntry(form, dateformat="%d-%m-%Y", firstweekday=0, bootstyle="info", width=13)
        self.ent_dispatch_date.grid(row=1, column=2, sticky="w", padx=(0, 8), pady=(0, 8))

        self._field_label(form, "Lý do xuất").grid(row=0, column=3, sticky="w", padx=(0, 5), pady=(8, 3))
        self.cmb_reason = tb.Combobox(form, values=["Cấp phát", "Hủy kho", "Chuyển kho", "Khác"], state="readonly", width=16)
        self.cmb_reason.set("Cấp phát")
        self.cmb_reason.grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=(0, 8))

        self._field_label(form, "Ghi chú").grid(row=0, column=4, sticky="w", padx=(0, 5), pady=(8, 3))
        self.ent_dispatch_note = tb.Entry(form)
        self.ent_dispatch_note.grid(row=1, column=4, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 8))
        self.refresh_receiving_units_combo()

        fefo = tk.Frame(root, bg=COLORS["info_bg"], highlightbackground=COLORS["info_border"], highlightthickness=1)
        fefo.pack(fill="x", padx=8, pady=(0, 7))
        tk.Label(
            fefo,
            text="FEFO đang bật  •  Lô hết hạn hoặc không còn tồn tại ngày chứng từ sẽ không được tự động phân bổ.",
            bg=COLORS["info_bg"], fg=COLORS["info"], font=TYPOGRAPHY["compact"], anchor="w",
        ).pack(fill="x", padx=10, pady=6)

        editor = self._transaction_panel(root, "CHỌN HÀNG XUẤT")
        editor.pack(fill="x", padx=8, pady=(0, 7))
        box = editor.content
        for col in range(8):
            box.grid_columnconfigure(col, weight=1 if col in {1, 3, 5, 7} else 0)

        self._field_label(box, "Barcode").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(8, 3))
        barcode_wrap = tk.Frame(box, bg=COLORS["surface"])
        barcode_wrap.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 6))
        self.ent_barcode = tb.Entry(barcode_wrap)
        self.ent_barcode.pack(side="left", fill="x", expand=True)
        self.ent_barcode.bind("<Return>", lambda event: self.scan_and_add_dispatch())
        self.ent_barcode.bind("<KP_Enter>", lambda event: self.scan_and_add_dispatch())
        scan_cmd = self.open_barcode_scanner_dispatch if BARCODE_AVAILABLE else self.show_barcode_install_info
        tb.Button(barcode_wrap, text="Quét", style="Shell.Secondary.TButton", command=scan_cmd).pack(side="left", padx=(5, 0))

        self._field_label(box, "Tìm sản phẩm").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(8, 3))
        self.search_pos = tb.Entry(box)
        self.search_pos.grid(row=1, column=2, columnspan=2, sticky="ew", padx=(0, 8), pady=(0, 6))
        self.search_pos.bind("<KeyRelease>", lambda event: self.filter_product_list_dispatch())
        self.search_pos.bind("<Down>", lambda event: (self.cmb_prod_pos.focus_set(), self.cmb_prod_pos.event_generate("<Alt-Down>")))

        self._field_label(box, "Sản phẩm").grid(row=0, column=4, sticky="w", padx=(0, 5), pady=(8, 3))
        self.cmb_prod_pos = tb.Combobox(box, state="readonly")
        self.cmb_prod_pos.grid(row=1, column=4, columnspan=3, sticky="ew", padx=(0, 8), pady=(0, 6))
        self.cmb_prod_pos.bind("<<ComboboxSelected>>", lambda event: self.update_dispatch_unit_label())
        self.cmb_prod_pos.bind("<Escape>", lambda event: self.search_pos.focus_set())
        self.cmb_prod_pos.bind("<Return>", lambda event: (self.cmb_lot_pos.focus_set(), self.cmb_lot_pos.event_generate("<Alt-Down>")))

        tb.Button(box, text="+ Thêm dòng", style="Shell.Primary.TButton", command=self.add_to_dispatch_cart).grid(row=1, column=7, sticky="e", padx=(0, 10), pady=(0, 6))

        self._field_label(box, "Lô xuất").grid(row=2, column=0, sticky="w", padx=(10, 5), pady=(5, 3))
        self.cmb_lot_pos = tb.Combobox(box, state="readonly")
        self.cmb_lot_pos.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(10, 8), pady=(0, 8))
        self.cmb_lot_pos.bind("<<ComboboxSelected>>", lambda event: self.update_dispatch_funds())
        self.cmb_lot_pos.bind("<Return>", lambda event: (self.cmb_fund_pos.focus_set(), self.cmb_fund_pos.event_generate("<Alt-Down>")))

        self._field_label(box, "Nguồn xuất").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=(5, 3))
        self.cmb_fund_pos = tb.Combobox(box, state="readonly")
        self.cmb_fund_pos.grid(row=3, column=2, columnspan=2, sticky="ew", padx=(0, 8), pady=(0, 8))
        self.cmb_fund_pos.bind("<Return>", lambda event: self.ent_qty_pos.focus_set())

        self._field_label(box, "Số lượng xuất").grid(row=2, column=4, sticky="w", padx=(0, 5), pady=(5, 3))
        self.ent_qty_pos = tb.Entry(box, width=12)
        self.ent_qty_pos.insert(0, "1")
        self.ent_qty_pos.grid(row=3, column=4, sticky="ew", padx=(0, 8), pady=(0, 8))
        self._numberize(self.ent_qty_pos)
        self.ent_qty_pos.bind("<Return>", lambda event: self.add_to_dispatch_cart())

        self.lbl_unit_pos = tk.Label(
            box,
            text="Đơn vị tính: -",
            bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"], anchor="w", justify="left",
        )
        self.lbl_unit_pos.grid(row=3, column=5, columnspan=3, sticky="ew", padx=(0, 10), pady=(0, 8))

        table = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        table.pack(fill="both", expand=True, padx=8, pady=(0, 58))
        cols = ("productId", "productName", "lotNo", "expiryDate", "fundSource", "unitCode", "price", "qty", "amount")
        self.tree_cart = tb.Treeview(table, columns=cols, show="headings")
        for key, width, label, anchor in (
            ("productId", 55, "PID", "center"),
            ("productName", 245, "TÊN HÀNG HÓA", "w"),
            ("lotNo", 95, "SỐ LÔ", "center"),
            ("expiryDate", 95, "HSD", "center"),
            ("fundSource", 150, "NGUỒN KINH PHÍ", "w"),
            ("unitCode", 60, "ĐVT", "center"),
            ("price", 85, "ĐƠN GIÁ", "e"),
            ("qty", 75, "SL XUẤT", "e"),
            ("amount", 105, "THÀNH TIỀN", "e"),
        ):
            self.tree_cart.heading(key, text=label, command=lambda col=key: self.sort_tree(self.tree_cart, col))
            self.tree_cart.column(key, width=width, anchor=anchor, stretch=(key in {"productName", "fundSource"}))
        self.tree_cart.pack(fill="both", expand=True, padx=1, pady=1)

        footer = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1, height=52)
        footer.place(relx=0, rely=1, relwidth=1, height=52, anchor="sw")
        tk.Label(footer, text="Xuất kho chỉ ghi nhận sau khi bấm Tạo phiếu xuất", bg=COLORS["surface"], fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"]).pack(side="left", padx=12, pady=12)
        tb.Button(footer, text="Xóa dòng", style="Shell.Secondary.TButton", command=self.remove_selected_dispatch_item).pack(side="left", padx=3, pady=8)
        tb.Button(footer, text="Xóa danh sách", style="Shell.Secondary.TButton", command=self.clear_dispatch_cart).pack(side="left", padx=3, pady=8)
        tb.Button(footer, text="Tạo phiếu xuất", style="Shell.Primary.TButton", command=self.confirm_dispatch).pack(side="right", padx=(3, 10), pady=8)
        tb.Button(footer, text="In phiếu gần nhất", style="Shell.Secondary.TButton", command=self.print_dispatch_note).pack(side="right", padx=3, pady=8)

    def _transaction_page_header(self, root, title, subtitle, note):
        header = tk.Frame(root, bg=COLORS["canvas"])
        header.pack(fill="x", padx=8, pady=(8, 6))
        tk.Label(header, text=title, bg=COLORS["canvas"], fg=COLORS["text"], font=TYPOGRAPHY["headline"]).pack(anchor="w")
        tk.Label(header, text=subtitle, bg=COLORS["canvas"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["body"]).pack(anchor="w", pady=(1, 0))
        tk.Label(header, text=note, bg=COLORS["canvas"], fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"]).pack(anchor="w", pady=(1, 0))

    class _Panel:
        pass

    def _transaction_panel(self, parent, title):
        outer = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        head = tk.Frame(outer, bg=COLORS["surface_subdued"])
        head.pack(fill="x")
        tk.Label(head, text=title, bg=COLORS["surface_subdued"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["badge"], anchor="w").pack(fill="x", padx=10, pady=6)
        content = tk.Frame(outer, bg=COLORS["surface"])
        content.pack(fill="x")
        panel = self._Panel()
        panel.pack = outer.pack
        panel.grid = outer.grid
        panel.content = content
        panel.frame = outer
        return panel

    def _field_label(self, parent, text):
        return tk.Label(parent, text=text, bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"])
