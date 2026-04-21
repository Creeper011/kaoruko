import asyncio
from collections.abc import Awaitable, Callable
from logging import Logger
from src.application.services.download import DownloaderService
from src.application.protocols import RemoteStorageServiceProtocol
from src.application.protocols import TempServiceProtocol
from src.application.services.download import DownloadRequestValidator
from src.application.services.download import StorageDecisionStrategy
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.domain.enum.download_destination import DownloadDestination


class DownloadUsecase():
    """Usecase for downloading files and deciding how they should be delivered."""

    def __init__(self, downloader_service: DownloaderService,
                 storage_service: RemoteStorageServiceProtocol,
                 temp_service: TempServiceProtocol, validator: DownloadRequestValidator,
                 decision_strategy: StorageDecisionStrategy,
                 logger: Logger) -> None:
        self.downloader_service = downloader_service
        self.storage_service = storage_service
        self.temp_service = temp_service
        self.validator = validator
        self.decision_strategy = decision_strategy
        self.logger = logger

        self.logger.info("DownloadUsecase initialized")

    async def execute(
        self,
        request: DownloadRequest,
        progress_callback: Callable[[float], Awaitable[None]] | None = None,
    ) -> DownloadOutput:
        self._validate_request(request)

        async with self.temp_service.create_session() as temp_folder:
            downloaded_file = await self.downloader_service.download(
                request,
                temp_folder,
                progress_callback=progress_callback,
            )
            decision = await self.decision_strategy.decide(request, downloaded_file)

            if decision.destination == DownloadDestination.REMOTE:
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

    def _validate_request(self, request: DownloadRequest):
        self.validator.validate(request)
