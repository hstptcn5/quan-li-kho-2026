# -*- coding: utf-8 -*-
import inspect
import unittest

from ui_support_final import SUPPORT_WORKSPACES, SupportFinalUiMixin


class SupportFinalUiTests(unittest.TestCase):
    def test_all_remaining_support_workspaces_are_covered(self):
        self.assertEqual(set(SUPPORT_WORKSPACES), {"temp", "data", "advanced", "admin"})

    def test_wrappers_delegate_to_legacy_builders(self):
        for name in (
            "build_temp_log_tab",
            "build_backup_tab",
            "build_advanced_reports_tab",
            "build_mobile_tab",
        ):
            source = inspect.getsource(getattr(SupportFinalUiMixin, name))
            self.assertIn("super().", source)
            self.assertIn("_decorate_support_workspace", source)

    def test_presentation_layer_does_not_absorb_support_business_actions(self):
        forbidden = {
            "save_temp_log", "delete_selected_temp_log", "export_temp_log_pdf", "plot_temp_chart",
            "create_manual_backup", "restore_selected_backup", "delete_selected_backup",
            "export_data", "import_data", "start_mobile_server", "stop_mobile_server",
            "show_purchase_history", "show_dispatch_history",
        }
        self.assertFalse(forbidden.intersection(SupportFinalUiMixin.__dict__))


if __name__ == "__main__":
    unittest.main()
