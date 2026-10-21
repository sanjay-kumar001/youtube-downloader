# YouTube Audio & High-Quality Video Downloader

A command-line guide for the `youtube-downloader` project. The program uses **yt-dlp** to retrieve media and **FFmpeg** to extract/convert audio or merge separate video and audio streams. Installation commands in this manual focus on Ubuntu/Linux; other platforms need the equivalent Python, `uv`, and FFmpeg setup.

> **Use responsibly:** Download only content you own, have permission to download, or are otherwise allowed to save under applicable law and YouTube's terms. This program does not bypass DRM, paywalls, or access controls.

---

## Index

1. [Overview](#1-overview)
2. [Requirements](#2-requirements)
3. [Installation and setup on Ubuntu](#3-installation-and-setup-on-ubuntu)
4. [Project layout](#4-project-layout)
5. [Quick start](#5-quick-start)
6. [Command-line reference](#6-command-line-reference)
7. [Audio download examples](#7-audio-download-examples)
8. [Video download examples](#8-video-download-examples)
9. [Playlist downloads](#9-playlist-downloads)
10. [Output files, naming, and folders](#10-output-files-naming-and-folders)
11. [Duplicate prevention and download archives](#11-duplicate-prevention-and-download-archives)
12. [JSON reports and logs](#12-json-reports-and-logs)
13. [How quality and formats work](#13-how-quality-and-formats-work)
14. [Troubleshooting](#14-troubleshooting)
15. [Updating the tool](#15-updating-the-tool)
16. [Typical workflows](#16-typical-workflows)

---

## 1. Overview

The script supports:

- Audio-only downloads, including the best available audio stream, MP3, or M4A.
- Video downloads with audio, up to a requested maximum height of 4320p (8K), if the source provides it.
- MKV or MP4 output containers for merged video downloads.
- Single videos and playlists, including selecting specific playlist entries.
- Retry attempts and continued downloads where supported.
- Duplicate prevention using yt-dlp's download archive.
- Portable filename restrictions and video IDs in filenames to reduce collisions.
- A JSON summary report for each run.
- Progress information and error summaries.

**Important:** A resolution setting is a *maximum*, not a promise. If a video is only available at 1080p, selecting 2160p will not create a 4K version; yt-dlp selects the best compatible format at or below the requested cap when possible.

## 2. Requirements

- Ubuntu/Linux (commands below are for Ubuntu).
- Python 3.10 or later. The project setup described here uses [`uv`](https://docs.astral.sh/uv/) to manage Python and dependencies.
- `yt-dlp`, installed in the project environment.
- **FFmpeg**, installed and available on `PATH`, for MP3/M4A extraction and merging video/audio streams.
- Internet access and a supported YouTube URL.

## 3. Installation and setup on Ubuntu

### 3.1 Install system packages

Update package metadata and install FFmpeg and basic tools:

```bash
sudo apt update
sudo apt install -y ffmpeg curl ca-certificates
```

Confirm FFmpeg is available:

```bash
ffmpeg -version
```

If this prints version/build information, FFmpeg is installed. If the command is not found, check your package installation and `PATH`.

### 3.2 Install `uv` (if it is not already installed)

One common installation method is:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen the terminal if needed, then verify:

```bash
uv --version
```

If your system already has `uv`, you can skip this step.

### 3.3 Open the project directory

For a public GitHub checkout, clone the repository and enter it:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/youtube-downloader.git
cd youtube-downloader
```

Replace `YOUR_GITHUB_USERNAME` with the GitHub account that hosts the repository. If you are working from a local copy instead, open the directory that contains `youtube_downloader.py` and `pyproject.toml`.

### 3.4 Create or sync the Python environment

**Existing project:** from the project directory, run:

```bash
uv sync
```

If `yt-dlp` is not listed as a project dependency yet, add it:

```bash
uv add yt-dlp
```

**Fresh project without `pyproject.toml`:** initialize it and add the dependency:

```bash
uv init
uv add yt-dlp
```

Do not run `uv init` over an existing project unless you intend to initialize or modify its project metadata.

### 3.5 Verify the script and command-line options

Run the help screen:

```bash
uv run youtube_downloader.py --help
```

You can also verify that Python can compile the script:

```bash
uv run python -m py_compile youtube_downloader.py
```

No output from the compilation command normally means syntax compilation succeeded.

## 4. Project layout

The repository contains the application, project metadata, documentation, tests, and GitHub Actions workflow. After you run the program, your local output directory may contain downloaded media, hidden archive files, and timestamped JSON reports. These local artifacts should not be committed to GitHub. The `.gitignore` file excludes the common generated files. Hidden archive files start with a dot.

## 5. Quick start

Run all commands from the project directory:

```bash
cd ~/Music/youtube-downloader
```

### Download best available audio

```bash
uv run youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download audio as MP3

```bash
uv run youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --format mp3
```

### Download video, up to 4K, as MKV

```bash
uv run youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --mode video --resolution 2160
```

### Download a playlist

```bash
uv run youtube_downloader.py "https://www.youtube.com/playlist?list=PLAYLIST_ID" --playlist
```

Replace the example URLs with the actual video or playlist URL. Keep the URL in quotation marks, especially when it contains `&` query parameters.

## 6. Command-line reference

The complete built-in reference is available at any time:

```bash
uv run youtube_downloader.py --help
```

### Arguments

| Argument | Default | Purpose / accepted values |
|---|---|---|
| `url` | Required | YouTube video or playlist URL. |
| `--mode {audio,video}` | `audio` | `audio` downloads audio only; `video` downloads video with audio. |
| `--resolution {best,720,1080,1440,2160,4320}` | `2160` | Video mode only. Maximum video height in pixels: 720p, 1080p, 1440p, 2160p (4K), or 4320p (8K). `best` requests the best available format without a height cap. |
| `--video-container {mkv,mp4}` | `mkv` | Video mode only. Container for merged video/audio streams. MKV is the default and generally accommodates a wider range of codecs without re-encoding; MP4 may be more convenient for some devices. |
| `-f, --format {best,mp3,m4a}` | `best` | Audio mode only. `best` keeps the best available audio stream; `mp3` or `m4a` extracts/converts to that format using FFmpeg. |
| `-q, --quality {128,192,256,320,0}` | `320` | MP3 bitrate in kbps. `128`, `192`, `256`, and `320` are bitrate targets; `0` selects best VBR quality. Applies only when `--format mp3` is selected. |
| `-o, --output PATH` | `downloads` | Destination directory. Created automatically if needed. Relative paths are relative to the current working directory. |
| `-p, --playlist` | Off | Enable playlist downloading. Without it, the script treats the URL as a single video and disables playlist expansion. |
| `--playlist-items VALUE` | All entries | Select playlist entries, e.g. `1-5` or `1,3,7`. Requires `--playlist`. |
| `--retries N` | `5` | Number of retry attempts for network, fragments, and file operations. Must be zero or greater. |
| `--archive PATH` | Automatic | Use a specified yt-dlp download archive file. If omitted, the script creates a mode/format-specific archive in the output directory. See [Duplicate prevention](#11-duplicate-prevention-and-download-archives). |
| `--report PATH` | Automatic | Write the JSON run report to this path. If omitted, a timestamped report is created in the output directory. |
| `-v, --verbose` | Off | Enable more detailed diagnostic logs. Useful for troubleshooting. |
| `-h, --help` | — | Show help and exit. |

### Argument compatibility and validation

- `--playlist-items` requires `--playlist`.
- `--quality` is only meaningful with `--format mp3`. If using `--format best`, omit `--quality` or leave its default.
- `--mode video` cannot be combined with `--format mp3` or `--format m4a`; video mode selects video and audio streams and merges them instead.
- `--resolution` and `--video-container` are relevant to video mode.
- `--retries` must be zero or greater.

## 7. Audio download examples

### Best available audio stream

```bash
uv run youtube_downloader.py "VIDEO_URL"
```

This keeps the best available audio stream in its downloaded format when possible. It does not force MP3 conversion.

### Convert to MP3 at 320 kbps

```bash
uv run youtube_downloader.py "VIDEO_URL" --format mp3
```

### Convert to MP3 at 192 kbps

```bash
uv run youtube_downloader.py "VIDEO_URL" --format mp3 --quality 192
```

### Convert to best VBR MP3 quality

```bash
uv run youtube_downloader.py "VIDEO_URL" --format mp3 --quality 0
```

### Extract/convert to M4A

```bash
uv run youtube_downloader.py "VIDEO_URL" --format m4a
```

The `--quality` option does not set an M4A bitrate; it applies to MP3 only.

### Choose a different output directory

```bash
uv run youtube_downloader.py "VIDEO_URL" --format mp3 --output "$HOME/Music/YouTube-Audio"
```

## 8. Video download examples

### Best available video, no resolution cap

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution best
```

### Up to 720p / 1080p / 1440p

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 720
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 1080
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 1440
```

### Up to 4K (2160p), default MKV container

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 2160
```

### Up to 8K (4320p)

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 4320
```

8K downloads work only if a suitable source stream exists and can be accessed. They can require substantial bandwidth, disk space, and time.

### Use MP4 instead of MKV

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 2160 --video-container mp4
```

The selected streams are normally merged without re-encoding. Container compatibility depends on the codecs in the source streams; MP4 is not guaranteed to support every codec. If the merge fails or playback compatibility is poor, try the default MKV container.

### Save video to a separate folder

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 2160 --output "$HOME/Videos/YouTube"
```

## 9. Playlist downloads

The `--playlist` switch must be present to download playlist entries. Playlist files are placed in a folder named after the playlist, with an index prefix in each filename.

### Download all playlist entries as audio

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist
```

### Download all entries as MP3

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --format mp3
```

### Download only the first five entries

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --playlist-items 1-5
```

### Download entries 1, 3, and 7 as MP3

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --playlist-items 1,3,7 --format mp3
```

### Download a playlist as up-to-4K video

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --mode video --resolution 2160
```

### Notes on playlist selection

- Playlist item numbers refer to positions in the playlist, not YouTube video IDs.
- `--playlist-items` has no effect unless `--playlist` is also supplied; the script reports this as an argument error.
- Unavailable, private, deleted, age-restricted, or otherwise inaccessible entries may fail or be skipped depending on yt-dlp and the source. Check the summary and JSON report.

## 10. Output files, naming, and folders

### Filename behavior

The script uses yt-dlp's filename restrictions and includes the YouTube video ID in each filename. This helps make filenames more portable and avoids collisions when different videos share a title. For playlists, the playlist index is also included.

Examples of the general naming pattern:

```text
A_video_title_[VIDEO_ID].mp4
My_Playlist/
└── 001_A_video_title_[VIDEO_ID].mkv
```

Exact names and extensions depend on the title, playlist metadata, selected format, and yt-dlp's filename handling. Characters may be normalized or replaced to make names portable; do not rely on the original punctuation or emoji being retained.

### Temporary files

During a download or merge, yt-dlp/FFmpeg may create temporary files. Do not manually delete files while a download is active. If a run is interrupted, inspect the output directory after the process has stopped before removing leftover temporary files.

## 11. Duplicate prevention and download archives

The script maintains a yt-dlp archive so that media IDs already recorded as downloaded can be skipped on later runs. This is useful for resuming a playlist or rerunning a command without intentionally downloading every completed item again.

By default, archive files are separated by mode and settings. Common examples include:

```text
.download-archive-audio-best.txt
.download-archive-audio-mp3.txt
.download-archive-audio-m4a.txt
.download-archive-video-2160-mkv.txt
.download-archive-video-2160-mp4.txt
```

The exact archive filename is based on the selected mode, resolution, and container (for video) or audio format (for audio). If you change resolution or container, a different default video archive is used.

### Set a custom archive path

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --archive "$HOME/Music/youtube-audio-archive.txt"
```

**Caution:** An explicitly supplied archive is used as-is. Since archive entries identify media rather than encoding choices, do not share one custom archive between audio and video workflows if you expect to download both versions of the same video. Use separate archive files, for example `audio-archive.txt` and `video-archive.txt`.

If you want to intentionally download an item again, understand that the archive may skip it. You can specify a different archive path for a separate run. Avoid deleting archive entries unless you understand that this can cause media to be downloaded again.

## 12. JSON reports and logs

After each run, the script writes a JSON report. By default, the report is stored in the output directory with a timestamped name such as:

```text
download-report-video-20261021-134500.json
```

The report can include:

- Run timestamp in UTC.
- Source URL and output directory.
- Mode and format setting.
- Exit status.
- Counts of completed items and collected errors.
- Completed-item details such as video ID, title, source URL, output path, and status, when yt-dlp provides them.
- Error messages captured during the run.

### Choose a report path

```bash
uv run youtube_downloader.py "VIDEO_URL" --report "$HOME/Downloads/my-download-report.json"
```

### Enable verbose logs

```bash
uv run youtube_downloader.py "VIDEO_URL" --verbose
```

You can combine `--verbose` with other options. Reports are useful for diagnosing failures, but items skipped because they are already in the archive may not appear in the completed list.

## 13. How quality and formats work

### Audio

- `--format best`: downloads the best available audio stream without forcing MP3 conversion.
- `--format mp3`: uses FFmpeg to extract/convert audio to MP3. `--quality` controls the MP3 quality target.
- `--format m4a`: uses FFmpeg to extract/convert audio to M4A; the script requests best quality for this conversion.

Converting a lower-quality source to a higher bitrate does not restore missing audio detail. For most users, `320` is a high MP3 bitrate; `0` selects best VBR quality through FFmpeg.

### Video

- `--resolution 2160` means “choose the best available stream up to 2160 pixels high,” not “upscale to 4K.”
- `--resolution best` removes the script's explicit height cap.
- YouTube may provide video and audio as separate streams. FFmpeg merges them into the selected container.
- The script does not intentionally re-encode video to improve quality. The result is limited by the source stream and available formats.
- Higher resolutions generally need more bandwidth, storage, and processing time.

## 14. Troubleshooting

### `ffmpeg` or `ffprobe` not found

Install FFmpeg and verify it is on `PATH`:

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

### `uv: command not found`

Install `uv` using the steps in [Installation and setup](#3-installation-and-setup-on-ubuntu), then reopen the terminal. If it is already installed, check that its install directory is on `PATH`.

### `No module named yt_dlp`

From the project directory, run:

```bash
uv add yt-dlp
uv sync
```

Then use `uv run youtube_downloader.py ...` so the script runs in the project's managed environment.

### `--playlist-items requires --playlist`

Add `--playlist` to the command, for example:

```bash
uv run youtube_downloader.py "PLAYLIST_URL" --playlist --playlist-items 1-5
```

### `--quality applies only to MP3`

Use `--format mp3` when setting a quality value:

```bash
uv run youtube_downloader.py "VIDEO_URL" --format mp3 --quality 192
```

For best available audio without MP3 conversion, omit `--quality`.

### `--format mp3/m4a is for audio mode`

For video downloads, remove `--format mp3` or `--format m4a` and specify video mode:

```bash
uv run youtube_downloader.py "VIDEO_URL" --mode video --resolution 2160
```

### A requested resolution is not available

Check whether the source actually offers that resolution. Try a lower cap such as `--resolution 1080`, or use `--resolution best` to let yt-dlp choose the best available format. `best` does not guarantee a specific resolution.

### A download fails or is interrupted

Retry the command; the program already uses retry settings and attempts to continue partial downloads. You can increase the retry count:

```bash
uv run youtube_downloader.py "VIDEO_URL" --retries 10 --verbose
```

If an entry is unavailable, retrying may not fix it. Review the terminal error and the JSON report.

### `No supported JavaScript runtime could be found` warning

yt-dlp may warn that a supported JavaScript runtime is unavailable. Depending on YouTube changes and the video, this can reduce extraction reliability or format availability. Check the current yt-dlp installation guidance for supported JavaScript runtimes and install/configure one if needed. Update yt-dlp before investigating further.

### File already exists / temporary-file collision

- Let the current download finish before starting another process against the same output directory.
- The script includes video IDs in filenames and disables overwriting, which reduces name collisions.
- If a previous run was interrupted, stop all downloader processes and inspect the directory for stale temporary files before cleaning anything up.
- Do not delete the download archive just to fix a temporary-file error; the archive and temporary files serve different purposes.

### A video is skipped as already downloaded

The archive may already contain its ID. Use a different archive path for a separate run, or inspect the archive if you need to understand why it is being skipped. Be aware that changing the archive can cause already-downloaded items to be fetched again.

### Get more diagnostic information

Add `--verbose` and save the output if you need to investigate:

```bash
uv run youtube_downloader.py "VIDEO_URL" --verbose
```

## 15. Updating the tool

From the project directory, update the yt-dlp dependency:

```bash
cd ~/Music/youtube-downloader
uv lock --upgrade-package yt-dlp
uv sync
```

Check the installed version:

```bash
uv run yt-dlp --version
```

The standalone `yt-dlp` command is useful for checking the dependency version; normal downloads should still be run through the Python script.

## 16. Typical workflows

### A. Download a playlist as MP3 and keep a JSON report

```bash
uv run youtube_downloader.py "PLAYLIST_URL" \
  --playlist \
  --format mp3 \
  --quality 320 \
  --output "$HOME/Music/YouTube-Audio" \
  --report "$HOME/Music/YouTube-Audio/report.json"
```

### B. Download a playlist in up-to-4K MKV

```bash
uv run youtube_downloader.py "PLAYLIST_URL" \
  --playlist \
  --mode video \
  --resolution 2160 \
  --video-container mkv \
  --output "$HOME/Videos/YouTube"
```

### C. Download only selected playlist entries with more retries

```bash
uv run youtube_downloader.py "PLAYLIST_URL" \
  --playlist \
  --playlist-items 1-5 \
  --retries 10 \
  --verbose
```

### D. See all options

```bash
uv run youtube_downloader.py --help
```

---

## Quick reference

| Goal | Command options |
|---|---|
| Best audio | *(no mode/format options)* |
| MP3 | `--format mp3` |
| MP3 at 192 kbps | `--format mp3 --quality 192` |
| M4A | `--format m4a` |
| Video up to 1080p | `--mode video --resolution 1080` |
| Video up to 4K | `--mode video --resolution 2160` |
| Video up to 8K | `--mode video --resolution 4320` |
| Best available video | `--mode video --resolution best` |
| MP4 container | `--mode video --video-container mp4` |
| Playlist | `--playlist` |
| First five playlist entries | `--playlist --playlist-items 1-5` |
| Custom destination | `--output "/path/to/folder"` |
| More retries and diagnostics | `--retries 10 --verbose` |

*End of manual.*
