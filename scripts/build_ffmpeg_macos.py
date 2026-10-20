from __future__ import annotations

import lzma
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FFMPEG_COMMIT = "894da5ca7d742e4429ffb2af534fcda0103ef593"
X264_COMMIT = "31e19f92f00c7003fa115047ce50978bc98c3a0d"
FFMPEG_VERSION = "8.0.1"


def run(command: list[str], folder: Path, environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=folder, env=environment, check=True)


def checkout(url: str, commit: str, folder: Path, environment: dict[str, str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    run(["git", "init"], folder, environment)
    run(["git", "fetch", "--depth", "1", url, commit], folder, environment)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], folder, environment)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=folder, text=True).strip()
    if actual != commit:
        raise ValueError(f"Unexpected source commit: {actual}")


def archive_source(folder: Path, destination: Path) -> None:
    process = subprocess.Popen(["git", "archive", "--format=tar", "HEAD"], cwd=folder, stdout=subprocess.PIPE)
    assert process.stdout is not None
    with process.stdout, lzma.open(destination, "wb") as output:
        shutil.copyfileobj(process.stdout, output)
    if process.wait() != 0:
        raise ValueError(f"Cannot archive sources: {folder}")


def main() -> None:
    from macos import build_target, validate_ffmpeg

    architecture, minimum = build_target()
    tools = ["git", "make", "clang", "pkg-config"]
    if architecture == "x86_64":
        tools.append("nasm")
    for tool in tools:
        if shutil.which(tool) is None:
            raise ValueError(f"Missing build tool: {tool}")
    work = ROOT / ".build-mac" / architecture / "ffmpeg-source"
    prefix = work / "prefix"
    output = ROOT / "Third-party" / "FFmpeg-Mac" / architecture
    prefix.mkdir(parents=True, exist_ok=True)
    (output / "bin").mkdir(parents=True, exist_ok=True)
    (output / "source").mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["MACOSX_DEPLOYMENT_TARGET"] = minimum
    environment["PKG_CONFIG_LIBDIR"] = str(prefix / "lib" / "pkgconfig")
    environment["PKG_CONFIG_PATH"] = str(prefix / "lib" / "pkgconfig")
    compiler_flags = f"-arch {architecture} -mmacosx-version-min={minimum}"
    configure_arch = "aarch64" if architecture == "arm64" else "x86_64"
    x264 = work / "x264"
    ffmpeg = work / "ffmpeg"
    checkout("https://github.com/mirror/x264.git", X264_COMMIT, x264, environment)
    checkout("https://github.com/FFmpeg/FFmpeg.git", FFMPEG_COMMIT, ffmpeg, environment)
    jobs = str(min(os.cpu_count() or 2, 4))
    x264_options = [
        "./configure", f"--prefix={prefix}", f"--host={configure_arch}-apple-darwin",
        "--enable-static", "--disable-cli", "--disable-opencl", "--enable-pic",
        f"--extra-cflags={compiler_flags}", f"--extra-ldflags={compiler_flags}",
    ]
    run(x264_options, x264, environment)
    run(["make", f"-j{jobs}"], x264, environment)
    run(["make", "install"], x264, environment)
    ffmpeg_options = [
        "./configure", f"--prefix={prefix}", f"--arch={configure_arch}", "--target-os=darwin", "--cc=clang",
        "--disable-autodetect", "--enable-gpl", "--enable-version3", "--enable-libx264", "--enable-zlib",
        "--enable-static", "--disable-shared", "--disable-ffplay", "--disable-ffprobe",
        "--disable-doc", "--disable-debug", "--disable-network", "--pkg-config-flags=--static",
        f"--extra-cflags={compiler_flags} -I{prefix / 'include'}",
        f"--extra-ldflags={compiler_flags} -L{prefix / 'lib'}",
    ]
    run(ffmpeg_options, ffmpeg, environment)
    run(["make", f"-j{jobs}"], ffmpeg, environment)
    shutil.copy2(ffmpeg / "ffmpeg", output / "bin" / "ffmpeg")
    shutil.copy2(ffmpeg / "COPYING.GPLv3", output / "COPYING.GPLv3.txt")
    shutil.copy2(x264 / "COPYING", output / "COPYING.x264.txt")
    archive_source(ffmpeg, output / "source" / f"ffmpeg-{FFMPEG_VERSION}.tar.xz")
    archive_source(x264, output / "source" / f"x264-{X264_COMMIT}.tar.xz")
    notice = (
        "FFmpeg is a separate executable, not part of Kinetho's MIT license.\n"
        "This FFmpeg build links x264 statically and is distributed under GPLv3.\n"
        "FFmpeg and x264 sources and licenses accompany this build.\n"
        "System libraries are provided by macOS. No Homebrew runtime libraries are required.\n"
    )
    (output / "FFmpeg-GPLv3-Notice.txt").write_text(notice, encoding="utf-8")
    build_info = (
        f"FFmpeg {FFMPEG_VERSION}: https://github.com/FFmpeg/FFmpeg/tree/{FFMPEG_COMMIT}\n"
        f"x264: https://github.com/mirror/x264/tree/{X264_COMMIT}\n"
        f"Architecture: {architecture}. Build target: macOS {minimum} (application compatibility must be tested).\n"
        "Build recipe: scripts/build_ffmpeg_macos.py in the Kinetho repository.\n"
        f"x264 configuration: {x264_options!r}\nFFmpeg configuration: {ffmpeg_options!r}\n"
    )
    (output / "README.txt").write_text(build_info, encoding="utf-8")
    shutil.copy2(Path(__file__), output / "source" / "build_ffmpeg_macos.py")
    validate_ffmpeg(output)
    print(f"Standalone FFmpeg with sources and licenses prepared: {output}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"FFmpeg macOS build: {error}", file=sys.stderr)
        sys.exit(1)