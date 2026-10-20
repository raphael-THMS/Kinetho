from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def app_version(root: Path) -> str:
    tree = ast.parse((root / "src" / "branding.py").read_text(encoding="utf-8-sig"))
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "APP_VERSION" for target in statement.targets):
            value = ast.literal_eval(statement.value)
            if isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+", value):
                return value
    raise ValueError("A numeric APP_VERSION was not found.")


def validate_request(root: Path, tag: str, commit: str) -> list[Path]:
    version = app_version(root)
    if re.fullmatch(rf"v{re.escape(version)}-macos\.[1-9]\d*", tag) is None:
        raise ValueError(f"Use a new tag such as v{version}-macos.1 matching APP_VERSION.")
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("A full source commit SHA is required.")
    packages = [
        root / "release-mac" / f"Kinetho-{version}-macOS-{architecture}.{extension}"
        for architecture in ("x86_64", "arm64")
        for extension in ("dmg", "zip")
    ]
    for package in packages:
        if not package.is_file() or package.stat().st_size == 0:
            raise ValueError(f"Missing or empty Mac package: {package.name}")
    return packages


def gh(arguments: list[str]) -> str:
    return subprocess.check_output(["gh", *arguments], text=True)


def require_unused(endpoint: str) -> None:
    result = subprocess.run(["gh", "api", endpoint], text=True, capture_output=True)
    if result.returncode == 0:
        raise ValueError("This release tag already exists; choose a new pre-release number.")
    if "404" not in result.stderr:
        raise RuntimeError(f"Cannot check GitHub publication permissions: {result.stderr.strip()}")


def main() -> None:
    repository = os.environ.get("GH_REPO", "")
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise ValueError("GH_REPO must identify the publication repository.")
    tag = os.environ.get("RELEASE_TAG", "")
    commit = os.environ.get("RELEASE_COMMIT", "")
    packages = validate_request(ROOT, tag, commit)
    require_unused(f"repos/{repository}/releases/tags/{tag}")
    require_unused(f"repos/{repository}/git/ref/tags/{tag}")
    checksums = ROOT / "release-mac" / "SHA256SUMS.txt"
    lines = []
    for package in packages:
        digest = hashlib.sha256()
        with package.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        lines.append(f"{digest.hexdigest()}  {package.name}\n")
    checksums.write_text("".join(lines), encoding="ascii")
    guide = ROOT / "README-Installation-Mac.md"
    if not guide.is_file():
        raise ValueError("Mac installation guide is missing.")
    assets = [*packages, checksums, guide]
    with tempfile.TemporaryDirectory(prefix="Kinetho-release-") as temporary:
        notes = Path(temporary) / "notes.md"
        notes.write_text(
            f"## Kinetho macOS - test release\n\nSource commit: `{commit}`.\n\n"
            "- Intel: choose `macOS-x86_64.dmg`, targeting Ventura 13 or newer.\n"
            "- Apple Silicon: choose `macOS-arm64.dmg`, targeting macOS 14 or newer.\n"
            "- Open the DMG, drag Kinetho.app into Applications, then launch it.\n"
            "- Python, Tkinter, Pillow, FFmpeg and x264 are bundled. No Homebrew installation is required.\n"
            "- Includes the current annotation/calibration, export, and remembered-folder improvements.\n"
            "- ZIP alternatives, SHA-256 checksums and installation guide are attached.\n"
            "- Corresponding FFmpeg/x264 sources and licenses are included in the app.\n\n"
            "The app is ad-hoc signed, not Developer ID signed or Apple-notarized. Gatekeeper may block it. "
            "Build-time checks are not certification on Ventura or every Mac: test before adopting it. "
            "Do not use GitHub's automatic Source code archives as installers.\n",
            encoding="utf-8",
        )
        gh(["release", "create", tag, "--repo", repository, "--target", commit, "--title", f"Kinetho {app_version(ROOT)} - macOS test", "--notes-file", str(notes), "--prerelease", "--draft"])
    gh(["release", "upload", tag, "--repo", repository, *[str(asset) for asset in assets]])
    uploaded = json.loads(gh(["api", f"repos/{repository}/releases/tags/{tag}"]))
    actual = {asset["name"]: asset["size"] for asset in uploaded["assets"]}
    expected = {asset.name: asset.stat().st_size for asset in assets}
    if actual != expected or uploaded["target_commitish"] != commit or not uploaded["draft"] or not uploaded["prerelease"]:
        raise RuntimeError("Release verification failed; the release remains a draft.")
    gh(["release", "edit", tag, "--repo", repository, "--draft=false", "--prerelease", "--latest=false"])
    print(f"Published Mac test release: https://github.com/{repository}/releases/tag/{tag}")


if __name__ == "__main__":
    main()