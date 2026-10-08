from __future__ import annotations

import json
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path

from PIL import Image

from app_paths import RESOURCE_DIR
from branding import load_logo
from studio import VideoTrackingStudio
from video_processing import VideoProcessingWindow


def run(report: Path) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        VideoTrackingStudio(root)
        logo = load_logo(root, (100, 100))
        if logo is None:
            raise RuntimeError("Bundled logo was not found.")
        video_window = VideoProcessingWindow(root)
        ffmpeg = video_window._find_ffmpeg()
        subprocess.run([ffmpeg, "-version"], check=True, capture_output=True)
        with tempfile.TemporaryDirectory(prefix="Kinetho-smoke-") as temporary:
            folder = Path(temporary)
            video = folder / "sample.mp4"
            image = folder / "frame.png"
            subprocess.run([
                ffmpeg, "-hide_banner", "-y", "-f", "lavfi", "-i", "color=c=red:s=64x64:d=1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
            ], check=True, capture_output=True)
            subprocess.run([
                ffmpeg, "-hide_banner", "-y", "-i", str(video), "-frames:v", "1", str(image),
            ], check=True, capture_output=True)
            with Image.open(image) as decoded:
                if decoded.size != (64, 64):
                    raise RuntimeError("Frame extraction returned unexpected dimensions.")
        report.write_text(json.dumps({"ok": True, "resources": str(RESOURCE_DIR), "ffmpeg": ffmpeg}), encoding="utf-8")
    finally:
        root.destroy()