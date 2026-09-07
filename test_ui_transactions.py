# -*- coding: utf-8 -*-
import unittest

from ui_transactions import (
    DISPATCH_WIDGET_CONTRACT,
    PURCHASE_WIDGET_CONTRACT,
    TransactionUiMixin,
)


class TransactionUiContractTests(unittest.TestCase):
    def test_purchase_widget_contract_keeps_legacy_business_hooks(self):
        self.assertEqual(
            set(PURCHASE_WIDGET_CONTRACT),
            {
                "cmb_supplier", "ent_purchase_date", "cmb_purchase_reason", "ent_purchase_note",
                "search_purchase", "cmb_prod", "lbl_unit_purchase", "ent_qty", "ent_lot",
                "ent_exp", "ent_cost", "ent_line_total", "cmb_item_fund", "tree_purchase_cart",
                "lbl_purchase_cart_total",
            },
        )

    def test_dispatch_widget_contract_keeps_legacy_fefo_hooks(self):
        self.assertEqual(
            set(DISPATCH_WIDGET_CONTRACT),
            {
                "cmb_receiving_unit", "ent_dispatch_date", "cmb_reason", "ent_dispatch_note",
                "ent_barcode", "search_pos", "cmb_prod_pos", "cmb_lot_pos", "cmb_fund_pos",
                "ent_qty_pos", "lbl_unit_pos", "tree_cart",
            },
        )

    def test_presentation_mixin_does_not_override_transaction_business_methods(self):
        owned = set(TransactionUiMixin.__dict__)
        forbidden = {
            "add_to_purchase_cart",
            "confirm_purchase",
            "print_purchase_note",
            "add_to_dispatch_cart",
            "confirm_dispatch",
            "print_dispatch_note",
            "update_dispatch_unit_label",
            "update_dispatch_funds",
        }
        self.assertTrue(forbidden.isdisjoint(owned))
        self.assertIn("build_purchase_tab", owned)
        self.assertIn("build_dispatch_tab", owned)


if __name__ == "__main__":
    unittest.main()
