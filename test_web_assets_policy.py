# -*- coding: utf-8 -*-
"""Kiểm tra tĩnh cho web/: không có API nguy hiểm, mọi tham chiếu đều tồn tại,
token màu đạt WCAG AA và khớp bảng màu Tkinter, điều hướng khớp ui_design."""

import hashlib
import re
import unittest
from pathlib import Path

from ui_design import COLORS, NAV_ITEMS

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
VENDOR_DIR = WEB / "js" / "vendor"
TOKENS = WEB / "css" / "tokens.css"


def own_files(*suffixes):
    """File do dự án viết (không gồm thư viện đặt sẵn trong js/vendor)."""
    return [
        path for path in sorted(WEB.rglob("*"))
        if path.is_file() and path.suffix in suffixes and VENDOR_DIR not in path.parents
    ]


def read(path):
    return path.read_text(encoding="utf-8")


BANNED = {
    "innerHTML": r"innerHTML",
    "outerHTML": r"outerHTML",
    "insertAdjacentHTML": r"insertAdjacentHTML",
    "document.write": r"document\.write",
    "dangerouslySetInnerHTML": r"dangerouslySetInnerHTML",
    "eval(": r"\beval\s*\(",
    "new Function": r"new\s+Function\b",
    "Function(": r"(?<![\w.])Function\s*\(",
    "thuộc tính sự kiện nội tuyến (on*=)": r"\son[a-z]+\s*=\s*[\"']",
    "thuộc tính style nội tuyến": r"\sstyle\s*=\s*[\"']",
    "javascript: URL": r"javascript:",
}


def exported_names(source):
    names = set()
    for match in re.finditer(r"export\s+(?:async\s+)?function\s+(\w+)", source):
        names.add(match.group(1))
    for match in re.finditer(r"export\s+(?:class|const|let|var)\s+(\w+)", source):
        names.add(match.group(1))
    for match in re.finditer(r"export\s*\{([^}]*)\}", source):
        for item in match.group(1).split(","):
            item = item.strip()
            if item:
                names.add(item.split(" as ")[-1].strip())
    return names


def parse_tokens():
    raw = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", read(TOKENS)))

    def resolve(name):
        value = raw[name].strip()
        alias = re.fullmatch(r"var\(--([a-z0-9-]+)\)", value)
        return resolve(alias.group(1)) if alias else value.upper()

    return {name: resolve(name) for name in raw}


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class ForbiddenApiTests(unittest.TestCase):
    def test_no_dangerous_apis_or_inline_handlers_in_own_files(self):
        problems = []
        for path in own_files(".js", ".html", ".css"):
            text = read(path)
            for label, pattern in BANNED.items():
                if re.search(pattern, text):
                    problems.append(f"{path.relative_to(WEB)}: {label}")
        self.assertEqual(problems, [])

    def test_html_has_no_inline_script_or_style_blocks(self):
        problems = []
        for path in own_files(".html"):
            text = read(path)
            if re.search(r"<script(?![^>]*\ssrc=)[^>]*>", text):
                problems.append(f"{path.relative_to(WEB)}: <script> nội tuyến")
            if re.search(r"<style\b", text):
                problems.append(f"{path.relative_to(WEB)}: <style> nội tuyến")
        self.assertEqual(problems, [])


class ReferenceTests(unittest.TestCase):
    def test_every_relative_import_and_asset_reference_resolves(self):
        missing = []
        for path in own_files(".js"):
            text = read(path)
            for spec in re.findall(r"\bfrom\s+[\"']([^\"']+)[\"']", text) + re.findall(
                r"\bimport\s+[\"']([^\"']+)[\"']", text
            ):
                if spec.startswith("."):
                    target = (path.parent / spec).resolve()
                    if not target.is_file():
                        missing.append(f"{path.relative_to(WEB)} -> {spec}")
        for path in own_files(".html"):
            for ref in re.findall(r"(?:src|href)=\"([^\"]+)\"", read(path)):
                if ref.startswith(("http:", "https:", "#", "data:")):
                    missing.append(f"{path.relative_to(WEB)} -> {ref} (tham chiếu ngoài)")
                    continue
                target = (WEB / ref.lstrip("/")).resolve() if ref.startswith("/") else (path.parent / ref).resolve()
                if not target.is_file():
                    missing.append(f"{path.relative_to(WEB)} -> {ref}")
        self.assertEqual(missing, [])

    def test_named_imports_exist_in_the_target_module(self):
        problems = []
        for path in own_files(".js"):
            for names, spec in re.findall(
                r"import\s*\{([^}]*)\}\s*from\s*[\"']([^\"']+)[\"']", read(path)
            ):
                if not spec.startswith("."):
                    continue
                target = (path.parent / spec).resolve()
                if VENDOR_DIR in target.parents or not target.is_file():
                    continue
                available = exported_names(read(target))
                for item in names.split(","):
                    name = item.strip().split(" as ")[0].strip()
                    if name and name not in available:
                        problems.append(f"{path.relative_to(WEB)}: '{name}' không được xuất bởi {spec}")
        self.assertEqual(problems, [])

    def test_css_only_uses_defined_tokens(self):
        defined = set(parse_tokens())
        problems = []
        for path in own_files(".css"):
            for name in re.findall(r"var\(--([a-z0-9-]+)\)", read(path)):
                if name not in defined:
                    problems.append(f"{path.relative_to(WEB)}: var(--{name}) chưa định nghĩa")
        self.assertEqual(problems, [])


class VendorTests(unittest.TestCase):
    def test_vendored_library_matches_its_recorded_hash_and_exports_what_the_app_uses(self):
        record = read(VENDOR_DIR / "VENDOR.md")
        match = re.search(r"^htm-preact\.js\s+sha256:\s*([0-9a-f]{64})\s*$", record, re.M)
        self.assertIsNotNone(match, "VENDOR.md phải có dòng 'htm-preact.js sha256: <64 hex>'")
        data = (VENDOR_DIR / "htm-preact.js").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), match.group(1))
        available = exported_names(data.decode("utf-8"))
        for name in ("html", "render", "Component"):
            self.assertIn(name, available)

    def test_licenses_are_shipped_with_the_vendored_library(self):
        for name in ("LICENSE-htm.txt", "LICENSE-preact.txt"):
            self.assertGreater((VENDOR_DIR / name).stat().st_size, 200, name)


class DesignTokenTests(unittest.TestCase):
    def test_palette_matches_tkinter_tokens_except_the_documented_muted_text(self):
        tokens = parse_tokens()
        for key, value in COLORS.items():
            name = key.replace("_", "-")
            expected = "#5F6F85" if key == "text_muted" else value.upper()
            with self.subTest(token=name):
                self.assertEqual(tokens[name], expected)

    def test_text_and_background_pairs_meet_wcag_aa(self):
        tokens = parse_tokens()
        pairs = [
            ("text", "surface"), ("text", "canvas"), ("text", "selected"), ("text", "row-near-bg"),
            ("text-muted", "surface"), ("text-muted", "canvas"), ("text-muted", "surface-subdued"),
            ("text-subtle", "surface"), ("text-subtle", "canvas"), ("text-subtle", "surface-subdued"),
            ("on-primary", "primary"), ("on-primary", "primary-hover"),
            ("primary", "nav-active-bg"), ("primary", "canvas"), ("primary", "surface"),
            ("success", "success-bg"), ("success", "surface"),
            ("warning", "warning-bg"), ("warning", "surface"), ("warning", "row-near-bg"),
            ("danger", "danger-bg"), ("danger", "surface"),
            ("info", "info-bg"), ("info", "surface"),
        ]
        failures = []
        for fg, bg in pairs:
            ratio = contrast(tokens[fg], tokens[bg])
            if ratio < 4.5:
                failures.append(f"--{fg} trên --{bg}: {ratio:.2f}:1")
        self.assertEqual(failures, [])


class NavigationTests(unittest.TestCase):
    def test_nav_js_matches_tkinter_nav_items_and_only_the_dashboard_is_live(self):
        text = read(WEB / "js" / "nav.js")
        items = re.findall(
            r"\{\s*id:\s*\"([^\"]+)\",\s*label:\s*\"([^\"]+)\",\s*tab:\s*\"([^\"]+)\",\s*"
            r"hotkey:\s*\"([^\"]+)\",\s*live:\s*(true|false)\s*\}",
            text,
        )
        self.assertEqual([item[:4] for item in items], list(NAV_ITEMS))
        self.assertEqual([item[0] for item in items if item[4] == "true"], ["dashboard"])


if __name__ == "__main__":
    unittest.main()
