# -*- coding: utf-8 -*-
"""Final visual pass for support/admin workspaces.

UI-6 intentionally wraps the existing builders instead of recreating their
forms. Temperature logging, backup/restore, advanced reports and LAN/mobile
administration keep all original widgets and business handlers; this mixin adds
one consistent clinical header/callout to each workspace.
"""

from __future__ import annotations

import tkinter as tk

from ui_design import COLORS, TYPOGRAPHY


SUPPORT_WORKSPACES = {
    "temp": {
        "tab": "tab_temp_log",
        "title": "Nhiệt độ & độ ẩm",
        "subtitle": "Nhật ký theo dõi điều kiện bảo quản phục vụ thực hành GSP.",
        "note": "Số liệu được ghi thủ công vào cơ sở dữ liệu hiện có; cảnh báo ngưỡng vẫn dùng logic cũ.",
        "tone": "info",
    },
    "data": {
        "tab": "tab_backup",
        "title": "Công cụ dữ liệu & sao lưu",
        "subtitle": "Sao lưu, khôi phục và trao đổi dữ liệu có kiểm soát.",
        "note": "Khôi phục/xóa dữ liệu nhạy cảm vẫn yêu cầu quyền Admin; UI-6 không thay đổi cơ chế backup.",
        "tone": "warning",
    },
    "advanced": {
        "tab": "tab_advanced_reports",
        "title": "Báo cáo nâng cao",
        "subtitle": "Tra cứu lịch sử chứng từ và các góc nhìn phân tích hiện có.",
        "note": "Các truy vấn, PDF và thao tác chứng từ tiếp tục dùng implementation cũ.",
        "tone": "info",
    },
    "admin": {
        "tab": "tab_mobile",
        "title": "Quản trị hệ thống & LAN",
        "subtitle": "Điều khiển dịch vụ truy cập nội bộ và các công cụ quản trị vận hành.",
        "note": "LAN/mobile chỉ nên dùng trong mạng tin cậy; xác thực và server lifecycle không đổi ở batch UI này.",
        "tone": "warning",
    },
}


class SupportFinalUiMixin:
    """Decorate support pages after their legacy builders create real widgets."""

    def build_temp_log_tab(self):
        super().build_temp_log_tab()
        self._decorate_support_workspace("temp")

    def build_backup_tab(self):
        super().build_backup_tab()
        self._decorate_support_workspace("data")

    def build_advanced_reports_tab(self):
        super().build_advanced_reports_tab()
        self._decorate_support_workspace("advanced")

    def build_mobile_tab(self):
        super().build_mobile_tab()
        self._decorate_support_workspace("admin")

    def _decorate_support_workspace(self, key):
        spec = SUPPORT_WORKSPACES[key]
        root = getattr(self, spec["tab"])
        children = list(root.winfo_children())

        banner = tk.Frame(
            root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        title_row = tk.Frame(banner, bg=COLORS["surface"])
        title_row.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(
            title_row,
            text=spec["title"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["headline"],
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_row,
            text=spec["subtitle"],
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["body"],
            anchor="w",
        ).pack(anchor="w", pady=(1, 6))

        tone = spec["tone"]
        tone_bg = COLORS[f"{tone}_bg"]
        tone_fg = COLORS[tone]
        tone_border = COLORS[f"{tone}_border"]
        callout = tk.Frame(
            banner,
            bg=tone_bg,
            highlightbackground=tone_border,
            highlightthickness=1,
        )
        callout.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(
            callout,
            text=spec["note"],
            bg=tone_bg,
            fg=tone_fg,
            font=TYPOGRAPHY["compact"],
            anchor="w",
        ).pack(fill="x", padx=9, pady=6)

        # Every legacy support builder currently uses pack on its root. Insert
        # the banner before the first legacy child so functionality/layout stays
        # otherwise untouched. Desktop UI smoke protects this assumption.
        if children:
            banner.pack(fill="x", padx=8, pady=(8, 6), before=children[0])
        else:
            banner.pack(fill="x", padx=8, pady=(8, 6))

        if not hasattr(self, "support_workspace_headers"):
            self.support_workspace_headers = {}
        self.support_workspace_headers[key] = banner
