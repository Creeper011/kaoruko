import asyncio
import os
import time
import logging
from typing import Optional, Tuple
from src.infrastructure.services.downloader import Downloader
from src.infrastructure.services.drive import Drive
from src.domain.entities import DownloadResult
from src.core.models import Result

logger = logging.getLogger(__name__)

class DownloaderService:
    def __init__(self, url: str, format: str, cancel_at_seconds: int = None, max_file_size: int = 120 * 1024 * 1024):
        self.url = url
        self.format = format
        self.max_file_size = max_file_size
        self.cancel_at_seconds = cancel_at_seconds
        self.drive = Drive("")
        self.downloader = None
        self._temp_file_paths = []  # List to track temporary files

    async def download(self) -> Tuple[DownloadResult, Result]:
        start = time.time()
        try:
            if self.cancel_at_seconds:
                downloader = Downloader(self.url, self.format)
                self.downloader = downloader
                filepath = await asyncio.wait_for(
                    self._download_with_context(downloader),
                    timeout=self.cancel_at_seconds
                )
            else:
                async with Downloader(self.url, self.format) as downloader:
                    self.downloader = downloader
                    filepath = downloader.get_filepath()
            
            elapsed = time.time() - start
            
            logger.debug(f"Download completed. Filepath: {filepath}")
            
            if not filepath:
                logger.error("Download completed but no filepath returned")
                await self._cleanup_temp_files()
                return DownloadResult(elapsed=elapsed), Result.failure(error="Download completed but no file found")
            
            if not os.path.exists(filepath):
                logger.error(f"Filepath returned but file does not exist: {filepath}")
                await self._cleanup_temp_files()
                return DownloadResult(elapsed=elapsed), Result.failure(error=f"File not found: {filepath}")
            
            self._temp_file_paths.append(filepath)
            logger.debug(f"File downloaded successfully: {filepath}")
            
            download_result, result = await self._resolve_filepath(filepath, elapsed)
            return download_result, result
        
        except asyncio.TimeoutError:
            logger.warning("Download timeout")
            if self.downloader:
                self.downloader.cancel_download()
            await self._cleanup_temp_files()
            return None, None
        except Exception as error:
            logger.error(f"Download error: {error}")
            elapsed = time.time() - start
            download_result = DownloadResult()
            download_result.elapsed = elapsed
            await self._cleanup_temp_files()
            return download_result, Result.failure(error=str(error))

    async def _download_with_context(self, downloader: Downloader):
        """Helper method to use context manager with timeout"""
        async with downloader:
            return downloader.get_filepath()
        
    async def _resolve_filepath(self, file_path: str, elapsed: float) -> Tuple[DownloadResult, Result]:
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File does not exist in _resolve_filepath: {file_path}")
            raise FileNotFoundError(f"File does not exist: {file_path}")

        download_result = DownloadResult()
        download_result.elapsed = elapsed
        download_result.file_size = os.path.getsize(file_path)
        
        logger.debug(f"Resolving filepath: {file_path}, size: {download_result.file_size} bytes")

        if download_result.file_size > self.max_file_size:
            logger.debug(f"File is large ({download_result.file_size} bytes), uploading to Drive")
            try:
                download_result.link = await self.drive.uploadToDrive(file_path)
                # After uploading to Drive, clean up the parent directory (UUID4)
                if self.downloader:
                    self.downloader._cleanup()
                result = Result.success()
                return download_result, result
            
            except Exception as error:
                logger.error(f"Error uploading to Drive: {str(error)}")
                # Fallback to file path if drive upload fails
                download_result.filepath = file_path
                result = Result.success()
                return download_result, result
        else:
            logger.debug(f"File is small ({download_result.file_size} bytes), keeping local for Discord upload")
            download_result.filepath = file_path
            result = Result.success()
            return download_result, result

    async def _cleanup_temp_files(self):
        """Cleans up the parent directory (UUID4) that contains all temporary files"""
        # Clean up the parent directory (UUID4) if downloader exists
        if self.downloader:
            self.downloader._cleanup()
        
        self._temp_file_paths.clear()


    async def cleanup_after_send(self, file_path: str):
        """Method to clean up the parent directory (UUID4) after sending via Discord"""
        if file_path in self._temp_file_paths:
            self._temp_file_paths.remove(file_path)
            logger.debug(f"Removed file from tracking: {file_path}")
        
        # Clean up the parent directory (UUID4) if downloader exists
        if self.downloader:
            self.downloader._cleanup()
            logger.debug("Cleaned up parent directory (UUID4) after Discord send")

    async def schedule_cleanup(self, delay_seconds: int = 30):
        """Schedules automatic cleanup after a specific time"""
        async def delayed_cleanup():
            await asyncio.sleep(delay_seconds)
            await self._cleanup_temp_files()
            logger.debug(f"Scheduled cleanup completed after {delay_seconds} seconds")
        
        asyncio.create_task(delayed_cleanup())
        logger.debug(f"Scheduled cleanup in {delay_seconds} seconds")

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel_download()
            # The downloader's cancel_download already calls _cleanup(), but we'll ensure
            # that our cleanup is also executed
        asyncio.create_task(self._cleanup_temp_files())
