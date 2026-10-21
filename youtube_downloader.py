#!/usr/bin/env python3
"""
YouTube Audio Downloader — enhanced edition

Features
- ASCII-only filenames for track titles and playlist folders; spaces/symbols become underscores
- Audio downloads: best source, MP3, or M4A
- Video downloads: best available video + audio, merged with FFmpeg
- Video resolution caps up to 8K (4320p), subject to source availability
- Video container selection (MKV or MP4)
- Video and playlist support, including selected playlist entries
- Duplicate detection using yt-dlp's download archive
- Retry/backoff settings
- Per-run JSON summary report
- Progress display and error collection

Use only for content you own, have permission to download, or are otherwise
allowed to download under applicable terms. This tool does not bypass DRM or
access controls.

Requirements:
    Python 3.10+
    python -m pip install --upgrade yt-dlp
    FFmpeg installed and available on PATH for audio conversion and video merging
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError

LOGGER = logging.getLogger("youtube_audio_downloader")


class RunTracker:
    """Collect per-run download, skip, and error information."""

    def __init__(self) -> None:
        self.completed: dict[str, dict[str, Any]] = {}
        self.errors: list[str] = []
        self.skipped: dict[str, dict[str, Any]] = {}
        self.current_titles: dict[str, str] = {}

    @staticmethod
    def video_key(info: dict[str, Any]) -> str:
        return str(info.get("id") or info.get("webpage_url") or info.get("title") or "unknown")

    def progress_hook(self, data: dict[str, Any]) -> None:
        status = data.get("status")
        info = data.get("info_dict") or {}
        key = self.video_key(info)
        title = str(info.get("title") or data.get("filename") or key)
        self.current_titles[key] = title

        if status == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            if total:
                percent = min(100.0, downloaded * 100 / total)
                speed = data.get("speed")
                speed_text = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "speed n/a"
                print(f"\rDownloading {title[:55]}: {percent:5.1f}% | {speed_text}", end="", flush=True)
        elif status == "finished":
            print(f"\nDownloaded stream: {title}")

    def postprocessor_hook(self, data: dict[str, Any]) -> None:
        if data.get("status") != "finished":
            return
        info = data.get("info_dict") or {}
        key = self.video_key(info)
        self.completed[key] = {
            "id": info.get("id"),
            "title": info.get("title"),
            "url": info.get("webpage_url"),
            "output": info.get("filepath") or info.get("_filename"),
            "status": "completed",
        }

    # yt-dlp's logger interface uses these exact method names.
    def error(self, message: str) -> None:
        self.errors.append(message)
        LOGGER.error(message)

    def warning(self, message: str) -> None:
        LOGGER.warning(message)

    def debug(self, message: str) -> None:
        LOGGER.debug(message)

    def info(self, message: str) -> None:
        LOGGER.info(message)


def sanitize_filename(title: str, max_length: int = 180, fallback: str = "audio") -> str:
    """Return an ASCII-only filename component with underscores as separators.

    Emojis and non-ASCII characters are removed. Runs of punctuation or
    whitespace become one underscore. The caller should keep the file extension
    separate and should provide an ID-based fallback when titles are empty.
    """
    import unicodedata

    normalized = unicodedata.normalize("NFKD", str(title))
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", ascii_title)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    cleaned = cleaned[:max_length].rstrip("_")
    return cleaned or fallback


def build_options(args: argparse.Namespace, tracker: RunTracker) -> dict[str, Any]:
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.playlist:
        output_template = str(
            output_dir
            / "%(playlist_title|Playlist)s"
            / "%(playlist_index|0)03d_%(title)s_[%(id)s].%(ext)s"
        )
    else:
        output_template = str(output_dir / "%(title)s_[%(id)s].%(ext)s")

    if args.mode == "video":
        if args.resolution == "best":
            video_format = "bestvideo+bestaudio/best"
        else:
            video_format = (
                f"bestvideo[height<={args.resolution}]+bestaudio/"
                f"best[height<={args.resolution}]"
            )
        selected_format = video_format
    else:
        selected_format = "bestaudio/best"

    # Keep audio and video archive entries separate, otherwise downloading
    # audio first could make a later video request look already completed.
    archive_key = (
        f"video-{args.resolution}-{args.video_container}"
        if args.mode == "video"
        else f"audio-{args.format}"
    )
    archive_path = (
        Path(args.archive).expanduser()
        if args.archive
        else output_dir / f".download-archive-{archive_key}.txt"
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    options: dict[str, Any] = {
        "format": selected_format,
        "outtmpl": output_template,
        "noplaylist": not args.playlist,
        "ignoreerrors": True,
        "continuedl": True,
        "retries": args.retries,
        "fragment_retries": args.retries,
        "file_access_retries": args.retries,
        "retry_sleep": {
            "http": "linear=1::5",
            "fragment": "linear=1::5",
            "file_access": "linear=1::5",
        },
        "download_archive": str(archive_path),
        "overwrites": False,
        "windowsfilenames": True,
        "trim_file_name": 180,
        # Use yt-dlp's native portable filename sanitization: ASCII-safe
        # names with spaces/special characters normalized for filenames.
        "restrictfilenames": True,
        "post_hooks": [],
        "progress_hooks": [tracker.progress_hook],
        "postprocessor_hooks": [tracker.postprocessor_hook],
        "logger": tracker,
        "quiet": True,
        "no_warnings": False,
        "socket_timeout": 30,
    }

    if args.playlist_items:
        options["playlist_items"] = args.playlist_items

    if args.mode == "video":
        # MKV is the safest default for retaining the selected video/audio
        # codecs without re-encoding. MP4 is available for wider compatibility.
        options["merge_output_format"] = args.video_container
    elif args.format in ("mp3", "m4a"):
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": args.format,
                "preferredquality": args.quality if args.format == "mp3" else "0",
            },
            {"key": "FFmpegMetadata"},
        ]

    return options


def write_report(
    report_path: Path,
    url: str,
    output_dir: Path,
    format_name: str,
    tracker: RunTracker,
    exit_status: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "started_or_finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": url,
        "output_directory": str(output_dir.resolve()),
        "format": format_name,
        "mode": getattr(tracker, "mode", "audio"),
        "exit_status": exit_status,
        "completed_count": len(tracker.completed),
        "error_count": len(tracker.errors),
        "completed": list(tracker.completed.values()),
        "errors": tracker.errors,
        "note": (
            "The archive prevents re-downloading IDs already recorded as successful. "
            "Items skipped because they are already in the archive may not appear in completed. "
            "Output filenames include video IDs to prevent title collisions."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download audio or high-quality video from a YouTube video or playlist.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument(
        "--mode", choices=("audio", "video"), default="audio",
        help="Download audio only or video with audio",
    )
    parser.add_argument(
        "--resolution",
        choices=("best", "720", "1080", "1440", "2160", "4320"),
        default="2160",
        help="Maximum video height in pixels; video mode only",
    )
    parser.add_argument(
        "--video-container", choices=("mkv", "mp4"), default="mkv",
        help="Container for merged video downloads; video mode only",
    )
    parser.add_argument("-f", "--format", choices=("best", "mp3", "m4a"), default="best")
    parser.add_argument(
        "-q", "--quality", choices=("128", "192", "256", "320", "0"), default="320",
        help="MP3 bitrate in kbps; 0 selects best VBR quality",
    )
    parser.add_argument("-o", "--output", default="downloads", help="Output directory")
    parser.add_argument("-p", "--playlist", action="store_true", help="Enable playlist downloading")
    parser.add_argument("--playlist-items", help="Selection such as 1-5 or 1,3,7")
    parser.add_argument("--retries", type=int, default=5, help="Retry count for network/file operations")
    parser.add_argument("--archive", help="Path to download archive; defaults to OUTPUT/.download-archive.txt")
    parser.add_argument("--report", help="JSON report path; defaults to OUTPUT/download-report-<timestamp>.json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed diagnostic logs")

    args = parser.parse_args()
    if args.playlist_items and not args.playlist:
        parser.error("--playlist-items requires --playlist")
    if args.retries < 0:
        parser.error("--retries must be zero or greater")
    if args.format == "best" and args.quality != "320":
        parser.error("--quality applies only to MP3; use --format mp3 or omit --quality")
    if args.mode == "video" and args.format != "best":
        parser.error("--format mp3/m4a is for audio mode; use --mode audio for audio extraction")
    return args


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    output_dir = Path(args.output).expanduser().resolve()
    report_path = (
        Path(args.report).expanduser()
        if args.report
        else output_dir / f"download-report-{args.mode}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    tracker = RunTracker()
    tracker.mode = args.mode
    exit_status = 1

    try:
        options = build_options(args, tracker)
        with yt_dlp.YoutubeDL(options) as downloader:
            result = downloader.download([args.url])
        # yt-dlp may return non-zero if one or more entries fail.
        exit_status = 0 if result == 0 and not tracker.errors else 1
    except DownloadError as exc:
        tracker.errors.append(str(exc))
        LOGGER.error("Download failed: %s", exc)
    except KeyboardInterrupt:
        tracker.errors.append("Interrupted by user.")
        LOGGER.warning("Interrupted by user.")
    except OSError as exc:
        tracker.errors.append(str(exc))
        LOGGER.error("File system error: %s", exc)
    except Exception as exc:
        tracker.errors.append(f"{type(exc).__name__}: {exc}")
        LOGGER.exception("Unexpected error")
    finally:
        try:
            write_report(report_path, args.url, output_dir, args.format, tracker, exit_status)
            print("\n--- Download summary ---")
            print(f"Completed: {len(tracker.completed)}")
            print(f"Errors:    {len(tracker.errors)}")
            print(f"Report:    {report_path}")
            print(f"Output:    {output_dir}")
            if tracker.errors:
                print("\nErrors:")
                for error in tracker.errors:
                    print(f"  - {error}")
        except OSError as exc:
            LOGGER.error("Could not write report: %s", exc)
            exit_status = 1

    return exit_status


if __name__ == "__main__":
    sys.exit(main())
