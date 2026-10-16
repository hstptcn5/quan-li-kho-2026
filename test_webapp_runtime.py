# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from webapp.runtime import app_root, webview2_runtime_version

GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WOW64 = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + GUID
NATIVE = r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + GUID


class _Key:
    def __init__(self, ident):
        self.ident = ident

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWinreg:
    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CURRENT_USER = "HKCU"

    def __init__(self, values):
        self.values = values

    def OpenKey(self, hive, path):
        if (hive, path) not in self.values:
            raise FileNotFoundError(path)
        return _Key((hive, path))

    def QueryValueEx(self, key, name):
        assert name == "pv"
        return self.values[key.ident], 1


class RuntimeTests(unittest.TestCase):
    def test_app_root_in_source_mode_contains_the_web_directory(self):
        self.assertTrue((app_root() / "web").is_dir())

    def test_app_root_when_frozen_uses_the_pyinstaller_bundle_dir(self):
        bundle = tempfile.gettempdir()
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "_MEIPASS", bundle, create=True):
            self.assertEqual(app_root(), Path(bundle))

    def test_webview2_version_is_found_in_the_first_matching_location(self):
        fake = FakeWinreg({("HKLM", WOW64): "154.0.4258.37"})
        self.assertEqual(webview2_runtime_version(fake), "154.0.4258.37")

    def test_webview2_version_falls_back_to_other_locations(self):
        self.assertEqual(webview2_runtime_version(FakeWinreg({("HKLM", NATIVE): "120.0.1"})), "120.0.1")
        self.assertEqual(webview2_runtime_version(FakeWinreg({("HKCU", NATIVE): "119.0.2"})), "119.0.2")

    def test_missing_or_placeholder_version_means_not_installed(self):
        self.assertIsNone(webview2_runtime_version(FakeWinreg({})))
        self.assertIsNone(webview2_runtime_version(FakeWinreg({("HKLM", WOW64): "0.0.0.0"})))
        self.assertIsNone(webview2_runtime_version(FakeWinreg({("HKLM", WOW64): ""})))


if __name__ == "__main__":
    unittest.main()
