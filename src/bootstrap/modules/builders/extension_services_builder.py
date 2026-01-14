import logging
from typing import Iterable, Any
from src.bootstrap.models import Builder

from src.infrastructure.services.config.models import ApplicationSettings

from src.application.usecases.download_usecase import DownloadUsecase
from src.application.usecases.timed_download_usecase import TimedDownloadUseCase
from src.application.services import CacheManager
from src.application.services.download import DownloaderService, DownloadRequestValidator, DownloadCacheService, SizeBasedStorageDecisionStrategy
from src.domain.models.settings import DownloadSettings
from src.infrastructure.services.ytdlp import YtdlpDownloadService, YtdlpFormatMapper
from src.infrastructure.services.url_validator import UrlValidator
from src.infrastructure.services.temp_service import TempService
from src.infrastructure.services.cache import JSONCacheStorage
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.infrastructure.services.drive.google_drive_uploader_service import GoogleDriveUploaderService

class ExtensionServicesBuilder(Builder):
    """Builds services related to extensions that gonna be used by Discord Module"""

    def __init__(self, settings: ApplicationSettings, drive_login: GoogleDriveLoginService) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = settings
        self.drive_login = drive_login

    def build(self) -> Iterable[Any]:
        """Builds and returns services for extensions."""
        self.logger.info("Building extension services")

        if self.settings.download_settings is None:
            raise RuntimeError("Download settings must be configured to build services.")
        
        cache_manager = CacheManager(storage=JSONCacheStorage(logger=self.logger))
        downloader_service = DownloaderService(
            download_service=YtdlpDownloadService(ytdlp_format_mapper=YtdlpFormatMapper()),
            logger=self.logger
        )
        validator = DownloadRequestValidator(
            url_validator=UrlValidator(),
            blacklist_sites=self.settings.download_settings.blacklist_sites
        )
        download_cache_service = DownloadCacheService(cache_manager=cache_manager)
        decision_strategy = SizeBasedStorageDecisionStrategy()
        storage_service = GoogleDriveUploaderService(
            login_service=self.drive_login,
            drive_folder_id=self.settings.drive_settings.folder_id,
        )
        temp_service = TempService()

        usecase = DownloadUsecase(
            downloader_service=downloader_service,
            cache_manager=cache_manager,
            storage_service=storage_service,
            temp_service=temp_service,
            validator=validator,
            decision_strategy=decision_strategy,
            download_cache_service=download_cache_service,
            logger=self.logger
        )

        timed_usecase = TimedDownloadUseCase(usecase=usecase, logger=self.logger)

        extension_services: tuple[Any, ...] = (
            timed_usecase,
            DownloadSettings(
                file_size_limit=self.settings.download_settings.file_size_limit,
                blacklist_sites=self.settings.download_settings.blacklist_sites,
            ),
        )

        self.logger.info("Extension services built successfully")
        return extension_services