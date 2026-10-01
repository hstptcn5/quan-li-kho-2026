# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path

from webapp.static import CONTENT_TYPES, resolve_static, serve_static


class StaticServingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.web = base / "web"
        (self.web / "css").mkdir(parents=True)
        (self.web / "js").mkdir()
        (self.web / "index.html").write_text("<!doctype html><p>trang chủ</p>", encoding="utf-8")
        (self.web / "css" / "a.css").write_text("body{}", encoding="utf-8")
        (self.web / "js" / "a.js").write_text("export const a = 1;", encoding="utf-8")
        (self.web / "notes.txt").write_text("không được phục vụ", encoding="utf-8")
        (self.web / ".hidden.js").write_text("x", encoding="utf-8")
        (base / "secret.txt").write_text("bí mật", encoding="utf-8")

    def test_root_serves_index_html(self):
        response = serve_static(self.web, "/")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("trang chủ".encode("utf-8"), response.body)
        self.assertEqual(response.headers["Cache-Control"], "no-cache")

    def test_content_types_for_allowed_extensions(self):
        self.assertEqual(serve_static(self.web, "/css/a.css").content_type, "text/css; charset=utf-8")
        self.assertEqual(serve_static(self.web, "/js/a.js").content_type, "text/javascript; charset=utf-8")
        self.assertEqual(
            sorted(CONTENT_TYPES),
            [".css", ".html", ".ico", ".js", ".png", ".svg", ".woff2"],
        )

    def test_path_escape_attempts_are_all_404(self):
        attempts = [
            "/../secret.txt",
            "/%2e%2e/secret.txt",
            "/css/../../secret.txt",
            "/css/%2e%2e/%2e%2e/secret.txt",
            "/js//a.js",
            "/js\\a.js",
            "/%5cjs%5ca.js",
            "/C:/Windows/win.ini",
            "/js/a.js\x00",
            "/%00",
            "/js/a.js::$DATA",
            "/.hidden.js",
            "/css/",
            "/css",
            "/js/missing.js",
            "/notes.txt",
        ]
        for path in attempts:
            with self.subTest(path=path):
                response = serve_static(self.web, path)
                self.assertEqual(response.status, 404)
                self.assertNotIn("bí mật".encode("utf-8"), response.body)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_resolve_never_leaves_the_web_root(self):
        for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/css/../../secret.txt"):
            self.assertIsNone(resolve_static(self.web, path))
        resolved = resolve_static(self.web, "/js/a.js")
        self.assertEqual(resolved, (self.web / "js" / "a.js").resolve())

    def test_symlinks_are_refused(self):
        link = self.web / "js" / "link.js"
        try:
            os.symlink(self.web.parent / "secret.txt", link)
        except (OSError, NotImplementedError):
            self.skipTest("Không tạo được symlink (thiếu quyền trên Windows)")
        self.assertEqual(serve_static(self.web, "/js/link.js").status, 404)


if __name__ == "__main__":
    unittest.main()
