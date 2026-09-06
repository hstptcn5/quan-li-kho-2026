# -*- coding: utf-8 -*-
"""Shared desktop visual tokens for the QUẢN LÝ KHO 2026 redesign.

The values are derived from the approved Google Stitch "Clinical Logistics
Authority" baseline.  Keep this module free of business logic so later UI
batches can reuse one visual system without changing inventory semantics.
"""

from __future__ import annotations

import ttkbootstrap as tb


COLORS = {
    "canvas": "#F3F6F9",
    "surface": "#FFFFFF",
    "surface_subdued": "#EDF2F7",
    "surface_hover": "#F8FAFC",
    "border": "#D1D9E2",
    "border_soft": "#E2E8F0",
    "text": "#0B1C30",
    "text_muted": "#64748B",
    "text_subtle": "#475569",
    "primary": "#0D3B66",
    "primary_hover": "#1B4D7E",
    "secondary": "#164E63",
    "success": "#166534",
    "success_bg": "#DCFCE7",
    "success_border": "#BBF7D0",
    "warning": "#B45309",
    "warning_bg": "#FEF3C7",
    "warning_border": "#FDE68A",
    "danger": "#B91C1C",
    "danger_bg": "#FEE2E2",
    "danger_border": "#FECACA",
    "info": "#1D4ED8",
    "info_bg": "#DBEAFE",
    "info_border": "#BFDBFE",
    "selected": "#E0F2FE",
}

SPACING = {
    "xs": 4,
    "sm": 6,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "xxl": 20,
    "table_row": 34,
    "input_height": 32,
}

TYPOGRAPHY = {
    "display": ("Segoe UI", 18, "bold"),
    "headline": ("Segoe UI", 14, "bold"),
    "title": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "body_medium": ("Segoe UI", 10, "bold"),
    "compact": ("Segoe UI", 9),
    "badge": ("Segoe UI", 8, "bold"),
    "mono": ("Consolas", 9),
}


# Navigation is data, not layout.  Tests can verify that the approved shell
# keeps every legacy workspace reachable while later batches replace content.
NAV_ITEMS = (
    ("dashboard", "▦  Tổng quan", "tab_operations", "F4"),
    ("products", "▤  Danh mục hàng hóa", "tab_products", "F1"),
    ("purchase", "↧  Nhập kho", "tab_purchase", "F2"),
    ("dispatch", "↥  Xuất kho", "tab_dispatch", "F3"),
    ("stock", "⌛  Tồn kho (FEFO)", "tab_stock", "F5"),
    ("alerts", "⚠  Cảnh báo HSD", "tab_alerts", "F6"),
    ("report", "▧  Báo cáo XNT", "tab_report", "F7"),
    ("temp", "♨  Nhiệt độ & độ ẩm", "tab_temp_log", "F11"),
    ("data", "⌘  Công cụ dữ liệu", "tab_backup", "F8"),
    ("advanced", "▥  Báo cáo nâng cao", "tab_advanced_reports", "F12"),
    ("admin", "⚙  Quản trị hệ thống", "tab_mobile", "F10"),
)


LEGACY_HOTKEYS = {
    "F1": "tab_products",
    "F2": "tab_purchase",
    "F3": "tab_dispatch",
    "F4": "tab_operations",
    "F5": "tab_stock",
    "F6": "tab_alerts",
    "F7": "tab_report",
    "F8": "tab_backup",
    "F10": "tab_mobile",
    "F11": "tab_temp_log",
    "F12": "tab_advanced_reports",
}


def apply_clinical_styles() -> tb.Style:
    """Configure ttk styles shared by all redesigned desktop workspaces."""
    style = tb.Style()

    style.configure("TLabel", font=TYPOGRAPHY["body"], foreground=COLORS["text"])
    style.configure("TButton", font=TYPOGRAPHY["body_medium"], padding=(10, 5))
    style.configure("TEntry", font=TYPOGRAPHY["body"], padding=(7, 4))
    style.configure("TCombobox", font=TYPOGRAPHY["body"], padding=(7, 3))

    style.configure(
        "Treeview",
        rowheight=SPACING["table_row"],
        font=TYPOGRAPHY["body"],
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border_soft"],
        lightcolor=COLORS["border_soft"],
        darkcolor=COLORS["border_soft"],
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["selected"])],
        foreground=[("selected", COLORS["text"])],
    )
    style.configure(
        "Treeview.Heading",
        font=TYPOGRAPHY["compact"] + ("bold",),
        background=COLORS["surface_subdued"],
        foreground=COLORS["text_subtle"],
        padding=(8, 5),
    )

    # Hide the legacy Notebook tabs.  The notebook is retained internally so
    # old code using self.nb.select(...) continues to work unchanged.
    try:
        style.layout("Shell.TNotebook.Tab", [])
    except Exception:
        pass
    style.configure("Shell.TNotebook", borderwidth=0, tabmargins=0)

    style.configure(
        "Shell.Nav.TButton",
        font=TYPOGRAPHY["body"],
        anchor="w",
        padding=(12, 7),
        background=COLORS["canvas"],
        foreground=COLORS["text_subtle"],
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Shell.Nav.TButton",
        background=[("active", COLORS["surface_subdued"])],
        foreground=[("active", COLORS["text"])],
    )
    style.configure(
        "Shell.NavActive.TButton",
        font=TYPOGRAPHY["body_medium"],
        anchor="w",
        padding=(12, 7),
        background="#DCE9FF",
        foreground=COLORS["primary"],
        borderwidth=0,
        relief="flat",
    )
    style.map("Shell.NavActive.TButton", background=[("active", "#D3E4FE")])

    style.configure(
        "Shell.Primary.TButton",
        font=TYPOGRAPHY["body_medium"],
        padding=(12, 5),
        background=COLORS["primary"],
        foreground="#FFFFFF",
        borderwidth=1,
        relief="flat",
    )
    style.map("Shell.Primary.TButton", background=[("active", COLORS["primary_hover"])])

    style.configure(
        "Shell.Secondary.TButton",
        font=TYPOGRAPHY["body"],
        padding=(10, 5),
        background=COLORS["surface"],
        foreground=COLORS["text"],
        borderwidth=1,
        relief="solid",
    )
    style.map("Shell.Secondary.TButton", background=[("active", COLORS["surface_subdued"])])

    style.configure(
        "Shell.Header.TLabel",
        font=TYPOGRAPHY["headline"],
        foreground=COLORS["text"],
        background=COLORS["surface"],
    )
    style.configure(
        "Shell.Meta.TLabel",
        font=TYPOGRAPHY["compact"],
        foreground=COLORS["text_muted"],
        background=COLORS["surface"],
    )
    style.configure(
        "Shell.Status.TLabel",
        font=TYPOGRAPHY["compact"],
        foreground=COLORS["text_muted"],
        background=COLORS["canvas"],
    )
    return style
