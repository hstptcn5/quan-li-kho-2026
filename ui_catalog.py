# -*- coding: utf-8 -*-
"""Stitch-aligned catalog and product-detail workspace.

UI-2 keeps the existing product creation, standard medicine catalog, barcode,
Excel import and inventory domain behaviour.  The module only reorganizes how
those capabilities are presented and adds read-only product detail views.
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk

import ttkbootstrap as tb

from date_utils import format_date_display, format_datetime_display
from ui_design import COLORS, TYPOGRAPHY


PRODUCT_TYPE_LABELS = {
    "thuoc": "Thuốc",
    "vaccine": "Vaccine",
    "vtyt": "VTYT",
    "khac": "Khác",
}


def _parse_date(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def build_catalog_rows(products, inventory_rows, *, today=None, warning_days=90):
    """Aggregate fund-separated inventory into one read-only catalog row/product."""
    today = today or dt.date.today()
    warning_until = today + dt.timedelta(days=int(warning_days))
    inv_by_product = {}
    for raw in inventory_rows or []:
        row = dict(raw)
        inv_by_product.setdefault(row.get("productId"), []).append(row)

    result = []
    for raw in products or []:
        product = dict(raw)
        product_id = product.get("id")
        stock_rows = inv_by_product.get(product_id, [])
        total_stock = sum(float(r.get("stockBase") or 0) for r in stock_rows)
        positive = [r for r in stock_rows if float(r.get("stockBase") or 0) > 0]
        active_lots = {r.get("batchId") for r in positive if r.get("batchId") is not None}
        funds = sorted({str(r.get("fundSource") or "").strip() for r in positive if str(r.get("fundSource") or "").strip()})
        expiry_dates = [d for d in (_parse_date(r.get("expiryDate")) for r in positive) if d is not None]
        nearest = min(expiry_dates) if expiry_dates else None

        if total_stock <= 0:
            status = "Hết tồn"
            status_rank = 3
        elif nearest and nearest < today:
            status = "Có lô hết hạn"
            status_rank = 0
        elif nearest and nearest <= warning_until:
            status = "Cận hạn"
            status_rank = 1
        else:
            status = "Còn hàng"
            status_rank = 2

        result.append({
            "id": product_id,
            "name": product.get("name") or "",
            "barcode": product.get("barcode") or "",
            "productType": product.get("productType") or "khac",
            "registrationNumber": product.get("registrationNumber") or "",
            "defaultUnit": product.get("defaultUnit") or "",
            "totalStock": total_stock,
            "lotCount": len(active_lots),
            "nearestExpiry": nearest.isoformat() if nearest else "",
            "fundSources": funds,
            "status": status,
            "statusRank": status_rank,
        })
    return result


def filter_catalog_rows(rows, *, keyword="", product_type="Tất cả", stock_status="Tất cả", fund_source="Tất cả"):
    keyword = str(keyword or "").strip().lower()
    product_type = str(product_type or "Tất cả")
    stock_status = str(stock_status or "Tất cả")
    fund_source = str(fund_source or "Tất cả")
    filtered = []
    for row in rows or []:
        haystack = " ".join([
            str(row.get("id") or ""),
            str(row.get("name") or ""),
            str(row.get("barcode") or ""),
            str(row.get("registrationNumber") or ""),
        ]).lower()
        if keyword and keyword not in haystack:
            continue
        if product_type != "Tất cả" and row.get("productType") != product_type:
            continue
        if stock_status != "Tất cả" and row.get("status") != stock_status:
            continue
        if fund_source != "Tất cả" and fund_source not in (row.get("fundSources") or []):
            continue
        filtered.append(row)
    return filtered


class CatalogUiMixin:
    """Replace the legacy Products tab with catalog + detail presentation."""

    def build_products_tab(self):
        root = self.tab_products
        self._catalog_rows = []
        self._catalog_selected_product_id = None

        self.catalog_list_page = tk.Frame(root, bg=COLORS["canvas"])
        self.catalog_list_page.pack(fill="both", expand=True)
        self.product_detail_page = tk.Frame(root, bg=COLORS["canvas"])

        self._build_catalog_list_page(self.catalog_list_page)
        self._build_catalog_create_panel(self.catalog_list_page)
        self._build_product_detail_page(self.product_detail_page)

    def _build_catalog_list_page(self, root):
        header = tk.Frame(root, bg=COLORS["canvas"])
        header.pack(fill="x", padx=8, pady=(8, 6))
        title_wrap = tk.Frame(header, bg=COLORS["canvas"])
        title_wrap.pack(side="left")
        tk.Label(title_wrap, text="Danh mục hàng hóa", bg=COLORS["canvas"], fg=COLORS["text"], font=TYPOGRAPHY["headline"]).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="Thuốc, vaccine và vật tư y tế • tra cứu tồn và HSD ngay trên danh mục",
            bg=COLORS["canvas"], fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"],
        ).pack(anchor="w")

        tb.Button(header, text="+ Thêm sản phẩm", style="Shell.Primary.TButton", command=self._toggle_catalog_create_panel).pack(side="right", padx=(6, 0))
        tb.Button(header, text="Nhập Excel", style="Shell.Secondary.TButton", command=self.bulk_import_from_excel).pack(side="right", padx=(6, 0))
        tb.Button(header, text="Tải Excel mẫu", style="Shell.Secondary.TButton", command=self.export_import_template).pack(side="right", padx=(6, 0))

        filters = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        filters.pack(fill="x", padx=8, pady=(0, 7))

        self.catalog_search_var = tk.StringVar()
        self.catalog_search = tb.Entry(filters, textvariable=self.catalog_search_var, width=35)
        self.catalog_search.pack(side="left", padx=(10, 8), pady=8)
        self.catalog_search.insert(0, "")
        self.catalog_search.bind("<KeyRelease>", lambda event: self._apply_catalog_filters())

        self.catalog_type_var = tk.StringVar(value="Tất cả")
        self.catalog_type_combo = tb.Combobox(
            filters,
            textvariable=self.catalog_type_var,
            values=["Tất cả", "thuoc", "vaccine", "vtyt", "khac"],
            state="readonly",
            width=12,
        )
        self.catalog_type_combo.pack(side="left", padx=4, pady=8)
        self.catalog_type_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_catalog_filters())

        self.catalog_stock_var = tk.StringVar(value="Tất cả")
        self.catalog_stock_combo = tb.Combobox(
            filters,
            textvariable=self.catalog_stock_var,
            values=["Tất cả", "Còn hàng", "Cận hạn", "Có lô hết hạn", "Hết tồn"],
            state="readonly",
            width=16,
        )
        self.catalog_stock_combo.pack(side="left", padx=4, pady=8)
        self.catalog_stock_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_catalog_filters())

        self.catalog_fund_var = tk.StringVar(value="Tất cả")
        self.catalog_fund_combo = tb.Combobox(filters, textvariable=self.catalog_fund_var, values=["Tất cả"], state="readonly", width=22)
        self.catalog_fund_combo.pack(side="left", padx=4, pady=8)
        self.catalog_fund_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_catalog_filters())

        tb.Button(filters, text="↻", style="Shell.Secondary.TButton", width=3, command=self.refresh_products).pack(side="right", padx=10, pady=8)
        self.catalog_count_label = tk.Label(filters, text="0 mặt hàng", bg=COLORS["surface"], fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"])
        self.catalog_count_label.pack(side="right", padx=6)

        table_wrap = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        table_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        columns = ("id", "barcode", "name", "type", "unit", "stock", "lots", "expiry", "status")
        tree = tb.Treeview(table_wrap, columns=columns, show="headings")
        specs = (
            ("id", 60, "MÃ", "center"),
            ("barcode", 110, "BARCODE", "w"),
            ("name", 290, "TÊN HÀNG & QUY CÁCH", "w"),
            ("type", 80, "LOẠI", "center"),
            ("unit", 70, "ĐVT", "center"),
            ("stock", 85, "TỔNG TỒN", "e"),
            ("lots", 65, "SỐ LÔ", "center"),
            ("expiry", 95, "HSD GẦN NHẤT", "center"),
            ("status", 115, "TRẠNG THÁI", "center"),
        )
        for key, width, label, anchor in specs:
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=anchor, stretch=(key == "name"))
        tree.tag_configure("expired", background=COLORS["danger_bg"], foreground=COLORS["danger"])
        tree.tag_configure("near", background="#FFF9E8")
        tree.tag_configure("out", foreground=COLORS["text_muted"])
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        tree.bind("<Double-1>", lambda event: self._open_selected_catalog_product())
        tree.bind("<Return>", lambda event: self._open_selected_catalog_product())
        self.catalog_tree = tree

        footer = tk.Frame(root, bg=COLORS["canvas"])
        footer.pack(fill="x", padx=8, pady=(0, 8))
        self.catalog_info_label = tb.Label(footer, text="Chưa load danh mục thuốc", bootstyle="secondary", font=TYPOGRAPHY["compact"])
        self.catalog_info_label.pack(side="left")
        tb.Button(footer, text="Load thuoc.csv", style="Shell.Secondary.TButton", command=self.load_default_csv).pack(side="right", padx=(6, 0))
        tb.Button(footer, text="Load danh mục CSV/Excel", style="Shell.Secondary.TButton", command=self.load_medicine_catalog).pack(side="right", padx=(6, 0))
        tb.Button(footer, text="Thông tin danh mục", style="Shell.Secondary.TButton", command=self.show_catalog_info).pack(side="right", padx=(6, 0))

    def _build_catalog_create_panel(self, root):
        panel = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["primary"], highlightthickness=1)
        self.catalog_create_panel = panel

        head = tk.Frame(panel, bg=COLORS["surface"])
        head.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(head, text="Thêm sản phẩm", bg=COLORS["surface"], fg=COLORS["text"], font=TYPOGRAPHY["body_medium"]).pack(side="left")
        tb.Button(head, text="Đóng", style="Shell.Secondary.TButton", command=self._hide_catalog_create_panel).pack(side="right")

        form = tk.Frame(panel, bg=COLORS["surface"])
        form.pack(fill="x", padx=10, pady=(0, 8))
        for col in range(8):
            form.grid_columnconfigure(col, weight=1 if col in {1, 3, 5, 7} else 0)

        self.product_source_var = tk.StringVar(value="catalog")
        source = tk.Frame(form, bg=COLORS["surface"])
        source.grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 5))
        tk.Label(source, text="Nguồn sản phẩm:", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).pack(side="left", padx=(0, 8))
        self.r_catalog = tb.Radiobutton(source, text="Từ danh mục chuẩn", variable=self.product_source_var, value="catalog", command=self.on_product_source_change)
        self.r_catalog.pack(side="left", padx=(0, 12))
        self.r_free = tb.Radiobutton(source, text="Ngoài danh mục", variable=self.product_source_var, value="free", command=self.on_product_source_change)
        self.r_free.pack(side="left")

        tk.Label(form, text="Tên sản phẩm", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=4)
        self.p_name = tb.Entry(form, width=34)
        self.p_name.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=4)
        self.p_name.bind("<KeyRelease>", self.on_product_name_change)
        self.p_name.bind("<FocusOut>", self.on_product_name_focus_out)
        self.p_name.bind("<Down>", self.on_arrow_down)
        self.p_name.bind("<Up>", self.on_arrow_up)

        tk.Label(form, text="Loại", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).grid(row=1, column=4, sticky="w", padx=(0, 5), pady=4)
        self.p_type = tb.Combobox(form, values=["thuoc", "vaccine", "vtyt", "khac"], state="readonly", width=12)
        self.p_type.set("thuoc")
        self.p_type.grid(row=1, column=5, sticky="ew", padx=(0, 8), pady=4)
        self.p_type.bind("<<ComboboxSelected>>", self.on_product_type_change)

        tk.Label(form, text="Đơn vị cơ sở", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).grid(row=1, column=6, sticky="w", padx=(0, 5), pady=4)
        self.p_base = tb.Entry(form, width=12)
        self.p_base.insert(0, "vien")
        self.p_base.grid(row=1, column=7, sticky="ew", pady=4)

        tk.Label(form, text="Barcode", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).grid(row=3, column=0, sticky="w", padx=(0, 5), pady=4)
        barcode_wrap = tk.Frame(form, bg=COLORS["surface"])
        barcode_wrap.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(0, 8), pady=4)
        self.p_barcode = tb.Entry(barcode_wrap)
        self.p_barcode.pack(side="left", fill="x", expand=True)
        tb.Button(barcode_wrap, text="Quét", style="Shell.Secondary.TButton", command=self.scan_barcode_for_product).pack(side="left", padx=(5, 0))

        self.p_reg_label = tk.Label(form, text="Số đăng ký", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"])
        self.p_reg_label.grid(row=3, column=3, sticky="w", padx=(0, 5), pady=4)
        self.p_reg_number = tb.Entry(form)
        self.p_reg_number.grid(row=3, column=4, columnspan=2, sticky="ew", padx=(0, 8), pady=4)

        actions = tk.Frame(form, bg=COLORS["surface"])
        actions.grid(row=3, column=6, columnspan=2, sticky="e", pady=4)
        tb.Button(actions, text="Lưu sản phẩm", style="Shell.Primary.TButton", command=self._save_catalog_product).pack(side="right")

        self.suggestions_frame = tb.Frame(form)
        self.suggestions_frame.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=(0, 4))
        self.suggestions_listbox = tk.Listbox(self.suggestions_frame, height=5, font=TYPOGRAPHY["compact"])
        self.suggestions_listbox.pack(fill="both", expand=True)
        self.suggestions_listbox.bind("<Double-Button-1>", self.on_suggestion_selected)
        self.suggestions_listbox.bind("<Button-1>", self.on_suggestion_click)
        self.suggestions_listbox.bind("<ButtonRelease-1>", self.on_suggestion_click)
        self.suggestions_listbox.bind("<Return>", self.on_suggestion_selected)
        self.suggestions_listbox.bind("<Escape>", self.hide_suggestions)
        self.suggestions_listbox.bind("<Up>", self.on_suggestion_up)
        self.suggestions_listbox.bind("<Down>", self.on_suggestion_down)
        self.suggestions_frame.grid_remove()
        self.current_suggestions = []
        self.on_product_source_change()
        self.on_product_type_change()

    def _toggle_catalog_create_panel(self):
        if self.catalog_create_panel.winfo_manager():
            self._hide_catalog_create_panel()
        else:
            # Place the editor between filter strip and table without changing
            # any legacy product creation behaviour.
            self.catalog_create_panel.pack(fill="x", padx=8, pady=(0, 7), before=self.catalog_tree.master)
            self.p_name.focus_set()

    def _hide_catalog_create_panel(self):
        self.catalog_create_panel.pack_forget()
        self.hide_suggestions()

    def _save_catalog_product(self):
        before = len(self.db.q("SELECT id FROM products"))
        self.save_product()
        after = len(self.db.q("SELECT id FROM products"))
        if after > before:
            self._hide_catalog_create_panel()

    def refresh_products(self):
        products = self.db.q(
            "SELECT id, name, defaultUnit, barcode, productType, registrationNumber "
            "FROM products ORDER BY LOWER(name), id"
        )
        self._products = [{"id": p["id"], "name": p["name"]} for p in products]
        options = [f"{p['id']} — {p['name']}" for p in self._products]

        # Preserve all legacy purchase/dispatch selectors without relying on
        # their original tab index or assuming every selector already exists.
        for attr_name in ("cmb_prod", "cmb_prod_pos"):
            combo = getattr(self, attr_name, None)
            if combo is not None:
                try:
                    current = combo.get()
                    combo["values"] = options
                    if current in options:
                        combo.set(current)
                    elif options:
                        combo.current(0)
                except Exception:
                    pass
        try:
            if options and hasattr(self, "update_purchase_unit_and_price"):
                self.update_purchase_unit_and_price()
        except Exception:
            pass
        try:
            if options and hasattr(self, "update_dispatch_unit_label"):
                self.update_dispatch_unit_label()
        except Exception:
            pass

        inventory = self.db.get_inventory()
        self._catalog_rows = build_catalog_rows(products, inventory)
        funds = sorted({fund for row in self._catalog_rows for fund in row.get("fundSources", [])})
        if hasattr(self, "catalog_fund_combo"):
            self.catalog_fund_combo["values"] = ["Tất cả"] + funds
            if self.catalog_fund_var.get() not in self.catalog_fund_combo["values"]:
                self.catalog_fund_var.set("Tất cả")
            self._apply_catalog_filters()

    def _apply_catalog_filters(self):
        if not hasattr(self, "catalog_tree"):
            return
        rows = filter_catalog_rows(
            self._catalog_rows,
            keyword=self.catalog_search_var.get(),
            product_type=self.catalog_type_var.get(),
            stock_status=self.catalog_stock_var.get(),
            fund_source=self.catalog_fund_var.get(),
        )
        tree = self.catalog_tree
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            status = row.get("status") or ""
            tag = "expired" if status == "Có lô hết hạn" else "near" if status == "Cận hạn" else "out" if status == "Hết tồn" else ""
            tree.insert(
                "", "end", iid=f"product-{row['id']}",
                values=(
                    f"TH-{int(row['id']):05d}" if row.get("id") is not None else "",
                    row.get("barcode") or "-",
                    row.get("name") or "",
                    PRODUCT_TYPE_LABELS.get(row.get("productType"), row.get("productType") or "Khác"),
                    row.get("defaultUnit") or "",
                    f"{float(row.get('totalStock') or 0):g}",
                    row.get("lotCount") or 0,
                    format_date_display(row.get("nearestExpiry")) if row.get("nearestExpiry") else "-",
                    status,
                ),
                tags=(tag,) if tag else (),
            )
        self.catalog_count_label.config(text=f"Hiển thị {len(rows)} / {len(self._catalog_rows)} mặt hàng")

    def _open_selected_catalog_product(self):
        selection = self.catalog_tree.selection()
        if not selection:
            return
        values = self.catalog_tree.item(selection[0]).get("values") or []
        if not values:
            return
        iid = str(selection[0])
        try:
            product_id = int(iid.split("product-", 1)[1])
        except Exception:
            return
        self._show_product_detail(product_id)

    def _build_product_detail_page(self, root):
        self.product_detail_header = tk.Frame(root, bg=COLORS["canvas"])
        self.product_detail_header.pack(fill="x", padx=8, pady=(8, 6))
        tb.Button(self.product_detail_header, text="← Danh mục", style="Shell.Secondary.TButton", command=self._show_catalog_list).pack(side="left", padx=(0, 10))
        self.product_detail_title = tk.Label(self.product_detail_header, text="Chi tiết sản phẩm", bg=COLORS["canvas"], fg=COLORS["text"], font=TYPOGRAPHY["headline"])
        self.product_detail_title.pack(side="left")

        actions = tk.Frame(self.product_detail_header, bg=COLORS["canvas"])
        actions.pack(side="right")
        tb.Button(actions, text="Nhập kho", style="Shell.Primary.TButton", command=lambda: self.nb.select(self.tab_purchase)).pack(side="left", padx=3)
        tb.Button(actions, text="Xuất kho", style="Shell.Primary.TButton", command=lambda: self.nb.select(self.tab_dispatch)).pack(side="left", padx=3)
        tb.Button(actions, text="Kiểm kê", style="Shell.Secondary.TButton", command=self._open_inventory_check_from_detail).pack(side="left", padx=3)

        summary = tk.Frame(root, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        summary.pack(fill="x", padx=8, pady=(0, 7))
        self.product_detail_meta = tk.Label(summary, text="-", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["body"], justify="left", anchor="w")
        self.product_detail_meta.pack(fill="x", padx=12, pady=10)

        nb = tb.Notebook(root)
        nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.product_detail_nb = nb
        self.product_lots_tab = tb.Frame(nb)
        self.product_history_tab = tb.Frame(nb)
        self.product_units_tab = tb.Frame(nb)
        self.product_info_tab = tb.Frame(nb)
        nb.add(self.product_lots_tab, text="Tồn kho theo lô")
        nb.add(self.product_history_tab, text="Lịch sử nhập xuất")
        nb.add(self.product_units_tab, text="Đơn vị quy đổi")
        nb.add(self.product_info_tab, text="Thông tin sản phẩm")

        self._build_product_lots_table()
        self._build_product_history_table()
        self._build_product_units_table()
        self.product_info_text = tk.Label(self.product_info_tab, text="-", bg=COLORS["surface"], fg=COLORS["text"], font=TYPOGRAPHY["body"], justify="left", anchor="nw")
        self.product_info_text.pack(fill="both", expand=True, padx=14, pady=14)

    def _build_product_lots_table(self):
        cols = ("lot", "exp", "fund", "stock", "status")
        tree = tb.Treeview(self.product_lots_tab, columns=cols, show="headings")
        for key, width, label, anchor in (
            ("lot", 130, "SỐ LÔ", "center"),
            ("exp", 120, "HẠN SỬ DỤNG", "center"),
            ("fund", 220, "NGUỒN KINH PHÍ", "w"),
            ("stock", 120, "TỒN KHẢ DỤNG", "e"),
            ("status", 140, "TRẠNG THÁI", "center"),
        ):
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=anchor, stretch=(key == "fund"))
        tree.tag_configure("expired", background=COLORS["danger_bg"], foreground=COLORS["danger"])
        tree.tag_configure("near", background="#FFF9E8")
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.product_lots_tree = tree

    def _build_product_history_table(self):
        cols = ("time", "type", "lot", "fund", "qty", "unit", "partner", "reason")
        tree = tb.Treeview(self.product_history_tab, columns=cols, show="headings")
        for key, width, label, anchor in (
            ("time", 135, "THỜI GIAN", "center"),
            ("type", 95, "LOẠI", "center"),
            ("lot", 95, "LÔ", "center"),
            ("fund", 150, "NGUỒN", "w"),
            ("qty", 90, "SL QUY ĐỔI", "e"),
            ("unit", 80, "ĐVT", "center"),
            ("partner", 150, "ĐƠN VỊ/NCC", "w"),
            ("reason", 170, "LÝ DO", "w"),
        ):
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=anchor, stretch=(key in {"partner", "reason"}))
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.product_history_tree = tree

    def _build_product_units_table(self):
        cols = ("unit", "factor", "price")
        tree = tb.Treeview(self.product_units_tab, columns=cols, show="headings")
        tree.heading("unit", text="ĐƠN VỊ")
        tree.heading("factor", text="QUY ĐỔI VỀ ĐƠN VỊ CƠ SỞ")
        tree.heading("price", text="GIÁ")
        tree.column("unit", width=180, anchor="w")
        tree.column("factor", width=220, anchor="e")
        tree.column("price", width=160, anchor="e")
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.product_units_tree = tree

    def _show_product_detail(self, product_id):
        rows = self.db.q(
            "SELECT id, name, defaultUnit, barcode, productType, registrationNumber, createdAt "
            "FROM products WHERE id=?",
            (int(product_id),),
        )
        if not rows:
            return
        product = rows[0]
        self._catalog_selected_product_id = int(product_id)
        self.catalog_list_page.pack_forget()
        self.product_detail_page.pack(fill="both", expand=True)
        self.product_detail_title.config(text=product.get("name") or "Chi tiết sản phẩm")

        inventory = [r for r in self.db.get_inventory() if int(r.get("productId")) == int(product_id)]
        total = sum(float(r.get("stockBase") or 0) for r in inventory)
        active_lots = {r.get("batchId") for r in inventory if float(r.get("stockBase") or 0) > 0}
        self.product_detail_meta.config(
            text=(
                f"Mã: TH-{int(product_id):05d}    •    Loại: {PRODUCT_TYPE_LABELS.get(product.get('productType'), product.get('productType') or 'Khác')}    •    "
                f"ĐVT cơ sở: {product.get('defaultUnit') or '-'}    •    Tổng tồn: {total:g}    •    Số lô còn tồn: {len(active_lots)}\n"
                f"Barcode: {product.get('barcode') or '-'}    •    Số đăng ký: {product.get('registrationNumber') or '-'}"
            )
        )
        self._fill_product_lots(inventory)
        self._fill_product_history(product_id)
        self._fill_product_units(product_id)
        self.product_info_text.config(
            text=(
                f"Tên sản phẩm: {product.get('name') or ''}\n\n"
                f"Loại sản phẩm: {PRODUCT_TYPE_LABELS.get(product.get('productType'), product.get('productType') or 'Khác')}\n"
                f"Đơn vị cơ sở: {product.get('defaultUnit') or '-'}\n"
                f"Barcode: {product.get('barcode') or '-'}\n"
                f"Số đăng ký: {product.get('registrationNumber') or '-'}\n"
                f"Ngày tạo: {format_datetime_display(product.get('createdAt'))}"
            )
        )
        self.product_detail_nb.select(self.product_lots_tab)

    def _fill_product_lots(self, inventory):
        tree = self.product_lots_tree
        for item in tree.get_children():
            tree.delete(item)
        today = dt.date.today()
        for row in sorted(inventory, key=lambda r: (_parse_date(r.get("expiryDate")) or dt.date.max, str(r.get("fundSource") or ""))):
            stock = float(row.get("stockBase") or 0)
            if stock <= 0:
                continue
            expiry = _parse_date(row.get("expiryDate"))
            if expiry and expiry < today:
                status, tag = "Đã hết hạn", "expired"
            elif expiry and expiry <= today + dt.timedelta(days=90):
                status, tag = "Cận hạn", "near"
            else:
                status, tag = "Còn hàng", ""
            tree.insert("", "end", values=(
                row.get("lotNo") or "",
                format_date_display(row.get("expiryDate")),
                row.get("fundSource") or "(không rõ)",
                f"{stock:g}",
                status,
            ), tags=(tag,) if tag else ())

    def _fill_product_history(self, product_id):
        tree = self.product_history_tree
        for item in tree.get_children():
            tree.delete(item)
        try:
            rows = self.db.product_lot_history(product_id=int(product_id), limit=250)
        except Exception:
            rows = []
        for row in rows:
            qty = float(row.get("qtyBase") if row.get("qtyBase") is not None else row.get("qty") or 0)
            tree.insert("", "end", values=(
                format_datetime_display(row.get("createdAt")),
                row.get("type") or "",
                row.get("lotNo") or "",
                row.get("fundSource") or "",
                f"{qty:g}",
                row.get("originalUnit") or row.get("unitCode") or "",
                row.get("receivingUnit") or "",
                row.get("reason") or "",
            ))

    def _fill_product_units(self, product_id):
        tree = self.product_units_tree
        for item in tree.get_children():
            tree.delete(item)
        rows = self.db.q(
            "SELECT unitCode, toBaseQty, price FROM product_units WHERE productId=? ORDER BY toBaseQty, unitCode",
            (int(product_id),),
        )
        for row in rows:
            tree.insert("", "end", values=(
                row.get("unitCode") or "",
                f"1 {row.get('unitCode') or ''} = {float(row.get('toBaseQty') or 0):g} đơn vị cơ sở",
                f"{float(row.get('price') or 0):,.0f}",
            ))

    def _show_catalog_list(self):
        self.product_detail_page.pack_forget()
        self.catalog_list_page.pack(fill="both", expand=True)
        self._catalog_selected_product_id = None
        self.refresh_products()
        self.catalog_search.focus_set()

    def _open_inventory_check_from_detail(self):
        self.nb.select(self.tab_operations)
        try:
            self.ops_nb.select(self.ops_inventory_tab)
        except Exception:
            pass

    def focus_search(self):
        """Route Ctrl+F by actual page identity, not legacy Notebook index."""
        try:
            selected = self.nametowidget(self.nb.select())
        except Exception:
            selected = None
        if selected is getattr(self, "tab_products", None) and hasattr(self, "catalog_search"):
            self.catalog_search.focus_set()
            return
        if selected is getattr(self, "tab_purchase", None) and hasattr(self, "search_purchase"):
            self.search_purchase.focus_set()
            return
        if selected is getattr(self, "tab_dispatch", None) and hasattr(self, "search_pos"):
            self.search_pos.focus_set()
            return
        # Other pages currently have no canonical text search target.
        try:
            self.status.config(text="Màn hình này chưa có ô tìm kiếm nhanh")
        except Exception:
            pass
