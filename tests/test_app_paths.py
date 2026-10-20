from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "src" / "app_paths.py"


def load_paths(executable: Path, resources: Path, platform: str = "win32"):
    spec = importlib.util.spec_from_file_location("packaged_app_paths", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with (
        patch.object(sys, "frozen", True, create=True),
        patch.object(sys, "executable", str(executable)),
        patch.object(sys, "_MEIPASS", str(resources), create=True),
        patch.object(sys, "platform", platform),
    ):
        spec.loader.exec_module(module)
    return module


class PackagedPathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.resources = self.root / "_internal"
        self.resources.mkdir()
        (self.resources / "points.txt").write_text("default", encoding="utf-8")
        self.paths = load_paths(self.root / "Kinetho.exe", self.resources)

    def test_packaged_resources_and_documentation(self) -> None:
        self.assertEqual(self.paths.RESOURCE_DIR, self.resources)
        self.assertEqual(self.paths.PROJECT_DIR, self.root)
        self.assertEqual(self.paths.DOCUMENTATION_DIR, self.root / "docs")
        self.assertEqual(self.paths.settings_directory(), self.root / "data")
        self.assertEqual(self.paths.points_file().read_text(encoding="utf-8"), "default")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["_internal", "data"])

    def test_legacy_preferences_are_migrated_without_resetting(self) -> None:
        for name, value in (("points.txt", "custom"), ("kinetho_settings.json", '{"language":"fr","folders":{}}')):
            (self.root / name).write_text(value, encoding="utf-8")
        data = self.paths.settings_directory()
        self.assertEqual(self.paths.points_file().read_text(encoding="utf-8"), "custom")
        self.assertEqual((data / "kinetho_settings.json").read_text(encoding="utf-8"), '{"language":"fr","folders":{}}')
        self.assertFalse((self.root / "points.txt").exists())
        self.assertFalse((self.root / "kinetho_settings.json").exists())

    def test_migration_does_not_overwrite_newer_preferences(self) -> None:
        data = self.paths.settings_directory()
        (data / "points.txt").write_text("new", encoding="utf-8")
        (self.root / "points.txt").write_text("old", encoding="utf-8")
        self.assertEqual(self.paths.points_file().read_text(encoding="utf-8"), "new")
        self.assertEqual((self.root / "points.txt").read_text(encoding="utf-8"), "old")

    def test_macos_keeps_application_support_and_bundle_resources(self) -> None:
        with patch("pathlib.Path.home", return_value=self.root):
            paths = load_paths(self.root / "MacOS" / "Kinetho", self.resources, "darwin")
        self.assertEqual(paths.DATA_DIR, self.root / "Library" / "Application Support" / "Kinetho")
        self.assertEqual(paths.DOCUMENTATION_DIR, self.resources)
        self.assertEqual(paths.points_file().read_text(encoding="utf-8"), "default")


if __name__ == "__main__":
    unittest.main()
