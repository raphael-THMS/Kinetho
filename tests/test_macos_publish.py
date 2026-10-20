from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import publish_macos


class MacPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "branding.py").write_text('APP_VERSION = "0.3.0"\n', encoding="utf-8")
        (self.root / "release-mac").mkdir()
        for architecture in ("arm64", "x86_64"):
            for extension in ("dmg", "zip"):
                (self.root / "release-mac" / f"Kinetho-0.3.0-macOS-{architecture}.{extension}").write_bytes(b"test-package")

    def test_four_packages_required(self) -> None:
        packages = publish_macos.validate_request(self.root, "v0.3.0-macos.1", "a" * 40)
        self.assertEqual(len(packages), 4)

    def test_missing_architecture_refused(self) -> None:
        (self.root / "release-mac" / "Kinetho-0.3.0-macOS-x86_64.dmg").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or empty"):
            publish_macos.validate_request(self.root, "v0.3.0-macos.1", "a" * 40)

    def test_wrong_version_or_unsafe_tag_refused(self) -> None:
        for tag in ("v0.2.0-macos.1", "v0.3.0", "v0.3.0-macos.0", "--target=main"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                publish_macos.validate_request(self.root, tag, "a" * 40)

    def test_exact_commit_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "commit SHA"):
            publish_macos.validate_request(self.root, "v0.3.0-macos.1", "main")

    def test_existing_release_never_overwritten(self) -> None:
        result = subprocess.CompletedProcess([], 0, "{}", "")
        with patch("subprocess.run", return_value=result), self.assertRaisesRegex(ValueError, "already exists"):
            publish_macos.require_unused("repos/owner/repo/releases/tags/tag")

    def test_permission_failure_not_treated_as_missing_release(self) -> None:
        result = subprocess.CompletedProcess([], 1, "", "HTTP 403")
        with patch("subprocess.run", return_value=result), self.assertRaisesRegex(RuntimeError, "permissions"):
            publish_macos.require_unused("repos/owner/repo/releases/tags/tag")

    def test_missing_release_allowed(self) -> None:
        result = subprocess.CompletedProcess([], 1, "", "HTTP 404")
        with patch("subprocess.run", return_value=result):
            publish_macos.require_unused("repos/owner/repo/releases/tags/tag")

    def run_publication(self, incomplete: bool = False) -> list[list[str]]:
        (self.root / "README-Installation-Mac.md").write_text("Installation guide")
        commands: list[list[str]] = []

        def fake_gh(arguments: list[str]) -> str:
            commands.append(arguments)
            if arguments[0] == "api":
                assets = [*sorted((self.root / "release-mac").iterdir()), self.root / "README-Installation-Mac.md"]
                return json.dumps({
                    "assets": [{"name": asset.name, "size": asset.stat().st_size} for asset in assets if not incomplete],
                    "target_commitish": "a" * 40,
                    "draft": True,
                    "prerelease": True,
                })
            return ""

        with patch.object(publish_macos, "ROOT", self.root), patch.object(publish_macos, "gh", side_effect=fake_gh):
            with patch.object(publish_macos, "require_unused"), patch.dict(os.environ, {
                "GH_REPO": "owner/repo", "RELEASE_TAG": "v0.3.0-macos.1", "RELEASE_COMMIT": "a" * 40,
            }):
                if incomplete:
                    with self.assertRaisesRegex(RuntimeError, "remains a draft"):
                        publish_macos.main()
                else:
                    publish_macos.main()
        return commands

    def test_publish_only_after_draft_upload_verification(self) -> None:
        commands = self.run_publication()
        self.assertIn("--draft", commands[0])
        self.assertEqual(commands[1][:2], ["release", "upload"])
        self.assertEqual(commands[2][0], "api")
        self.assertEqual(commands[3][:2], ["release", "edit"])
        self.assertIn("--latest=false", commands[3])
        self.assertTrue((self.root / "release-mac" / "SHA256SUMS.txt").is_file())

    def test_incomplete_upload_never_published(self) -> None:
        commands = self.run_publication(incomplete=True)
        self.assertFalse(any(command[:2] == ["release", "edit"] for command in commands))


if __name__ == "__main__":
    unittest.main()