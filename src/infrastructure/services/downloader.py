import time
import validators
import yt_dlp
import logging
import uuid
import shutil
import asyncio
import json
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.domain.interfaces.dto.output.download_output import DownloadOutput

logger = logging.getLogger(__name__)

DEFAULT_YT_DLP_SETTINGS = {
    'format': 'best',
    'postprocessors': [],
    'restrictfilenames': True,
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'concurrent_fragment_downloads': 10,
    'continue_dl': True,
    'external_downloader': 'aria2c',
    'external_downloader_args': {'default': ['-x', '16', '-s', '16', '-k', '1M']},
    'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
}

class Downloader:
    """
    Downloader class to handle video/audio downloads using yt_dlp.

    Attributes:
        url (str): The URL of the media to download.
        format (str): Desired output format (e.g., 'mp4', 'mp3').
        quality (str, optional): Desired quality (e.g., '720p', 'best').
    """

    FORMAT_MAP = {
            "mp4": {
                "format": "bestvideo{video_quality}[ext=mp4][vcodec^=avc1]+bestaudio{audio_quality}[ext=m4a]/bestvideo+bestaudio/best",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mp4"}],
                "is_audio": False
            },
            "mp3": {
                "format": "bestaudio{audio_quality}/best",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "mp3", 'preferredquality': '0'}],
                "is_audio": True
            },
            "mkv": {
                "format": "bestvideo{video_quality}+bestaudio{audio_quality}/best",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mkv"}],
                "is_audio": False
            },
            "webm": {
                "format": "bestvideo{video_quality}[ext=webm][vcodec=vp9]+bestaudio{audio_quality}[ext=webm]/bestvideo+bestaudio/best",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "webm"}],
                "is_audio": False
            },
            "ogg": {
                "format": "bestaudio{audio_quality}/best",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "vorbis", 'preferredquality': '0'}],
                "is_audio": True
            }
    }
    
    def __init__(self, url: str, format: str, quality: Optional[str] = None):
        """Initialize downloader with URL, format, and optional quality."""
        self.url = url
        self.format = format.lower()
        self.quality = quality
        self.is_audio = False
        self.session_id = str(uuid.uuid4())
        self.temp_dir = self._create_temp_directory("temp/downloads")
        self.downloaded_filepath: Optional[Path] = None
        self._download_task: Optional[asyncio.Future] = None
        self.start_time: Optional[float] = None
        self.result: Optional[DownloadOutput] = None

        self.yt_dlp_opts = DEFAULT_YT_DLP_SETTINGS.copy()
        self.yt_dlp_opts['outtmpl'] = str(Path(self.temp_dir) / "%(title)s.%(ext)s")

    async def __aenter__(self):
        """Async context manager entry: starts the download task."""
        loop = asyncio.get_running_loop()
        self._download_task = loop.run_in_executor(None, self._download)
        self.downloaded_filepath = await self._download_task
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: placeholder (cleanup handled elsewhere)."""
        pass

    async def get_response(self) -> DownloadOutput:
        """
        Get the download result wrapped in a DownloadOutput object.

        Returns:
            DownloadOutput: Contains file path, elapsed time, and cleanup callback.
        """
        elapsed = (time.time() - self.start_time) if self.start_time else None
        if not self.result:
            self.result = DownloadOutput(
                file_path=self.downloaded_filepath,
                elapsed=elapsed,
                is_audio=self.is_audio,
                cleanup=self._cleanup,
                cleanup_speed_included=False,
                frame_rate=self._resolve_frame_rate(self.downloaded_filepath),
                resolution=self._resolve_resolution(self.downloaded_filepath),
            )
        return self.result

    def _resolve_resolution(self, filepath: Path) -> Optional[str]:
        """
        Retrieve the video resolution from the given file using ffprobe.

        Args:
            filepath (Path): Path to the media file.

        Returns:
            Optional[str]: Resolution in the format "widthxheight" (e.g., "1920x1080"),
                        or None if unavailable.
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json",
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            if not info.get("streams"):
                return None

            stream = info["streams"][0]
            width = stream.get("width")
            height = stream.get("height")
            return f"{width}x{height}" if width and height else None

        except Exception as e:
            logger.warning(f"Failed to resolve resolution for {filepath}: {e}")
            return None


    def _resolve_frame_rate(self, filepath: Path) -> Optional[float]:
        """
        Retrieve the frame rate (fps) from the given file using ffprobe.

        Args:
            filepath (Path): Path to the media file.

        Returns:
            Optional[float]: Frame rate as a float (rounded to 2 decimals),
                            or None if unavailable.
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "json",
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            if not info.get("streams"):
                return None

            stream = info["streams"][0]
            fr = stream.get("r_frame_rate")
            if fr and fr != "0/0":
                num, den = map(int, fr.split("/"))
                return round(num / den, 2)

            return None

        except Exception as e:
            logger.warning(f"Failed to resolve frame rate for {filepath}: {e}")
            return None

    def _create_temp_directory(self, base_dir: str) -> Path:
        """
        Create a temporary directory for downloads.

        Args:
            base_dir (str): Base directory path.

        Returns:
            Path: Full path to the temporary directory.
        """
        temp_path = Path(base_dir).absolute() / self.session_id
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path

    def _cleanup(self):
        """Remove the temporary download directory."""
        try:
            temp_path = Path(self.temp_dir)
            if temp_path.exists():
                shutil.rmtree(temp_path, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}")

    def cancel_download(self):
        """Cancel the ongoing download task and clean up temporary files."""
        if self._download_task and not self._download_task.done():
            self._download_task.cancel()
            logger.debug("Download task cancelled")
        self._cleanup()

    def _resolve_format(self, ytdl_format: str) -> tuple[str, List[Dict[str, Any]]]:
        """
        Resolve yt_dlp format string and postprocessors based on requested format and quality.

        Args:
            ytdl_format (str): Desired output format.

        Returns:
            tuple: (yt_dlp format string, postprocessors list)
        """
        video_quality, audio_quality = ("", "")
        if self.quality:
            video_quality, audio_quality = self.quality.split("_")

        if ytdl_format not in self.FORMAT_MAP:
            raise ValueError("Invalid format specified.")

        fmt_template = self.FORMAT_MAP[ytdl_format]["format"]
        postprocessors = self.FORMAT_MAP[ytdl_format]["post"]
        self.is_audio = self.FORMAT_MAP[ytdl_format]["is_audio"]

        fmt = fmt_template.format(video_quality=video_quality, audio_quality=audio_quality)
        return fmt, postprocessors

    def _download(self) -> Optional[Path]:
        """
        Start the download process with fallback to 'best' format if the requested format fails.

        Returns:
            Optional[Path]: Path to the downloaded file, or None if not found.
        """
        self.start_time = time.time() 

        if not validators.url(self.url):
            self.url = f"ytsearch:{self.url}"
        try:
            return self._attempt_download(self.format)
        except Exception as e:
            logger.warning(f"Download failed ({self.format}): {e}")
            try:
                return self._attempt_download('best', postprocessors=[])
            except Exception as err:
                logger.error(f"Download failed completely: {err}")
                return None

    def _attempt_download(self, format: str, postprocessors: Optional[List[Dict[str, Any]]] = None) -> Optional[Path]:
        """
        Attempt to download using the specified format and postprocessors.

        Args:
            format (str): Desired format.
            postprocessors (list, optional): List of yt_dlp postprocessors.

        Returns:
            Optional[Path]: Path to the downloaded file.
        """
        ytdl_format, default_post = self._resolve_format(format)
        postprocessors = postprocessors or default_post

        opts = self.yt_dlp_opts.copy()
        opts.update({'format': ytdl_format, 'postprocessors': postprocessors})

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(self.url, download=True)
            if "entries" in info:
                info = info["entries"][0]

        return self._resolve_downloaded_file()

    def _resolve_downloaded_file(self) -> Optional[Path]:
        """
        Determine the actual downloaded file from the temporary directory.

        Returns:
            Optional[Path]: Path to the downloaded file, or None if not found.
        """
        temp_path = Path(self.temp_dir)
        if not temp_path.exists():
            logger.error(f"Temp directory does not exist: {temp_path}")
            return None

        files = [f for f in temp_path.iterdir() if f.is_file()]
        if not files:
            logger.error(f"No files found in temp directory: {temp_path}")
            return None

        format_files = [f for f in files if f.suffix.lower() == f".{self.format}"]
        selected_file = max(format_files or files, key=lambda f: f.stat().st_mtime)
        return selected_file