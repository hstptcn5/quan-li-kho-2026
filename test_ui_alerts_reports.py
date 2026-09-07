# -*- coding: utf-8 -*-
import unittest

from ui_alerts_reports import (
    ALERT_WIDGET_CONTRACT,
    REPORT_WIDGET_CONTRACT,
    AlertsReportsUiMixin,
)


class AlertsReportsUiContractTests(unittest.TestCase):
    def test_alert_widget_contract_is_complete(self):
        self.assertEqual(ALERT_WIDGET_CONTRACT, ("ent_warn_days", "tree_alerts"))

    def test_report_widget_contract_is_complete(self):
        self.assertEqual(
            REPORT_WIDGET_CONTRACT,
            ("de_from", "de_to", "cmb_report_fund", "tree_report"),
        )

    def test_presentation_mixin_does_not_take_business_ownership(self):
        forbidden = {
            "refresh_alerts",
            "refresh_report",
            "refresh_report_funds_combo",
            "export_report_csv",
            "export_report_excel",
            "export_report_pdf",
            "print_inventory_check_pdf",
        }
        self.assertFalse(forbidden.intersection(AlertsReportsUiMixin.__dict__))

    def test_only_expected_page_builders_are_overridden(self):
        self.assertIn("build_alerts_tab", AlertsReportsUiMixin.__dict__)
        self.assertIn("build_report_tab", AlertsReportsUiMixin.__dict__)


if __name__ == "__main__":
    unittest.main()
