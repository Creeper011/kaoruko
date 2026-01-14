from logging import Logger
from src.application.services.download import DownloaderService
from src.application.services import CacheManager
from src.application.protocols import RemoteStorageServiceProtocol
from src.application.protocols import TempServiceProtocol
from src.application.services.download import DownloadRequestValidator
from src.application.services.download import StorageDecisionStrategy
from src.application.services.download import DownloadCacheService
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput


class DownloadUsecase():
    """Usecase for downloading files with caching and storage handling."""
    
    def __init__(self, downloader_service: DownloaderService,
                 cache_manager: CacheManager, storage_service: RemoteStorageServiceProtocol,
                 temp_service: TempServiceProtocol, validator: DownloadRequestValidator,
                 decision_strategy: StorageDecisionStrategy, download_cache_service: DownloadCacheService,
                 logger: Logger) -> None:
        self.downloader_service = downloader_service
        self.cache_manager = cache_manager
        self.storage_service = storage_service
        self.temp_service = temp_service
        self.validator = validator
        self.decision_strategy = decision_strategy
        self.download_cache_service = download_cache_service
        self.logger = logger

        self.logger.info("DownloadUsecase initialized")

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        self._validate_request(request)

        cached_output = await self.download_cache_service.get_cached_output(request)
        if cached_output:
            return cached_output

        async with self.temp_service.create_session() as temp_folder:
            downloaded_file = await self.downloader_service.download(request, temp_folder)
            decision = await self.decision_strategy.decide(request, downloaded_file)
            cache_key = self.download_cache_service.create_cache_key(request)
            return await self.download_cache_service.store_download(cache_key, downloaded_file, decision.destination, self.storage_service)
            
    def _validate_request(self, request: DownloadRequest):
        self.validator.validate(request)