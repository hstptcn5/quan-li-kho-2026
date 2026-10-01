# -*- coding: utf-8 -*-
import contextlib
import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock

from database import DB
from webapp import smoke
from webapp.services import dashboard as service
from webapp_testkit import seed_demo_database

REAL_SLEEP = time.sleep  # lấy trước khi vá, để bản vá không gọi lại chính nó
COUNTS = {"all": 3, "expired": 1, "near": 1, "low": 1}
EXPECT = json.dumps({"counts": COUNTS, "literal": "<b>x</b>"})


class FakeDashboardWindow:
    """Mô phỏng vừa đủ DOM của Tổng quan để chạy kịch bản smoke."""

    def __init__(self, counts, literal="<b>x</b>", ready=True, bold=0, csp=None, stale_rows=False):
        self.counts = counts
        self.literal = literal
        self.ready = ready
        self.bold = bold
        self.csp = csp or []
        self.stale_rows = stale_rows
        self.pressed = "all"
        self.rows_from = "all"
        self.hash = ""

    def _severities(self, source):
        c = self.counts
        return {
            "all": ["0"] * c["expired"] + ["2"] * c["near"] + ["3"] * c["low"],
            "expired": ["0"] * c["expired"],
            "near": ["2"] * c["near"],
            "low": ["3"] * c["low"],
        }[source]

    def evaluate_js(self, script):
        if script == smoke.STATE:
            c = self.counts
            return json.dumps({
                "ready": self.ready,
                "error": False,
                "title": "Tổng quan vận hành kho",
                "activeNav": "▦  Tổng quan F4",
                "chipLabels": [f"Tất cả {c['all']}", f"Hết hạn {c['expired']}", f"Cận hạn {c['near']}", f"Tồn thấp {c['low']}"],
                "pressed": [self.pressed],
                "severities": self._severities(self.rows_from),
                "tableText": self.literal or "",
                "boldCount": self.bold,
                "diagnostics": {"cspViolations": self.csp, "errors": []},
            })
        for name in ("expired", "near", "low", "all"):
            if script == smoke.click_script(name):
                self.pressed = self.rows_from = name
                return True
        if script == smoke.RAPID_CLICKS:
            self.pressed = "low"
            # Lỗi mô phỏng: phản hồi của chip đầu tiên đến muộn và ghi đè bảng.
            self.rows_from = "expired" if self.stale_rows else "low"
            return True
        if script == smoke.OPEN_UNAVAILABLE_ROUTE:
            self.hash = "#/products"
            return True
        raise AssertionError(f"Script lạ: {script[:80]}")


def run(window, expect=EXPECT):
    out = io.StringIO()
    env = {"QLK_SMOKE_EXPECT": expect} if expect is not None else {}
    with mock.patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(out):
        if expect is None:
            os.environ.pop("QLK_SMOKE_EXPECT", None)
        code = smoke.run_smoke(window)
    return code, out.getvalue()


class SmokeScenarioTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.multiple(smoke, TIMEOUT_SECONDS=0.5, POLL_SECONDS=0.02)
        patcher.start()
        self.addCleanup(patcher.stop)
        sleeper = mock.patch.object(smoke.time, "sleep", lambda seconds: REAL_SLEEP(min(seconds, 0.02)))
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_healthy_dashboard_passes(self):
        window = FakeDashboardWindow(COUNTS)
        code, output = run(window)
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))
        self.assertEqual(window.hash, "#/products")

    def test_basic_checks_without_an_expectation(self):
        code, output = run(FakeDashboardWindow({"all": 0, "expired": 0, "near": 0, "low": 0}), expect=None)
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))

    def test_empty_database_scenario_passes(self):
        zero = {"all": 0, "expired": 0, "near": 0, "low": 0}
        code, output = run(FakeDashboardWindow(zero, literal=None), json.dumps({"counts": zero, "literal": None}))
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))

    def test_text_rendered_as_html_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, bold=1))
        self.assertEqual(code, 1)
        self.assertIn("<b>", output)

    def test_csp_violation_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, csp=["script-src-elem https://evil.example"]))
        self.assertEqual(code, 1)
        self.assertIn("CSP", output)

    def test_stale_response_overwriting_the_last_chip_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, stale_rows=True))
        self.assertEqual(code, 1)
        self.assertIn("WEB_SMOKE_FAIL", output)

    def test_wrong_chip_counts_fail(self):
        wrong = dict(COUNTS, all=4)
        code, output = run(FakeDashboardWindow(wrong))
        self.assertEqual(code, 1)
        self.assertIn("chip", output.lower())

    def test_page_that_never_becomes_ready_times_out(self):
        code, output = run(FakeDashboardWindow(COUNTS, ready=False))
        self.assertEqual(code, 1)
        self.assertIn("Quá thời gian chờ", output)


class DemoSeedTests(unittest.TestCase):
    def test_seed_matches_the_expectation_used_by_the_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "QuanLyXNT", "pharm.db")
            expectation = seed_demo_database(path)
            db = DB(path)
            try:
                warnings = service.build_dashboard_payload(db)["warnings"]
            finally:
                db.conn.close()
        self.assertEqual(warnings["counts"], expectation["counts"])
        names = [row["productName"] for row in warnings["rows"]]
        self.assertTrue(any(expectation["literal"] in name for name in names))


if __name__ == "__main__":
    unittest.main()
