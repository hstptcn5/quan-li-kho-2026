# -*- coding: utf-8 -*-
"""Desktop shell for the approved Stitch visual baseline.

UI-0 intentionally changes navigation and shared styling only. Existing page
builders remain the source of business behaviour until their dedicated UI
batches are implemented.
"""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as tb

from config import APP_NAME, APP_VERSION
from ui_design import COLORS, LEGACY_HOTKEYS, NAV_ITEMS, TYPOGRAPHY, apply_clinical_styles


class ClinicalShellMixin:
    """Replace the legacy visible tab strip with a persistent operations shell."""

    def make_style(self):
        # Keep any compatibility styles defined by the legacy application, then
        # layer the approved clinical design tokens on top.
        super().make_style()
        apply_clinical_styles()

    def make_ui(self):
        self._build_shell_menu()
        self.configure(background=COLORS["canvas"])
        try:
            self.geometry("1360x820")
            self.minsize(1120, 700)
        except Exception:
            pass

        shell = tk.Frame(self, bg=COLORS["canvas"], highlightthickness=0)
        shell.pack(fill="both", expand=True)
        self.shell_root = shell

        sidebar = tk.Frame(
            shell,
            bg=COLORS["canvas"],
            width=205,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.shell_sidebar = sidebar

        content = tk.Frame(shell, bg=COLORS["canvas"], highlightthickness=0)
        content.pack(side="left", fill="both", expand=True)
        self.shell_content = content

        self._build_shell_header(content)

        workspace = tk.Frame(content, bg=COLORS["canvas"], padx=12, pady=10)
        workspace.pack(fill="both", expand=True)

        # Retain an internal Notebook because existing code, keyboard shortcuts,
        # and refresh handlers already use self.nb.select(frame). Its visual tabs
        # are hidden by Shell.TNotebook.Tab in ui_design.py.
        self.nb = tb.Notebook(workspace, style="Shell.TNotebook")
        self.nb.pack(fill="both", expand=True)

        self.tab_products = tb.Frame(self.nb)
        self.tab_purchase = tb.Frame(self.nb)
        self.tab_dispatch = tb.Frame(self.nb)
        self.tab_operations = tb.Frame(self.nb)
        self.tab_stock = tb.Frame(self.nb)
        self.tab_alerts = tb.Frame(self.nb)
        self.tab_report = tb.Frame(self.nb)
        self.tab_backup = tb.Frame(self.nb)
        self.tab_advanced_reports = tb.Frame(self.nb)
        self.tab_mobile = tb.Frame(self.nb)
        self.tab_temp_log = tb.Frame(self.nb)

        self._page_frames = {
            "tab_products": self.tab_products,
            "tab_purchase": self.tab_purchase,
            "tab_dispatch": self.tab_dispatch,
            "tab_operations": self.tab_operations,
            "tab_stock": self.tab_stock,
            "tab_alerts": self.tab_alerts,
            "tab_report": self.tab_report,
            "tab_backup": self.tab_backup,
            "tab_advanced_reports": self.tab_advanced_reports,
            "tab_mobile": self.tab_mobile,
            "tab_temp_log": self.tab_temp_log,
        }

        for _, label, attr_name, _ in NAV_ITEMS:
            self.nb.add(self._page_frames[attr_name], text=label)

        # Existing builders are deliberately reused in UI-0. Dedicated screens
        # will replace them one-by-one in UI-1..UI-6.
        self.build_products_tab()
        self.build_purchase_tab()
        self.build_dispatch_tab()
        self.build_operations_tab()
        self.build_stock_tab()
        self.build_alerts_tab()
        self.build_report_tab()
        self.build_backup_tab()
        self.build_advanced_reports_tab()
        self.build_mobile_tab()
        self.build_temp_log_tab()

        self._build_shell_sidebar(sidebar)
        self._build_shell_statusbar(content)
        self._bind_shell_shortcuts()

        self.nb.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.nb.select(self.tab_operations)
        self.on_tab_changed()
        self.update_db_status()
        self._refresh_shell_runtime_status()

    def _build_shell_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label="Phím tắt", command=self.show_shortcuts)
        helpm.add_command(label="Hướng dẫn sử dụng", command=self.open_user_guide)
        helpm.add_separator()
        helpm.add_command(label="Mở thư mục dữ liệu", command=self.open_data_folder)
        helpm.add_command(label="Giới thiệu (About)…", command=self.show_about)
        menubar.add_cascade(label="Trợ giúp", menu=helpm)

    def _build_shell_header(self, parent):
        header = tk.Frame(
            parent,
            bg=COLORS["surface"],
            height=54,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        self.shell_header = header

        title_wrap = tk.Frame(header, bg=COLORS["surface"])
        title_wrap.pack(side="left", fill="y", padx=(16, 10))
        self.shell_page_title = tk.Label(
            title_wrap,
            text="Tổng quan",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["headline"],
            anchor="w",
        )
        self.shell_page_title.pack(anchor="w", pady=(8, 0))
        self.shell_page_hint = tk.Label(
            title_wrap,
            text="Kho thuốc, vaccine và vật tư y tế",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        )
        self.shell_page_hint.pack(anchor="w")

        header_actions = tk.Frame(header, bg=COLORS["surface"])
        header_actions.pack(side="right", fill="y", padx=12)

        self._lan_status_label = tk.Label(
            header_actions,
            text="● LAN: Tắt",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
        )
        self._lan_status_label.pack(side="left", padx=(4, 12), pady=16)

        tb.Button(
            header_actions,
            text="⌕  Tìm nhanh (Ctrl+F)",
            style="Shell.Secondary.TButton",
            command=self.focus_search,
        ).pack(side="left", padx=(0, 8), pady=10)

        self.role_label = tk.Label(
            header_actions,
            text="Bảo mật: Đã khóa",
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["compact"],
            padx=8,
        )
        self.role_label.pack(side="left", pady=16)

    def _build_shell_sidebar(self, sidebar):
        brand = tk.Frame(sidebar, bg=COLORS["primary"], height=66)
        brand.pack(fill="x")
        brand.pack_propagate(False)

        tk.Label(
            brand,
            text="▣  QUẢN LÝ KHO 2026",
            bg=COLORS["primary"],
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(
            brand,
            text="Thuốc • Vaccine • VTYT",
            bg=COLORS["primary"],
            fg="#D3E4FE",
            font=TYPOGRAPHY["compact"],
            anchor="w",
        ).pack(fill="x", padx=12, pady=(2, 8))

        quick = tk.Frame(sidebar, bg=COLORS["canvas"], padx=8, pady=8)
        quick.pack(fill="x")
        tb.Button(
            quick,
            text="⌕  Tìm / quét nhanh",
            style="Shell.Primary.TButton",
            command=self.focus_search,
        ).pack(fill="x")

        separator = tk.Frame(sidebar, height=1, bg=COLORS["border"])
        separator.pack(fill="x", padx=8, pady=(0, 5))

        nav_wrap = tk.Frame(sidebar, bg=COLORS["canvas"], padx=5)
        nav_wrap.pack(fill="both", expand=True)

        self._nav_buttons = {}
        for key, label, attr_name, shortcut in NAV_ITEMS:
            row_text = label if not shortcut else f"{label}    {shortcut}"
            button = tb.Button(
                nav_wrap,
                text=row_text,
                style="Shell.Nav.TButton",
                command=lambda name=attr_name: self.nb.select(getattr(self, name)),
            )
            button.pack(fill="x", pady=1)
            self._nav_buttons[attr_name] = button

        footer = tk.Frame(
            sidebar,
            bg=COLORS["canvas"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        footer.pack(fill="x", side="bottom")
        tk.Label(
            footer,
            text=f"Phiên bản {APP_VERSION}",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=(7, 0))
        self._sidebar_runtime_label = tk.Label(
            footer,
            text="LAN node • Đã tắt",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        )
        self._sidebar_runtime_label.pack(fill="x", padx=10, pady=(1, 7))

    def _build_shell_statusbar(self, parent):
        status_frame = tk.Frame(
            parent,
            bg=COLORS["canvas"],
            height=27,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.status = tk.Label(
            status_frame,
            text="Sẵn sàng • Ctrl+F: Tìm kiếm • F9: In phiếu xuất",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        )
        self.status.pack(side="left", fill="x", expand=True, padx=10)

        self.db_status = tk.Label(
            status_frame,
            text="Database: Đang kết nối...",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="e",
        )
        self.db_status.pack(side="right", padx=10)

    def _bind_shell_shortcuts(self):
        for key, attr_name in LEGACY_HOTKEYS.items():
            self.bind(f"<{key}>", lambda event, name=attr_name: self.nb.select(getattr(self, name)))
        self.bind("<Control-f>", lambda event: self.focus_search())
        self.bind("<F9>", lambda event: self.print_dispatch_note())
        self.bind("<Control-Return>", lambda event: self.confirm_dispatch())

    def on_tab_changed(self, event=None):
        try:
            selected_id = self.nb.select()
            if not selected_id:
                return
            selected_widget = self.nametowidget(selected_id)
            selected_attr = None
            selected_title = "Quản lý kho"
            for _, label, attr_name, _ in NAV_ITEMS:
                frame = getattr(self, attr_name, None)
                if frame is selected_widget:
                    selected_attr = attr_name
                    selected_title = label.split("  ", 1)[-1]
                    break

            for attr_name, button in getattr(self, "_nav_buttons", {}).items():
                button.configure(
                    style="Shell.NavActive.TButton" if attr_name == selected_attr else "Shell.Nav.TButton"
                )
            if hasattr(self, "shell_page_title"):
                self.shell_page_title.config(text=selected_title)
        except Exception as exc:
            print(f"Lỗi cập nhật điều hướng shell: {exc}")

    def _refresh_shell_runtime_status(self):
        try:
            server = getattr(self, "mobile_server", None)
            running = bool(server and getattr(server, "is_running", False))
            if running:
                port = getattr(server, "port", 5000)
                header_text = f"● LAN: Trực tuyến :{port}"
                footer_text = f"LAN node • :{port}"
                color = COLORS["success"]
            else:
                header_text = "● LAN: Tắt"
                footer_text = "LAN node • Đã tắt"
                color = COLORS["text_muted"]

            if hasattr(self, "_lan_status_label"):
                self._lan_status_label.config(text=header_text, fg=color)
            if hasattr(self, "_sidebar_runtime_label"):
                self._sidebar_runtime_label.config(text=footer_text, fg=color)
        except Exception:
            pass

        try:
            if self.winfo_exists():
                self.after(2000, self._refresh_shell_runtime_status)
        except Exception:
            pass
