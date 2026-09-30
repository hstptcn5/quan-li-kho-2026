# -*- coding: utf-8 -*-
"""Regression gate: user-controlled fields must be escaped before entering HTML.

Product names, units, barcodes, temperature-log sessions and similar fields are
free text that any authenticated LAN client (or a data import) can store. The
mobile page renders them through template literals assigned to ``innerHTML``,
so every such interpolation must go through ``escapeHtml(...)``.
"""

import re
import unittest

import mobile_templates

# Fields whose values originate from user input, imports or the database.
UNTRUSTED_FIELDS = (
    "name", "unit", "unitCode", "barcode", "lotNo", "expiryDate", "fundSource",
    "logDate", "session", "location", "recordedBy", "partner", "reason", "note",
    "noteNumber", "details", "createdAt", "supplier", "productName",
    "regNumber", "address",
)
_FIELD_REF = re.compile(r"\b[A-Za-z_]\w*\.(?:%s)\b" % "|".join(UNTRUSTED_FIELDS))
_INTERPOLATION = re.compile(r"\$\{([^{}]*)\}")


def raw_untrusted_interpolations(html):
    """Return ``(line, expression)`` for unescaped untrusted fields in HTML literals.

    Only template literals that contain markup before the interpolation are
    considered. Plain-text sinks (``textContent``, toast messages) do not need
    escaping, and strings that are escaped later at render time are not HTML yet.
    """
    findings = []
    for match in _INTERPOLATION.finditer(html):
        expression = match.group(1)
        if not _FIELD_REF.search(expression) or "escapeHtml(" in expression:
            continue
        literal_start = html.rfind("`", 0, match.start())
        if literal_start == -1 or "<" not in html[literal_start:match.start()]:
            continue
        line = html.count("\n", 0, match.start()) + 1
        findings.append((line, expression.strip()))
    return findings


class MobileTemplateEscapingTests(unittest.TestCase):
    def test_untrusted_fields_are_escaped_inside_html_template_literals(self):
        findings = raw_untrusted_interpolations(mobile_templates.MOBILE_HTML)
        self.assertEqual(
            findings,
            [],
            "Unescaped user-controlled fields rendered into HTML "
            "(wrap each in escapeHtml): " + "; ".join(f"line {n}: ${{{e}}}" for n, e in findings),
        )

    def test_detector_flags_raw_interpolation_and_accepts_escaped_one(self):
        raw = "el.innerHTML = `<span>${p.name}</span>`;"
        escaped = "el.innerHTML = `<span>${escapeHtml(p.name)}</span>`;"
        text_sink = "toast(`Added ${product.unit}`);"
        self.assertEqual(raw_untrusted_interpolations(raw), [(1, "p.name")])
        self.assertEqual(raw_untrusted_interpolations(escaped), [])
        self.assertEqual(raw_untrusted_interpolations(text_sink), [])


if __name__ == "__main__":
    unittest.main()
