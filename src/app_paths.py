from __future__ import annotations

import shutil
import sys
from pathlib import Path


FROZEN = getattr(sys, "frozen", False)
SOURCE_DIR = Path(__file__).resolve().parent
EXECUTABLE_DIR = Path(sys.executable).resolve().parent
IS_MAC = sys.platform == "darwin"
RESOURCE_DIR = (
    Path(getattr(sys, "_MEIPASS", SOURCE_DIR))
    if FROZEN and IS_MAC
    else EXECUTABLE_DIR if FROZEN else SOURCE_DIR
)
PROJECT_DIR = RESOURCE_DIR if FROZEN else SOURCE_DIR.parent
DATA_DIR = (
    Path.home() / "Library" / "Application Support" / "Kinetho"
    if IS_MAC
    else EXECUTABLE_DIR if FROZEN else SOURCE_DIR
)
WORKSPACE_DIR = DATA_DIR / "Workspace" if IS_MAC else PROJECT_DIR


def settings_directory() -> Path:
    if IS_MAC:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def points_file() -> Path:
    target = settings_directory() / "points.txt"
    if IS_MAC and not target.exists():
        shutil.copyfile(RESOURCE_DIR / "points.txt", target)
    return target