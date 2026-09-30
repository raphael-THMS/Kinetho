from __future__ import annotations

import csv
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from branding import BRAND_BACKGROUND, BRAND_BLACK, BRAND_NAME, BRAND_RED, load_logo, load_window_icon
from localization import load_language, translate


APP_DIR = Path(__file__).resolve().parent
FROZEN = getattr(sys, "frozen", False)
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else APP_DIR.parent
INPUT_DIR = APP_ROOT / "Image folders"
POINTS_FILE = (APP_ROOT if FROZEN else APP_DIR) / "points.txt"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
POINT_COLORS = [
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#fabed4",
    "#469990",
    "#dcbeff",
    "#9a6324",
    "#800000",
    "#aaffc3",
    "#808000",
    "#000075",
    "#e6ab02",
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#a6761d",
    "#666666",
]


class PointAnnotator:
    def __init__(self, root: tk.Tk, initial_folder: Path | None = None) -> None:
        self.root = root
        self.language = load_language()
        self.root.title(f"{BRAND_NAME} | {translate('Point Annotator', self.language)}")
        self.root.geometry("1180x780")
        self.root.minsize(760, 520)
        self.root.configure(background=BRAND_BACKGROUND)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BRAND_BACKGROUND)
        style.configure("TLabel", background=BRAND_BACKGROUND, foreground=BRAND_BLACK)
        style.configure("TButton", foreground=BRAND_BLACK)
        style.configure("TCheckbutton", background=BRAND_BACKGROUND, foreground=BRAND_BLACK)
        self.brand_logo = load_logo(root, (54, 40))
        self.window_icon = load_window_icon(root)
        if self.window_icon is not None:
            self.root.iconphoto(True, self.window_icon)

        self.point_names = self._read_point_names()
        self.image_paths: list[Path] = []
        self.current_index = 0
        self.current_folder: Path | None = None
        self.annotations: dict[str, dict[str, tuple[float, float] | None]] = {}
        self.image: Image.Image | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.display_scale = 1.0
        self.display_offset = (0.0, 0.0)
        self.display_size = (0, 0)

        self._build_interface()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Left>", lambda _event: self.previous_image())
        self.root.bind("<Right>", lambda _event: self.next_image())
        self.root.bind("<Delete>", lambda _event: self.delete_selected_point())
        self.root.bind("<BackSpace>", lambda _event: self.delete_selected_point())

        if not self.point_names:
            messagebox.showerror(
                translate("No points configured", self.language),
                translate("Add at least one point name to points.txt, then restart the application.", self.language),
            )
            self.root.after(0, self.root.destroy)
            return

        self.select_point(0)
        if initial_folder is None:
            self.root.after(100, self.open_default_folder)
        else:
            self.root.after(100, lambda: self.load_folder(initial_folder))

    def _read_point_names(self) -> list[str]:
        try:
            lines = POINTS_FILE.read_text(encoding="utf-8-sig").splitlines()
        except OSError as exc:
            messagebox.showerror(translate("points.txt not found", self.language), str(exc))
            return []

        names = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
        if len(names) != len(set(names)):
            messagebox.showerror(
                translate("Duplicate point names", self.language),
                translate("Each point name in points.txt must be unique.", self.language),
            )
            return []
        return names

    def _build_interface(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(10, 8))
        toolbar.pack(side="top", fill="x")

        if self.brand_logo is not None:
            ttk.Label(toolbar, image=self.brand_logo).pack(side="left", padx=(0, 10))
        ttk.Button(
            toolbar,
            text=translate("Open image folder", self.language),
            command=self.choose_folder,
        ).pack(side="left")
        self.auto_advance = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text=translate("Advance after placing a point", self.language),
            variable=self.auto_advance,
        ).pack(side="right", padx=(12, 0))
        self.folder_label = ttk.Label(toolbar, text=translate("No folder open", self.language), anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(12, 0))

        content = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        content.pack(side="top", fill="both", expand=True)

        side_panel = ttk.Frame(content, width=220)
        side_panel.pack(side="left", fill="y", padx=(0, 10))
        side_panel.pack_propagate(False)

        ttk.Label(
            side_panel,
            text=translate("Points to annotate", self.language),
            font=("Segoe UI", 11, "bold"),
            foreground=BRAND_RED,
        ).pack(anchor="w", pady=(4, 6))
        self.point_list = tk.Listbox(side_panel, exportselection=False, activestyle="dotbox", font=("Segoe UI", 10))
        self.point_list.pack(fill="both", expand=True)
        self.point_list.bind("<<ListboxSelect>>", self.on_point_selected)
        self.point_list.bind("<Double-Button-1>", self.on_point_selected)
        for index, name in enumerate(self.point_names):
            self.point_list.insert("end", name)
            self.point_list.itemconfigure(index, foreground=self.point_color(name))

        ttk.Label(
            side_panel,
            text=translate(
                "Select a point, then click the image to place it. Click again to move that point.",
                self.language,
            ),
            wraplength=205,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))
        ttk.Button(
            side_panel,
            text=translate("Delete selected point", self.language),
            command=self.delete_selected_point,
        ).pack(
            fill="x", pady=(10, 0)
        )

        self.canvas = tk.Canvas(content, background="#202428", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Button-3>", lambda _event: self.delete_selected_point())

        navigation = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        navigation.pack(side="bottom", fill="x")
        self.previous_button = ttk.Button(
            navigation, text=translate("Previous image", self.language), command=self.previous_image
        )
        self.previous_button.pack(side="left")
        self.next_button = ttk.Button(
            navigation, text=translate("Next image", self.language), command=self.next_image
        )
        self.next_button.pack(side="left", padx=(6, 0))
        self.image_status = ttk.Label(navigation, text=translate("No image", self.language), anchor="center")
        self.image_status.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(
            navigation,
            text=translate("Left/right arrows: navigate | Delete: remove point", self.language),
        ).pack(side="right")

    def point_color(self, name: str) -> str:
        return POINT_COLORS[self.point_names.index(name) % len(POINT_COLORS)]

    def choose_folder(self) -> None:
        initial_dir = self.current_folder or (INPUT_DIR if INPUT_DIR.is_dir() else APP_DIR.parent)
        folder = filedialog.askdirectory(
            title=translate("Select the folder containing images", self.language), initialdir=initial_dir
        )
        if folder:
            self.load_folder(Path(folder))

    def open_default_folder(self) -> None:
        if INPUT_DIR.is_dir() and any(path.is_file() for path in INPUT_DIR.iterdir()):
            self.load_folder(INPUT_DIR)
        else:
            self.choose_folder()

    def load_folder(self, folder: Path) -> None:
        paths = sorted(
            (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS),
            key=lambda path: path.name.casefold(),
        )
        if not paths:
            messagebox.showwarning(
                translate("No images found", self.language),
                translate("This folder contains no supported image files.", self.language),
            )
            return

        if self.current_folder is not None:
            self.save_annotations()

        self.current_folder = folder
        self.image_paths = paths
        self.current_index = 0
        self.annotations = {path.name: {name: None for name in self.point_names} for path in paths}
        self.load_annotations()
        self.folder_label.configure(text=str(folder))
        self.show_current_image()

    @property
    def csv_path(self) -> Path | None:
        if self.current_folder is None:
            return None
        return self.current_folder / "annotations.csv"

    def load_annotations(self) -> None:
        csv_path = self.csv_path
        if csv_path is None or not csv_path.exists():
            return
        try:
            with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
                for row in csv.DictReader(csv_file):
                    image_name = row.get("image", "")
                    point_name = row.get("point", "")
                    if image_name not in self.annotations or point_name not in self.point_names:
                        continue
                    x_value, y_value = row.get("x", ""), row.get("y", "")
                    if x_value and y_value:
                        self.annotations[image_name][point_name] = (float(x_value), float(y_value))
        except (OSError, ValueError, csv.Error) as exc:
            messagebox.showerror(
                translate("Read error", self.language),
                translate("Could not read {path}:\n{error}", self.language).format(path=csv_path, error=exc),
            )

    def save_annotations(self) -> None:
        csv_path = self.csv_path
        if csv_path is None:
            return
        temporary_path = csv_path.with_suffix(".csv.tmp")
        try:
            with temporary_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["image", "point", "x", "y"])
                for image_path in self.image_paths:
                    for point_name in self.point_names:
                        coordinate = self.annotations[image_path.name][point_name]
                        writer.writerow(
                            [image_path.name, point_name, coordinate[0], coordinate[1]]
                            if coordinate is not None
                            else [image_path.name, point_name, "", ""]
                        )
            temporary_path.replace(csv_path)
        except OSError as exc:
            messagebox.showerror(
                translate("Save error", self.language),
                translate("Could not write {path}:\n{error}", self.language).format(path=csv_path, error=exc),
            )

    def current_image_name(self) -> str:
        return self.image_paths[self.current_index].name

    def show_current_image(self) -> None:
        if not self.image_paths:
            return
        image_path = self.image_paths[self.current_index]
        try:
            with Image.open(image_path) as source:
                self.image = source.convert("RGB")
        except OSError as exc:
            messagebox.showerror(
                translate("Unreadable image", self.language),
                translate("Could not open {path}:\n{error}", self.language).format(path=image_path, error=exc),
            )
            self.next_image()
            return
        self.redraw()
        self.update_status()

    def redraw(self) -> None:
        self.canvas.delete("all")
        if self.image is None:
            return
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_width < 2 or canvas_height < 2:
            return
        image_width, image_height = self.image.size
        self.display_scale = min(canvas_width / image_width, canvas_height / image_height, 1.0)
        self.display_size = (
            max(1, round(image_width * self.display_scale)),
            max(1, round(image_height * self.display_scale)),
        )
        self.display_offset = (
            (canvas_width - self.display_size[0]) / 2,
            (canvas_height - self.display_size[1]) / 2,
        )
        rendered = self.image.resize(self.display_size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(rendered)
        self.canvas.create_image(*self.display_offset, image=self.photo, anchor="nw")

        image_annotations = self.annotations.get(self.current_image_name(), {})
        for point_name in self.point_names:
            coordinate = image_annotations.get(point_name)
            if coordinate is None:
                continue
            screen_x, screen_y = self.image_to_screen(*coordinate)
            color = self.point_color(point_name)
            radius = 6
            self.canvas.create_oval(
                screen_x - radius,
                screen_y - radius,
                screen_x + radius,
                screen_y + radius,
                fill=color,
                outline="white",
                width=2,
            )
            self.canvas.create_text(
                screen_x + 10,
                screen_y - 10,
                text=point_name,
                fill="white",
                anchor="sw",
                font=("Segoe UI", 10, "bold"),
            )

    def image_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.display_offset[0] + x * self.display_scale,
            self.display_offset[1] + y * self.display_scale,
        )

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.image is None or self.current_index >= len(self.image_paths):
            return
        offset_x, offset_y = self.display_offset
        shown_width, shown_height = self.display_size
        if not (offset_x <= event.x <= offset_x + shown_width and offset_y <= event.y <= offset_y + shown_height):
            return
        selection = self.point_list.curselection()
        if not selection:
            return
        x = min(max((event.x - offset_x) / self.display_scale, 0), self.image.width - 1)
        y = min(max((event.y - offset_y) / self.display_scale, 0), self.image.height - 1)
        point_name = self.point_names[selection[0]]
        self.annotations[self.current_image_name()][point_name] = (round(x, 2), round(y, 2))
        self.redraw()
        self.update_status()
        if self.auto_advance.get():
            self.next_image()

    def on_point_selected(self, _event: tk.Event | None = None) -> None:
        self.update_status()

    def select_point(self, index: int) -> None:
        self.point_list.selection_clear(0, "end")
        self.point_list.selection_set(index)
        self.point_list.activate(index)
        self.point_list.see(index)

    def delete_selected_point(self) -> None:
        selection = self.point_list.curselection()
        if not selection or not self.image_paths:
            return
        point_name = self.point_names[selection[0]]
        self.annotations[self.current_image_name()][point_name] = None
        self.redraw()
        self.update_status()

    def previous_image(self) -> None:
        if self.current_index <= 0:
            return
        self.save_annotations()
        self.current_index -= 1
        self.show_current_image()

    def next_image(self) -> None:
        if not self.image_paths:
            return
        self.save_annotations()
        if self.current_index >= len(self.image_paths) - 1:
            return
        self.current_index += 1
        self.show_current_image()

    def update_status(self) -> None:
        if not self.image_paths:
            self.image_status.configure(text=translate("No image", self.language))
            return
        values = self.annotations[self.current_image_name()]
        placed = sum(value is not None for value in values.values())
        selection = self.point_list.curselection()
        selected_name = self.point_names[selection[0]] if selection else translate("no point selected", self.language)
        self.image_status.configure(
            text=translate(
                "Image {index}/{total}: {name}  |  {placed}/{count} points placed  |  Selected: {selected}",
                self.language,
            ).format(
                index=self.current_index + 1,
                total=len(self.image_paths),
                name=self.current_image_name(),
                placed=placed,
                count=len(self.point_names),
                selected=selected_name,
            )
        )
        self.previous_button.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_index < len(self.image_paths) - 1 else "disabled")

    def close(self) -> None:
        self.save_annotations()
        self.root.destroy()


def run(initial_folder: Path | None = None) -> None:
    root = tk.Tk()
    PointAnnotator(root, initial_folder)
    root.mainloop()


def main() -> None:
    initial_folder = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
    run(initial_folder)


if __name__ == "__main__":
    main()
