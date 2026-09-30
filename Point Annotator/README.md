# Kinetho | Video Tracking and Annotation

Kinetho is a Windows application for preparing videos, extracting image frames, and placing named points without modifying the source files.

## Getting started

1. Extract `Kinetho-Windows.zip` to a writable folder.
2. Double-click `Create Kinetho Desktop Shortcut.vbs` once to add the logo shortcut to your desktop.
3. Double-click the **Kinetho** desktop icon. On first launch, setup installs the local Python environment and Pillow; allow the download to finish.
4. Choose **Video Processing** to prepare videos and extract frames, or choose **Point Annotator** to start annotating.
5. In Point Annotator's configuration page, add, rename, remove, or reorder point names, then click **Save and Continue**. Kinetho saves the list to `points.txt`.
6. Click **Open image folder** and select the relevant image folder. Extracted frames are saved under `Image folders`, one subfolder per source video.
7. Select a point from the list on the left, then click the image to place it. By default, the application advances to the next image after each placement and keeps the same point selected. Uncheck **Advance after placing a point** to annotate multiple points on the same image.
8. Use **Previous image** and **Next image**, or the left/right arrow keys, to navigate. Annotations are saved automatically when changing images and when closing the application.

Each point is assigned its own marker color. Kinetho provides 24 distinct colors before the palette repeats.

Supported image formats are JPEG, PNG, BMP, TIFF, and WebP. Only images directly inside the selected folder are opened.

## Output file

Each image folder contains an `annotations.csv` file. It stores one row per image and point, with `x` and `y` coordinates in pixels of the original image. Empty coordinates mean that the point has not been placed. The file is updated automatically; the original images remain unchanged.

To resume work, reopen the same folder. Existing points will be loaded from the CSV file. Point names can be changed from the configuration page each time you open Point Annotator.

## Development setup

`Setup.bat` creates or repairs a Python environment local to this application and installs Pillow. Python 3.10 or later and Internet access are required for the initial setup. The setup checks and repairs environments whose original Python installation is unavailable, so Kinetho can be moved to another Windows computer.

The `.venv` environment is local and does not affect other Python installations. It is excluded from the portable ZIP and is created on the destination computer.
