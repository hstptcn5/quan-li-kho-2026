# -*- coding: utf-8 -*-
"""Launch the real desktop app briefly as a CI smoke test.

Run this only as a standalone process. It redirects LOCALAPPDATA before any
application import so the smoke test never touches a developer/user database.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time


def main():
    temp_root = tempfile.mkdtemp(prefix="quan-ly-kho-ui-smoke-")
    os.environ["LOCALAPPDATA"] = temp_root
    os.environ["XDG_DATA_HOME"] = temp_root

    app = None
    try:
        from quanly_xnt import App

        app = App()
        deadline = time.time() + 2.8
        while time.time() < deadline:
            app.update()
            time.sleep(0.02)

        title = str(app.title())
        if "Lỗi khởi tạo" in title:
            raise AssertionError(f"Desktop UI fell back to initialization-error screen: {title}")

        required = [
            "shell_sidebar",
            "shell_header",
            "dashboard_warning_tree",
            "catalog_tree",
            "catalog_search",
            "catalog_create_panel",
            "product_detail_page",
            "tree_purchase_cart",
            "lbl_purchase_cart_total",
            "cmb_supplier",
            "ent_purchase_date",
            "search_purchase",
            "cmb_prod",
            "ent_lot",
            "ent_exp",
            "cmb_item_fund",
            "tree_cart",
            "cmb_receiving_unit",
            "ent_dispatch_date",
            "ent_barcode",
            "search_pos",
            "cmb_prod_pos",
            "cmb_lot_pos",
            "cmb_fund_pos",
            "ent_qty_pos",
            "stock_workspace_nb",
            "stock_current_tab",
            "stock_purchase_tab",
            "stock_dispatch_tab",
            "stock_search",
            "stock_fund_filter",
            "stock_status_filter",
            "tree_stock2",
            "purchase_history_tree",
            "purchase_preview_tree",
            "dispatch_history_tree",
            "dispatch_preview_tree",
        ]
        missing = [name for name in required if not hasattr(app, name)]
        if missing:
            raise AssertionError("Desktop UI smoke missing widgets: " + ", ".join(missing))

        # Exercise the new catalog page and real refresh path on an empty DB.
        app.nb.select(app.tab_products)
        app.refresh_products()
        app.update_idletasks()
        if app.catalog_count_label.cget("text") != "Hiển thị 0 / 0 mặt hàng":
            raise AssertionError("Empty catalog did not render deterministically")

        # Exercise shell search routing after the Notebook reordering in UI-0.
        app.focus_search()
        if app.focus_get() is not app.catalog_search:
            raise AssertionError("Ctrl+F routing did not focus the catalog search field")

        # UI-3 must replace only page construction. The hardened transaction,
        # FEFO, print and validation methods must still come from legacy mixins.
        if app.build_purchase_tab.__func__.__module__ != "ui_transactions":
            raise AssertionError("Purchase page did not resolve to UI-3 presentation mixin")
        if app.build_dispatch_tab.__func__.__module__ != "ui_transactions":
            raise AssertionError("Dispatch page did not resolve to UI-3 presentation mixin")
        if app.confirm_purchase.__func__.__module__ != "ui_purchase":
            raise AssertionError("Purchase transaction logic was unexpectedly overridden")
        if app.confirm_dispatch.__func__.__module__ != "ui_dispatch":
            raise AssertionError("Dispatch transaction logic was unexpectedly overridden")
        if app.update_dispatch_unit_label.__func__.__module__ != "ui_dispatch":
            raise AssertionError("FEFO preview logic was unexpectedly overridden")

        # Both transaction screens must remain reachable and keep Ctrl+F routing.
        app.nb.select(app.tab_purchase)
        app.update_idletasks()
        app.focus_search()
        if app.focus_get() is not app.search_purchase:
            raise AssertionError("Ctrl+F did not focus purchase product search")

        app.nb.select(app.tab_dispatch)
        app.update_idletasks()
        app.focus_search()
        if app.focus_get() is not app.search_pos:
            raise AssertionError("Ctrl+F did not focus dispatch product search")

        # UI-4 owns only the stock/history presentation. PDF reprint remains
        # delegated to the legacy methods in ui.py.
        if app.build_stock_tab.__func__.__module__ != "ui_stock_history":
            raise AssertionError("Stock page did not resolve to UI-4 presentation mixin")
        if app.refresh_stock.__func__.__module__ != "ui_stock_history":
            raise AssertionError("Stock refresh did not resolve to UI-4 presentation mixin")
        if app.reprint_selected_purchase.__func__.__module__ != "ui":
            raise AssertionError("Purchase reprint implementation was unexpectedly replaced")
        if app.reprint_selected_dispatch.__func__.__module__ != "ui":
            raise AssertionError("Dispatch reprint implementation was unexpectedly replaced")

        app.nb.select(app.tab_stock)
        app.refresh_stock()
        app.update_idletasks()
        if app.stock_count_label.cget("text") != "Hiển thị 0 / 0 số dư tồn":
            raise AssertionError("Empty FEFO stock workspace did not render deterministically")
        if app.purchase_history_tree.get_children() or app.dispatch_history_tree.get_children():
            raise AssertionError("Empty document history should not contain rows")

        print("DESKTOP_UI_SMOKE_OK")
    finally:
        if app is not None:
            try:
                app.destroy()
            except Exception:
                pass
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
