from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def execute(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=ROOT)


def package_application(application: Path, release: Path, version: str) -> None:
    release.mkdir(exist_ok=True)
    archive = release / f"Kinetho-{version}-macOS-arm64.zip"
    execute(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(application), str(archive)])
    disk_image = release / f"Kinetho-{version}-macOS-arm64.dmg"
    with tempfile.TemporaryDirectory(prefix="Kinetho-DMG-") as temporary:
        stage = Path(temporary)
        shutil.copytree(application, stage / "Kinetho.app", symlinks=True)
        os.symlink("/Applications", stage / "Applications", target_is_directory=True)
        shutil.copy2(ROOT / "README-Installation-Mac.md", stage / "LIRE-MOI.md")
        execute(["hdiutil", "create", "-volname", "Kinetho", "-srcfolder", str(stage), "-ov", "-format", "UDZO", str(disk_image)])
    print(f"Application: {application}\nZIP: {archive}\nDMG: {disk_image}")


def validate_ffmpeg(folder: Path) -> Path:
    binary = folder / "bin" / "ffmpeg"
    for path in (binary, folder / "COPYING.GPLv3.txt", folder / "FFmpeg-GPLv3-Notice.txt", folder / "README.txt"):
        if not path.is_file():
            raise ValueError(f"Missing macOS FFmpeg file: {path}")
    if not any((folder / "source").glob("*.tar.*")):
        raise ValueError("Include the corresponding FFmpeg source archive in the source folder.")
    architectures = subprocess.check_output(["lipo", "-archs", str(binary)], text=True)
    if "arm64" not in architectures.split():
        raise ValueError("FFmpeg must contain an arm64 architecture, not a Windows or Intel-only binary.")
    libraries = subprocess.check_output(["otool", "-L", str(binary)], text=True)
    dependencies = [line.strip().split(" (", 1)[0] for line in libraries.splitlines()[1:]]
    unsupported = [path for path in dependencies if not path.startswith(("/usr/lib/", "/System/Library/"))]
    if unsupported:
        raise ValueError(f"FFmpeg is not standalone; external libraries: {unsupported}")
    encoders = subprocess.check_output([str(binary), "-hide_banner", "-encoders"], text=True)
    if "libx264" not in encoders:
        raise ValueError("FFmpeg must include libx264 for Kinetho video operations.")
    return binary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--ffmpeg-folder", type=Path, default=ROOT / "Third-party" / "FFmpeg-Mac")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise ValueError("Run this command on macOS; Windows cannot build a macOS app.")
    if platform.machine() != "arm64":
        raise ValueError("Use a native Apple Silicon Python, not an Intel Python under Rosetta.")
    if not (3, 10) <= sys.version_info[:2] < (3, 15):
        raise ValueError("Use Python 3.10 to 3.14; Python 3.13 from python.org is recommended.")
    execute([sys.executable, "-c", "import tkinter; root=tkinter.Tk(); root.withdraw(); root.destroy()"])
    environment = ROOT / ".venv-mac"
    python = environment / "bin" / "python"
    if not python.is_file():
        execute([sys.executable, "-m", "venv", str(environment)])
    execute([str(python), "-m", "pip", "install", "-r", str(ROOT / "src" / "build-requirements.txt")])
    if not args.build:
        execute([str(python), str(ROOT / "src" / "kinetho_app.py")])
        return

    ffmpeg_folder = args.ffmpeg_folder.expanduser().resolve()
    binary = validate_ffmpeg(ffmpeg_folder)
    version_text = (ROOT / "src" / "branding.py").read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"', version_text)
    if match is None:
        raise ValueError("APP_VERSION was not found.")
    version = match.group(1)
    build = ROOT / ".build-mac"
    build.mkdir(exist_ok=True)
    icon = build / "Kinetho.icns"
    execute([str(python), "-c", "from PIL import Image; import sys; Image.open(sys.argv[1]).convert('RGBA').resize((1024,1024)).save(sys.argv[2],format='ICNS')", str(ROOT / "src" / "kinetho_logo_white.png"), str(icon)])
    command = [
        str(python), "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", "Kinetho", "--target-arch", "arm64", "--icon", str(icon),
        "--osx-bundle-identifier", "io.github.raphael-thms.kinetho",
        "--distpath", str(build / "dist"), "--workpath", str(build / "work"),
        "--specpath", str(build), "--paths", str(ROOT / "src"), "--collect-all", "PIL",
        "--add-binary", f"{binary}:ffmpeg/bin",
    ]
    for name in ("kinetho_logo.png", "kinetho_logo_white.png", "points.txt"):
        command.extend(["--add-data", f"{ROOT / 'src' / name}:."])
    for name in ("README.md", "README-fr.md", "README-Mac.md", "README-Installation-Mac.md", "LICENSE"):
        command.extend(["--add-data", f"{ROOT / name}:."])
    for document in sorted(ffmpeg_folder.glob("*.txt")):
        command.extend(["--add-data", f"{document}:ffmpeg"])
    command.extend(["--add-data", f"{ffmpeg_folder / 'source'}:ffmpeg/source"])
    command.append(str(ROOT / "src" / "kinetho_app.py"))
    execute(command)
    application = build / "dist" / "Kinetho.app"
    import plistlib

    metadata = application / "Contents" / "Info.plist"
    with metadata.open("rb") as stream:
        info = plistlib.load(stream)
    info.update(CFBundleShortVersionString=version, CFBundleVersion=version, LSMinimumSystemVersion="14.0")
    with metadata.open("wb") as stream:
        plistlib.dump(info, stream)
    execute(["codesign", "--force", "--deep", "--sign", "-", str(application)])
    release = ROOT / "release-mac"
    package_application(application, release, version)
    print("Ad-hoc signed only; not Apple-notarized. Test on a Mac before distributing.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Kinetho macOS: {error}", file=sys.stderr)
        sys.exit(1)