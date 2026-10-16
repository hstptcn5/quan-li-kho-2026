# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build_web_release


class BuildCommandTests(unittest.TestCase):
    def test_command_bundles_web_and_excludes_desktop_only_libraries(self):
        command = build_web_release.build_command("python")
        self.assertEqual(command[:3], ["python", "-m", "PyInstaller"])
        for flag in ("--onedir", "--console", "--noconfirm", "--clean", "--name=QuanLyKhoWeb"):
            self.assertIn(flag, command)
        web = build_web_release.ROOT / "web"
        self.assertIn(f"--add-data={web}{os.pathsep}web", command)
        for module in ("cv2", "pyzbar", "matplotlib", "pandas", "tkinter"):
            self.assertIn(f"--exclude-module={module}", command)
        self.assertEqual(command[-1], str(build_web_release.ROOT / "quanly_web.py"))


class ValidateDistributionTests(unittest.TestCase):
    def make_dist(self, root: Path):
        (root / "QuanLyKhoWeb.exe").write_bytes(b"0" * (1024 * 1024 + 1))
        for rel in build_web_release.REQUIRED_WEB_FILES:
            target = root / "_internal" / "web" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")

    def test_complete_distribution_passes_and_missing_asset_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_dist(root)
            with mock.patch.object(build_web_release, "APP_DIST", root):
                build_web_release._validate_distribution()
                (root / "_internal" / "web" / "js" / "app.js").unlink()
                with self.assertRaises(RuntimeError) as ctx:
                    build_web_release._validate_distribution()
                self.assertIn("js/app.js", str(ctx.exception))

    def test_tiny_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_dist(root)
            (root / "QuanLyKhoWeb.exe").write_bytes(b"0" * 10)
            with mock.patch.object(build_web_release, "APP_DIST", root):
                with self.assertRaises(RuntimeError):
                    build_web_release._validate_distribution()


if __name__ == "__main__":
    unittest.main()
