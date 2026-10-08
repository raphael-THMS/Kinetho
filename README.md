# Kinetho

Kinetho is a Windows application for preparing videos, extracting frames, and annotating image points.

## Install Kinetho

1. Extract `Kinetho-Windows.zip`.
2. Double-click `Install Kinetho.bat`.
3. In the setup window, choose the installation folder and whether to create a desktop shortcut. The default folder is `%LOCALAPPDATA%\Programs\Kinetho`.
4. Click **Install** and wait for the progress bar to finish. Setup does not start Kinetho automatically.
5. Start Kinetho from the desktop shortcut, if selected, or open `Kinetho.exe` in the chosen folder. No separate Python installation is required.
6. Choose **Video Processing** to prepare videos or extract frames; choose **Point Annotator** to configure and annotate named points.

Use the language menu on the home page to switch between English and French. Kinetho remembers your choice.

To remove Kinetho and its bundled FFmpeg dependency, use **Uninstall Kinetho** on the home page and confirm. The desktop shortcut and application files are removed; point configuration, videos, extracted images, and annotations are kept in the installation folder.

For **Split by time**, enter seconds (`30s`), minutes (`5m`), hours (`1h`), `mm:ss`, or `hh:mm:ss`. A number without a unit is still interpreted as minutes.

## Requirements

- Windows 10 or Windows 11
- No separate Python installation is required; Kinetho.exe includes its runtime.
- FFmpeg 9.0.2 is included in the Kinetho package; no separate FFmpeg installation is required.

The bundled FFmpeg build includes `libx264` and is distributed under GPLv3. See `ffmpeg\FFmpeg-GPLv3-Notice.txt` and the accompanying license and build information before redistributing Kinetho.

The distributed EXE is not code-signed. Windows SmartScreen or an organization's application-control policy may warn about or block it. For unrestricted international distribution, sign the EXE with a trusted code-signing certificate.

## For maintainers

Run `Setup FFmpeg.ps1` once to download and verify the pinned FFmpeg build, build the application with `Build Kinetho EXE.ps1`, then run `Create Portable Package.ps1` to produce `Kinetho-Windows.zip`. The package excludes local videos, extracted frames, and annotations.

Annotations are stored in `annotations.csv` next to the image files. Keep or share data folders separately; they are intentionally excluded from the software package.

## Folders

- `%LOCALAPPDATA%\Programs\Kinetho\`: installed executable, runtime, and point-name configuration
- `Video edition\`: FFmpeg tools and raw video input folder
- `Videos\`: processed videos
- `Image folders\`: extracted frames, organized by source video
- `Kinetho.ico`: white-background Windows icon used by the desktop shortcut and taskbar

## License

Kinetho is released under the MIT License. Copyright (c) 2026 Raphael Thomas. See `LICENSE`.

The bundled FFmpeg executable is a separate program distributed under GPLv3; see `ffmpeg\FFmpeg-GPLv3-Notice.txt`.
