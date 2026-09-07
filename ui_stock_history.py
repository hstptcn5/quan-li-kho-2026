# -*- coding: utf-8 -*-
"""Stitch-aligned FEFO stock, document history and stored-document preview.

UI-4 is presentation/read-only.  It reads existing inventory/purchase/dispatch
records and delegates PDF reprint actions to the legacy hardened methods.
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as tb

from date_utils import format_date_display, format_datetime_display
from ui_design import COLORS, TYPOGRAPHY


STOCK_WARNING_DAYS = 90


def _as_date(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def build_stock_snapshot(inventory_rows, *, today=None, warning_days=STOCK_WARNING_DAYS):
    """Build a deterministic FEFO display model from fund-separated balances."""
    today = today or dt.date.today()
    warning_until = today + dt.timedelta(days=int(warning_days))
    rows = []
    physical_lots = set()
    products = set()
    expired_lots = set()
    near_lots = set()

    for raw in inventory_rows or []:
        row = dict(raw)
        stock = float(row.get("stockBase") or 0)
        if stock <= 0:
            continue

        product_id = row.get("productId")
        batch_id = row.get("batchId")
        lot_key = (product_id, batch_id)
        expiry = _as_date(row.get("expiryDate"))
        status = "Còn hạn"
        status_key = "ok"
        severity = 3
        days_left = None

        if expiry is None:
            status = "Chưa có HSD"
            status_key = "unknown"
            severity = 2
        else:
            days_left = (expiry - today).days
            if expiry < today:
                status = "Đã hết hạn"
                status_key = "expired"
                severity = 0
                expired_lots.add(lot_key)
            elif expiry <= warning_until:
                status = "Hết hạn hôm nay" if days_left == 0 else f"Cận hạn {days_left} ngày"
                status_key = "near"
                severity = 1
                near_lots.add(lot_key)

        products.add(product_id)
        physical_lots.add(lot_key)
        rows.append({
            "productId": product_id,
            "batchId": batch_id,
            "productName": row.get("productName") or "",
            "lotNo": row.get("lotNo") or "",
            "expiryDate": row.get("expiryDate") or "",
            "fundSource": row.get("fundSource") or "",
            "stockBase": stock,
            "status": status,
            "statusKey": status_key,
            "daysLeft": days_left,
            "severity": severity,
        })

    rows.sort(key=lambda item: (
        item["severity"],
        _as_date(item.get("expiryDate")) or dt.date.max,
        str(item.get("productName") or "").lower(),
        str(item.get("fundSource") or "").lower(),
    ))
    return {
        "rows": rows,
        "product_count": len(products),
        "physical_lot_count": len(physical_lots),
        "fund_balance_count": len(rows),
        "expired_lot_count": len(expired_lots),
        "near_lot_count": len(near_lots),
    }


class StockHistoryUiMixin:
    """Replace only the stock page and its refresh presentation."""

    def build_stock_tab(self):
        root = self.tab_stock
        header = tk.Frame(root, bg=COLORS["canvas"])
        header.pack(fill="x", padx=8, pady=(8, 6))
        tk.Label(
            header,
            text="Tồn kho (FEFO)",
            bg=COLORS["canvas"],
            fg=COLORS["text"],
            font=TYPOGRAPHY["headline"],
        ).pack(side="left")
        tk.Label(
            header,
            text="Theo dõi số dư theo lô, HSD và nguồn kinh phí • xem lại chứng từ đã lưu",
            bg=COLORS["canvas"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
        ).pack(side="left", padx=(12, 0), pady=(4, 0))
        tb.Button(
            header,
            text="↻  Tải lại",
            style="Shell.Secondary.TButton",
            command=self.refresh_stock,
        ).pack(side="right")

        self.stock_metric_labels = {}
        metrics = tk.Frame(root, bg=COLORS["canvas"])
        metrics.pack(fill="x", padx=8, pady=(0, 7))
        for key, title, subtitle, tone in (
            ("product_count", "MẶT HÀNG CÒN TỒN", "Có số dư dương", "neutral"),
            ("physical_lot_count", "LÔ ĐANG TỒN", "Không lặp theo nguồn", "success"),
            ("near_lot_count", "CẬN HẠN ≤90 NGÀY", "Ưu tiên FEFO", "warning"),
            ("expired_lot_count", "LÔ ĐÃ HẾT HẠN", "Cần xử lý nghiệp vụ", "danger"),
        ):
            card, value = self._stock_metric_card(metrics, title, subtitle, tone)
            card.pack(side="left", fill="x", expand=True, padx=3)
            self.stock_metric_labels[key] = value

        self.stock_workspace_nb = tb.Notebook(root)
        self.stock_workspace_nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.stock_current_tab = tk.Frame(self.stock_workspace_nb, bg=COLORS["canvas"])
        self.stock_purchase_tab = tk.Frame(self.stock_workspace_nb, bg=COLORS["canvas"])
        self.stock_dispatch_tab = tk.Frame(self.stock_workspace_nb, bg=COLORS["canvas"])
        self.stock_workspace_nb.add(self.stock_current_tab, text="Tồn hiện tại")
        self.stock_workspace_nb.add(self.stock_purchase_tab, text="Phiếu nhập")
        self.stock_workspace_nb.add(self.stock_dispatch_tab, text="Phiếu xuất")

        self._build_current_stock_view(self.stock_current_tab)
        self._build_purchase_history_view(self.stock_purchase_tab)
        self._build_dispatch_history_view(self.stock_dispatch_tab)
        self.refresh_stock()

    def _stock_metric_card(self, parent, title, subtitle, tone):
        palette = {
            "neutral": (COLORS["surface"], COLORS["border"], COLORS["text"]),
            "success": (COLORS["success_bg"], COLORS["success_border"], COLORS["success"]),
            "warning": (COLORS["warning_bg"], COLORS["warning_border"], COLORS["warning"]),
            "danger": (COLORS["danger_bg"], COLORS["danger_border"], COLORS["danger"]),
        }
        bg, border, accent = palette[tone]
        card = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1, height=78)
        card.pack_propagate(False)
        tk.Label(card, text=title, bg=bg, fg=accent, font=TYPOGRAPHY["badge"], anchor="w").pack(fill="x", padx=10, pady=(7, 0))
        value = tk.Label(card, text="0", bg=bg, fg=COLORS["text"], font=TYPOGRAPHY["display"], anchor="w")
        value.pack(fill="x", padx=10, pady=(1, 0))
        tk.Label(card, text=subtitle, bg=bg, fg=COLORS["text_muted"], font=TYPOGRAPHY["compact"], anchor="w").pack(fill="x", padx=10, pady=(0, 6))
        return card, value

    def _build_current_stock_view(self, parent):
        controls = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        controls.pack(fill="x", pady=(0, 6))
        tk.Label(controls, text="Tìm tên / số lô", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).pack(side="left", padx=(10, 5), pady=8)
        self.stock_search = tb.Entry(controls, width=28)
        self.stock_search.pack(side="left", padx=(0, 10), pady=6)
        self.stock_search.bind("<KeyRelease>", lambda event: self._render_stock_rows())

        tk.Label(controls, text="Nguồn", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).pack(side="left", padx=(0, 5), pady=8)
        self.stock_fund_filter = tb.Combobox(controls, state="readonly", width=24)
        self.stock_fund_filter.pack(side="left", padx=(0, 10), pady=6)
        self.stock_fund_filter.bind("<<ComboboxSelected>>", lambda event: self._render_stock_rows())

        tk.Label(controls, text="Trạng thái", bg=COLORS["surface"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["compact"]).pack(side="left", padx=(0, 5), pady=8)
        self.stock_status_filter = tb.Combobox(
            controls,
            state="readonly",
            width=18,
            values=["Tất cả", "Còn hạn", "Cận hạn", "Đã hết hạn", "Chưa có HSD"],
        )
        self.stock_status_filter.set("Tất cả")
        self.stock_status_filter.pack(side="left", padx=(0, 10), pady=6)
        self.stock_status_filter.bind("<<ComboboxSelected>>", lambda event: self._render_stock_rows())

        self.stock_count_label = tk.Label(
            controls,
            text="Hiển thị 0 / 0 số dư tồn",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=TYPOGRAPHY["compact"],
        )
        self.stock_count_label.pack(side="right", padx=10, pady=8)

        table = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        table.pack(fill="both", expand=True)
        cols = ("pid", "batch", "product", "lot", "exp", "fund", "qty", "status")
        self.tree_stock2 = tb.Treeview(
            table,
            columns=cols,
            displaycolumns=("product", "lot", "exp", "fund", "qty", "status"),
            show="headings",
        )
        for key, width, title, anchor in (
            ("pid", 55, "PID", "center"),
            ("batch", 65, "BATCH", "center"),
            ("product", 280, "TÊN THUỐC / VACCINE / VTYT", "w"),
            ("lot", 100, "SỐ LÔ", "center"),
            ("exp", 105, "HẠN SỬ DỤNG", "center"),
            ("fund", 170, "NGUỒN KINH PHÍ", "w"),
            ("qty", 95, "TỒN (BASE)", "e"),
            ("status", 135, "TRẠNG THÁI", "center"),
        ):
            self.tree_stock2.heading(key, text=title, command=lambda col=key: self.sort_tree(self.tree_stock2, col))
            self.tree_stock2.column(key, width=width, anchor=anchor, stretch=(key in {"product", "fund"}))
        self.tree_stock2.tag_configure("expired", background=COLORS["danger_bg"], foreground=COLORS["danger"])
        self.tree_stock2.tag_configure("near", background=COLORS["warning_bg"], foreground=COLORS["text"])
        self.tree_stock2.tag_configure("unknown", background=COLORS["surface_subdued"])
        self.tree_stock2.pack(fill="both", expand=True, padx=1, pady=1)

    def _build_purchase_history_view(self, parent):
        split = tk.PanedWindow(parent, orient="horizontal", sashwidth=5, bg=COLORS["canvas"], bd=0)
        split.pack(fill="both", expand=True)
        left = self._history_list_panel(split, "PHIẾU NHẬP GẦN ĐÂY")
        right = self._history_preview_panel(split, "XEM TRƯỚC PHIẾU NHẬP", "purchase")
        split.add(left, minsize=520, stretch="always")
        split.add(right, minsize=410, stretch="always")

        self.purchase_history_search = tb.Entry(left)
        self.purchase_history_search.pack(fill="x", padx=8, pady=(8, 6))
        self.purchase_history_search.insert(0, "")
        self.purchase_history_search.bind("<KeyRelease>", lambda event: self._render_purchase_history())

        cols = ("id", "number", "date", "supplier", "reason", "items")
        self.purchase_history_tree = tb.Treeview(left, columns=cols, displaycolumns=("number", "date", "supplier", "reason", "items"), show="headings")
        for key, width, title, anchor in (
            ("id", 50, "ID", "center"),
            ("number", 135, "SỐ PHIẾU", "center"),
            ("date", 125, "NGÀY NHẬP", "center"),
            ("supplier", 210, "NGUỒN CẤP / NHÀ CC", "w"),
            ("reason", 155, "LÝ DO", "w"),
            ("items", 70, "DÒNG", "e"),
        ):
            self.purchase_history_tree.heading(key, text=title)
            self.purchase_history_tree.column(key, width=width, anchor=anchor, stretch=(key in {"supplier", "reason"}))
        self.purchase_history_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.purchase_history_tree.bind("<<TreeviewSelect>>", lambda event: self._preview_selected_purchase())
        self.purchase_history_tree.bind("<Double-1>", lambda event: self._preview_selected_purchase())

    def _build_dispatch_history_view(self, parent):
        split = tk.PanedWindow(parent, orient="horizontal", sashwidth=5, bg=COLORS["canvas"], bd=0)
        split.pack(fill="both", expand=True)
        left = self._history_list_panel(split, "PHIẾU XUẤT GẦN ĐÂY")
        right = self._history_preview_panel(split, "XEM TRƯỚC PHIẾU XUẤT", "dispatch")
        split.add(left, minsize=520, stretch="always")
        split.add(right, minsize=410, stretch="always")

        self.dispatch_history_search = tb.Entry(left)
        self.dispatch_history_search.pack(fill="x", padx=8, pady=(8, 6))
        self.dispatch_history_search.bind("<KeyRelease>", lambda event: self._render_dispatch_history())

        cols = ("id", "number", "date", "unit", "reason", "items")
        self.dispatch_history_tree = tb.Treeview(left, columns=cols, displaycolumns=("number", "date", "unit", "reason", "items"), show="headings")
        for key, width, title, anchor in (
            ("id", 50, "ID", "center"),
            ("number", 135, "SỐ PHIẾU", "center"),
            ("date", 125, "NGÀY XUẤT", "center"),
            ("unit", 210, "ĐƠN VỊ NHẬN", "w"),
            ("reason", 155, "LÝ DO", "w"),
            ("items", 70, "DÒNG", "e"),
        ):
            self.dispatch_history_tree.heading(key, text=title)
            self.dispatch_history_tree.column(key, width=width, anchor=anchor, stretch=(key in {"unit", "reason"}))
        self.dispatch_history_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.dispatch_history_tree.bind("<<TreeviewSelect>>", lambda event: self._preview_selected_dispatch())
        self.dispatch_history_tree.bind("<Double-1>", lambda event: self._preview_selected_dispatch())

    def _history_list_panel(self, parent, title):
        frame = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(frame, text=title, bg=COLORS["surface_subdued"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["badge"], anchor="w").pack(fill="x", padx=0, pady=0, ipadx=8, ipady=6)
        return frame

    def _history_preview_panel(self, parent, title, kind):
        frame = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(frame, text=title, bg=COLORS["surface_subdued"], fg=COLORS["text_subtle"], font=TYPOGRAPHY["badge"], anchor="w").pack(fill="x", ipadx=8, ipady=6)

        meta = tk.Label(
            frame,
            text="Chọn một phiếu để xem chi tiết đã lưu.",
            bg=COLORS["surface"],
            fg=COLORS["text_subtle"],
            font=TYPOGRAPHY["compact"],
            justify="left",
            anchor="nw",
        )
        meta.pack(fill="x", padx=10, pady=9)

        cols = ("product", "lot", "exp", "fund", "unit", "qty", "amount")
        tree = tb.Treeview(frame, columns=cols, show="headings", height=9)
        for key, width, label, anchor in (
            ("product", 190, "HÀNG HÓA", "w"),
            ("lot", 80, "LÔ", "center"),
            ("exp", 90, "HSD", "center"),
            ("fund", 130, "NGUỒN", "w"),
            ("unit", 55, "ĐVT", "center"),
            ("qty", 65, "SL", "e"),
            ("amount", 95, "THÀNH TIỀN", "e"),
        ):
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=anchor, stretch=(key in {"product", "fund"}))
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        actions = tk.Frame(frame, bg=COLORS["surface"])
        actions.pack(fill="x", padx=8, pady=(0, 8))
        if kind == "purchase":
            self.purchase_preview_meta = meta
            self.purchase_preview_tree = tree
            self.purchase_reprint_button = tb.Button(actions, text="In lại PDF", style="Shell.Primary.TButton", command=self._reprint_preview_purchase, state="disabled")
            self.purchase_reprint_button.pack(side="right")
            tb.Button(actions, text="Lập phiếu nhập mới", style="Shell.Secondary.TButton", command=lambda: self.nb.select(self.tab_purchase)).pack(side="right", padx=(0, 6))
        else:
            self.dispatch_preview_meta = meta
            self.dispatch_preview_tree = tree
            self.dispatch_reprint_button = tb.Button(actions, text="In lại PDF", style="Shell.Primary.TButton", command=self._reprint_preview_dispatch, state="disabled")
            self.dispatch_reprint_button.pack(side="right")
            tb.Button(actions, text="Lập phiếu xuất mới", style="Shell.Secondary.TButton", command=lambda: self.nb.select(self.tab_dispatch)).pack(side="right", padx=(0, 6))
        return frame

    def refresh_stock(self):
        """Refresh FEFO balances and recent documents without changing inventory."""
        try:
            self._stock_snapshot = build_stock_snapshot(self.db.get_inventory())
            for key, label in getattr(self, "stock_metric_labels", {}).items():
                label.config(text=f"{self._stock_snapshot.get(key, 0):,}")

            funds = sorted({row.get("fundSource") or "" for row in self._stock_snapshot["rows"]})
            if hasattr(self, "stock_fund_filter"):
                current = self.stock_fund_filter.get() or "Tất cả"
                options = ["Tất cả"] + [(fund or "(Không ghi nguồn)") for fund in funds]
                self.stock_fund_filter["values"] = options
                self.stock_fund_filter.set(current if current in options else "Tất cả")
            self._render_stock_rows()
            self._refresh_stock_document_history()
        except Exception as exc:
            try:
                messagebox.showerror("Lỗi", f"Không thể tải tồn kho: {exc}")
            except Exception:
                print(f"Không thể tải tồn kho: {exc}")

    def _render_stock_rows(self):
        if not hasattr(self, "tree_stock2"):
            return
        snapshot = getattr(self, "_stock_snapshot", {"rows": []})
        keyword = (self.stock_search.get() or "").strip().lower() if hasattr(self, "stock_search") else ""
        fund_filter = self.stock_fund_filter.get() if hasattr(self, "stock_fund_filter") else "Tất cả"
        status_filter = self.stock_status_filter.get() if hasattr(self, "stock_status_filter") else "Tất cả"

        for item in self.tree_stock2.get_children():
            self.tree_stock2.delete(item)

        visible = []
        for row in snapshot.get("rows", []):
            haystack = f"{row.get('productName','')} {row.get('lotNo','')}".lower()
            if keyword and keyword not in haystack:
                continue
            display_fund = row.get("fundSource") or "(Không ghi nguồn)"
            if fund_filter and fund_filter != "Tất cả" and fund_filter != display_fund:
                continue
            status_key = row.get("statusKey")
            if status_filter == "Còn hạn" and status_key != "ok":
                continue
            if status_filter == "Cận hạn" and status_key != "near":
                continue
            if status_filter == "Đã hết hạn" and status_key != "expired":
                continue
            if status_filter == "Chưa có HSD" and status_key != "unknown":
                continue
            visible.append(row)
            self.tree_stock2.insert("", "end", values=(
                row.get("productId") or "",
                row.get("batchId") or "",
                row.get("productName") or "",
                row.get("lotNo") or "",
                format_date_display(row.get("expiryDate")),
                display_fund,
                f"{float(row.get('stockBase') or 0):g}",
                row.get("status") or "",
            ), tags=(status_key,))

        if hasattr(self, "stock_count_label"):
            self.stock_count_label.config(text=f"Hiển thị {len(visible)} / {len(snapshot.get('rows', []))} số dư tồn")

    def _refresh_stock_document_history(self):
        self._purchase_history_rows = self.db.get_purchase_notes() if hasattr(self.db, "get_purchase_notes") else []
        self._dispatch_history_rows = self.db.get_dispatch_notes() if hasattr(self.db, "get_dispatch_notes") else []
        self._render_purchase_history()
        self._render_dispatch_history()

    def _render_purchase_history(self):
        if not hasattr(self, "purchase_history_tree"):
            return
        keyword = (self.purchase_history_search.get() or "").strip().lower() if hasattr(self, "purchase_history_search") else ""
        for item in self.purchase_history_tree.get_children():
            self.purchase_history_tree.delete(item)
        for row in getattr(self, "_purchase_history_rows", []):
            haystack = f"{row.get('noteNumber','')} {row.get('supplier','')} {row.get('reason','')} {row.get('note','')}".lower()
            if keyword and keyword not in haystack:
                continue
            self.purchase_history_tree.insert("", "end", values=(
                row.get("id"),
                row.get("noteNumber") or "",
                format_datetime_display(row.get("createdAt")),
                row.get("supplier") or "",
                row.get("reason") or "",
                row.get("item_count") or 0,
            ))

    def _render_dispatch_history(self):
        if not hasattr(self, "dispatch_history_tree"):
            return
        keyword = (self.dispatch_history_search.get() or "").strip().lower() if hasattr(self, "dispatch_history_search") else ""
        for item in self.dispatch_history_tree.get_children():
            self.dispatch_history_tree.delete(item)
        for row in getattr(self, "_dispatch_history_rows", []):
            haystack = f"{row.get('noteNumber','')} {row.get('receivingUnit','')} {row.get('reason','')} {row.get('note','')}".lower()
            if keyword and keyword not in haystack:
                continue
            self.dispatch_history_tree.insert("", "end", values=(
                row.get("id"),
                row.get("noteNumber") or "",
                format_datetime_display(row.get("createdAt")),
                row.get("receivingUnit") or "",
                row.get("reason") or "",
                row.get("item_count") or 0,
            ))

    def _preview_selected_purchase(self):
        selection = self.purchase_history_tree.selection()
        if not selection:
            return
        purchase_id = int(self.purchase_history_tree.item(selection[0])["values"][0])
        note = next((row for row in getattr(self, "_purchase_history_rows", []) if int(row.get("id") or 0) == purchase_id), None)
        details = self.db.get_purchase_detail(purchase_id)
        self._stock_selected_purchase_id = purchase_id
        if note:
            self.purchase_preview_meta.config(text=(
                f"Số phiếu: {note.get('noteNumber') or '-'}\n"
                f"Ngày nhập: {format_datetime_display(note.get('createdAt'))}\n"
                f"Nguồn cấp/Nhà CC: {note.get('supplier') or '-'}\n"
                f"Lý do: {note.get('reason') or '-'}\n"
                f"Ghi chú: {note.get('note') or '-'}"
            ))
        self._fill_document_preview(self.purchase_preview_tree, details)
        self.purchase_reprint_button.config(state="normal")

    def _preview_selected_dispatch(self):
        selection = self.dispatch_history_tree.selection()
        if not selection:
            return
        dispatch_id = int(self.dispatch_history_tree.item(selection[0])["values"][0])
        note = next((row for row in getattr(self, "_dispatch_history_rows", []) if int(row.get("id") or 0) == dispatch_id), None)
        details = self.db.get_dispatch_detail(dispatch_id)
        self._stock_selected_dispatch_id = dispatch_id
        if note:
            self.dispatch_preview_meta.config(text=(
                f"Số phiếu: {note.get('noteNumber') or '-'}\n"
                f"Ngày xuất: {format_datetime_display(note.get('createdAt'))}\n"
                f"Đơn vị nhận: {note.get('receivingUnit') or '-'}\n"
                f"Lý do: {note.get('reason') or '-'}\n"
                f"Ghi chú: {note.get('note') or '-'}"
            ))
        self._fill_document_preview(self.dispatch_preview_tree, details)
        self.dispatch_reprint_button.config(state="normal")

    def _fill_document_preview(self, tree, details):
        for item in tree.get_children():
            tree.delete(item)
        for row in details or []:
            amount = row.get("totalAmount")
            if amount is None:
                amount = float(row.get("qty") or 0) * float(row.get("cost") or 0)
            tree.insert("", "end", values=(
                row.get("productName") or "",
                row.get("lotNo") or "",
                format_date_display(row.get("expiryDate")),
                row.get("fundSource") or "",
                row.get("unitCode") or "",
                f"{float(row.get('qty') or 0):g}",
                f"{float(amount or 0):,.0f}",
            ))

    def _reprint_preview_purchase(self):
        purchase_id = getattr(self, "_stock_selected_purchase_id", None)
        if purchase_id is not None:
            self.reprint_selected_purchase(purchase_id)

    def _reprint_preview_dispatch(self):
        dispatch_id = getattr(self, "_stock_selected_dispatch_id", None)
        if dispatch_id is not None:
            self.reprint_selected_dispatch(dispatch_id)
