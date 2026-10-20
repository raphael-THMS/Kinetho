from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import macos


class MacBuildTests(unittest.TestCase):
    def test_native_targets(self) -> None:
        for architecture, minimum in (("x86_64", "13.0"), ("arm64", "14.0")):
            with self.subTest(architecture=architecture), patch.dict(os.environ, {}, clear=True):
                with patch.object(sys, "platform", "darwin"), patch("platform.machine", return_value=architecture):
                    self.assertEqual(macos.build_target(), (architecture, minimum))

    def test_architecture_mismatch(self) -> None:
        with patch.dict(os.environ, {"KINETHO_MAC_ARCH": "x86_64"}, clear=True):
            with patch.object(sys, "platform", "darwin"), patch("platform.machine", return_value="arm64"):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    macos.build_target()

    def test_windows_build_refused(self) -> None:
        with patch.object(sys, "platform", "win32"):
            with self.assertRaisesRegex(ValueError, "macOS Python"):
                macos.build_target()

    def check_binary(self, commands: str, minimum: str = "13.0") -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary)
            (bundle / "Kinetho").write_bytes(bytes.fromhex("cffaedfe"))
            (bundle / "data.txt").write_text("not a binary")
            with patch("subprocess.check_output", return_value=commands) as inspect:
                macos.validate_bundle(bundle, "x86_64", minimum)
            self.assertEqual(inspect.call_count, 1)
            self.assertEqual(inspect.call_args.args[0][:4], ["otool", "-arch", "x86_64", "-l"])

    def test_legacy_macho(self) -> None:
        self.check_binary("Load command 0\n cmd LC_VERSION_MIN_MACOSX\n cmdsize 16\n version 10.13\n sdk 15.0\n")

    def test_ventura_macho(self) -> None:
        self.check_binary("Load command 0\n cmd LC_BUILD_VERSION\n cmdsize 32\n platform 1\n minos 13.0\n sdk 15.0\n")

    def test_newer_dependency_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires macOS 14.0"):
            self.check_binary("Load command 0\n cmd LC_BUILD_VERSION\n cmdsize 32\n platform 1\n minos 14.0\n sdk 15.0\n")

    def test_missing_minimum_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "Cannot verify"):
            self.check_binary("Load command 0\n cmd LC_SEGMENT_64\n")

    def test_architecture_package_names(self) -> None:
        for architecture in ("x86_64", "arm64"):
            with self.subTest(architecture=architecture), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                application = folder / "Kinetho.app"
                application.mkdir()
                with patch.object(macos, "execute") as execute:
                    with patch("os.symlink"), patch("shutil.copy2"):
                        macos.package_application(application, folder / "release", "0.2.0", architecture)
                commands = [call.args[0] for call in execute.call_args_list]
                self.assertTrue(commands[0][-1].endswith(f"macOS-{architecture}.zip"))
                self.assertTrue(commands[1][-1].endswith(f"macOS-{architecture}.dmg"))


if __name__ == "__main__":
    unittest.main()