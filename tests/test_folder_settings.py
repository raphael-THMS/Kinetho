from __future__ import annotations

import json
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import localization
import point_annotator
import video_processing
from point_annotator import PointAnnotator
from video_processing import VideoProcessingWindow


class SettingsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.settings_dir = self.base / "settings"
        self.settings_dir.mkdir()
        settings_patch = patch("localization.settings_directory", return_value=self.settings_dir)
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

    def settings(self) -> dict[str, object]:
        return json.loads((self.settings_dir / "kinetho_settings.json").read_text(encoding="utf-8"))


class FolderSettingsTests(SettingsTestCase):
    def test_language_and_folders_are_preserved_together(self) -> None:
        folder = self.base / "videos"
        folder.mkdir()
        localization.save_language("fr")
        self.assertTrue(localization.remember_path("video_input", folder))
        localization.save_language("en")
        self.assertEqual(localization.load_language(), "en")
        self.assertEqual(localization.remembered_path("video_input"), folder.resolve())
        self.assertEqual(self.settings()["language"], "en")

    def test_missing_or_unknown_paths(self) -> None:
        missing = self.base / "deleted"
        missing.mkdir()
        localization.remember_path("frames_output", missing)
        missing.rmdir()
        self.assertIsNone(localization.remembered_path("frames_output"))
        self.assertIsNone(localization.remembered_path("annotation_folder"))
        self.assertFalse(localization.remember_path("video_output", "  "))
        with self.assertRaises(ValueError):
            localization.remember_path("unknown", self.base)

    def test_corrupt_settings_do_not_break_loading(self) -> None:
        (self.settings_dir / "kinetho_settings.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(localization.load_language(), "en")
        self.assertIsNone(localization.remembered_path("video_input"))
        localization.save_language("fr")
        self.assertEqual(localization.load_language(), "fr")

    def test_no_default_work_folders_remain(self) -> None:
        for module, name in (
            (video_processing, "RAW_VIDEO_DIR"),
            (video_processing, "PROCESSED_VIDEO_DIR"),
            (video_processing, "IMAGE_OUTPUT_DIR"),
            (point_annotator, "INPUT_DIR"),
        ):
            self.assertFalse(hasattr(module, name), name)


class WindowFolderTests(SettingsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def make_video_window(self) -> VideoProcessingWindow:
        window = VideoProcessingWindow(self.root)
        self.addCleanup(window.window.destroy)
        return window

    def test_video_window_starts_empty_then_uses_remembered_folders(self) -> None:
        window = self.make_video_window()
        self.assertEqual(window.input_dir.get(), "")
        self.assertEqual(window.output_dir.get(), "")

        source = self.base / "source"
        frames = self.base / "frames"
        source.mkdir()
        frames.mkdir()
        localization.remember_path("video_input", source)
        localization.remember_path("frames_output", frames)
        window = self.make_video_window()
        self.assertEqual(Path(window.input_dir.get()), source.resolve())
        self.assertEqual(Path(window.output_dir.get()), frames.resolve())

    def test_output_choice_is_remembered_per_operation(self) -> None:
        window = self.make_video_window()
        frames = self.base / "frames"
        frames.mkdir()
        with patch("video_processing.filedialog.askdirectory", return_value=str(frames)) as ask:
            window._choose_output()
        self.assertEqual(Path(ask.call_args.kwargs["initialdir"]), Path.home())
        self.assertEqual(localization.remembered_path("frames_output"), frames.resolve())
        self.assertIsNone(localization.remembered_path("video_output"))

    def test_start_requires_input_and_output(self) -> None:
        window = self.make_video_window()
        with patch("video_processing.messagebox.showerror") as error:
            window.start()
        self.assertIn("Choose a video", error.call_args.args[1])

        video = self.base / "clip.mp4"
        video.write_bytes(b"")
        window.input_dir.set(str(video))
        window.output_dir.set("")
        with patch("video_processing.messagebox.showerror") as error:
            window.start()
        self.assertIn("Choose an output folder", error.call_args.args[1])
        self.assertIsNone(window.worker)

    def test_annotator_remembers_image_folder(self) -> None:
        images = self.base / "images"
        images.mkdir()
        Image.new("RGB", (20, 10), "white").save(images / "a.png")
        window = tk.Toplevel(self.root)
        self.addCleanup(window.destroy)
        with patch.object(PointAnnotator, "_read_point_names", return_value=["nose"]):
            with patch.object(window, "after", return_value="startup"):
                app = PointAnnotator(window, images)
        with patch("point_annotator.filedialog.askdirectory", return_value="") as ask:
            app.choose_folder()
        self.assertEqual(ask.call_args.kwargs["initialdir"], Path.home())

        app.load_folder(images)
        self.assertEqual(localization.remembered_path("annotation_folder"), images.resolve())
        app.current_folder = None
        with patch("point_annotator.filedialog.askdirectory", return_value="") as ask:
            app.choose_folder()
        self.assertEqual(Path(ask.call_args.kwargs["initialdir"]), images.resolve())


if __name__ == "__main__":
    unittest.main()
