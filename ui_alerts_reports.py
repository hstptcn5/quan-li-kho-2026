# -*- coding: utf-8 -*-
"""Stitch-aligned expiry-alert and XNT-report workspaces.

UI-5 is presentation-only. Existing InventoryApp methods continue to own alert
queries, XNT calculations and CSV/Excel/PDF exports. This mixin recreates only
the widget contracts consumed by those hardened methods.
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry

from ui_design import COLORS, TYPOGRAPHY


ALERT_WIDGET_CONTRACT = ("ent_warn_days", "tree_alerts")
REPORT_WIDGET_CONTRACT = ("de_from", "de_to", "cmb_report_fund", "tree_report")


class AlertsReportsUiMixin:
    """Override only the expiry-alert and standard XNT page builders."""

    def build_alerts_tab(self):
        root = self.tab_alerts
        self._page_header(
            root,
            "Cảnh báo hạn sử dụng",
            "Theo dõi các lô còn tồn có hạn sử dụng nằm trong khoảng cảnh báo.",
            "Dữ liệu lấy trực tiếp từ tồn kho hiện tại; màn này không thay đổi FEFO hay số dư.",
        )

        controls = self._panel(root, "BỘ LỌC CẢNH BÁO")
        controls.pack(fill="x", padx=8, pady=(0, 7))
        row = controls.content

        self._label(row, "Cảnh báo trong").pack(side="left", padx=(10, 6), pady=9)
        self.ent_warn_days = tb.Entry(row, width=8)
        self.ent_warn_days.insert(0, "180")
        self.ent_warn_days.pack(side="left", pady=7)
        self._numberize(self.ent_warn_days)
        tk.Label(
            row,
            text="ngày",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
        ).pack(side="left", padx=(5, 12), pady=9)

        tb.Button(
            row,
            text="↻  Làm mới",
            style="Shell.Primary.TButton",
            command=self.refresh_alerts,
        ).pack(side="left", padx=(0, 6), pady=6)
        tb.Button(
            row,
            text="Mở tồn kho FEFO",
            style="Shell.Secondary.TButton",
            command=lambda: self.nb.select(self.tab_stock),
        ).pack(side="left", pady=6)

        note = tk.Frame(
            root,
            bg=COLORS["warning_bg"],
            highlightbackground=COLORS["warning_border"],
            highlightthickness=1,
        )
        note.pack(fill="x", padx=8, pady=(0, 7))
        tk.Label(
            note,
            text="Ưu tiên xử lý lô gần HSD trước. Danh sách chỉ hiển thị lô còn tồn dương trong khoảng ngày đã chọn.",
            bg=COLORS["warning_bg"],
            fg=COLORS["warning"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=7)

        table = tk.Frame(
            root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = ("product", "productName", "batch", "lot", "exp", "qty")
        self.tree_alerts = tb.Treeview(table, columns=cols, show="headings")
        specs = (
            ("product", 65, "PID", "center"),
            ("productName", 350, "TÊN THUỐC / VACCINE / VTYT", "w"),
            ("batch", 75, "BATCH", "center"),
            ("lot", 120, "SỐ LÔ", "center"),
            ("exp", 120, "HẠN SỬ DỤNG", "center"),
            ("qty", 110, "TỒN (BASE)", "e"),
        )
        for key, width, label, anchor in specs:
            self.tree_alerts.heading(
                key,
                text=label,
                command=lambda col=key: self.sort_tree(self.tree_alerts, col),
            )
            self.tree_alerts.column(
                key,
                width=width,
                anchor=anchor,
                stretch=(key == "productName"),
            )
        self.tree_alerts.tag_configure("odd", background=COLORS["surface_hover"])
        self.tree_alerts.pack(fill="both", expand=True, padx=1, pady=1)

    def build_report_tab(self):
        root = self.tab_report
        self._page_header(
            root,
            "Báo cáo Xuất – Nhập – Tồn",
            "Đối chiếu tồn đầu kỳ, nhập, xuất và tồn cuối theo sản phẩm, lô và nguồn kinh phí.",
            "Khoảng ngày và nguồn lọc được áp dụng cho cùng logic XNT hiện có; không tính lại tồn ở lớp giao diện.",
        )

        controls = self._panel(root, "ĐIỀU KIỆN BÁO CÁO")
        controls.pack(fill="x", padx=8, pady=(0, 7))
        row = controls.content

        self._label(row, "Từ ngày").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(8, 2))
        self.de_from = DateEntry(row, dateformat="%d-%m-%Y", firstweekday=0, bootstyle="secondary")
        self.de_from.entry.delete(0, "end")
        self.de_from.entry.insert(0, dt.date.today().replace(day=1).strftime("%d-%m-%Y"))
        self.de_from.grid(row=1, column=0, sticky="ew", padx=(10, 8), pady=(0, 8))

        self._label(row, "Đến ngày").grid(row=0, column=1, sticky="w", padx=(0, 5), pady=(8, 2))
        self.de_to = DateEntry(row, dateformat="%d-%m-%Y", firstweekday=0, bootstyle="secondary")
        self.de_to.entry.delete(0, "end")
        self.de_to.entry.insert(0, dt.date.today().strftime("%d-%m-%Y"))
        self.de_to.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 8))

        self._label(row, "Nguồn kinh phí").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(8, 2))
        self.cmb_report_fund = tb.Combobox(row, state="readonly", width=24)
        self.cmb_report_fund.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(0, 8))
        self.cmb_report_fund.bind("<<ComboboxSelected>>", lambda event: self.refresh_report())

        buttons = tk.Frame(row, bg=COLORS["surface"])
        buttons.grid(row=0, column=3, rowspan=2, sticky="e", padx=(6, 10), pady=7)
        tb.Button(buttons, text="↻  Làm mới", style="Shell.Primary.TButton", command=self.refresh_report).pack(side="left", padx=3)
        tb.Button(buttons, text="CSV", style="Shell.Secondary.TButton", command=self.export_report_csv).pack(side="left", padx=3)
        tb.Button(buttons, text="Excel", style="Shell.Secondary.TButton", command=self.export_report_excel).pack(side="left", padx=3)
        tb.Button(buttons, text="PDF", style="Shell.Secondary.TButton", command=self.export_report_pdf).pack(side="left", padx=3)
        tb.Button(buttons, text="Biên bản kiểm kê", style="Shell.Secondary.TButton", command=self.print_inventory_check_pdf).pack(side="left", padx=3)

        for col in range(3):
            row.grid_columnconfigure(col, weight=1)

        context = tk.Frame(
            root,
            bg=COLORS["info_bg"],
            highlightbackground=COLORS["info_border"],
            highlightthickness=1,
        )
        context.pack(fill="x", padx=8, pady=(0, 7))
        tk.Label(
            context,
            text="Tồn đầu = trước ngày bắt đầu • Nhập = PURCHASE • Xuất = SALE / DISCARD / DISPATCH • Tồn cuối = đến hết ngày kết thúc.",
            bg=COLORS["info_bg"],
            fg=COLORS["info"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=7)

        table = tk.Frame(
            root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = (
            "product", "productName", "lotNo", "expiryDate", "fundSource",
            "opening", "inbound", "outbound", "closing",
        )
        self.tree_report = tb.Treeview(table, columns=cols, show="headings")
        specs = (
            ("product", 55, "PID", "center"),
            ("productName", 270, "TÊN HÀNG HÓA", "w"),
            ("lotNo", 90, "SỐ LÔ", "center"),
            ("expiryDate", 100, "HSD", "center"),
            ("fundSource", 155, "NGUỒN KINH PHÍ", "w"),
            ("opening", 85, "TỒN ĐẦU", "e"),
            ("inbound", 80, "NHẬP", "e"),
            ("outbound", 80, "XUẤT", "e"),
            ("closing", 85, "TỒN CUỐI", "e"),
        )
        for key, width, label, anchor in specs:
            self.tree_report.heading(
                key,
                text=label,
                command=lambda col=key: self.sort_tree(self.tree_report, col),
            )
            self.tree_report.column(
                key,
                width=width,
                anchor=anchor,
                stretch=(key in {"productName", "fundSource"}),
            )
        self.tree_report.tag_configure("odd", background=COLORS["surface_hover"])
        self.tree_report.tag_configure("total", background=COLORS["success_bg"])
        self.tree_report.pack(fill="both", expand=True, padx=1, pady=1)

    def _page_header(self, root, title, subtitle, note):
        header = tk.Frame(root, bg=COLORS["canvas"])
        header.pack(fill="x", padx=8, pady=(8, 6))
        tk.Label(header, text=title, bg=COLORS["canvas"], fg=COLORS["text"], font=TYPOGRAPHY["headline"]).pack(anchor="w")
        tk.Label(header, text=subtitle, bg=COLORS["canvas"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["body"]).pack(anchor="w", pady=(1, 0))
        tk.Label(header, text=note, bg=COLORS["canvas"], fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"]).pack(anchor="w", pady=(1, 0))

    class _Panel:
        pass

    def _panel(self, parent, title):
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

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"])
