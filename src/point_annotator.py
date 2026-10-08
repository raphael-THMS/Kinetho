from __future__ import annotations

import csv
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from branding import BRAND_BACKGROUND, BRAND_BLACK, BRAND_NAME, BRAND_RED, load_logo, load_window_icon
from localization import load_language, translate
from app_paths import WORKSPACE_DIR, points_file


APP_DIR = Path(__file__).resolve().parent
FROZEN = getattr(sys, "frozen", False)
APP_ROOT = WORKSPACE_DIR
INPUT_DIR = APP_ROOT / "Image folders"
POINTS_FILE = points_file()
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
        self.base_scale = 1.0
        self.display_offset = (0.0, 0.0)
        self.display_size = (0, 0)
        self.zoom_factor = 1.0
        self.pan_offset = (0.0, 0.0)
        self.pan_start: tuple[float, float] | None = None
        self.tool_mode = tk.StringVar(master=root, value="point")
        self.annotation_mode = tk.StringVar(master=root, value="point_by_point")
        self.zoom_preview_id: str | None = None
        self.zoom_quality_id: str | None = None
        self.active_point_drag: str | None = None
        self.advance_after_point_drag = False

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
        self.folder_label = ttk.Label(toolbar, text=translate("No folder open", self.language), anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(12, 0))

        content = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        content.pack(side="top", fill="both", expand=True)

        side_panel = ttk.Frame(content, width=220)
        side_panel.pack(side="left", fill="y", padx=(0, 10))
        side_panel.pack_propagate(False)

        points_section = ttk.Frame(side_panel)
        points_section.pack(side="top", fill="both", expand=True)
        ttk.Label(
            points_section,
            text=translate("Points to annotate", self.language),
            font=("Segoe UI", 11, "bold"),
            foreground=BRAND_RED,
        ).pack(anchor="w", pady=(4, 6))
        point_list_frame = ttk.Frame(points_section)
        point_list_frame.pack(fill="both", expand=True)
        self.point_list = tk.Listbox(
            point_list_frame, exportselection=False, activestyle="dotbox", font=("Segoe UI", 10)
        )
        self.point_list.pack(side="left", fill="both", expand=True)
        point_scrollbar = ttk.Scrollbar(point_list_frame, orient="vertical", command=self.point_list.yview)
        point_scrollbar.pack(side="right", fill="y")
        self.point_list.configure(yscrollcommand=point_scrollbar.set)
        self.point_list.bind("<<ListboxSelect>>", self.on_point_selected)
        self.point_list.bind("<Double-Button-1>", self.on_point_selected)
        self.point_list.bind("<MouseWheel>", self._scroll_point_list)
        self.point_list.bind("<Button-4>", self._scroll_point_list)
        self.point_list.bind("<Button-5>", self._scroll_point_list)
        for index, name in enumerate(self.point_names):
            self.point_list.insert("end", name)
            self.point_list.itemconfigure(index, foreground=self.point_color(name))

        mode_section = ttk.Frame(side_panel)
        mode_section.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Separator(mode_section).pack(fill="x", pady=(0, 10))
        ttk.Label(
            mode_section,
            text=translate("Modes", self.language),
            font=("Segoe UI", 11, "bold"),
            foreground=BRAND_RED,
        ).pack(anchor="w", pady=(0, 6))
        ttk.Radiobutton(
            mode_section,
            text=translate("Point by point", self.language),
            value="point_by_point",
            variable=self.annotation_mode,
        ).pack(fill="x", pady=2)
        ttk.Radiobutton(
            mode_section,
            text=translate("Scroll through points", self.language),
            value="scroll_points",
            variable=self.annotation_mode,
        ).pack(fill="x", pady=2)

        tools_section = ttk.Frame(side_panel)
        tools_section.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Separator(tools_section).pack(fill="x", pady=(0, 10))
        ttk.Label(
            tools_section,
            text=translate("Tools", self.language),
            font=("Segoe UI", 11, "bold"),
            foreground=BRAND_RED,
        ).pack(anchor="w", pady=(0, 6))
        ttk.Radiobutton(
            tools_section,
            text=translate("Place points", self.language),
            value="point",
            variable=self.tool_mode,
            command=self._update_canvas_tool,
        ).pack(fill="x", pady=2)
        ttk.Radiobutton(
            tools_section,
            text=translate("Move image", self.language),
            value="pan",
            variable=self.tool_mode,
            command=self._update_canvas_tool,
        ).pack(fill="x", pady=2)
        ttk.Label(
            tools_section,
            text=translate("Drag to place or move points | Move mode: click a point to select it", self.language),
            wraplength=205,
            justify="left",
            foreground="#5c5c5c",
        ).pack(anchor="w", pady=(6, 0))
        ttk.Button(
            tools_section,
            text=translate("Delete selected point", self.language),
            command=self.delete_selected_point,
        ).pack(
            fill="x", pady=(8, 0)
        )

        self.canvas = tk.Canvas(content, background="#202428", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)
        self.canvas.bind("<Button-4>", self.on_canvas_zoom)
        self.canvas.bind("<Button-5>", self.on_canvas_zoom)
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
        self._cancel_zoom_redraws()
        self.zoom_factor = 1.0
        self.pan_offset = (0.0, 0.0)
        self.pan_start = None
        self.redraw()
        self.update_status()

    def redraw(self, interactive: bool = False) -> None:
        self.canvas.delete("all")
        if self.image is None:
            return
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_width < 2 or canvas_height < 2:
            return
        image_width, image_height = self.image.size
        self.base_scale = min(canvas_width / image_width, canvas_height / image_height, 1.0)
        self.display_scale = self.base_scale * self.zoom_factor
        self.display_size = (
            max(1, round(image_width * self.display_scale)),
            max(1, round(image_height * self.display_scale)),
        )
        self.display_offset = (
            (canvas_width - self.display_size[0]) / 2 + self.pan_offset[0],
            (canvas_height - self.display_size[1]) / 2 + self.pan_offset[1],
        )
        resampling = Image.Resampling.BILINEAR if interactive else Image.Resampling.LANCZOS
        rendered = self.image.resize(self.display_size, resampling)
        self.photo = ImageTk.PhotoImage(rendered)
        self.canvas.delete("view")
        self.canvas.create_image(*self.display_offset, image=self.photo, anchor="nw", tags=("view",))

        image_annotations = self.annotations.get(self.current_image_name(), {})
        for point_index, point_name in enumerate(self.point_names):
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
                tags=("view",),
            )
            marker_id = self.canvas.find_all()[-1]
            self.canvas.addtag_withtag(f"point-marker-{point_index}", marker_id)
            self.canvas.create_text(
                screen_x + 10,
                screen_y - 10,
                text=point_name,
                fill="white",
                anchor="sw",
                font=("Segoe UI", 10, "bold"),
                tags=("view",),
            )
            label_id = self.canvas.find_all()[-1]
            self.canvas.addtag_withtag(f"point-label-{point_index}", label_id)

    def image_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.display_offset[0] + x * self.display_scale,
            self.display_offset[1] + y * self.display_scale,
        )

    def _scroll_point_list(self, event: tk.Event) -> str:
        if getattr(event, "delta", 0):
            direction = -1 if event.delta > 0 else 1
        else:
            direction = -1 if event.num == 4 else 1
        self.point_list.yview_scroll(direction, "units")
        return "break"

    def _update_canvas_tool(self) -> None:
        self.pan_start = None
        self.canvas.configure(cursor="fleur" if self.tool_mode.get() == "pan" else "crosshair")

    def _cancel_zoom_redraws(self) -> None:
        if self.zoom_preview_id is not None:
            self.root.after_cancel(self.zoom_preview_id)
            self.zoom_preview_id = None
        if self.zoom_quality_id is not None:
            self.root.after_cancel(self.zoom_quality_id)
            self.zoom_quality_id = None

    def on_canvas_zoom(self, event: tk.Event) -> str:
        if self.image is None:
            return "break"
        if getattr(event, "delta", 0):
            steps = (
                max(-4, min(4, event.delta / 10))
                if sys.platform == "darwin"
                else max(1, abs(event.delta) // 120) * (1 if event.delta > 0 else -1)
            )
        else:
            steps = 1 if event.num == 4 else -1

        new_zoom = min(8.0, max(0.1, self.zoom_factor * (1.2**steps)))
        if new_zoom == self.zoom_factor:
            return "break"

        old_scale = self.base_scale * self.zoom_factor
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        image_width, image_height = self.image.size
        old_offset_x = (canvas_width - round(image_width * old_scale)) / 2 + self.pan_offset[0]
        old_offset_y = (canvas_height - round(image_height * old_scale)) / 2 + self.pan_offset[1]
        image_x = (event.x - old_offset_x) / old_scale
        image_y = (event.y - old_offset_y) / old_scale
        new_scale = self.base_scale * new_zoom
        centered_x = (canvas_width - round(image_width * new_scale)) / 2
        centered_y = (canvas_height - round(image_height * new_scale)) / 2
        self.pan_offset = (
            event.x - image_x * new_scale - centered_x,
            event.y - image_y * new_scale - centered_y,
        )
        self.zoom_factor = new_zoom
        self.display_scale = new_scale
        self.display_size = (max(1, round(image_width * new_scale)), max(1, round(image_height * new_scale)))
        self.display_offset = (centered_x + self.pan_offset[0], centered_y + self.pan_offset[1])
        if self.zoom_preview_id is None:
            self.zoom_preview_id = self.root.after(16, self._redraw_zoom_preview)
        if self.zoom_quality_id is not None:
            self.root.after_cancel(self.zoom_quality_id)
        self.zoom_quality_id = self.root.after(140, self._redraw_zoom_quality)
        return "break"

    def _redraw_zoom_preview(self) -> None:
        self.zoom_preview_id = None
        self.redraw(interactive=True)

    def _redraw_zoom_quality(self) -> None:
        self.zoom_quality_id = None
        self.redraw()

    def on_canvas_drag(self, event: tk.Event) -> None:
        if self.active_point_drag is not None:
            self._move_active_point(event.x, event.y)
            return
        if self.tool_mode.get() != "pan" or self.pan_start is None:
            return
        delta_x = event.x - self.pan_start[0]
        delta_y = event.y - self.pan_start[1]
        self.pan_offset = (self.pan_offset[0] + delta_x, self.pan_offset[1] + delta_y)
        self.display_offset = (self.display_offset[0] + delta_x, self.display_offset[1] + delta_y)
        self.pan_start = (event.x, event.y)
        self.canvas.move("view", delta_x, delta_y)

    def on_canvas_release(self, _event: tk.Event) -> None:
        self.pan_start = None
        if self.active_point_drag is None:
            return
        should_advance = self.advance_after_point_drag
        self.active_point_drag = None
        self.advance_after_point_drag = False
        self.update_status()
        if not should_advance:
            return
        if self.annotation_mode.get() == "point_by_point":
            self.next_image()
            return
        selection = self.point_list.curselection()
        next_point = selection[0] + 1 if selection else 0
        if next_point < len(self.point_names):
            self.select_point(next_point)
            self.update_status()

    def _point_at(self, screen_x: float, screen_y: float, radius: float = 12) -> str | None:
        image_annotations = self.annotations.get(self.current_image_name(), {})
        nearest_name = None
        nearest_distance = radius
        for point_name in self.point_names:
            coordinate = image_annotations.get(point_name)
            if coordinate is None:
                continue
            point_x, point_y = self.image_to_screen(*coordinate)
            distance = ((screen_x - point_x) ** 2 + (screen_y - point_y) ** 2) ** 0.5
            if distance <= nearest_distance:
                nearest_name = point_name
                nearest_distance = distance
        return nearest_name

    def _move_active_point(self, screen_x: float, screen_y: float) -> None:
        if self.image is None or self.active_point_drag is None:
            return
        image_x = min(max((screen_x - self.display_offset[0]) / self.display_scale, 0), self.image.width - 1)
        image_y = min(max((screen_y - self.display_offset[1]) / self.display_scale, 0), self.image.height - 1)
        coordinate = (round(image_x, 2), round(image_y, 2))
        self.annotations[self.current_image_name()][self.active_point_drag] = coordinate
        point_index = self.point_names.index(self.active_point_drag)
        marker_x, marker_y = self.image_to_screen(*coordinate)
        self.canvas.coords(f"point-marker-{point_index}", marker_x - 6, marker_y - 6, marker_x + 6, marker_y + 6)
        self.canvas.coords(f"point-label-{point_index}", marker_x + 10, marker_y - 10)
        self.canvas.tag_raise(f"point-marker-{point_index}")
        self.canvas.tag_raise(f"point-label-{point_index}")

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.image is None or self.current_index >= len(self.image_paths):
            return
        if self.tool_mode.get() == "pan":
            hit_point = self._point_at(event.x, event.y)
            if hit_point is not None:
                self.active_point_drag = hit_point
                self.advance_after_point_drag = False
                self.select_point(self.point_names.index(hit_point))
                self.update_status()
                return
            self.pan_start = (event.x, event.y)
            return
        offset_x, offset_y = self.display_offset
        shown_width, shown_height = self.display_size
        if not (offset_x <= event.x <= offset_x + shown_width and offset_y <= event.y <= offset_y + shown_height):
            return
        selection = self.point_list.curselection()
        if not selection:
            return
        self.active_point_drag = self.point_names[selection[0]]
        self.advance_after_point_drag = True
        self._move_active_point(event.x, event.y)
        self.redraw()

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
