import logging
import os
from typing import Optional
from pathlib import Path

from src.domain.interfaces.dto.output.download_output import DownloadOutput
from src.infrastructure.services import YtDlpDownloader
from src.infrastructure.services import MediaInfoExtractor
from src.infrastructure.services import DriveLoader

logger = logging.getLogger(__name__)

class DownloadOrchestrator:
    """
    Orchestrates the download process, deciding whether to use Drive or direct file upload
    based on a custom file size limit.
    """

    def __init__(self, url: str, format: str, quality: Optional[str] = None, 
                 min_size_for_drive_upload: Optional[int] = None, should_transcode: bool = False,
                 verbose: bool = False):
        """
        Initialize orchestrator with download parameters.
        
        Args:
            url (str): URL to download
            format (str): Output format (mp4, mp3, etc.)
            quality (Optional[str]): Quality specification
            file_limit (Optional[int]): Custom file size limit in bytes. If None, uses 120MB default.
            should_transcode (bool): Whether to force transcoding even if not strictly necessary.
            verbose (bool): Send more detailed info about the output media file if true.
        """
        logger.debug(f"Initializing DownloadOrchestrator with url={url}, format={format}, quality={quality}, min size for upload drive={min_size_for_drive_upload}")

        self.url = url
        self.format = format
        self.quality = quality
        self.min_size_for_drive_upload = min_size_for_drive_upload or 120 * 1024 * 1024
        self.verbose = verbose
        self.extra_info = {}
        logger.debug(f"File size limit set to: {self.min_size_for_drive_upload} bytes ({self.min_size_for_drive_upload / (1024*1024):.2f}MB)")

        self.downloader = YtDlpDownloader(url, format, quality, should_transcode)
        self.drive_loader = DriveLoader()
        self.downloaded_file_path: Optional[Path] = None
        self.drive_link: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry: starts the download process."""
        logger.debug("Starting download process in orchestrator")
        await self.downloader.download()
        self.downloaded_file_path = self.downloader.get_file_path()

        logger.debug(f"Download completed, file path: {self.downloaded_file_path}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: cleanup handled by orchestrator."""
        logger.debug(f"Exiting orchestrator context manager, exc_type={exc_type}")
        pass
    
    def _get_video_information(self):
        logger.debug("Extracting video metadata")
        resolution = MediaInfoExtractor.get_resolution(self.downloaded_file_path)
        frame_rate = MediaInfoExtractor.get_frame_rate(self.downloaded_file_path)

        if self.verbose:
            codec_video = MediaInfoExtractor.get_video_codec(self.downloaded_file_path)
            duration = MediaInfoExtractor.get_duration(self.downloaded_file_path)
            bitrate = MediaInfoExtractor.get_bitrate(self.downloaded_file_path)
            audio_codec = MediaInfoExtractor.get_audio_codec(self.downloaded_file_path)
            sample_rate = MediaInfoExtractor.get_audio_sample_rate(self.downloaded_file_path)
            channels = MediaInfoExtractor.get_audio_channels(self.downloaded_file_path)
            self.extra_info['video_codec'] = codec_video
            self.extra_info['duration'] = duration
            self.extra_info['bitrate'] = bitrate
            self.extra_info['audio_codec'] = audio_codec
            self.extra_info['audio_sample_rate'] = sample_rate
            self.extra_info['audio_channels'] = channels
            logger.debug(f"Verbose mode: video_codec={codec_video}, duration={duration}, bitrate={bitrate}, audio_codec={audio_codec}, sample_rate={sample_rate}, channels={channels}")

        logger.debug(f"Video metadata - resolution: {resolution}, frame_rate: {frame_rate}fps")
        return (resolution, frame_rate)

    def _extract_basic_information_media(self):
        logger.debug("Extracting file information")
        elapsed_time = self.downloader.get_elapsed_time()
        is_audio = self.downloader.get_is_audio()
        file_size = MediaInfoExtractor.get_file_size(self.downloaded_file_path)

        if self.verbose and is_audio:
            duration = MediaInfoExtractor.get_duration(self.downloaded_file_path)
            bitrate = MediaInfoExtractor.get_bitrate(self.downloaded_file_path)
            audio_codec = MediaInfoExtractor.get_audio_codec(self.downloaded_file_path)
            sample_rate = MediaInfoExtractor.get_audio_sample_rate(self.downloaded_file_path)
            channels = MediaInfoExtractor.get_audio_channels(self.downloaded_file_path)
            self.extra_info['duration'] = duration
            self.extra_info['bitrate'] = bitrate
            self.extra_info['audio_codec'] = audio_codec
            self.extra_info['audio_sample_rate'] = sample_rate
            self.extra_info['audio_channels'] = channels
            logger.debug(f"Verbose mode (audio): duration={duration}, bitrate={bitrate}, audio_codec={audio_codec}, sample_rate={sample_rate}, channels={channels}")

        logger.debug(f"File info - size: {file_size} bytes, is_audio: {is_audio}, elapsed: {elapsed_time}s")
        return (elapsed_time, is_audio, file_size)

    async def get_response(self) -> DownloadOutput:
        """
        Assemble and return the DownloadOutput object based on collected
        information and upload decisions.
        """
        logger.debug("Starting DownloadOutput assembly")

        if not self.downloaded_file_path:
            logger.error("No file was downloaded")
            raise RuntimeError("No file was downloaded")

        elapsed_time, is_audio, file_size = self._extract_basic_information_media()
        if not is_audio:
            resolution, frame_rate = self._get_video_information()
        else:
            resolution, frame_rate = None, None

        self.drive_link = await self._handle_drive_upload(file_size)
        
        result = DownloadOutput(
            file_path=self.downloaded_file_path if not self.drive_link else None,
            drive_link=self.drive_link,
            elapsed=elapsed_time,
            filesize=file_size,
            is_audio=is_audio,
            cleanup=self.downloader.cleanup,
            frame_rate=frame_rate,
            resolution=resolution,
            extra_info=self.extra_info if self.extra_info else None
        )

        logger.debug(f"DownloadOutput successfully created: {result}")
        return result


    async def _handle_drive_upload(self, file_size: int) -> Optional[str]:
        """Handle Drive upload if needed and return the link."""
        should_use_drive = file_size > self.min_size_for_drive_upload
        if not should_use_drive:
            return None
        logger.debug(f"Drive decision: file_size={file_size} bytes ({file_size / (1024*1024):.2f}MB) > limit={self.min_size_for_drive_upload} bytes ({self.min_size_for_drive_upload / (1024*1024):.2f}MB) = {should_use_drive}")

        try:
            logger.info("File exceeds limit, starting upload to Drive")
            drive = self.drive_loader.get_drive()
            drive_link = await drive.uploadToDrive(str(self.downloaded_file_path))
            logger.info(f"Upload completed successfully: {drive_link}")
            return drive_link
        except Exception as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return None

    def cancel_download(self):
        """Cancel the ongoing download task and clean up temporary files."""
        logger.debug("Cancelling download in orchestrator")
        self.downloader.cancel_download()
        logger.debug("Download cancellation completed")
