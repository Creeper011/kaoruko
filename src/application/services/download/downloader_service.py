from logging import Logger
from pathlib import Path
from src.application.protocols import DownloadServiceProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.domain.models import DownloadedFile

class DownloaderService():
    """Downloads media to a specified output path"""

    def __init__(self, download_service: DownloadServiceProtocol, logger: Logger) -> None:
        self.logger = logger
        self.download_service = download_service

    async def download(self, request: DownloadRequest, output_path: Path) -> DownloadedFile:
        """Download to the specified output path"""
        return await self.download_service.download(request.url, request.format, request.quality, output_path)