from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from branding import BRAND_BACKGROUND, BRAND_BLACK, BRAND_MUTED, BRAND_NAME, BRAND_RED, load_logo, load_window_icon
from localization import english_text, remember_path, remembered_path, translate
from app_paths import RESOURCE_DIR, PROJECT_DIR


FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
VIDEO_EXTENSIONS = {
    ".3gp",
    ".asf",
    ".avi",
    ".f4v",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".mxf",
    ".ogv",
    ".ts",
    ".vob",
    ".webm",
    ".wmv",
}
OPERATIONS = {
    "Correct doubled duration": "correct_duration",
    "Enhance quality / brightness": "enhance",
    "Split by time": "split_time",
    "Crop or split by dimensions": "spatial",
    "Extract frames": "extract",
    "Merge numbered parts": "merge",
    "Repair duration / timestamps": "repair",
}
OPERATION_HELP = {
    "Correct doubled duration": (
        "Correct a video whose recorded playback is twice as fast as intended. "
        "Adjust timestamps to slow it down, or drop every second frame when frames were duplicated. "
        "The result is re-encoded; choose whether to keep the original audio."
    ),
    "Enhance quality / brightness": (
        "Apply a visual preset to every input video: brighten, denoise and sharpen, combine those filters, "
        "or re-encode without a visual filter. The selected encoding profile controls output quality and speed."
    ),
    "Split by time": (
        "Create video segments from the start times and durations you enter. Values accept seconds, minutes, "
        "hours, mm:ss, or hh:mm:ss; one duration can be reused for all segments. Fast cuts may snap to keyframes, "
        "while precise cuts re-encode."
    ),
    "Crop or split by dimensions": (
        "Crop each video using margins, keep one equal slice, split into two halves, or create four quadrants. "
        "Cropped and split outputs are re-encoded with the selected profile."
    ),
    "Extract frames": (
        "Save the first decoded frame, then sample frames at the selected seconds/minutes/hours interval. "
        "MP4/MOV edit lists are handled so a stored final frame is not silently omitted. "
        "Frames are grouped into one subfolder per source video; the originals are unchanged."
    ),
    "Merge numbered parts": (
        "Join video parts named like Name_1.mp4, Name_2.mp4, and so on. Safe mode re-encodes for reliable "
        "timestamps; fast mode copies streams and works best when all parts have matching codecs and settings."
    ),
    "Repair duration / timestamps": (
        "Repair videos with incorrect duration or damaged timestamps. Fast mode remuxes without re-encoding; "
        "safe mode re-encodes and is slower but can repair more timestamp problems."
    ),
}


class VideoProcessingWindow:
    def __init__(self, parent: tk.Misc, language: str = "en") -> None:
        self.parent = parent
        self.language = language
        self.window = tk.Toplevel(parent)
        self.window.title(f"{BRAND_NAME} | {translate('Video Processing', self.language)}")
        self.window.geometry("980x760")
        self.window.minsize(820, 640)
        self.window.configure(background=BRAND_BACKGROUND)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("TFrame", background=BRAND_BACKGROUND)
        style.configure("TLabel", background=BRAND_BACKGROUND, foreground=BRAND_BLACK)
        style.configure("TLabelframe", background=BRAND_BACKGROUND, foreground=BRAND_BLACK)
        style.configure("TLabelframe.Label", background=BRAND_BACKGROUND, foreground=BRAND_BLACK, font=("Segoe UI", 9, "bold"))
        style.configure("PageTitle.TLabel", font=("Segoe UI", 19, "bold"), foreground=BRAND_BLACK)
        style.configure("SectionTitle.TLabel", font=("Segoe UI", 10, "bold"), foreground=BRAND_BLACK)
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 7),
            background=BRAND_RED,
            foreground="white",
            borderwidth=0,
        )
        style.map("Action.TButton", background=[("active", "#cc0000"), ("pressed", "#a90000")])
        style.configure("TEntry", fieldbackground="white")
        style.configure("TCombobox", fieldbackground="white")
        self.brand_logo = load_logo(self.window, (66, 52))
        self.window_icon = load_window_icon(self.window)
        if self.window_icon is not None:
            self.window.iconphoto(True, self.window_icon)

        self.operation = tk.StringVar(value=translate("Extract frames", self.language))
        remembered_input = remembered_path("video_input")
        self.input_dir = tk.StringVar(value=str(remembered_input) if remembered_input is not None else "")
        self.output_dir = tk.StringVar(value="")
        self.parameter_vars: dict[str, tk.StringVar] = {}
        self.active_process: subprocess.Popen[str] | None = None
        self.worker: threading.Thread | None = None
        self.cancel_requested = False
        self.close_requested = False
        self.temporary_files: list[Path] = []
        self.operation_fields: ttk.Frame | None = None

        self._build_ui()
        self._build_operation_fields()
        self._set_status("Ready")

    def _choice_value(self, key: str, default: str = "") -> str:
        if key not in self.parameter_vars:
            return default
        return english_text(str(self.parameter_vars[key].get()), self.language)

    def _build_ui(self) -> None:
        page = ttk.Frame(self.window, padding=(24, 20))
        page.pack(fill="both", expand=True)

        header = ttk.Frame(page)
        header.pack(fill="x", pady=(0, 14))
        if self.brand_logo is not None:
            ttk.Label(header, image=self.brand_logo).pack(side="left", padx=(0, 12))
        header_text = ttk.Frame(header)
        header_text.pack(side="left", anchor="center")
        ttk.Label(header_text, text=BRAND_NAME, style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header_text,
            text=translate("VIDEO PROCESSING", self.language),
            foreground=BRAND_RED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=translate("FFmpeg workflow", self.language),
            foreground=BRAND_MUTED,
        ).pack(side="right", anchor="s")

        paths = ttk.LabelFrame(page, text=translate("Input and output", self.language), padding=12)
        paths.pack(fill="x", pady=(0, 12))
        self._add_input_path_row(paths, "Input videos", self.input_dir, 0)
        self._add_path_row(paths, "Output", self.output_dir, self._choose_output, 1)

        operation_frame = ttk.Frame(page)
        operation_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(
            operation_frame,
            text=translate("Operation", self.language),
            style="SectionTitle.TLabel",
        ).pack(side="left", padx=(0, 10))
        self.operation_keys = list(OPERATIONS)
        operation_labels = [translate(key, self.language) for key in self.operation_keys]
        self.operation_box = ttk.Combobox(
            operation_frame,
            textvariable=self.operation,
            values=operation_labels,
            state="readonly",
            width=36,
        )
        self.operation_box.pack(side="left")
        self.operation_box.bind("<<ComboboxSelected>>", self._on_operation_selected)
        help_button = ttk.Button(operation_frame, text="?", width=3, command=self.show_operation_help)
        help_button.pack(side="left", padx=(7, 0))
        self._attach_tooltip(help_button, translate("Explain the selected operation", self.language))

        self.operation_fields = ttk.LabelFrame(
            page, text=translate("Settings", self.language), padding=12
        )
        self.operation_fields.pack(fill="x", pady=(0, 12))

        controls = ttk.Frame(page)
        controls.pack(fill="x", pady=(0, 8))
        self.start_button = ttk.Button(
            controls,
            text=translate("Start processing", self.language),
            style="Action.TButton",
            command=self.start,
        )
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(
            controls,
            text=translate("Cancel", self.language),
            command=self.cancel,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=(8, 0))
        self.status_label = ttk.Label(controls, text=translate("Ready", self.language), anchor="e")
        self.status_label.pack(side="right", fill="x", expand=True)

        self.progress = ttk.Progressbar(page, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 10))

        ttk.Label(
            page,
            text=translate("Activity", self.language),
            style="SectionTitle.TLabel",
        ).pack(anchor="w", pady=(0, 5))
        log_frame = ttk.Frame(page)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(
            log_frame,
            height=10,
            wrap="word",
            state="disabled",
            background="#f4f6f8",
            foreground="#202428",
            relief="flat",
            padx=10,
            pady=8,
            font=("Consolas", 9),
        )
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)

    def _add_path_row(self, parent: ttk.LabelFrame, label: str, variable: tk.StringVar, command, row: int) -> None:
        ttk.Label(parent, text=label, width=13).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=4)
        ttk.Button(parent, text=translate("Browse...", self.language), command=command).grid(
            row=row, column=2, pady=4
        )
        parent.columnconfigure(1, weight=1)

    def _add_input_path_row(
        self, parent: ttk.LabelFrame, label: str, variable: tk.StringVar, row: int
    ) -> None:
        ttk.Label(parent, text=translate(label, self.language), width=13).grid(
            row=row, column=0, sticky="w", pady=4
        )
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=4)
        ttk.Button(parent, text=translate("Choose folder...", self.language), command=self._choose_input_folder).grid(
            row=row, column=2, padx=(0, 6), pady=4
        )
        ttk.Button(parent, text=translate("Choose video...", self.language), command=self._choose_input_video).grid(
            row=row, column=3, pady=4
        )
        parent.columnconfigure(1, weight=1)

    @staticmethod
    def _initial_folder(*candidates: str | Path | None) -> Path:
        for candidate in candidates:
            if candidate is None or not str(candidate).strip():
                continue
            path = Path(candidate).expanduser()
            if path.is_file():
                path = path.parent
            if path.is_dir():
                return path
        return Path.home()

    def _output_setting_key(self) -> str:
        operation_label = english_text(self.operation.get(), self.language)
        return "frames_output" if operation_label == "Extract frames" else "video_output"

    def _choose_input_folder(self) -> None:
        initial = self._initial_folder(self.input_dir.get(), remembered_path("video_input"))
        selected = filedialog.askdirectory(
            parent=self.window,
            title=translate("Choose the input video folder", self.language),
            initialdir=initial,
        )
        if selected:
            self.input_dir.set(selected)
            remember_path("video_input", selected)

    def _choose_input_video(self) -> None:
        initial = self._initial_folder(self.input_dir.get(), remembered_path("video_input"))
        patterns = " ".join(f"*{extension}" for extension in sorted(VIDEO_EXTENSIONS))
        selected = filedialog.askopenfilename(
            parent=self.window,
            title=translate("Choose a video to process", self.language),
            initialdir=initial,
            filetypes=(("Video files", patterns), ("All files", "*.*")),
        )
        if selected:
            self.input_dir.set(selected)
            remember_path("video_input", selected)

    def _select_videos_to_process(self, input_path: Path) -> list[Path]:
        patterns = " ".join(f"*{extension}" for extension in sorted(VIDEO_EXTENSIONS))
        selected = filedialog.askopenfilenames(
            parent=self.window,
            title=translate("Select videos to process", self.language),
            initialdir=input_path,
            filetypes=((translate("Video files", self.language), patterns),),
        )
        return [Path(path) for path in selected]

    def _choose_output(self) -> None:
        key = self._output_setting_key()
        initial = self._initial_folder(self.output_dir.get(), remembered_path(key), self.input_dir.get())
        selected = filedialog.askdirectory(
            parent=self.window,
            title=translate("Choose the output folder", self.language),
            initialdir=initial,
        )
        if selected:
            self.output_dir.set(selected)
            remember_path(key, selected)

    def _on_operation_selected(self, _event: tk.Event | None = None) -> None:
        operation_label = english_text(self.operation.get(), self.language)
        self.operation.set(operation_label)
        self._build_operation_fields()
        self.operation.set(translate(operation_label, self.language))

    def _build_operation_fields(self) -> None:
        if self.operation_fields is None:
            return
        for child in self.operation_fields.winfo_children():
            child.destroy()
        self.parameter_vars.clear()
        operation_label = english_text(self.operation.get(), self.language)
        operation = OPERATIONS[operation_label]

        if operation == "correct_duration":
            self._add_choice("Correction", "correction", ("Adjust timestamps", "Drop every second frame"), 0)
            self._add_choice("Encoding", "profile", ("Fast", "High quality"), 1)
            self._add_check("Keep audio", "keep_audio", False, 2)
        elif operation == "enhance":
            self._add_choice("Preset", "preset", ("Brighten", "Denoise + sharpen", "Brighten + denoise + sharpen", "Re-encode only"), 0)
            self._add_choice("Encoding", "profile", ("Fast", "High quality"), 1)
            self._add_check("Keep audio", "keep_audio", False, 2)
        elif operation == "split_time":
            self._add_entry("Start times", "start_times", "0m, 10m", 0)
            self._add_entry("Durations", "durations", "10m", 1)
            ttk.Label(
                self.operation_fields,
                text=translate("Use comma-separated values: 30s, 5m, 1h, mm:ss, or hh:mm:ss. Bare numbers still mean minutes. One duration applies to all parts.", self.language),
                wraplength=690,
            ).grid(row=2, column=1, columnspan=2, sticky="w", pady=4)
            self._add_choice("Cut mode", "cut_mode", ("Fast (keyframe cuts)", "Precise (re-encode)"), 3)
            self._add_choice("Encoding", "profile", ("Fast", "High quality"), 4)
            self._add_check("Keep audio", "keep_audio", False, 5)
        elif operation == "spatial":
            self._add_choice("Crop / split", "spatial_mode", ("Manual crop", "Keep one equal slice", "Split into two halves", "Split into four quadrants"), 0)
            self._add_choice("Direction", "direction", ("Vertical (left/right)", "Horizontal (top/bottom)"), 1)
            self._add_entry("Number of slices", "slice_count", "2", 2)
            self._add_entry("Slice to keep", "slice_index", "1", 3)
            self._add_entry("Margins L, R, T, B", "margins", "0, 0, 0, 0", 4)
            self._add_choice("Encoding", "profile", ("Fast", "High quality"), 5)
            self._add_check("Keep audio", "keep_audio", False, 6)
            ttk.Label(
                self.operation_fields,
                text=translate("Manual crop margins are fractions from 0 to 0.5, entered as left, right, top, bottom.", self.language),
            ).grid(row=7, column=1, columnspan=2, sticky="w", pady=4)
        elif operation == "extract":
            self._add_entry("Frame interval", "interval", "5", 0)
            self._add_choice("Time unit", "interval_unit", ("Seconds", "Minutes", "Hours"), 1)
            self._add_choice("Image format", "image_format", ("JPG", "PNG"), 2)
            ttk.Label(
                self.operation_fields,
                text=translate("The first decoded frame is always saved, then one frame is saved after each interval.", self.language),
                wraplength=690,
            ).grid(row=3, column=1, columnspan=2, sticky="w", pady=4)
        elif operation == "merge":
            self._add_choice("Merge mode", "merge_mode", ("Safe (re-encode)", "Fast (stream copy)"), 0)
            ttk.Label(
                self.operation_fields,
                text=translate("Merge files named Name_1.mp4, Name_2.mp4, etc.", self.language),
            ).grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        elif operation == "repair":
            self._add_choice("Repair mode", "repair_mode", ("Fast (remux)", "Safe (re-encode)"), 0)

        remembered_output = remembered_path("frames_output" if operation == "extract" else "video_output")
        self.output_dir.set(str(remembered_output) if remembered_output is not None and remembered_output.is_dir() else "")

    def show_operation_help(self) -> None:
        operation_label = english_text(self.operation.get(), self.language)
        help_text = OPERATION_HELP.get(operation_label, "No explanation is available for this operation.")
        messagebox.showinfo(
            f"{translate('About: ', self.language)}{translate(operation_label, self.language)}",
            translate(help_text, self.language),
            parent=self.window,
        )

    def _attach_tooltip(self, widget: ttk.Widget, text: str) -> None:
        tooltip: tk.Toplevel | None = None

        def show(_event: tk.Event) -> None:
            nonlocal tooltip
            if tooltip is not None or not widget.winfo_exists():
                return
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty() + 2
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            ttk.Label(tooltip, text=text, padding=(7, 4), relief="solid").pack()

        def hide(_event: tk.Event) -> None:
            nonlocal tooltip
            if tooltip is not None:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _add_entry(self, label: str, key: str, default: str, row: int) -> None:
        variable = tk.StringVar(value=default)
        self.parameter_vars[key] = variable
        ttk.Label(self.operation_fields, text=translate(label, self.language)).grid(
            row=row, column=0, sticky="w", pady=4
        )
        ttk.Entry(self.operation_fields, textvariable=variable, width=42).grid(
            row=row, column=1, sticky="ew", padx=(8, 8), pady=4
        )
        self.operation_fields.columnconfigure(1, weight=1)

    def _add_choice(self, label: str, key: str, values: tuple[str, ...], row: int) -> None:
        variable = tk.StringVar(value=translate(values[0], self.language))
        self.parameter_vars[key] = variable
        ttk.Label(self.operation_fields, text=translate(label, self.language)).grid(
            row=row, column=0, sticky="w", pady=4
        )
        ttk.Combobox(
            self.operation_fields,
            textvariable=variable,
            values=tuple(translate(value, self.language) for value in values),
            state="readonly",
            width=38,
        ).grid(row=row, column=1, sticky="w", padx=(8, 8), pady=4)

    def _add_check(self, label: str, key: str, default: bool, row: int) -> None:
        variable = tk.BooleanVar(value=default)
        self.parameter_vars[key] = variable
        ttk.Checkbutton(
            self.operation_fields,
            text=translate(label, self.language),
            variable=variable,
        ).grid(row=row, column=1, sticky="w", padx=(8, 8), pady=4)

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=translate(text, self.language))

    def _log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _get_video_files(self, input_path: Path) -> list[Path]:
        if input_path.is_file():
            if input_path.suffix.lower() not in VIDEO_EXTENSIONS:
                raise ValueError(
                    f"Unsupported video file: {input_path}\n"
                    "Supported extensions include MP4, MOV, MKV, AVI, WMV, WebM, MPEG, and TS."
                )
            return [input_path]
        if not input_path.is_dir():
            raise ValueError(f"Input folder or video file does not exist: {input_path}")
        files = sorted(
            (path for path in input_path.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS),
            key=lambda path: path.name.casefold(),
        )
        if not files:
            raise ValueError(
                f"No supported video files found in: {input_path}\n"
                "Supported extensions include MP4, MOV, MKV, AVI, WMV, WebM, MPEG, and TS."
            )
        return files

    def _get_unsupported_files(self, input_path: Path) -> list[Path]:
        if not input_path.is_dir():
            return []
        return sorted(
            (
                path
                for path in input_path.iterdir()
                if path.is_file() and path.suffix.lower() not in VIDEO_EXTENSIONS
            ),
            key=lambda path: path.name.casefold(),
        )

    def _codec_args(self, profile: str) -> list[str]:
        if profile == "High quality":
            return ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p"]
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]

    def _audio_args(self, keep_audio: bool) -> list[str]:
        return [] if keep_audio else ["-an"]

    def _tagged_output(self, source: Path, tag: str, extension: str = ".mp4") -> Path:
        return Path(self.output_dir.get()) / f"{source.stem}{tag}{extension}"

    def _build_tasks(self, videos: list[Path]) -> list[tuple[str, list[str]]]:
        operation = OPERATIONS[english_text(self.operation.get(), self.language)]
        if not self.output_dir.get().strip():
            raise ValueError("Choose an output folder.")
        output_dir = Path(self.output_dir.get()).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        tasks: list[tuple[str, list[str]]] = []
        ffmpeg = self._find_ffmpeg()
        keep_audio = bool(self.parameter_vars.get("keep_audio", tk.BooleanVar(value=False)).get())
        audio_args = self._audio_args(keep_audio)
        profile = self._choice_value("profile", "Fast")
        codec_args = self._codec_args(profile)

        if operation == "correct_duration":
            method = self._choice_value("correction")
            for video in videos:
                if method == "Drop every second frame":
                    vf = "select=not(mod(n\\,2)),setpts=N/FRAME_RATE/TB"
                    tag = "_FIXEDdrop2"
                else:
                    vf = "setpts=0.5*PTS"
                    tag = "_FIXEDx2"
                command = [ffmpeg, "-hide_banner", "-y", "-i", str(video), "-vf", vf, *codec_args, *audio_args, str(self._tagged_output(video, tag))]
                tasks.append((video.name, command))
        elif operation == "enhance":
            preset = self._choice_value("preset")
            filters = {
                "Brighten": ("eq=gamma=0.85:contrast=1.05:brightness=0.02", "_ENH_P1"),
                "Denoise + sharpen": ("hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.35:3:3:0.0", "_ENH_P2"),
                "Brighten + denoise + sharpen": ("eq=gamma=0.85:contrast=1.05:brightness=0.02,hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.35:3:3:0.0", "_ENH_P3"),
                "Re-encode only": ("", "_ENH_P4"),
            }
            vf, tag = filters[preset]
            for video in videos:
                command = [ffmpeg, "-hide_banner", "-y", "-i", str(video)]
                if vf:
                    command.extend(["-vf", vf])
                command.extend([*codec_args, *audio_args, str(self._tagged_output(video, tag))])
                tasks.append((video.name, command))
        elif operation == "split_time":
            starts = self._parse_time_list(self.parameter_vars["start_times"].get(), "start times")
            durations = self._parse_time_list(self.parameter_vars["durations"].get(), "durations")
            if len(durations) not in {1, len(starts)}:
                raise ValueError("Enter one duration or one duration for each start time.")
            precise = self._choice_value("cut_mode").startswith("Precise")
            split_codec = codec_args if precise else ["-c", "copy"]
            split_audio = audio_args if precise else []
            for video in videos:
                for index, start in enumerate(starts, 1):
                    duration = durations[0] if len(durations) == 1 else durations[index - 1]
                    command = [ffmpeg, "-hide_banner", "-y"]
                    if not precise:
                        command.extend(["-ss", str(start)])
                    command.extend(["-i", str(video)])
                    if precise:
                        command.extend(["-ss", str(start)])
                    command.extend(["-t", str(duration), *split_codec, *split_audio, str(self._tagged_output(video, f"_part{index}"))])
                    tasks.append((f"{video.name} part {index}", command))
        elif operation == "spatial":
            mode = self._choice_value("spatial_mode")
            direction = self._choice_value("direction")
            direction_vertical = direction.startswith("Vertical")
            if mode == "Keep one equal slice":
                count = self._positive_int("slice_count")
                keep = self._positive_int("slice_index")
                if keep > count:
                    raise ValueError("Slice to keep must not exceed the number of slices.")
                if direction_vertical:
                    vf = f"crop=iw/{count}:ih:({keep}-1)*iw/{count}:0"
                else:
                    vf = f"crop=iw:ih/{count}:0:({keep}-1)*ih/{count}"
                suffix_filters = [(vf, "_CROP")]
            elif mode == "Split into two halves":
                if direction_vertical:
                    suffix_filters = [("crop=iw/2:ih:0:0", "_V1"), ("crop=iw/2:ih:iw/2:0", "_V2")]
                else:
                    suffix_filters = [("crop=iw:ih/2:0:0", "_H1"), ("crop=iw:ih/2:0:ih/2", "_H2")]
            elif mode == "Split into four quadrants":
                suffix_filters = [
                    ("crop=iw/2:ih/2:0:0", "_Q1"),
                    ("crop=iw/2:ih/2:iw/2:0", "_Q2"),
                    ("crop=iw/2:ih/2:0:ih/2", "_Q3"),
                    ("crop=iw/2:ih/2:iw/2:ih/2", "_Q4"),
                ]
            else:
                margins = self._parse_float_list(self.parameter_vars["margins"].get(), "margins", 4)
                left, right, top, bottom = margins
                if left + right >= 1 or top + bottom >= 1:
                    raise ValueError("Opposing crop margins must add up to less than 1.")
                vf = f"crop=iw*(1-{left}-{right}):ih*(1-{top}-{bottom}):iw*{left}:ih*{top}"
                suffix_filters = [(vf, "_CROP_MANUAL")]
            for video in videos:
                for vf, tag in suffix_filters:
                    command = [ffmpeg, "-hide_banner", "-y", "-i", str(video), "-vf", vf, *codec_args, *audio_args, str(self._tagged_output(video, tag))]
                    tasks.append((f"{video.name} {tag}", command))
        elif operation == "extract":
            interval = self._positive_float("interval")
            unit_seconds = {"Seconds": 1, "Minutes": 60, "Hours": 3600}
            interval_seconds = interval * unit_seconds[self._choice_value("interval_unit")]
            image_format = self._choice_value("image_format").lower()
            extension = "jpg" if image_format == "jpg" else "png"
            image_args = ["-q:v", "2"] if extension == "jpg" else []
            for video in videos:
                image_folder = output_dir / video.stem
                image_folder.mkdir(parents=True, exist_ok=True)
                pattern = image_folder / f"frame_%06d.{extension}"
                select_filter = f"select=eq(n\\,0)+gte(t-prev_selected_t\\,{interval_seconds:g})"
                input_options = ["-ignore_editlist", "1"] if video.suffix.lower() in {".mp4", ".mov", ".m4v"} else []
                command = [ffmpeg, "-hide_banner", "-y", *input_options, "-i", str(video), "-vf", select_filter, "-fps_mode", "vfr", *image_args, str(pattern)]
                tasks.append((f"Extract frames: {video.name}", command))
        elif operation == "merge":
            tasks.extend(self._build_merge_tasks(videos, ffmpeg))
        elif operation == "repair":
            safe = self._choice_value("repair_mode").startswith("Safe")
            for video in videos:
                if safe:
                    tag = "_REPAIRED_REENC"
                    command = [ffmpeg, "-hide_banner", "-y", "-err_detect", "ignore_err", "-fflags", "+genpts", "-i", str(video), "-map", "0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(self._tagged_output(video, tag))]
                else:
                    tag = "_REPAIRED_COPY"
                    command = [ffmpeg, "-hide_banner", "-y", "-err_detect", "ignore_err", "-fflags", "+genpts", "-i", str(video), "-map", "0", "-c", "copy", "-avoid_negative_ts", "make_zero", "-movflags", "+faststart", str(self._tagged_output(video, tag))]
                tasks.append((video.name, command))
        return tasks

    def _build_merge_tasks(self, videos: list[Path], ffmpeg: str) -> list[tuple[str, list[str]]]:
        grouped: dict[str, list[tuple[int, Path]]] = defaultdict(list)
        for video in videos:
            match = re.match(r"^(?P<base>.+)_(?P<index>\d+)$", video.stem)
            if match:
                grouped[match.group("base")].append((int(match.group("index")), video))
        if not grouped:
            raise ValueError("No videos match the Name_1, Name_2 naming pattern.")
        safe = self._choice_value("merge_mode").startswith("Safe")
        tasks: list[tuple[str, list[str]]] = []
        for base, parts in sorted(grouped.items()):
            parts.sort(key=lambda item: item[0])
            if len(parts) < 2:
                continue
            extensions = {part.suffix.lower() for _, part in parts}
            if len(extensions) != 1:
                raise ValueError(f"Merge group {base} contains mixed file extensions.")
            list_path = Path(tempfile.gettempdir()) / f"ffmpeg_concat_{next(tempfile._get_candidate_names())}.txt"
            lines = [f"file '{str(path).replace(chr(39), chr(92) + chr(39))}'" for _, path in parts]
            list_path.write_text("\n".join(lines), encoding="utf-8")
            self.temporary_files.append(list_path)
            output_extension = ".mp4" if safe else next(iter(extensions))
            output = Path(self.output_dir.get()) / f"{base}_MERGED{output_extension}"
            if safe:
                command = [ffmpeg, "-hide_banner", "-y", "-fflags", "+genpts", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
            else:
                command = [ffmpeg, "-hide_banner", "-y", "-fflags", "+genpts", "-avoid_negative_ts", "make_zero", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", "-movflags", "+faststart", str(output)]
            tasks.append((f"Merge {base}", command))
        if not tasks:
            raise ValueError("Each merge group needs at least two numbered parts.")
        return tasks

    def _find_ffmpeg(self) -> str:
        executable_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        for local in (
            RESOURCE_DIR / "ffmpeg" / "bin" / executable_name,
            PROJECT_DIR / "ffmpeg" / "bin" / executable_name,
            PROJECT_DIR / "Third-party" / "FFmpeg" / "bin" / executable_name,
        ):
            if local.is_file():
                return str(local)
        import shutil

        resolved = shutil.which("ffmpeg")
        if resolved:
            return resolved
        raise ValueError("FFmpeg was not found. Install FFmpeg and add it to PATH, or place ffmpeg.exe in ffmpeg\\bin.")

    def _positive_int(self, key: str) -> int:
        try:
            value = int(self.parameter_vars[key].get())
        except ValueError as exc:
            raise ValueError(f"{key.replace('_', ' ').title()} must be a whole number.") from exc
        if value < 1:
            raise ValueError(f"{key.replace('_', ' ').title()} must be at least 1.")
        return value

    def _positive_float(self, key: str) -> float:
        try:
            value = float(self.parameter_vars[key].get())
        except ValueError as exc:
            raise ValueError(f"{key.replace('_', ' ').title()} must be a number.") from exc
        if value <= 0:
            raise ValueError(f"{key.replace('_', ' ').title()} must be greater than 0.")
        return value

    def _parse_time_list(self, value: str, label: str) -> list[float]:
        values: list[float] = []
        for item in value.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                colon_parts = item.split(":")
                if len(colon_parts) == 3:
                    hours, minutes, seconds = (float(part.strip()) for part in colon_parts)
                    if minutes >= 60 or seconds >= 60:
                        raise ValueError
                    total = hours * 3600 + minutes * 60 + seconds
                elif len(colon_parts) == 2:
                    minutes, seconds = (float(part.strip()) for part in colon_parts)
                    if seconds >= 60:
                        raise ValueError
                    total = minutes * 60 + seconds
                else:
                    match = re.fullmatch(
                        r"\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*",
                        item,
                    )
                    if match is None:
                        raise ValueError
                    amount = float(match.group(1))
                    unit = match.group(2).lower()
                    if unit in {"", "m", "min", "mins", "minute", "minutes"}:
                        total = amount * 60
                    elif unit in {"s", "sec", "secs", "second", "seconds"}:
                        total = amount
                    elif unit in {"h", "hr", "hrs", "hour", "hours"}:
                        total = amount * 3600
                    else:
                        raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f"Invalid {label}: {item}. Use 30s, 5m, 1h, mm:ss, or hh:mm:ss."
                ) from exc
            if total < 0 or (label == "durations" and total <= 0):
                raise ValueError(f"Invalid {label}: values must be positive; start times may be zero.")
            values.append(total)
        if not values:
            raise ValueError(f"Enter at least one value for {label}.")
        return values

    def _parse_float_list(self, value: str, label: str, expected: int) -> list[float]:
        try:
            values = [float(item.strip()) for item in value.split(",")]
        except ValueError as exc:
            raise ValueError(f"Enter comma-separated numeric values for {label}.") from exc
        if len(values) != expected or any(value < 0 or value >= 0.5 for value in values):
            raise ValueError(f"Enter exactly {expected} values between 0 and 0.5 for {label}.")
        return values

    def start(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return
        try:
            if not self.input_dir.get().strip():
                raise ValueError("Choose a video or a folder of videos to process.")
            input_path = Path(self.input_dir.get()).expanduser()
            videos = self._get_video_files(input_path)
            if input_path.is_dir():
                videos = self._select_videos_to_process(input_path)
                if not videos:
                    return
            ignored_files = self._get_unsupported_files(input_path)
            tasks = self._build_tasks(videos)
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror(
                translate("Cannot start processing", self.language),
                translate(str(exc), self.language),
                parent=self.window,
            )
            return
        remember_path("video_input", input_path)
        remember_path(self._output_setting_key(), self.output_dir.get())
        self.cancel_requested = False
        self.progress.configure(mode="determinate", maximum=max(1, len(tasks)), value=0)
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self._log(
            translate("Starting {operation} for {count} video(s).", self.language).format(
                operation=self.operation.get(), count=len(videos)
            )
        )
        if ignored_files:
            self._log(
                f"Skipping {len(ignored_files)} file(s) with unsupported extensions: "
                + ", ".join(path.name for path in ignored_files)
            )
        self._log(
            translate(
                "A video that cannot be decoded will be marked as failed; other videos will continue.",
                self.language,
            )
        )
        self.worker = threading.Thread(target=self._run_tasks, args=(tasks,), daemon=True)
        self.worker.start()

    def _run_tasks(self, tasks: list[tuple[str, list[str]]]) -> None:
        completed = 0
        failed = 0
        for label, command in tasks:
            if self.cancel_requested:
                break
            self.window.after(
                0,
                lambda name=label: self._set_status(
                    translate("Processing: {name}", self.language).format(name=name)
                ),
            )
            self.window.after(0, lambda name=label: self._log(name))
            try:
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                self.active_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creation_flags,
                )
                assert self.active_process.stdout is not None
                for line in self.active_process.stdout:
                    message = line.rstrip()
                    if message:
                        self.window.after(0, lambda item=message: self._log(item))
                    if self.cancel_requested and self.active_process.poll() is None:
                        self.active_process.terminate()
                        break
                return_code = self.active_process.wait()
                if return_code == 0:
                    completed += 1
                else:
                    failed += 1
                    self.window.after(
                        0,
                        lambda name=label, code=return_code: self._log(
                            translate("FAILED ({code}): {name}", self.language).format(code=code, name=name)
                        ),
                    )
            except (OSError, ValueError) as exc:
                failed += 1
                self.window.after(
                    0,
                    lambda error=str(exc): self._log(
                        translate("ERROR: {error}", self.language).format(error=error)
                    ),
                )
            finally:
                self.active_process = None
            done = completed + failed
            self.window.after(0, lambda count=done: self.progress.configure(value=count))
        cancelled = self.cancel_requested
        self.window.after(0, lambda: self._finish(completed, failed, cancelled, len(tasks)))

    def _finish(self, completed: int, failed: int, cancelled: bool, total: int) -> None:
        for temporary_file in self.temporary_files:
            temporary_file.unlink(missing_ok=True)
        self.temporary_files.clear()
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if cancelled:
            self._set_status("Cancelled")
            self._log("Processing cancelled. Completed outputs were kept.")
        elif failed:
            self._set_status(
                translate("Finished: {completed}/{total} succeeded; {failed} failed", self.language).format(
                    completed=completed, total=total, failed=failed
                )
            )
            self._log(
                translate(
                    "Finished: {completed} succeeded, {failed} failed. Other videos were not stopped.",
                    self.language,
                ).format(completed=completed, failed=failed)
            )
        else:
            self._set_status("Complete")
            self._log(
                translate("Finished successfully: {count} task(s).", self.language).format(count=completed)
            )
        if self.close_requested:
            self.window.destroy()

    def cancel(self) -> None:
        self.cancel_requested = True
        self.cancel_button.configure(state="disabled")
        self._set_status("Cancelling after the current task...")
        process = self.active_process
        if process is not None and process.poll() is None:
            process.terminate()

    def close(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            if not messagebox.askyesno(
                translate("Processing is active", self.language),
                translate("Cancel processing and close this window?", self.language),
                parent=self.window,
            ):
                return
            self.close_requested = True
            self.cancel()
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)
            return
        self.window.destroy()
