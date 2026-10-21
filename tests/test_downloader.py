"""Offline tests for the CLI and option construction."""
from __future__ import annotations

import argparse
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Keep these unit tests runnable without network access or an installed yt-dlp.
# The real package is used automatically when it is installed.
try:
    import yt_dlp  # noqa: F401
except ModuleNotFoundError:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_utils = types.ModuleType("yt_dlp.utils")

    class DownloadError(Exception):
        pass

    fake_utils.DownloadError = DownloadError
    fake_yt_dlp.utils = fake_utils
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp
    sys.modules["yt_dlp.utils"] = fake_utils

import youtube_downloader as app  # noqa: E402


class DownloaderTests(unittest.TestCase):
    def parse(self, *argv: str) -> argparse.Namespace:
        with patch.object(sys, "argv", ["youtube_downloader.py", *argv]):
            return app.parse_args()

    def test_default_arguments(self) -> None:
        args = self.parse("https://www.youtube.com/watch?v=example")
        self.assertEqual(args.mode, "audio")
        self.assertEqual(args.format, "best")
        self.assertEqual(args.resolution, "2160")
        self.assertEqual(args.video_container, "mkv")
        self.assertEqual(args.output, "downloads")
        self.assertEqual(args.retries, 5)

    def test_playlist_items_requires_playlist(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self.parse("https://www.youtube.com/playlist?list=example", "--playlist-items", "1-5")
        self.assertEqual(exc.exception.code, 2)

    def test_negative_retries_rejected(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self.parse("https://www.youtube.com/watch?v=example", "--retries", "-1")
        self.assertEqual(exc.exception.code, 2)

    def test_mp3_quality_requires_mp3_format(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self.parse("https://www.youtube.com/watch?v=example", "--quality", "192")
        self.assertEqual(exc.exception.code, 2)

    def test_video_mode_rejects_audio_conversion(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self.parse("https://www.youtube.com/watch?v=example", "--mode", "video", "--format", "mp3")
        self.assertEqual(exc.exception.code, 2)

    def test_video_options_and_output_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            args = argparse.Namespace(
                output=temp_dir, playlist=True, mode="video", resolution="2160",
                video_container="mkv", format="best", quality="320", retries=3,
                archive=None, playlist_items="1-2",
            )
            options = app.build_options(args, app.RunTracker())
            self.assertIn("bestvideo[height<=2160]+bestaudio", options["format"])
            self.assertEqual(options["merge_output_format"], "mkv")
            self.assertEqual(options["playlist_items"], "1-2")
            self.assertFalse(options["noplaylist"])
            self.assertTrue(options["restrictfilenames"])
            self.assertIn("%(playlist_title|Playlist)s", options["outtmpl"])
            self.assertEqual(Path(options["download_archive"]).name, ".download-archive-video-2160-mkv.txt")

    def test_audio_archive_is_format_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            args = argparse.Namespace(
                output=temp_dir, playlist=False, mode="audio", resolution="2160",
                video_container="mkv", format="mp3", quality="192", retries=1,
                archive=None, playlist_items=None,
            )
            options = app.build_options(args, app.RunTracker())
            self.assertEqual(options["format"], "bestaudio/best")
            self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")
            self.assertEqual(Path(options["download_archive"]).name, ".download-archive-audio-mp3.txt")


if __name__ == "__main__":
    unittest.main()
