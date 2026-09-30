# Kinetho | Video Processing (Windows)

Kinetho opens the graphical Video Processing window. It uses FFmpeg to edit videos and extract frames; processing status and output are shown in the application instead of a console window.

## Quick start

1. Put source videos in `Video edition\Videos_before_modifications\` or processed videos in `Videos\` at the project root.
2. Run Kinetho and choose **Video Processing**.
3. Select an operation, its settings, input folder, and output folder in the graphical window.

## Extract frames for annotation

Choose **Extract frames**, enter the interval, and select seconds, minutes, or hours. The first decoded frame and the last encoded frame are preserved; intermediate frames are sampled at the selected interval. For MP4/MOV files, Kinetho reads through container edit lists that can otherwise hide the final frame. Choose JPG or PNG output. The application creates one folder per video under `Image folders\`, for example:

```text
Image folders\VideoName\frame_000001.jpg
```

In Point Annotator, click **Open image folder** and select the individual video folder, not the `Image folders` parent folder.

## Inputs and outputs

- Raw video input: `Video edition\Videos_before_modifications\`
- Processed video output and input: `Videos\`
- Extracted frame output: `Image folders\`

Most video operations let you choose between raw videos and processed videos as their input. Outputs are written separately; source videos are not overwritten.

The input scan recognizes MP4, MOV, MKV, AVI, WMV, WebM, MPEG/MPG, MTS/M2TS, TS, 3GP, FLV, ASF, MXF, OGV, VOB, and F4V. Files with other extensions are listed as skipped. If one recognized video is damaged or cannot be decoded, Kinetho marks that file as failed and continues with the remaining videos.

## FFmpeg

The application checks for FFmpeg in `ffmpeg\bin\ffmpeg.exe` at the project root and in the system `PATH`. Install FFmpeg and add it to `PATH`, or place a portable `ffmpeg.exe` in the project folder.

## Other video tools

- **Split by time** accepts comma-separated start times and durations in seconds (`30s`), minutes (`5m`), hours (`1h`), `mm:ss`, or `hh:mm:ss`. Bare numbers continue to mean minutes.
- **Crop or split by dimensions** supports manual margins, equal slices, two halves, and four quadrants.
- **Merge numbered parts** combines files such as `Name_1.mp4`, `Name_2.mp4`, and `Name_3.mp4` into `Name_MERGED.mp4`.
- **Repair duration / timestamps** offers fast remuxing or safe re-encoding.

The merge operation uses `Video edition\merge_by_suffix.ps1`. Keep that helper file when moving the project to another computer.
