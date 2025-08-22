import os
import shutil
import cv2
from time import time
import validators
from yt_dlp import utils
import logging
from src.domain.usecases.speedmedia import SpeedMedia, SpeedMediaResult
from src.domain.entities.download_entity import DownloadResult
from src.domain.exceptions.download_exceptions import MediaFilepathNotFound, FailedToUploadDrive
from src.infrastructure.services.downloader import Downloader
from src.infrastructure.services.drive import Drive

logger = logging.getLogger(__name__)

class DownloadUsecase:
    """Usecase for downloading media and optionally changing speed"""

    def __init__(self):
        self.speedmedia_service = SpeedMedia()
        self.config = {
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
                'match_filter': utils.match_filter_func("!is_live"),
            }
        }
        # parâmetros globais de cleanup
        self.cleanup_temp_dir = self.config["temp_dir"]
        self.cleanup_speed_included = False  
        self.session_id: str | None = None 
        self.drive = Drive("")
        self.max_file_size = 1024 * 1024 * 100

        logger.debug("Initialized DownloadUsecase")

    def _cleanup(self) -> None:
        """Delete temporary files and directories"""
        try:
            if not self.session_id:
                logger.debug("No session_id set for cleanup, skipping.")
                return
            path_id = os.path.join(self.cleanup_temp_dir, self.session_id)
            if path_id and os.path.exists(path_id):
                shutil.rmtree(path_id, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {path_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {self.cleanup_temp_dir}: {e}")
        if self.cleanup_speed_included:
            logger.debug("Speed media service cleanup called.")
            self.speedmedia_service._cleanup()

    def get_frame_rate(self, file_path: str) -> float:
        """Get the frame rate of a video file"""
        if os.path.exists(file_path):
            cv2_video = cv2.VideoCapture(file_path)
            return cv2_video.get(cv2.CAP_PROP_FPS)
        return 0.0
    
    def get_resolution(self, file_path: str) -> str:
        """Get the resolution of a video file"""
        if os.path.exists(file_path):
            cv2_video = cv2.VideoCapture(file_path)
            width = cv2_video.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cv2_video.get(cv2.CAP_PROP_FRAME_HEIGHT)
            return f"{int(width)}x{int(height)}"
        return "0x0"

    async def download(self, url: str, format: str, speed: float = None, preserve_pitch: bool = True, quality: str = None) -> SpeedMediaResult:
        """Download a media file and optionally change its speed"""

        start = time()
        
        if not validators.url(url):
            url = f"ytsearch:{url}"

        file_path, temp_dir, session_id, is_audio = await self._download_async(url, format, quality if quality else None)

        self.session_id = session_id  

        if not file_path or not os.path.exists(file_path):
            raise MediaFilepathNotFound(f"Downloaded file not found: {file_path}")

        drive_path = None

        if speed is not None:
            self.cleanup_speed_included = True
            result: SpeedMediaResult = await self.speedmedia_service.change_speed(file_path, speed, preserve_pitch, not_upload_to_drive=True)
            
            if result.exception:
                logger.error(f"Error changing speed: {result.exception}")
                raise result.exception

            if result.file_path and os.path.getsize(result.file_path) > self.max_file_size:
                try:
                    drive_path = await self.drive.uploadToDrive(result.file_path)
                    result.drive_path = drive_path
                    logger.debug(f"Large file uploaded to Drive: {drive_path}")
                except Exception as e:
                    logger.error(f"Failed to upload to Drive: {e}")
                    raise FailedToUploadDrive(f"Failed to upload {result.file_path} to Drive: {e}")

            return DownloadResult(
                file_path=result.file_path,
                drive_link=result.drive_path,
                elapsed=time() - start,
                download_path=temp_dir,
                speed_elapsed=result.elapsed,
                resolution=self.get_resolution(result.file_path), frame_rate=self.get_frame_rate(result.file_path),
                is_audio=is_audio
            )
        else:
            if file_path and os.path.getsize(file_path) > self.speedmedia_service.max_file_size:
                try:
                    drive_path = await self.speedmedia_service.drive.uploadToDrive(file_path)
                    logger.debug(f"Large file uploaded to Drive: {drive_path}")
                except Exception as e:
                    logger.error(f"Failed to upload to Drive: {e}")
                    raise FailedToUploadDrive(f"Failed to upload {file_path} to Drive: {e}")

        elapsed = time() - start
        return DownloadResult(file_path=file_path, drive_link=drive_path, elapsed=elapsed, download_path=temp_dir, resolution=self.get_resolution(file_path), frame_rate=self.get_frame_rate(file_path))

    async def _download_async(self, url: str, format: str, quality: str = None) -> str:
        """Perform the actual download and return the downloaded file path + session_id"""
        async with Downloader(url, format, quality) as downloader:
            file_path = downloader.get_filepath()
            temp_dir = downloader._get_temp_dir_abspath()
            session_id = downloader.session_id
            is_audio = downloader.is_audio
            logger.debug(f"File downloaded at: {file_path} (session_id={session_id})")
            return file_path, temp_dir, session_id, is_audio
