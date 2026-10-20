from __future__ import annotations

import shutil
import sys
from pathlib import Path


FROZEN = getattr(sys, "frozen", False)
SOURCE_DIR = Path(__file__).resolve().parent
EXECUTABLE_DIR = Path(sys.executable).resolve().parent
IS_MAC = sys.platform == "darwin"
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", EXECUTABLE_DIR / "_internal")) if FROZEN else SOURCE_DIR
PROJECT_DIR = RESOURCE_DIR if FROZEN and IS_MAC else EXECUTABLE_DIR if FROZEN else SOURCE_DIR.parent
DOCUMENTATION_DIR = PROJECT_DIR / "docs" if FROZEN and not IS_MAC else PROJECT_DIR
DATA_DIR = (
    Path.home() / "Library" / "Application Support" / "Kinetho"
    if IS_MAC
    else EXECUTABLE_DIR / "data" if FROZEN else SOURCE_DIR
)


def settings_directory() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if FROZEN and not IS_MAC:
        for name in ("points.txt", "kinetho_settings.json"):
            legacy = EXECUTABLE_DIR / name
            target = DATA_DIR / name
            if legacy.is_file():
                if not target.exists():
                    shutil.copyfile(legacy, target)
                if legacy.read_bytes() == target.read_bytes():
                    legacy.unlink()
    return DATA_DIR


def points_file() -> Path:
    target = settings_directory() / "points.txt"
    if not target.exists() and (IS_MAC or FROZEN):
        shutil.copyfile(RESOURCE_DIR / "points.txt", target)
    return target
