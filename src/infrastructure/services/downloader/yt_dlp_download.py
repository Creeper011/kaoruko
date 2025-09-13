import time
import validators
import yt_dlp
import logging
import uuid
import shutil
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.domain.exceptions import (
    DownloadFailed,
    MediaFilepathNotFound,
    UnsupportedFormat,
    NetworkError
)

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

class YtDlpDownloader:
    """
    Basic downloader class that handles video/audio downloads using yt_dlp.
    Returns primitive data only - no metadata extraction or complex processing.
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

    def get_file_path(self) -> Optional[Path]:
        """Get the downloaded file path."""
        return self.downloaded_filepath

    def get_elapsed_time(self) -> Optional[float]:
        """Get the elapsed download time."""
        return (time.time() - self.start_time) if self.start_time else None

    def get_is_audio(self) -> bool:
        """Get whether the downloaded file is audio."""
        return self.is_audio

    def cleanup(self):
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
        self.cleanup()

    def _create_temp_directory(self, base_dir: str) -> Path:
        """Create a temporary directory for downloads."""
        temp_path = Path(base_dir).absolute() / self.session_id
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path

    def _resolve_format(self, ytdl_format: str) -> tuple[str, List[Dict[str, Any]]]:
        """Resolve yt_dlp format string and postprocessors based on requested format and quality."""
        video_quality, audio_quality = ("", "")
        if self.quality:
            video_quality, audio_quality = self.quality.split("_")

        if ytdl_format not in self.FORMAT_MAP:
            raise UnsupportedFormat(f"Invalid format specified: {ytdl_format}")

        fmt_template = self.FORMAT_MAP[ytdl_format]["format"]
        postprocessors = self.FORMAT_MAP[ytdl_format]["post"]
        self.is_audio = self.FORMAT_MAP[ytdl_format]["is_audio"]

        fmt = fmt_template.format(video_quality=video_quality, audio_quality=audio_quality)
        return fmt, postprocessors

    def _download(self) -> Optional[Path]:
        """Start the download process with fallback to 'best' format if the requested format fails."""
        self.start_time = time.time() 

        try:
            return self._attempt_download(self.format)
        except yt_dlp.DownloadError as e:
            logger.warning(f"Download failed ({self.format}): {e}")
            # Convert yt-dlp specific error to domain exception
            raise DownloadFailed(str(e)) from e
        except Exception as e:
            logger.warning(f"Download failed ({self.format}): {e}")
            try:
                return self._attempt_download('best', postprocessors=[])
            except yt_dlp.DownloadError as err:
                logger.error(f"Download failed completely: {err}")
                raise DownloadFailed(str(err)) from err
            except Exception as err:
                logger.error(f"Download failed completely: {err}")
                raise DownloadFailed(str(err)) from err

    def _attempt_download(self, format: str, postprocessors: Optional[List[Dict[str, Any]]] = None) -> Optional[Path]:
        """Attempt to download using the specified format and postprocessors."""
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
        """Determine the actual downloaded file from the temporary directory."""
        temp_path = Path(self.temp_dir)
        if not temp_path.exists():
            logger.error(f"Temp directory does not exist: {temp_path}")
            raise MediaFilepathNotFound(f"Temp directory does not exist: {temp_path}")

        files = [f for f in temp_path.iterdir() if f.is_file()]
        if not files:
            logger.error(f"No files found in temp directory: {temp_path}")
            raise MediaFilepathNotFound(f"No files found in temp directory: {temp_path}")

        format_files = [f for f in files if f.suffix.lower() == f".{self.format}"]
        selected_file = max(format_files or files, key=lambda f: f.stat().st_mtime)
        return selected_file