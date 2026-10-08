from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from collections.abc import Callable

from branding import (
    APP_VERSION,
    BRAND_BACKGROUND,
    BRAND_BLACK,
    BRAND_MUTED,
    BRAND_NAME,
    BRAND_RED,
    load_logo,
    load_window_icon,
)
from localization import LANGUAGES, load_language, save_language, translate
from video_processing import VideoProcessingWindow
from app_paths import IS_MAC, PROJECT_DIR, points_file


FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
ROOT_DIR = PROJECT_DIR
README_PATH = ROOT_DIR / ("README-Mac.md" if IS_MAC else "README.md")
README_FR_PATH = ROOT_DIR / ("README-Mac.md" if IS_MAC else "README-fr.md")
UNINSTALL_SCRIPT = APP_DIR / "Uninstall Kinetho.ps1"
BUG_REPORT_URL = "https://github.com/raphael-THMS/Kinetho/issues"
ENTRY_SCRIPT = APP_DIR / "kinetho_app.py"
POINTS_FILE = points_file()


class PointConfigurationWindow:
    def __init__(self, parent: tk.Misc, on_continue: Callable[[], None], language: str) -> None:
        self.parent = parent
        self.on_continue = on_continue
        self.language = language
        self.window = tk.Toplevel(parent)
        self.window.title(f"{BRAND_NAME} | {translate('Configure Points', self.language)}")
        self.window.geometry("760x560")
        self.window.minsize(620, 460)
        self.window.configure(background=BRAND_BACKGROUND)
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        style = ttk.Style(self.window)
        style.configure("PointConfigTitle.TLabel", font=("Segoe UI", 18, "bold"), foreground=BRAND_BLACK)
        style.configure("PointConfigAction.TButton", padding=(8, 6))
        style.configure("PointConfigPrimary.TButton", padding=(12, 8), background=BRAND_RED, foreground="white")
        style.map("PointConfigPrimary.TButton", background=[("active", "#cc0000"), ("pressed", "#a90000")])

        self.names = self._read_names()
        self.selected_index: int | None = None
        self.name_var = tk.StringVar()
        self.count_var = tk.StringVar()
        self._build_interface()
        self._refresh_list()
        self.window.grab_set()

    def _read_names(self) -> list[str]:
        try:
            lines = POINTS_FILE.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            return []
        return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]

    def _build_interface(self) -> None:
        page = ttk.Frame(self.window, padding=22)
        page.pack(fill="both", expand=True)

        heading = ttk.Frame(page)
        heading.pack(fill="x", pady=(0, 14))
        logo = load_logo(self.window, (62, 48))
        self.logo = logo
        if logo is not None:
            ttk.Label(heading, image=logo).pack(side="left", padx=(0, 12))
        title_block = ttk.Frame(heading)
        title_block.pack(side="left", anchor="center")
        ttk.Label(
            title_block,
            text=translate("Configure annotation points", self.language),
            style="PointConfigTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            title_block,
            text=translate("Add, rename, remove, or reorder the points used for every image.", self.language),
            foreground=BRAND_MUTED,
        ).pack(anchor="w", pady=(3, 0))

        name_row = ttk.Frame(page)
        name_row.pack(fill="x", pady=(0, 8))
        ttk.Label(name_row, text=translate("Point name", self.language)).pack(side="left", padx=(0, 8))
        self.name_entry = ttk.Entry(name_row, textvariable=self.name_var)
        self.name_entry.pack(side="left", fill="x", expand=True)
        self.name_entry.bind("<Return>", lambda _event: self.add_point())
        ttk.Button(name_row, text=translate("Add point", self.language), command=self.add_point).pack(
            side="left", padx=(8, 0)
        )

        list_area = ttk.Frame(page)
        list_area.pack(fill="both", expand=True)
        self.point_list = tk.Listbox(
            list_area,
            exportselection=False,
            activestyle="dotbox",
            font=("Segoe UI", 11),
            background="white",
            foreground=BRAND_BLACK,
            selectbackground=BRAND_RED,
            selectforeground="white",
            highlightthickness=0,
        )
        self.point_list.pack(side="left", fill="both", expand=True)
        self.point_list.bind("<<ListboxSelect>>", self.on_selection_changed)
        scrollbar = ttk.Scrollbar(list_area, orient="vertical", command=self.point_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.point_list.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(list_area)
        actions.pack(side="left", fill="y", padx=(10, 0))
        ttk.Button(actions, text=translate("Rename selected", self.language), command=self.rename_selected).pack(
            fill="x", pady=(0, 6)
        )
        ttk.Button(actions, text=translate("Remove selected", self.language), command=self.remove_selected).pack(
            fill="x", pady=(0, 14)
        )
        ttk.Button(actions, text=translate("Move up", self.language), command=lambda: self.move_selected(-1)).pack(
            fill="x", pady=(0, 6)
        )
        ttk.Button(actions, text=translate("Move down", self.language), command=lambda: self.move_selected(1)).pack(
            fill="x"
        )

        footer = ttk.Frame(page)
        footer.pack(fill="x", pady=(14, 0))
        ttk.Label(footer, textvariable=self.count_var, foreground=BRAND_MUTED).pack(side="left")
        ttk.Button(footer, text=translate("Cancel", self.language), command=self.cancel).pack(side="right")
        ttk.Button(
            footer,
            text=translate("Save and Continue", self.language),
            style="PointConfigPrimary.TButton",
            command=self.save_and_continue,
        ).pack(side="right", padx=(0, 8))

    def _refresh_list(self, select_index: int | None = None) -> None:
        self.point_list.delete(0, "end")
        for name in self.names:
            self.point_list.insert("end", name)
        self.count_var.set(f"{len(self.names)} {translate('point(s)', self.language)}")
        self.selected_index = None
        if select_index is not None and 0 <= select_index < len(self.names):
            self.selected_index = select_index
            self.point_list.selection_set(select_index)
            self.point_list.activate(select_index)
            self.point_list.see(select_index)
            self.name_var.set(self.names[select_index])
        else:
            self.name_var.set("")

    def on_selection_changed(self, _event: tk.Event | None = None) -> None:
        selection = self.point_list.curselection()
        self.selected_index = selection[0] if selection else None
        self.name_var.set(self.names[self.selected_index] if self.selected_index is not None else "")

    def _validated_name(self) -> str | None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(
                translate("Point name required", self.language),
                translate("Enter a name for the point.", self.language),
                parent=self.window,
            )
            return None
        return name

    def add_point(self) -> None:
        name = self._validated_name()
        if name is None:
            return
        if any(existing.casefold() == name.casefold() for existing in self.names):
            messagebox.showwarning(
                translate("Duplicate point", self.language),
                translate("Each point name must be unique.", self.language),
                parent=self.window,
            )
            return
        self.names.append(name)
        self._refresh_list(len(self.names) - 1)

    def rename_selected(self) -> None:
        if self.selected_index is None:
            messagebox.showinfo(
                translate("Select a point", self.language),
                translate("Select a point to rename.", self.language),
                parent=self.window,
            )
            return
        name = self._validated_name()
        if name is None:
            return
        if any(
            index != self.selected_index and existing.casefold() == name.casefold()
            for index, existing in enumerate(self.names)
        ):
            messagebox.showwarning(
                translate("Duplicate point", self.language),
                translate("Each point name must be unique.", self.language),
                parent=self.window,
            )
            return
        self.names[self.selected_index] = name
        self._refresh_list(self.selected_index)

    def remove_selected(self) -> None:
        if self.selected_index is None:
            messagebox.showinfo(
                translate("Select a point", self.language),
                translate("Select a point to remove.", self.language),
                parent=self.window,
            )
            return
        removed_index = self.selected_index
        del self.names[removed_index]
        self._refresh_list(min(removed_index, len(self.names) - 1))

    def move_selected(self, direction: int) -> None:
        if self.selected_index is None:
            return
        destination = self.selected_index + direction
        if not 0 <= destination < len(self.names):
            return
        self.names[self.selected_index], self.names[destination] = self.names[destination], self.names[self.selected_index]
        self._refresh_list(destination)

    def save_and_continue(self) -> None:
        if not self.names:
            messagebox.showwarning(
                translate("Add a point", self.language),
                translate("Add at least one annotation point to continue.", self.language),
                parent=self.window,
            )
            return
        if len({name.casefold() for name in self.names}) != len(self.names):
            messagebox.showerror(
                translate("Duplicate point names", self.language),
                translate("Each point name must be unique.", self.language),
                parent=self.window,
            )
            return
        temporary_file = POINTS_FILE.with_suffix(".txt.tmp")
        try:
            content = "# Kinetho annotation point names\n# One point name per line.\n" + "\n".join(self.names) + "\n"
            temporary_file.write_text(content, encoding="utf-8")
            temporary_file.replace(POINTS_FILE)
        except OSError as exc:
            messagebox.showerror(translate("Could not save points", self.language), str(exc), parent=self.window)
            return
        self.window.grab_release()
        self.window.destroy()
        self.on_continue()

    def cancel(self) -> None:
        self.window.grab_release()
        self.window.destroy()
class VideoTrackingStudio:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = load_language()
        self.root.title(BRAND_NAME)
        self.root.geometry("820x640")
        self.root.minsize(720, 580)
        self.root.configure(background=BRAND_BACKGROUND)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BRAND_BACKGROUND)
        style.configure("TLabel", background=BRAND_BACKGROUND, foreground=BRAND_BLACK)
        style.configure("WorkflowTitle.TLabel", font=("Segoe UI", 12, "bold"), foreground=BRAND_BLACK)
        style.configure("WorkflowDescription.TLabel", font=("Segoe UI", 9), foreground=BRAND_MUTED)
        style.configure(
            "Workflow.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 9),
            background=BRAND_RED,
            foreground="white",
            borderwidth=0,
        )
        style.map("Workflow.TButton", background=[("active", "#cc0000"), ("pressed", "#a90000")])
        self.brand_logo = load_logo(root, (230, 160))
        self.window_icon = load_window_icon(root)
        if self.window_icon is not None:
            self.root.iconphoto(True, self.window_icon)
        self.video_processing_window: VideoProcessingWindow | None = None
        self.point_configuration_window: PointConfigurationWindow | None = None

        self._build_interface()

    def _build_interface(self) -> None:
        self.page = ttk.Frame(self.root, padding=(28, 24))
        self.page.pack(fill="both", expand=True)
        page = self.page

        brand_header = ttk.Frame(page)
        brand_header.pack(fill="x", pady=(0, 18))
        if self.brand_logo is not None:
            ttk.Label(brand_header, image=self.brand_logo).pack(anchor="center")
        ttk.Label(
            page,
            text=translate("Video preparation and point annotation", self.language),
            style="WorkflowDescription.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        language_row = ttk.Frame(page)
        language_row.pack(fill="x", pady=(0, 10))
        ttk.Label(language_row, text=translate("Language", self.language)).pack(side="right", padx=(0, 8))
        self.language_var = tk.StringVar(
            value=next(name for name, code in LANGUAGES.items() if code == self.language)
        )
        language_box = ttk.Combobox(
            language_row,
            textvariable=self.language_var,
            values=list(LANGUAGES),
            state="readonly",
            width=12,
        )
        language_box.pack(side="right")
        language_box.bind("<<ComboboxSelected>>", self.change_language)

        self._add_workflow(
            page,
            translate("Point Annotator", self.language),
            translate("Open an image folder and place named points on each frame.", self.language),
            translate("Open annotator", self.language),
            self.open_point_annotator,
        )
        ttk.Separator(page).pack(fill="x", pady=8)
        self._add_workflow(
            page,
            translate("Video Processing", self.language),
            translate("Edit videos or extract frames with the built-in FFmpeg workflow.", self.language),
            translate("Open video processing", self.language),
            self.open_video_tools,
        )

        footer = ttk.Frame(page)
        footer.pack(side="bottom", fill="x", pady=(16, 0))
        uninstall_button = ttk.Button(
            footer,
            text=translate("Uninstall Kinetho", self.language),
            command=self.uninstall,
        )
        if not IS_MAC:
            uninstall_button.pack(side="left")
        ttk.Button(
            footer,
            text=translate("Report a bug", self.language),
            command=self.report_bug,
        ).pack(side="left", padx=(8, 0))
        help_button = ttk.Button(
            footer,
            text="?",
            command=self.open_readme,
            width=3,
            style="Help.TButton",
        )
        help_button.pack(side="right")
        self._attach_help_tooltip(help_button, translate("Open the Kinetho guide", self.language))
        ttk.Label(
            footer,
            text=f"Version {APP_VERSION}",
            style="WorkflowDescription.TLabel",
        ).pack(side="right", padx=(0, 12))

    def report_bug(self) -> None:
        if not BUG_REPORT_URL:
            messagebox.showinfo(
                translate("Report a bug", self.language),
                translate("Bug reporting is not available yet. It will be added in a future version.", self.language),
                parent=self.root,
            )
            return
        webbrowser.open(BUG_REPORT_URL)

    def change_language(self, _event: tk.Event | None = None) -> None:
        selected_language = LANGUAGES.get(self.language_var.get())
        if selected_language is None or selected_language == self.language:
            return
        video_window = self.video_processing_window
        if video_window is not None and video_window.window.winfo_exists():
            if video_window.worker is not None and video_window.worker.is_alive():
                current_label = next(name for name, code in LANGUAGES.items() if code == self.language)
                self.language_var.set(current_label)
                messagebox.showinfo(
                    translate("Language change delayed", self.language),
                    translate(
                        "Finish or cancel video processing before changing the language.", self.language
                    ),
                    parent=self.root,
                )
                return
            video_window.window.destroy()
            self.video_processing_window = None
        try:
            save_language(selected_language)
        except OSError as exc:
            messagebox.showerror(
                translate("Could not save language preference", self.language),
                str(exc),
                parent=self.root,
            )
            return
        self.language = selected_language
        self.page.destroy()
        self._build_interface()

    def uninstall(self) -> None:
        if not FROZEN:
            messagebox.showinfo(
                translate("Uninstall Kinetho", self.language),
                translate("This option is available in the installed Kinetho application.", self.language),
                parent=self.root,
            )
            return

        confirmed = messagebox.askyesno(
            translate("Uninstall Kinetho", self.language),
            translate(
                "Remove Kinetho, its bundled FFmpeg dependency, and the Kinetho desktop shortcut?\n\n"
                "Your point configuration, videos, extracted images, and annotations will be kept.\n"
                "Close any other Kinetho or Point Annotator windows before continuing.",
                self.language,
            ),
            icon="warning",
            parent=self.root,
        )
        if not confirmed:
            return

        if not UNINSTALL_SCRIPT.is_file():
            messagebox.showerror(
                translate("Uninstaller not found", self.language), str(UNINSTALL_SCRIPT), parent=self.root
            )
            return

        temporary_script = Path(tempfile.gettempdir()) / f"Kinetho-Uninstall-{os.getpid()}.ps1"
        environment = os.environ.copy()
        environment["KINETHO_INSTALL_DIR"] = str(APP_DIR)
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            shutil.copyfile(UNINSTALL_SCRIPT, temporary_script)
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(temporary_script),
                ],
                cwd=tempfile.gettempdir(),
                env=environment,
                creationflags=creation_flags,
                close_fds=True,
            )
        except OSError as exc:
            temporary_script.unlink(missing_ok=True)
            messagebox.showerror(
                translate("Could not start uninstaller", self.language), str(exc), parent=self.root
            )
            return
        messagebox.showinfo(
            translate("Uninstall Kinetho", self.language),
            translate(
                "Kinetho will close now. The uninstaller will remove the application and FFmpeg, "
                "then confirm when cleanup is complete. Your data folders will be kept.",
                self.language,
            ),
            parent=self.root,
        )
        self.root.destroy()

    def _attach_help_tooltip(self, widget: ttk.Widget, text: str) -> None:
        tooltip: tk.Toplevel | None = None

        def show(_event: tk.Event) -> None:
            nonlocal tooltip
            if tooltip is not None or not widget.winfo_exists():
                return
            x = widget.winfo_rootx() + widget.winfo_width() + 6
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

    def open_readme(self) -> None:
        readme_path = README_FR_PATH if self.language == "fr" else README_PATH
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(translate("Guide not found", self.language), str(exc), parent=self.root)
            return

        help_window = tk.Toplevel(self.root)
        help_window.title(f"{BRAND_NAME} | {translate('Kinetho User Guide', self.language)}")
        help_window.geometry("820x700")
        help_window.minsize(600, 420)
        help_window.configure(background=BRAND_BACKGROUND)
        if self.window_icon is not None:
            help_window.iconphoto(True, self.window_icon)
        help_window.transient(self.root)

        content = ttk.Frame(help_window, padding=18)
        content.pack(fill="both", expand=True)
        ttk.Label(
            content,
            text=translate("Kinetho User Guide", self.language),
            style="WorkflowTitle.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        text_frame = ttk.Frame(content)
        text_frame.pack(fill="both", expand=True)
        guide = tk.Text(
            text_frame,
            wrap="word",
            padx=14,
            pady=12,
            font=("Segoe UI", 10),
            background="white",
            foreground=BRAND_BLACK,
            relief="flat",
        )
        guide.insert("1.0", readme_text)
        guide.configure(state="disabled")
        guide.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=guide.yview)
        scrollbar.pack(side="right", fill="y")
        guide.configure(yscrollcommand=scrollbar.set)

        ttk.Button(content, text=translate("Close", self.language), command=help_window.destroy).pack(
            anchor="e", pady=(12, 0)
        )

    def _add_workflow(
        self,
        parent: ttk.Frame,
        title: str,
        description: str,
        button_text: str,
        command,
    ) -> None:
        row = ttk.Frame(parent, padding=(0, 8))
        row.pack(fill="x")
        text_column = ttk.Frame(row)
        text_column.pack(side="left", fill="x", expand=True, padx=(0, 18))
        ttk.Label(text_column, text=title, style="WorkflowTitle.TLabel").pack(anchor="w")
        ttk.Label(
            text_column,
            text=description,
            style="WorkflowDescription.TLabel",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Button(
            row,
            text=button_text,
            style="Workflow.TButton",
            command=command,
            width=22,
        ).pack(side="right")

    def open_point_annotator(self, image_folder: Path | None = None) -> None:
        if self.point_configuration_window is not None and self.point_configuration_window.window.winfo_exists():
            self.point_configuration_window.window.deiconify()
            self.point_configuration_window.window.lift()
            return

        self.point_configuration_window = PointConfigurationWindow(
            self.root,
            lambda: self._launch_point_annotator(image_folder),
            self.language,
        )

    def _launch_point_annotator(self, image_folder: Path | None) -> None:
        self.point_configuration_window = None
        command = [sys.executable, "--point-annotator"] if FROZEN else [sys.executable, str(ENTRY_SCRIPT), "--point-annotator"]
        if image_folder is not None:
            command.append(str(image_folder))
        try:
            subprocess.Popen(command, cwd=str(APP_DIR))
        except OSError as exc:
            messagebox.showerror(
                translate("Could not start Point Annotator", self.language), str(exc), parent=self.root
            )

    def open_video_tools(self) -> None:
        if self.video_processing_window is not None and self.video_processing_window.window.winfo_exists():
            self.video_processing_window.window.deiconify()
            self.video_processing_window.window.lift()
            return
        if self.video_processing_window is None:
            self.video_processing_window = VideoProcessingWindow(self.root, self.language)


def main() -> None:
    root = tk.Tk()
    VideoTrackingStudio(root)
    root.mainloop()


if __name__ == "__main__":
    main()
