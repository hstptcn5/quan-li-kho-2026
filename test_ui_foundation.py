import unittest

from ui_design import COLORS, LEGACY_HOTKEYS, NAV_ITEMS, SPACING
from ui_shell import ClinicalShellMixin


class UiFoundationTests(unittest.TestCase):
    def test_navigation_targets_are_unique_and_complete(self):
        keys = [item[0] for item in NAV_ITEMS]
        attrs = [item[2] for item in NAV_ITEMS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(attrs), len(set(attrs)))

        required = {
            "tab_operations",
            "tab_products",
            "tab_purchase",
            "tab_dispatch",
            "tab_stock",
            "tab_alerts",
            "tab_report",
            "tab_temp_log",
            "tab_backup",
            "tab_advanced_reports",
            "tab_mobile",
        }
        self.assertEqual(set(attrs), required)

    def test_legacy_shortcuts_keep_existing_workspaces_reachable(self):
        nav_attrs = {item[2] for item in NAV_ITEMS}
        self.assertTrue(set(LEGACY_HOTKEYS.values()).issubset(nav_attrs))
        self.assertEqual(LEGACY_HOTKEYS["F2"], "tab_purchase")
        self.assertEqual(LEGACY_HOTKEYS["F3"], "tab_dispatch")
        self.assertEqual(LEGACY_HOTKEYS["F5"], "tab_stock")

    def test_stitch_baseline_density_tokens_are_locked(self):
        self.assertEqual(COLORS["primary"], "#0D3B66")
        self.assertEqual(COLORS["canvas"], "#F3F6F9")
        self.assertEqual(COLORS["border"], "#D1D9E2")
        self.assertEqual(SPACING["table_row"], 34)
        self.assertEqual(SPACING["input_height"], 32)

    def test_shell_mixin_exposes_navigation_refresh_hook(self):
        self.assertTrue(callable(getattr(ClinicalShellMixin, "on_tab_changed", None)))
        self.assertTrue(callable(getattr(ClinicalShellMixin, "_refresh_shell_runtime_status", None)))


if __name__ == "__main__":
    unittest.main()
