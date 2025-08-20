import yt_dlp
import logging
import uuid
import os
import shutil
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "temp_dir": "temp/downloads",
    "yt_dlp_options": {
        'format': 'best',
        'postprocessors': [],
        'windowsfilenames': True,
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'concurrent_fragment_downloads': 10,
        'external_downloader': 'aria2c',
        'external_downloader_args': {
            'default': ['-x', '16', '-s', '16', '-k', '1M']
        },
        'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
    }
}

class Downloader:
    def __init__(self, url: str, format: str, settings: Optional[Dict[str, Any]] = None, is_url_stream: bool = False):
        self.url = url
        self.format = format
        self.is_url_stream = is_url_stream
        self.loop = None
        self.session_id = str(uuid.uuid4())
        
        # Merge user settings with defaults
        self.settings = DEFAULT_SETTINGS.copy()
        if settings:
            self._deep_update(self.settings, settings)
        
        self.TEMP_DIR = self.settings["temp_dir"]
        self.temp_dir = self._create_temp_directory()
        self.downloaded_filepath = None
        self.stream_url = None
        self._download_task = None
        # Initialize base options from settings
        self.base_yt_dlp_opts = self.settings["yt_dlp_options"].copy()
        # Always set output template based on temp_dir
        self.base_yt_dlp_opts['outtmpl'] = os.path.join(self.temp_dir, "%(title)s.%(ext)s")

    def _deep_update(self, target_dict: dict, update_dict: dict) -> None:
        """Recursively update a dictionary with another dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in target_dict and isinstance(target_dict[key], dict):
                self._deep_update(target_dict[key], value)
            else:
                target_dict[key] = value

    async def __aenter__(self):
        self.loop = asyncio.get_event_loop()
        self._download_task = self.loop.run_in_executor(None, self._download)
        result = await self._download_task
        if self.is_url_stream:
            self.stream_url = result
        else:
            self.downloaded_filepath = result
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def _create_temp_directory(self):
        temp_dir = os.path.join(os.getcwd(), self.TEMP_DIR, self.session_id)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _cleanup(self):
        """Remove temporary files and directories."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}")

    def cancel_download(self):
        """Cancel the download process."""
        try:
            if self._download_task and not self._download_task.done():
                self._download_task.cancel()
                logger.debug("Download task cancelled")
        except Exception as e:
            logger.warning(f"Error cancelling download: {e}")
        
        # Limpar imediatamente
        self._cleanup()

    def _resolve_format(self, format: str):
        match format:
            case "mp4":
                # Try H.264, fallback to bestvideo+bestaudio/best
                fmt = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mp4"}]
            case "mp3":
                fmt = "bestaudio/best"
                post = [{'key': 'FFmpegExtractAudio', 'preferredcodec': "mp3", 'preferredquality': '0'}]
            case "mkv":
                fmt = "bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mkv"}]
            case "webm":
                # Try VP9, fallback to bestvideo+bestaudio/best
                fmt = "bestvideo[ext=webm][vcodec=vp9]+bestaudio[ext=webm]/bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "webm"}]
            case "ogg":
                fmt = "bestaudio/best"
                post = [{'key': 'FFmpegExtractAudio', 'preferredcodec': "vorbis", 'preferredquality': '0'}]
            case _:
                logger.error("error: Invalid format specified.")
                raise ValueError("Invalid format specified.")
        return fmt, post

    def _download(self):
        """Download or get stream URL depending on is_url_stream."""
        try:
            fmt, post = self._resolve_format(self.format)
            opts = self.base_yt_dlp_opts.copy()
            opts.update({'format': fmt, 'postprocessors': post})
            logger.debug(f"Downloading with format: {fmt}, postprocessors: {post}")
            logger.debug(f"Temp directory: {self.temp_dir}")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=not self.is_url_stream)
                if self.is_url_stream:
                    url_stream = info.get('url', None)
                    logger.debug(f"Stream URL: {url_stream}")
                    return url_stream
                else:
                    template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
                    filename = ydl.prepare_filename(info, outtmpl=template)
                    logger.debug(f"Expected filename: {filename}")
        except Exception as e:
            logger.warning(f"First download attempt failed: {e}")
            try:
                opts = self.base_yt_dlp_opts.copy()
                opts.update({'format': 'best', 'postprocessors': []})
                logger.debug("Retrying with 'best' format")
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(self.url, download=not self.is_url_stream)
                    if self.is_url_stream:
                        url_stream = info.get('url', None)
                        logger.debug(f"Stream URL: {url_stream}")
                        return url_stream
                    else:
                        template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
                        filename = ydl.prepare_filename(info, outtmpl=template)
                        logger.debug(f"Expected filename: {filename}")
            except Exception as error:
                logger.error(f"Download failed completely: {error}")
                raise error
        if self.is_url_stream:
            return None
        downloaded_file = self._resolve_downloaded_file()
        logger.debug(f"Final resolved filepath: {downloaded_file}")
        return downloaded_file

    def _resolve_downloaded_file(self):
        """Resolve the actual downloaded file from the temp directory"""
        try:
            logger.debug(f"Resolving downloaded file from: {self.temp_dir}")
            
            # Listar todos os arquivos no diretório temporário
            if not os.path.exists(self.temp_dir):
                logger.error(f"Temp directory does not exist: {self.temp_dir}")
                return None
                
            all_files = os.listdir(self.temp_dir)
            logger.debug(f"All items in temp dir: {all_files}")
            
            # Filtrar apenas arquivos (não diretórios)
            files = []
            for item in all_files:
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isfile(item_path):
                    files.append(item_path)
            
            logger.debug(f"Files found: {files}")
            
            if not files:
                logger.error(f"No files found in temp directory: {self.temp_dir}")
                return None
            
            # Primeiro, tentar encontrar arquivos com a extensão esperada
            format_files = [f for f in files if f.lower().endswith(f'.{self.format.lower()}')]
            logger.debug(f"Files with format {self.format}: {format_files}")
            
            if format_files:
                # Ordenar por data de modificação (mais recente primeiro)
                format_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                selected_file = format_files[0]
                logger.debug("Selected file with expected format: {selected_file}")
                return selected_file
            
            # Se não encontrar com a extensão esperada, usar o arquivo mais recente
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            selected_file = files[0]
            logger.debug(f"Selected most recent file: {selected_file}")
            return selected_file
            
        except Exception as e:
            logger.error(f"Error resolving downloaded file: {e}")
            return None

    def get_filepath(self):
        """Returns the downloaded file path."""
        return self.downloaded_filepath

    def _get_temp_dir_abspath(self):
        """Returns the absolute path of the temporary directory."""
        return os.path.abspath(self.temp_dir)

    def get_stream_url(self):
        """Returns the stream URL if is_url_stream is True."""
        return self.stream_url