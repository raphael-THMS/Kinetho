from __future__ import annotations

import csv
import math
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from point_annotator import PointAnnotator, ScaleDialog
from scale_calibration import SCALE_COLUMNS, ScaleCalibration


class CalibrationTests(unittest.TestCase):
    def test_distance_and_conversion(self) -> None:
        scale = ScaleCalibration("image.png", (10, 20), (40, 60), 10, "cm")
        self.assertEqual(scale.pixels, 50)
        self.assertEqual(float(scale.to_csv()["scale_units_per_pixel"]), 0.2)
        self.assertEqual(ScaleCalibration.from_csv(scale.to_csv()), scale)

    def test_legacy_and_empty_columns(self) -> None:
        self.assertIsNone(ScaleCalibration.from_csv({"image": "image.png", "x": "1", "y": "2"}))
        self.assertIsNone(ScaleCalibration.from_csv(dict.fromkeys(SCALE_COLUMNS, "")))

    def test_invalid_scales(self) -> None:
        for length in (0, -1, math.inf, math.nan):
            with self.subTest(length=length), self.assertRaises(ValueError):
                ScaleCalibration("image.png", (0, 0), (3, 4), length, "cm")
        for start, end in (((1, 1), (1, 1)), ((-1, 0), (1, 1)), ((0, 0), (math.nan, 2))):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                ScaleCalibration("image.png", start, end, 10, "cm")
        for image, unit in (("", "cm"), ("image.png", " ")):
            with self.subTest(image=image, unit=unit), self.assertRaises(ValueError):
                ScaleCalibration(image, (0, 0), (3, 4), 10, unit)
        with self.assertRaises(ValueError):
            ScaleCalibration.from_csv({"scale_image": "image.png"})


class AnnotatorScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        settings_patch = patch("localization.settings_directory", return_value=self.folder)
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        for name in ("a.png", "b.png"):
            Image.new("RGB", (200, 100), "white").save(self.folder / name)
        self.window = tk.Toplevel(self.root)
        self.addCleanup(self.window.destroy)
        with patch.object(PointAnnotator, "_read_point_names", return_value=["Scale", "nose"]):
            with patch.object(self.window, "after", return_value="startup"):
                self.app = PointAnnotator(self.window, self.folder)
        self.app.language = "fr"
        self.app.load_folder(self.folder)
        self.window.update()
        self.app.redraw()
        self.app.select_point(0)
        self.errors = patch("point_annotator.messagebox.showerror").start()
        self.addCleanup(patch.stopall)

    def click(self, x: float, y: float) -> None:
        sx, sy = self.app.image_to_screen(x, y)
        event = SimpleNamespace(x=sx, y=sy)
        self.app.on_canvas_click(event)
        self.app.on_canvas_release(event)

    def define(self, length: str = "10,5", unit: str = "cm", export_real: bool = False) -> None:
        def fill_dialog(
            parent: tk.Misc, language: str, initial_length: float, initial_unit: str, initial_export_real: bool,
        ) -> ScaleDialog:
            with patch.object(ScaleDialog, "wait_window"):
                dialog = ScaleDialog(parent, language, initial_length, initial_unit, initial_export_real)
            dialog.length_entry.delete(0, "end")
            dialog.length_entry.insert(0, length)
            dialog.unit_entry.delete(0, "end")
            dialog.unit_entry.insert(0, unit)
            dialog.export_real.set(export_real)
            dialog.ok()
            if dialog.winfo_exists():
                dialog.cancel()
            return dialog

        with patch("point_annotator.ScaleDialog", side_effect=fill_dialog):
            self.app.define_scale()

    def read_rows(self) -> list[dict[str, str]]:
        with (self.folder / "annotations.csv").open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    def test_two_clicks_export_reload_and_navigation(self) -> None:
        self.define()
        self.click(10, 20)
        self.assertIsNone(self.app.calibration)
        self.assertFalse((self.folder / "annotations.csv").exists())
        self.click(40, 60)
        expected = ScaleCalibration("a.png", (10, 20), (40, 60), 10.5, "cm")
        self.assertEqual(self.app.calibration, expected)
        self.assertEqual(self.app.current_index, 0)
        self.assertEqual(self.app.point_names, ["Scale", "nose"])
        self.assertEqual(self.app.tool_mode.get(), "point")
        rows = self.read_rows()
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["scale_image"], "a.png")
        self.assertEqual(rows[0]["scale_x1"], "10.0")
        self.assertEqual(rows[0]["scale_y2"], "60.0")
        self.assertEqual(float(rows[0]["scale_pixels"]), 50)
        self.assertEqual(float(rows[0]["scale_units_per_pixel"]), 0.21)
        self.assertTrue(all(row["x"] == row["y"] == "" for row in rows))
        self.app.next_image()
        self.assertEqual(self.app.calibration, expected)
        self.assertEqual(self.app.current_index, 1)
        self.app.show_scale_image()
        self.assertEqual(self.app.current_index, 0)
        self.app.calibration = None
        self.assertTrue(self.app.load_annotations())
        self.assertEqual(self.app.calibration, expected)
        self.errors.assert_not_called()

    def test_original_coordinates_with_zoom_and_pan(self) -> None:
        self.app.display_scale = 2.5
        self.app.display_offset = (-50, 30)
        self.app.display_size = (500, 250)
        self.define()
        # Defining the scale redraws using the real canvas transform.
        self.app.display_scale = 2.5
        self.app.display_offset = (-50, 30)
        self.app.display_size = (500, 250)
        self.click(40, 20)
        # The first marker redraw recalculates the transform; click uses that transform.
        self.click(80, 50)
        self.assertEqual(self.app.calibration.start, (40, 20))
        self.assertEqual(self.app.calibration.end, (80, 50))

    def test_identical_endpoints_can_be_corrected(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(10, 20)
        self.errors.assert_called_once()
        self.assertIsNone(self.app.calibration)
        self.assertEqual(self.app.tool_mode.get(), "scale")
        self.click(40, 60)
        self.assertIsNotNone(self.app.calibration)

    def test_cancel_and_navigation_preserve_existing_scale(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        previous = self.app.calibration
        self.define()
        self.click(80, 80)
        self.app.next_image()
        self.assertIsNone(self.app.scale_start)
        self.assertEqual(self.app.calibration, previous)
        self.assertEqual(self.app.tool_mode.get(), "point")
        self.define()
        self.click(30, 30)
        self.app.delete_selected_point()
        self.assertEqual(self.app.calibration, previous)
        self.assertIsNone(self.app.scale_start)

    def test_invalid_length_and_unit(self) -> None:
        for value in ("0", "-2", "nan", "inf", "bad"):
            with self.subTest(value=value):
                self.define(value)
                self.assertEqual(self.app.tool_mode.get(), "point")
                self.assertIsNone(self.app.calibration)
        self.define("10", " ")
        self.assertEqual(self.app.tool_mode.get(), "point")
        with patch("point_annotator.ScaleDialog") as dialog:
            dialog.return_value.result = None
            self.app.define_scale()
        self.assertIsNone(self.app.calibration)

    def test_length_and_unit_share_one_dialog_with_inline_validation(self) -> None:
        with patch.object(ScaleDialog, "wait_window"):
            dialog = ScaleDialog(self.window, "fr", 10, "cm")
        self.addCleanup(dialog.destroy)
        self.assertEqual(dialog.length_entry.master, dialog.unit_entry.master)
        self.assertEqual(dialog.length_entry.get(), "10")
        self.assertEqual(dialog.unit_entry.get(), "cm")
        dialog.length_entry.delete(0, "end")
        dialog.length_entry.insert(0, "invalid")
        dialog.ok()
        self.assertTrue(dialog.winfo_exists())
        self.assertIsNone(dialog.result)
        self.assertTrue(dialog.error_label.cget("text"))
        dialog.length_entry.delete(0, "end")
        dialog.length_entry.insert(0, "12,5")
        self.assertTrue(dialog.validate())
        dialog.apply()
        self.assertEqual(dialog.result, (12.5, "cm", False))
        self.errors.assert_not_called()

    def test_cancel_dialog_preserves_existing_scale(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        previous = self.app.calibration
        with patch("point_annotator.ScaleDialog") as dialog:
            dialog.return_value.result = None
            self.app.define_scale()
        self.assertEqual(self.app.calibration, previous)
        self.assertEqual(self.app.tool_mode.get(), "point")

    def test_remove_restores_legacy_export_and_preserves_points(self) -> None:
        self.app.annotations["a.png"]["nose"] = (1.25, 2.5)
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        with patch("point_annotator.messagebox.askyesno", return_value=True):
            self.app.remove_scale()
        self.assertIsNone(self.app.calibration)
        rows = self.read_rows()
        self.assertEqual(list(rows[0]), ["image", "point", "x", "y"])
        self.assertEqual(rows[1]["x"], "1.25")
        self.assertTrue(self.app.load_annotations())
        self.assertEqual(self.app.annotations["a.png"]["nose"], (1.25, 2.5))

    def test_corrupt_scale_does_not_replace_open_folder(self) -> None:
        other = self.folder / "other"
        other.mkdir()
        Image.new("RGB", (200, 100)).save(other / "a.png")
        bad_csv = other / "annotations.csv"
        bad_csv.write_text("image,point,x,y,scale_image\na.png,nose,1,2,a.png\n", encoding="utf-8")
        before = bad_csv.read_bytes()
        self.app.load_folder(other)
        self.errors.assert_called_once()
        self.assertEqual(self.app.current_folder, self.folder)
        self.assertEqual(bad_csv.read_bytes(), before)

    def test_new_folder_does_not_inherit_scale(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        other = self.folder / "other"
        other.mkdir()
        Image.new("RGB", (200, 100)).save(other / "a.png")
        self.app.load_folder(other)
        self.assertIsNone(self.app.calibration)
        self.app.load_folder(self.folder)
        self.assertIsNotNone(self.app.calibration)

    def test_failed_save_keeps_calibration_and_navigation(self) -> None:
        self.define()
        self.click(10, 20)
        with patch.object(Path, "replace", side_effect=PermissionError("locked CSV")):
            self.click(40, 60)
            self.assertIsNone(self.app.calibration)
            self.app.next_image()
            self.assertEqual(self.app.current_index, 0)
        self.assertEqual(self.errors.call_count, 2)

    def test_normal_point_placement_still_advances(self) -> None:
        self.click(10, 20)
        self.assertEqual(self.app.annotations["a.png"]["Scale"], (10, 20))
        self.assertEqual(self.app.current_index, 1)
        self.assertIsNone(self.app.calibration)

    def test_scale_controls_are_visible(self) -> None:
        self.window.geometry("760x520")
        self.window.update()
        self.assertGreater(self.app.point_list.winfo_height(), 30)
        self.assertEqual(self.app.scale_hint.winfo_manager(), "")
        self.assertLess(
            self.app.scale_button.winfo_rooty() + self.app.scale_button.winfo_height(),
            self.window.winfo_rooty() + self.window.winfo_height(),
        )
        self.assertEqual(self.app.scale_menu.entrycget(3, "state"), "disabled")
        self.define()
        self.window.update()
        self.assertEqual(self.app.scale_hint.winfo_manager(), "pack")
        self.assertEqual(self.app.scale_hint.cget("text"), "Cliquez sur la première extrémité de l’échelle.")
        self.click(10, 20)
        self.assertEqual(self.app.scale_hint.cget("text"), "Cliquez sur la seconde extrémité de l’échelle.")
        self.click(40, 60)
        self.assertEqual(self.app.scale_hint.winfo_manager(), "")
        self.assertEqual(self.app.scale_menu.entrycget(3, "state"), "normal")
        self.assertIn("a.png", self.app.scale_menu.entrycget(0, "label"))

    def test_real_export_and_reload_preserve_original_pixels(self) -> None:
        self.app.annotations["a.png"]["nose"] = (100.25, 50.5)
        self.define("10", "cm", export_real=True)
        self.click(10, 20)
        self.click(40, 60)
        rows = self.read_rows()
        nose = rows[1]
        self.assertAlmostEqual(float(nose["x"]), 20.05)
        self.assertAlmostEqual(float(nose["y"]), 10.1)
        self.assertEqual(nose["coordinate_unit"], "cm")
        self.assertEqual(nose["coordinate_space"], "real")
        self.assertEqual(float(nose["x_pixel"]), 100.25)
        self.assertEqual(float(nose["y_pixel"]), 50.5)
        self.assertEqual(rows[0]["x"], "")
        self.assertEqual(rows[0]["x_pixel"], "")
        self.app.annotations["a.png"]["nose"] = None
        self.assertTrue(self.app.load_annotations())
        self.assertTrue(self.app.calibration.export_real)
        self.assertEqual(self.app.annotations["a.png"]["nose"], (100.25, 50.5))
        self.assertTrue(self.app.save_annotations())
        self.assertEqual(self.read_rows(), rows)
        self.app.next_image()
        self.assertEqual(self.app.calibration.unit, "cm")
        self.assertIn("Sortie : cm", self.app.scale_menu.entrycget(0, "label"))

    def test_pixels_choice_and_scale_replacement_recompute_export(self) -> None:
        self.app.annotations["a.png"]["nose"] = (100, 50)
        for length, real, expected in (("10", True, 20), ("20", True, 40), ("20", False, 100)):
            self.define(length, "mm", export_real=real)
            self.click(10, 20)
            self.click(40, 60)
            row = self.read_rows()[1]
            self.assertEqual(float(row["x"]), expected)
            self.assertEqual(row["coordinate_unit"], "mm" if real else "px")
            self.assertEqual(row["coordinate_space"], "real" if real else "pixel")
        with patch("point_annotator.messagebox.askyesno", return_value=True):
            self.app.remove_scale()
        self.assertEqual(float(self.read_rows()[1]["x"]), 100)
        self.assertEqual(list(self.read_rows()[1]), ["image", "point", "x", "y"])

    def test_cancelled_real_scale_keeps_previous_export(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        previous = self.app.calibration
        self.define(export_real=True)
        self.click(50, 50)
        self.app.delete_selected_point()
        self.assertEqual(self.app.calibration, previous)
        self.assertFalse(self.app.calibration.export_real)
        self.app.save_annotations()
        self.assertEqual(self.read_rows()[0]["coordinate_space"], "pixel")

    def test_legacy_calibration_without_export_metadata_loads_as_pixels(self) -> None:
        self.define()
        self.click(10, 20)
        self.click(40, 60)
        rows = self.read_rows()
        fields = [name for name in rows[0] if name not in {"coordinate_space", "coordinate_unit"}]
        with (self.folder / "annotations.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        self.assertTrue(self.app.load_annotations())
        self.assertFalse(self.app.calibration.export_real)

    def test_real_export_missing_original_pixels_is_rejected(self) -> None:
        self.define(export_real=True)
        self.click(10, 20)
        self.click(40, 60)
        rows = self.read_rows()
        fields = [name for name in rows[0] if name not in {"x_pixel", "y_pixel"}]
        with (self.folder / "annotations.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        self.assertFalse(self.app.load_annotations())
        self.errors.assert_called_once()

    def test_close_without_scale_offers_return_or_save_and_close(self) -> None:
        with patch("point_annotator.messagebox.askyesno", return_value=False) as warning:
            with patch.object(self.window, "destroy") as destroy:
                self.app.close()
                warning.assert_called_once()
                self.assertIn("pixels", warning.call_args.args[1])
                self.assertEqual(warning.call_args.kwargs["default"], "no")
                destroy.assert_not_called()
        with patch("point_annotator.messagebox.askyesno", return_value=True):
            with patch.object(self.window, "destroy") as destroy:
                self.app.close()
                destroy.assert_called_once()
                self.assertEqual(list(self.read_rows()[0]), ["image", "point", "x", "y"])

    def test_close_with_scale_or_no_folder_has_no_warning(self) -> None:
        with patch("point_annotator.messagebox.askyesno") as warning:
            with patch.object(self.window, "destroy") as destroy:
                self.define()
                self.click(10, 20)
                self.click(40, 60)
                self.app.close()
                destroy.assert_called_once()
                warning.assert_not_called()
        self.app.image_paths = []
        self.app.current_folder = None
        self.app.calibration = None
        with patch("point_annotator.messagebox.askyesno") as warning:
            with patch.object(self.window, "destroy"):
                self.app.close()
                warning.assert_not_called()

    def test_close_after_confirmed_warning_stays_open_on_save_error(self) -> None:
        with patch("point_annotator.messagebox.askyesno", return_value=True):
            with patch.object(Path, "replace", side_effect=PermissionError("locked CSV")):
                with patch.object(self.window, "destroy") as destroy:
                    self.app.close()
                    destroy.assert_not_called()
        self.errors.assert_called_once()


if __name__ == "__main__":
    unittest.main()
