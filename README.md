# Kinetho

## Reference scale in Point Annotator

Open the reference image in a folder and choose **Scale > Define scale** in the top-right
menu. Enter the real length and unit together in one dialog (for example `10` and `cm`),
then click its two endpoints. Cyan markers and a
line show the scale without adding names to the annotation point list or advancing images.
One scale is saved per folder. Use **Show scale image** to return to it, **Define scale**
to replace it, or **Remove scale** to delete it. Switching images/tools or pressing Delete
during placement cancels the unfinished scale and preserves the previous one.

The complete scale is saved immediately in `annotations.csv`. Extra columns are
`scale_image`, `scale_x1`, `scale_y1`, `scale_x2`, `scale_y2`, `scale_length`, `scale_unit`,
`scale_pixels`, and `scale_units_per_pixel`, repeated on each annotation row.
Coordinates are original-image pixels, unaffected by zoom/pan. The conversion factor is
real length divided by pixel distance. In the scale dialog choose **Pixels** or
**Real unit entered above** for output `x,y`. Real output multiplies each coordinate
by `scale_units_per_pixel`; `x_pixel,y_pixel` preserve original pixels for resuming work.
`coordinate_space` is `pixel` or `real`; `coordinate_unit` is `px` or the entered unit.
The origin stays at the top-left, x right and y down; axes are not rotated.
Scale endpoints always remain in pixels. The choice reloads with the scale.
Replacing/removing the scale recalculates output from original pixels.
Closing without a complete scale asks whether to close and save in pixels (Yes)
or return to the annotator (No).
Scales reload when reopening a folder; without a scale, the four-column CSV format is unchanged,
and legacy CSV files remain supported. The conversion applies to other images only if their
framing and physical scale match the reference. Older Kinetho versions discard the extra
columns when saving and may interpret real units as pixels: only resume these files
with the updated application.

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
