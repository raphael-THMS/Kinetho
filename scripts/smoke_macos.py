from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from macos import build_target


def main() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Test the compiled Mac application on macOS.")
    architecture, _minimum = build_target()
    root = Path(__file__).resolve().parent.parent
    application = root / ".build-mac" / architecture / "dist" / "Kinetho.app"
    executable = application / "Contents" / "MacOS" / "Kinetho"
    with tempfile.TemporaryDirectory(prefix="Kinetho-test-home-") as temporary:
        folder = Path(temporary)
        environment = os.environ.copy()
        environment["HOME"] = str(folder)
        environment["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        report = folder / "report.json"
        subprocess.run([str(executable), "--self-test", str(report)], env=environment, check=True, timeout=120)
        result = json.loads(report.read_text(encoding="utf-8"))
        if result.get("ok") is not True:
            raise RuntimeError("Compiled app smoke test failed.")
        ffmpeg = Path(result["ffmpeg"]).resolve()
        if not ffmpeg.is_relative_to(application.resolve()):
            raise RuntimeError("The application used an external FFmpeg.")
        if not (folder / "Library" / "Application Support" / "Kinetho" / "points.txt").is_file():
            raise RuntimeError("Writable user point configuration was not initialized.")
    print("PASS: compiled Kinetho app runs with bundled FFmpeg and isolated user data, without Homebrew in PATH.")


if __name__ == "__main__":
    main()