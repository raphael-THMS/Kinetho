# Kinetho | Video Tracking and Annotation

Kinetho is a Windows application for preparing videos, extracting image frames, and placing named points without modifying the source files.

This folder contains the application source code. End users should install Kinetho from the [latest release](https://github.com/raphael-THMS/Kinetho/releases/latest); see the main `README.md`.

## Using Point Annotator

1. On the Kinetho home page, choose **Video Processing** to prepare videos and extract frames, or choose **Point Annotator** to start annotating.
2. In Point Annotator's configuration page, add, rename, remove, or reorder point names, then click **Save and Continue**. Kinetho saves the list to `points.txt`.
3. Click **Open image folder** and select the relevant image folder. Extracted frames are saved under `Image folders`, one subfolder per source video.
4. Select a point from the list on the left, then click the image to place it. By default, the application advances to the next image after each placement and keeps the same point selected. Uncheck **Advance after placing a point** to annotate multiple points on the same image.
5. Use **Previous image** and **Next image**, or the left/right arrow keys, to navigate. Annotations are saved automatically when changing images and when closing the application.

Each point is assigned its own marker color. Kinetho provides 24 distinct colors before the palette repeats.

Supported image formats are JPEG, PNG, BMP, TIFF, and WebP. Only images directly inside the selected folder are opened.

## Output file

Each image folder contains an `annotations.csv` file. It stores one row per image and point, with `x` and `y` coordinates in pixels of the original image. Empty coordinates mean that the point has not been placed. The file is updated automatically; the original images remain unchanged.

To resume work, reopen the same folder. Existing points will be loaded from the CSV file. Point names can be changed from the configuration page each time you open Point Annotator.

## Running from source (development)

Requirements: Python 3.10 or later. From the repository root, run `scripts\Build Kinetho EXE.ps1` once: it creates the local `.venv` with Pillow and PyInstaller. Then start Kinetho with:

```powershell
.venv\Scripts\pythonw.exe src\kinetho_app.py
```

The `.venv` environment is local, does not affect other Python installations, and is excluded from Git and from the release ZIP. Video processing from source needs FFmpeg: run `scripts\Setup FFmpeg.ps1` once. When run from source, videos, extracted frames and `kinetho_settings.json` are written in the repository and ignored by Git.
