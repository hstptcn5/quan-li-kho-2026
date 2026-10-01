# -*- coding: utf-8 -*-
import contextlib
import http.client
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import quanly_web


class CreateListenerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.listener = quanly_web.create_listener(os.path.join(self.tmp.name, "web.db"))
        self.listener.start()
        self.addCleanup(self.listener.stop)

    def get(self, path, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.listener.port, timeout=10)
        try:
            conn.request("GET", path, headers={"Cookie": cookie} if cookie else {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_boot_url_logs_in_and_the_dashboard_api_answers_from_the_given_database(self):
        boot_path = self.listener.boot_url().split(str(self.listener.port), 1)[1]
        status, headers, _ = self.get(boot_path)
        self.assertEqual(status, 302)
        cookie = headers["Set-Cookie"].split(";", 1)[0]

        status, _, body = self.get("/api/dashboard", cookie=cookie)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["cards"]["productCount"], 0)

        status, _, body = self.get("/", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn(b"<!doctype html", body.lower())


class WindowTests(unittest.TestCase):
    def test_missing_webview2_prints_help_and_returns_1(self):
        listener = mock.Mock()
        stderr = io.StringIO()
        with mock.patch.object(quanly_web, "webview2_runtime_version", return_value=None), \
                contextlib.redirect_stderr(stderr):
            code = quanly_web.run_window(listener)
        self.assertEqual(code, 1)
        self.assertIn("WebView2", stderr.getvalue())
        self.assertIn("go.microsoft.com/fwlink/p/?LinkId=2124703", stderr.getvalue())
        listener.start.assert_not_called()

    def test_window_allows_text_selection_so_pywebview_injects_no_inline_style(self):
        # pywebview chèn một <style> nội tuyến khi text_select=False (mặc định); CSP chặt của
        # giao diện (style-src 'self') sẽ chặn nó và smoke test báo vi phạm.
        fake_webview = mock.Mock()
        listener = mock.Mock()
        listener.boot_url.return_value = "http://127.0.0.1:1/boot/x"
        with mock.patch.object(quanly_web, "webview2_runtime_version", return_value="1.0"),                 mock.patch.dict(sys.modules, {"webview": fake_webview}):
            code = quanly_web.run_window(listener)
        self.assertEqual(code, 0)
        self.assertIs(fake_webview.create_window.call_args.kwargs["text_select"], True)


class ParserTests(unittest.TestCase):
    def test_serve_flag(self):
        self.assertFalse(quanly_web.build_parser().parse_args([]).serve)
        self.assertTrue(quanly_web.build_parser().parse_args(["--serve"]).serve)

    def test_smoke_flag_and_mutual_exclusion(self):
        self.assertTrue(quanly_web.build_parser().parse_args(["--smoke"]).smoke)
        self.assertFalse(quanly_web.build_parser().parse_args([]).smoke)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            quanly_web.build_parser().parse_args(["--serve", "--smoke"])


if __name__ == "__main__":
    unittest.main()
