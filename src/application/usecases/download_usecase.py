import asyncio
import logging
import validators
from pathlib import Path
from typing import Callable, Awaitable
from logging import Logger

from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.application.protocols import RemoteStorageServiceProtocol, TempServiceProtocol
from src.application.usecases.downloader_service import DownloaderService
from src.domain.enum.download_destination import DownloadDestination
from src.domain.exceptions import UrlException, BlacklistException
from src.domain.models import DownloadedFile
from src.domain.models.settings.download_settings import DownloadSettings

class DownloadUsecase():
    def __init__(
        self,
        downloader_service: DownloaderService,
        storage_service: RemoteStorageServiceProtocol,
        temp_service: TempServiceProtocol,
        settings: DownloadSettings,
        logger: Logger | None = None
    ) -> None:
        self.downloader_service = downloader_service
        self.storage_service = storage_service
        self.temp_service = temp_service
        self.settings = settings
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    async def execute(
        self,
        request: DownloadRequest,
        progress_callback: Callable[[float], Awaitable[None]] | None = None,
    ) -> DownloadOutput:
        if not validators.url(request.url):
            self.logger.warning("Invalid URL: %s", request.url)
            raise UrlException("Invalid URL: %s" % request.url)

        for site in self.settings.blacklist_sites:
            if site in request.url:
                self.logger.warning("Blacklisted: %s", request.url)
                raise BlacklistException("URL is blacklisted: %s" % request.url)

        async with self.temp_service.create_session() as temp_folder:
            self.logger.info("Downloading %s to %s", request.url, temp_folder)
            downloaded_file: DownloadedFile = await self.downloader_service.download(
                request,
                temp_folder,
                progress_callback=progress_callback,
            )

            destination = DownloadDestination.LOCAL
            if downloaded_file.file_size > request.file_size_limit:
                destination = DownloadDestination.REMOTE
            
            self.logger.info("Size: %d, Destination: %s", downloaded_file.file_size, destination)

            if destination == DownloadDestination.REMOTE:
                self.logger.info("Uploading %s", downloaded_file.file_path.name)
                final_url = await self.storage_service.upload(downloaded_file.file_path)
                return DownloadOutput(
                    file_url=final_url,
                    file_name=downloaded_file.file_path.name,
                    file_size=downloaded_file.file_size,
                )

            file_bytes = await asyncio.to_thread(downloaded_file.file_path.read_bytes)
            return DownloadOutput(
                file_name=downloaded_file.file_path.name,
                file_bytes=file_bytes,
                file_size=downloaded_file.file_size,
            )
