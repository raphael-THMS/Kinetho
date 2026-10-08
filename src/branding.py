from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk

from PIL import Image, ImageTk
from app_paths import RESOURCE_DIR


APP_DIR = RESOURCE_DIR
LOGO_PATH = APP_DIR / "kinetho_logo.png"
WINDOW_ICON_PATH = APP_DIR / "kinetho_logo_white.png"
BRAND_NAME = "Kinetho"
APP_VERSION = "0.2.0"
BRAND_RED = "#ff0000"
BRAND_BLACK = "#101010"
BRAND_BACKGROUND = "#f4f4f2"
BRAND_MUTED = "#5c5c5c"


def load_logo(master: tk.Misc, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
    if not LOGO_PATH.is_file():
        return None
    with Image.open(LOGO_PATH) as source:
        image = source.convert("RGBA")
        alpha_bounds = image.getchannel("A").getbbox()
        if alpha_bounds is not None:
            image = image.crop(alpha_bounds)
        image.thumbnail(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)


def load_window_icon(master: tk.Misc, size: tuple[int, int] = (64, 64)) -> ImageTk.PhotoImage | None:
    if not WINDOW_ICON_PATH.is_file():
        return load_logo(master, size)
    with Image.open(WINDOW_ICON_PATH) as source:
        image = source.convert("RGBA")
        image.thumbnail(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)