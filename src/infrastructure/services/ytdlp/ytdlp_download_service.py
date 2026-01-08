import yt_dlp
import asyncio
import logging
from typing import Optional
from pathlib import Path
from logging import Logger
from typing import Any, Dict
from src.core.constants import DEFAULT_YT_DLP_SETTINGS
from src.infrastructure.services.ytdlp import YtdlpFormatMapper
from src.domain.enum.formats import Formats

class YtdlpDownloadService():
    """Service for downloading files using yt-dlp."""

    def __init__(self, ytdlp_format_mapper: YtdlpFormatMapper, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.ytdlp_format_mapper = ytdlp_format_mapper
        self.logger.info("YtdlpDownloadService initialized")

    def _get_ydl_opts(self, format_value: Formats | None, output_folder: Path) -> Dict[str, Any]:
        """
        Get yt-dlp options for downloading.
        
        Args:
            output_folder: Folder where the file will be downloaded
            
        Returns:
            Dictionary with yt-dlp options
        """
        format_options = self.ytdlp_format_mapper.map_format(format_value)

        if 'post' in format_options:
            format_options['postprocessors'] = format_options.pop('post')
        
        if 'is_audio' in format_options:
            format_options.pop('is_audio')

        return {
            'outtmpl': str(output_folder / '%(title)s.%(ext)s'),
            **DEFAULT_YT_DLP_SETTINGS,
            'logger': self.logger,
            **format_options,
        }

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        Hook to log download progress.
        
        Args:
            d: Dictionary containing progress information
        """
        ...

    async def download(self, url: str, format_value: Formats | None, output_folder: Path) -> Path:
        """
        Download file from URL using yt-dlp.
        
        Args:
            url: URL to download from
            format_value: Format to download in
            output_folder: Folder where the file will be saved
            
        Returns:
            Path to the downloaded file
            
        Raises:
            Exception: If download fails
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._download_sync, url, format_value, output_folder)
    
    def _download_sync(self, url: str, format_value: Formats | None, output_folder: Path) -> Path:
        self.logger.info(f"Starting download from: {url}")
        
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created output folder: {output_folder}")

        ydl_opts = self._get_ydl_opts(format_value, output_folder)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
               
                info = ydl.extract_info(url, download=True)
                
                if info is None:
                    raise ValueError("Failed to extract video information")
                
                if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                    filename = info['requested_downloads'][0].get('filepath')
                    if filename:
                        file_path = Path(filename)
                        if file_path.exists():
                            self.logger.info(f"Successfully downloaded file to: {file_path}")
                            return file_path
                
                if not file_path.exists():
                    raise FileNotFoundError(f"Downloaded file not found at: {file_path}")
                
                self.logger.info(f"Successfully downloaded file to: {file_path}")
                return file_path
                
        except yt_dlp.DownloadError as error:
            self.logger.error(f"yt-dlp download error: {error}", exc_info=True)
            raise Exception(f"Failed to download from {url}: {error}") from error
            
        except Exception as error:
            self.logger.error(f"Unexpected error during download: {error}", exc_info=True)
            raise