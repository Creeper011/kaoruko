import logging
from typing import Iterable, Any

from src.infrastructure.services.config.models import ApplicationSettings

from src.application.usecases.download_usecase import DownloadUsecase
from src.application.services.cache_manager import CacheManager
from src.domain.models.download_settings import DownloadSettings
from src.infrastructure.services.ytdlp import YtdlpDownloadService, YtdlpFormatMapper
from src.infrastructure.services.url_validator import UrlValidator
from src.infrastructure.services.temp_service import TempService
from src.infrastructure.services.cache import JSONCacheStorage
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.infrastructure.services.drive.google_drive_uploader_service import GoogleDriveUploaderService

class ExtensionServicesBuilder:
    """Builds services related to extensions that gonna be used by Discord Module"""

    def __init__(self, drive_login: GoogleDriveLoginService) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.drive_login = drive_login

    def build_services(self, settings: ApplicationSettings) -> Iterable[Any]:
        """Builds and returns services for extensions."""
        self.logger.info("Building extension services")

        if settings.download_settings is None:
            raise RuntimeError("Download settings must be configured to build services.")
        
        extension_services: tuple[Any, ...] = (
            DownloadUsecase(
                logger=self.logger,
                download_service=YtdlpDownloadService(logger=self.logger, ytdlp_format_mapper=YtdlpFormatMapper()),
                temp_service=TempService(logger=self.logger),
                cache_manager=CacheManager(logger=self.logger, storage=JSONCacheStorage(logger=self.logger)),
                storage_service=GoogleDriveUploaderService(
                    logger=self.logger, 
                    login_service=self.drive_login,
                    drive_folder_id=settings.drive_settings.folder_id,
                ),
                url_validator=UrlValidator(self.logger),
                blacklist_sites=settings.download_settings.blacklist_sites,
            ),
            DownloadSettings(
                file_size_limit=settings.download_settings.file_size_limit,
                blacklist_sites=settings.download_settings.blacklist_sites,
            ),
        )

        self.logger.info("Extension services built successfully")
        return extension_services