# -*- coding: utf-8 -*-
"""Launch the real desktop app briefly as a CI smoke test.

Run this only as a standalone process.  It redirects LOCALAPPDATA before any
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
        deadline = time.time() + 2.5
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
