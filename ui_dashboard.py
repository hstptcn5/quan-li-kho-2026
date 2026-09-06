# -*- coding: utf-8 -*-
"""Operational dashboard for the approved QUẢN LÝ KHO 2026 desktop UI.

UI-1 is presentation-only: all counts and warnings are derived from existing
inventory, audit, backup and temperature data.  It deliberately does not add
minimum-stock configuration, IoT/device telemetry or other Stitch mock data.
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk

import ttkbootstrap as tb

from date_utils import format_date_display, format_datetime_display
from ui_design import COLORS, TYPOGRAPHY


LOW_STOCK_THRESHOLD = 10.0
WARNING_DAYS = 90


def _parse_iso_date(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def build_dashboard_snapshot(inventory_rows, *, today=None, warning_days=WARNING_DAYS):
    """Build a deterministic display model from current fund-separated stock.

    This helper performs no writes and deliberately keeps fund source visible.
    One warning row represents one product/batch/fund balance, while active-lot
    counts de-duplicate fund splits for the same physical lot.
    """
    today = today or dt.date.today()
    warning_until = today + dt.timedelta(days=int(warning_days))

    positive_rows = []
    active_lots = set()
    near_lots = set()
    expired_lots = set()
    low_keys = set()
    warning_rows = []

    for raw in inventory_rows or []:
        row = dict(raw)
        stock = float(row.get("stockBase") or 0)
        if stock <= 0:
            continue

        product_id = row.get("productId")
        batch_id = row.get("batchId")
        fund = row.get("fundSource") or ""
        lot_key = (product_id, batch_id)
        fund_key = (product_id, batch_id, fund)
        expiry = _parse_iso_date(row.get("expiryDate"))

        active_lots.add(lot_key)
        positive_rows.append(row)

        status = None
        severity = 99
        days_left = None
        if expiry is not None:
            days_left = (expiry - today).days
            if expiry < today:
                status = "Đã hết hạn"
                severity = 0
                expired_lots.add(lot_key)
            elif expiry == today:
                status = "Hết hạn hôm nay"
                severity = 1
                near_lots.add(lot_key)
            elif expiry <= warning_until:
                status = f"Cận hạn {days_left} ngày"
                severity = 2
                near_lots.add(lot_key)

        if stock <= LOW_STOCK_THRESHOLD:
            low_keys.add(fund_key)
            if status is None:
                status = "Tồn thấp ≤10"
                severity = 3

        if status is not None:
            warning_rows.append({
                "productId": product_id,
                "batchId": batch_id,
                "productName": row.get("productName") or "",
                "lotNo": row.get("lotNo") or "",
                "expiryDate": row.get("expiryDate") or "",
                "fundSource": fund,
                "stockBase": stock,
                "status": status,
                "severity": severity,
                "daysLeft": days_left,
            })

    warning_rows.sort(
        key=lambda item: (
            item["severity"],
            _parse_iso_date(item.get("expiryDate")) or dt.date.max,
            str(item.get("productName") or "").lower(),
            str(item.get("fundSource") or "").lower(),
        )
    )

    return {
        "active_lot_count": len(active_lots),
        "near_expiry_count": len(near_lots),
        "expired_count": len(expired_lots),
        "low_stock_count": len(low_keys),
        "warning_rows": warning_rows,
        "positive_rows": positive_rows,
    }


class DashboardUiMixin:
    """Override only the Operations dashboard; history/check tabs stay intact."""

    def _build_dashboard_tab(self):
        root = self.ops_dashboard_tab
        root.configure(padding=0)

        top = tk.Frame(root, bg=COLORS["canvas"])
        top.pack(fill="x", padx=8, pady=(8, 6))
        tk.Label(
            top,
            text="Tổng quan vận hành kho",
            bg=COLORS["canvas"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["headline"],
        ).pack(side="left")
        tk.Label(
            top,
            text="Ưu tiên các việc cần xử lý hôm nay • FEFO theo lô và HSD",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
        ).pack(side="left", padx=(12, 0), pady=(4, 0))
        tb.Button(
            top,
            text="↻  Tải lại",
            style="Shell.Secondary.TButton",
            command=self.refresh_dashboard,
        ).pack(side="right")

        self.dashboard_cards = {}
        cards = tk.Frame(root, bg=COLORS["canvas"])
        cards.pack(fill="x", padx=8, pady=(0, 6))
        for key, title, subtitle, tone in (
            ("product_count", "TỔNG MẶT HÀNG", "Danh mục đang quản lý", "neutral"),
            ("active_lot_count", "TỔNG LÔ ĐANG TỒN", "Lô có số dư dương", "success"),
            ("near_expiry_count", "CẬN HẠN ≤90 NGÀY", "Ưu tiên xuất theo FEFO", "warning"),
            ("expired_count", "LÔ ĐÃ HẾT HẠN", "Cần xử lý nghiệp vụ", "danger"),
            ("low_stock_count", "TỒN THẤP ≤10", "Lô/nguồn cần theo dõi", "warning"),
        ):
            card = self._dashboard_metric_card(cards, title, subtitle, tone)
            card["frame"].pack(side="left", fill="x", expand=True, padx=3)
            self.dashboard_cards[key] = card["value"]

        quick = tk.Frame(
            root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        quick.pack(fill="x", padx=8, pady=(0, 7))
        tk.Label(
            quick,
            text="ϟ  Tác nghiệp nhanh:",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["body_medium"],
        ).pack(side="left", padx=(10, 10), pady=8)
        self._dashboard_route_button(quick, "+ Nhập kho", self.tab_purchase, primary=True).pack(side="left", padx=(0, 6), pady=6)
        self._dashboard_route_button(quick, "− Xuất kho (FEFO)", self.tab_dispatch, primary=True).pack(side="left", padx=(0, 6), pady=6)
        self._dashboard_route_button(quick, "Tra cứu tồn kho", self.tab_stock).pack(side="left", padx=(0, 6), pady=6)
        self._dashboard_route_button(quick, "Lập báo cáo XNT", self.tab_report).pack(side="left", padx=(0, 6), pady=6)

        body = tk.Frame(root, bg=COLORS["canvas"])
        body.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        alerts = self._panel(body, "⚠  CẢNH BÁO CẦN XỬ LÝ TRONG NGÀY")
        alerts.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self._build_warning_table(alerts.content)

        right = tk.Frame(body, bg=COLORS["canvas"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)
        right.grid_columnconfigure(0, weight=1)

        activity = self._panel(right, "↶  HOẠT ĐỘNG GẦN ĐÂY")
        activity.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        self._build_activity_table(activity.content)

        status = self._panel(right, "✓  TRẠNG THÁI VẬN HÀNH")
        status.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._build_runtime_panel(status.content)

        footer = tk.Frame(root, bg=COLORS["canvas"])
        footer.pack(fill="x", padx=8, pady=(0, 8))
        self.dashboard_warning_summary = tk.Label(
            footer,
            text="-",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        )
        self.dashboard_warning_summary.pack(side="left")
        tk.Label(
            footer,
            text="Ngưỡng tồn thấp trên dashboard hiện là ≤10 đơn vị cơ sở; không phải định mức kho cấu hình.",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
            anchor="e",
        ).pack(side="right")

        self.refresh_dashboard()

    def _dashboard_metric_card(self, parent, title, subtitle, tone):
        palettes = {
            "neutral": (COLORS["surface"], COLORS["border"], COLORS["text"]),
            "success": (COLORS["success_bg"], COLORS["success_border"], COLORS["success"]),
            "warning": (COLORS["warning_bg"], COLORS["warning_border"], COLORS["warning"]),
            "danger": (COLORS["danger_bg"], COLORS["danger_border"], COLORS["danger"]),
        }
        bg, border, accent = palettes[tone]
        frame = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1, height=94)
        frame.pack_propagate(False)
        tk.Label(frame, text=title, bg=bg, fg=accent, font=TYPOGRAPHY["badge"], anchor="w").pack(fill="x", padx=10, pady=(8, 0))
        value = tk.Label(frame, text="0", bg=bg, fg=COLORS["text"], font=TYPOGRAPHY["display"], anchor="w")
        value.pack(fill="x", padx=10, pady=(4, 0))
        tk.Label(frame, text=subtitle, bg=bg, fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"], anchor="w").pack(fill="x", padx=10, pady=(1, 7))
        return {"frame": frame, "value": value}

    def _dashboard_route_button(self, parent, text, target, primary=False):
        return tb.Button(
            parent,
            text=text,
            style="Shell.Primary.TButton" if primary else "Shell.Secondary.TButton",
            command=lambda: self.nb.select(target),
        )

    class _PanelProxy:
        pass

    def _panel(self, parent, title):
        outer = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        header = tk.Frame(outer, bg=COLORS["surface"])
        header.pack(fill="x")
        tk.Label(
            header,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["body_medium"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=8)
        tk.Frame(outer, bg=COLORS["border_soft"], height=1).pack(fill="x")
        content = tk.Frame(outer, bg=COLORS["surface"])
        content.pack(fill="both", expand=True)
        proxy = self._PanelProxy()
        proxy.grid = outer.grid
        proxy.pack = outer.pack
        proxy.content = content
        proxy.frame = outer
        return proxy

    def _build_warning_table(self, parent):
        columns = ("product", "lot", "exp", "stock", "fund", "status")
        tree = tb.Treeview(parent, columns=columns, show="headings", height=12)
        specs = (
            ("product", 245, "MÃ & TÊN THUỐC - VẬT TƯ", "w"),
            ("lot", 82, "SỐ LÔ", "center"),
            ("exp", 95, "HẠN SỬ DỤNG", "center"),
            ("stock", 72, "TỒN", "e"),
            ("fund", 110, "NGUỒN KINH PHÍ", "w"),
            ("status", 125, "TRẠNG THÁI", "center"),
        )
        for key, width, label, anchor in specs:
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=anchor, stretch=(key in {"product", "fund"}))
        tree.tag_configure("expired", background=COLORS["danger_bg"], foreground=COLORS["danger"])
        tree.tag_configure("near", background="#FFF9E8")
        tree.tag_configure("low", background=COLORS["surface"])
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.dashboard_warning_tree = tree

    def _build_activity_table(self, parent):
        columns = ("time", "action", "detail")
        tree = tb.Treeview(parent, columns=columns, show="headings", height=7)
        tree.heading("time", text="THỜI GIAN")
        tree.heading("action", text="TÁC VỤ")
        tree.heading("detail", text="CHI TIẾT")
        tree.column("time", width=95, anchor="center", stretch=False)
        tree.column("action", width=115, anchor="w", stretch=False)
        tree.column("detail", width=190, anchor="w", stretch=True)
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.dashboard_activity_tree = tree

    def _build_runtime_panel(self, parent):
        wrap = tk.Frame(parent, bg=COLORS["surface"], padx=10, pady=8)
        wrap.pack(fill="both", expand=True)
        self.dashboard_backup_label = tk.Label(
            wrap,
            text="Sao lưu: -",
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
            justify="left",
        )
        self.dashboard_backup_label.pack(fill="x", pady=(0, 5))
        self.dashboard_temp_label = tk.Label(
            wrap,
            text="Nhiệt độ & độ ẩm: chưa có bản ghi",
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
            justify="left",
            wraplength=300,
        )
        self.dashboard_temp_label.pack(fill="x", pady=(0, 5))
        self.dashboard_integrity_label = tk.Label(
            wrap,
            text="Dữ liệu tồn kho: -",
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["compact"],
            anchor="w",
        )
        self.dashboard_integrity_label.pack(fill="x")

    def refresh_dashboard(self):
        try:
            summary = self.db.dashboard_summary(WARNING_DAYS)
            inventory = self.db.get_inventory()
            snapshot = build_dashboard_snapshot(inventory, warning_days=WARNING_DAYS)

            values = {
                "product_count": int(summary.get("product_count") or 0),
                "active_lot_count": snapshot["active_lot_count"],
                "near_expiry_count": snapshot["near_expiry_count"],
                "expired_count": snapshot["expired_count"],
                "low_stock_count": snapshot["low_stock_count"],
            }
            for key, label in self.dashboard_cards.items():
                label.config(text=f"{values.get(key, 0):,}".replace(",", "."))

            self._fill_dashboard_warning_rows(snapshot["warning_rows"][:80])
            self._fill_dashboard_activity()
            self._refresh_dashboard_runtime(summary, snapshot)

            total_warnings = len(snapshot["warning_rows"])
            self.dashboard_warning_summary.config(
                text=(
                    f"{total_warnings} dòng cần chú ý • "
                    f"{snapshot['expired_count']} lô hết hạn • "
                    f"{snapshot['near_expiry_count']} lô cận hạn • "
                    f"{snapshot['low_stock_count']} lô/nguồn tồn thấp"
                )
            )
        except Exception as exc:
            # The dashboard is informational. A refresh problem must not take
            # down purchase/dispatch workflows or the rest of the application.
            try:
                self.status.config(text=f"Không thể tải Tổng quan: {exc}")
            except Exception:
                print(f"Không thể tải Tổng quan: {exc}")

    def _fill_dashboard_warning_rows(self, rows):
        tree = self.dashboard_warning_tree
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            severity = int(row.get("severity", 99))
            tag = "expired" if severity <= 1 else "near" if severity == 2 else "low"
            product_display = row.get("productName") or ""
            if row.get("productId") is not None:
                product_display = f"#{row['productId']}  {product_display}"
            tree.insert(
                "",
                "end",
                values=(
                    product_display,
                    row.get("lotNo") or "",
                    format_date_display(row.get("expiryDate")),
                    f"{float(row.get('stockBase') or 0):g}",
                    row.get("fundSource") or "(không rõ)",
                    row.get("status") or "",
                ),
                tags=(tag,),
            )

    def _fill_dashboard_activity(self):
        tree = self.dashboard_activity_tree
        for item in tree.get_children():
            tree.delete(item)
        try:
            rows = self.db.q(
                "SELECT timestamp, action, details, ip FROM audit_logs "
                "ORDER BY datetime(timestamp) DESC, id DESC LIMIT 10"
            )
        except Exception:
            rows = []
        for row in rows:
            when = format_datetime_display(row.get("timestamp"))
            tree.insert(
                "",
                "end",
                values=(when, row.get("action") or "", row.get("details") or ""),
            )
        if not rows:
            tree.insert("", "end", values=("-", "Chưa có", "Chưa có hoạt động được ghi nhận"))

    def _refresh_dashboard_runtime(self, summary, snapshot):
        backup = summary.get("last_backup")
        if backup:
            self.dashboard_backup_label.config(
                text=f"✓ Sao lưu gần nhất: {format_datetime_display(backup.get('created'))}\n  {backup.get('file') or ''}",
                fg=COLORS["success"],
            )
        else:
            self.dashboard_backup_label.config(text="! Chưa có bản sao lưu", fg=COLORS["warning"])

        try:
            latest = self.db.q(
                "SELECT logDate, session, locationName, temperature, humidity, recordedBy "
                "FROM temperature_logs ORDER BY DATE(logDate) DESC, id DESC LIMIT 1"
            )
        except Exception:
            latest = []
        if latest:
            row = latest[0]
            humidity = row.get("humidity")
            humidity_text = f" • {float(humidity):g}%" if humidity is not None else ""
            self.dashboard_temp_label.config(
                text=(
                    f"Nhiệt độ gần nhất: {float(row.get('temperature') or 0):g}°C{humidity_text}\n"
                    f"{row.get('locationName') or ''} • {format_date_display(row.get('logDate'))} • {row.get('session') or ''}"
                ),
                fg=COLORS["text_subtle"],
            )
        else:
            self.dashboard_temp_label.config(text="Nhiệt độ & độ ẩm: chưa có bản ghi", fg=COLORS["text_muted"])

        negative_count = len([
            row for row in snapshot.get("positive_rows", [])
            if float(row.get("stockBase") or 0) < -0.0001
        ])
        # positive_rows intentionally excludes non-positive balances, so this is
        # normally zero. Keep the text explicit rather than claiming a DB check.
        if negative_count == 0:
            self.dashboard_integrity_label.config(text="✓ Không hiển thị dòng tồn âm trong tồn khả dụng", fg=COLORS["success"])
        else:
            self.dashboard_integrity_label.config(text=f"! Phát hiện {negative_count} dòng tồn âm", fg=COLORS["danger"])
