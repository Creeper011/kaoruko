import logging
import os
from typing import Optional
from pathlib import Path

from src.domain.interfaces.dto.output.download_output import DownloadOutput
from src.domain.interfaces.dto.request.download_request import DownloadRequest
from src.domain.interfaces.protocols.download_protocol import DownloadProtocol
from src.infrastructure.services.downloader.yt_dlp_download import YtDlpDownloader
from src.infrastructure.services.downloader.get_info import MediaInfoExtractor
from src.infrastructure.services.drive.drive_loader import DriveLoader

logger = logging.getLogger(__name__)

class DownloadOrchestrator:
    """
    Orchestrates the download process, deciding whether to use Drive or direct file upload
    based on a custom file size limit.
    """

    DEFAULT_FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120MB default limit

    def __init__(self, url: str, format: str, quality: Optional[str] = None, file_limit: Optional[int] = None):
        """
        Initialize orchestrator with download parameters.
        
        Args:
            url (str): URL to download
            format (str): Output format (mp4, mp3, etc.)
            quality (Optional[str]): Quality specification
            file_limit (Optional[int]): Custom file size limit in bytes. If None, uses 120MB default.
        """
        logger.debug(f"Initializing DownloadOrchestrator with url={url}, format={format}, quality={quality}, file_limit={file_limit}")
        self.url = url
        self.format = format
        self.quality = quality
        self.file_limit = file_limit or self.DEFAULT_FILE_SIZE_LIMIT
        logger.debug(f"File size limit set to: {self.file_limit} bytes ({self.file_limit / (1024*1024):.2f}MB)")
        self.downloader = YtDlpDownloader(url, format, quality)
        self.drive_loader = DriveLoader()
        self.file_path: Optional[Path] = None
        self.drive_link: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry: starts the download process."""
        logger.debug("Starting download process in orchestrator")
        await self.downloader.__aenter__()
        self.file_path = self.downloader.get_file_path()
        logger.debug(f"Download completed, file path: {self.file_path}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: cleanup handled by orchestrator."""
        logger.debug(f"Exiting orchestrator context manager, exc_type={exc_type}")
        pass

    async def get_response(self) -> DownloadOutput:
        """
        Orchestrates the complete download process and returns the final DownloadOutput.
        
        Returns:
            DownloadOutput: Complete result with file path, drive link, metadata, etc.
        """
        logger.debug("Starting orchestrator response generation")
        if not self.file_path:
            logger.error("No file was downloaded")
            raise RuntimeError("No file was downloaded")

        # Get basic file information
        logger.debug("Extracting file information")
        elapsed_time = self.downloader.get_elapsed_time()
        is_audio = self.downloader.get_is_audio()
        file_size = MediaInfoExtractor.get_file_size(self.file_path)
        logger.debug(f"File info - size: {file_size} bytes, is_audio: {is_audio}, elapsed: {elapsed_time}s")
        
        # Get media metadata (only for video files)
        resolution = None
        frame_rate = None
        if not is_audio:
            logger.debug("Extracting video metadata")
            resolution = MediaInfoExtractor.get_resolution(self.file_path)
            frame_rate = MediaInfoExtractor.get_frame_rate(self.file_path)
            logger.debug(f"Video metadata - resolution: {resolution}, frame_rate: {frame_rate}fps")

        # Decide whether to upload to Drive based on file size
        should_use_drive = self._should_use_drive(file_size)
        logger.debug(f"Drive upload decision: should_use_drive={should_use_drive}")
        
        if should_use_drive:
            limit_mb = self.file_limit / (1024*1024)
            logger.info(f"File size ({file_size / (1024*1024):.2f}MB) exceeds limit ({limit_mb:.0f}MB), uploading to Drive")
            logger.debug("Starting Drive upload process")
            try:
                drive = self.drive_loader.get_drive()
                logger.debug("Drive instance obtained, starting upload")
                self.drive_link = await drive.uploadToDrive(str(self.file_path))
                logger.info(f"Successfully uploaded to Drive: {self.drive_link}")
                logger.debug(f"Drive upload completed successfully")
            except Exception as e:
                logger.error(f"Failed to upload to Drive: {e}")
                logger.debug(f"Drive upload failed, falling back to file path: {e}")
                # Fallback: return file path even if Drive upload failed
                self.drive_link = None

        # Create cleanup function
        def cleanup():
            logger.debug("Executing cleanup function")
            self.downloader.cleanup()

        # Return the final DownloadOutput
        logger.debug("Creating final DownloadOutput object")
        result = DownloadOutput(
            file_path=self.file_path if not should_use_drive else None,
            drive_link=self.drive_link,
            elapsed=elapsed_time,
            filesize=file_size,
            is_audio=is_audio,
            cleanup=cleanup,
            cleanup_speed_included=False,
            frame_rate=frame_rate,
            resolution=resolution
        )
        logger.debug(f"Orchestrator response generation completed: file_path={result.file_path}, drive_link={result.drive_link}")
        return result

    def _should_use_drive(self, file_size: int) -> bool:
        """
        Determines whether the file should be uploaded to Drive based on the custom file size limit.
        
        Args:
            file_size (int): File size in bytes
            
        Returns:
            bool: True if file should be uploaded to Drive, False otherwise
        """
        should_use = file_size > self.file_limit
        logger.debug(f"Drive decision: file_size={file_size} bytes ({file_size / (1024*1024):.2f}MB) > limit={self.file_limit} bytes ({self.file_limit / (1024*1024):.2f}MB) = {should_use}")
        return should_use

    def cancel_download(self):
        """Cancel the ongoing download task and clean up temporary files."""
        logger.debug("Cancelling download in orchestrator")
        self.downloader.cancel_download()
        logger.debug("Download cancellation completed")
