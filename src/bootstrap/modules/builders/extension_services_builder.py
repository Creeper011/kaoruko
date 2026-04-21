import logging
from typing import Iterable, Any
from src.bootstrap.models import Builder
from src.infrastructure.services.config.models import ApplicationSettings
from src.application.usecases.download_usecase import DownloadUsecase
from src.application.usecases.timed_download_usecase import TimedDownloadUseCase
from src.application.services.download import DownloaderService, DownloadRequestValidator, SizeBasedStorageDecisionStrategy
from src.infrastructure.services.url_validator import UrlValidator
from src.infrastructure.services.temp_service import TempService
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.infrastructure.services.drive.google_drive_uploader_service import GoogleDriveUploaderService
from src.infrastructure.services.yumeapi import YumeApiDownloadService

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

        downloader_service = DownloaderService(
            download_service=YumeApiDownloadService(
                base_url=self.settings.download_settings.api_base_url,
                status_poll_interval_seconds=self.settings.download_settings.api_poll_interval_seconds,
                job_timeout_seconds=self.settings.download_settings.api_timeout_seconds,
                logger=self.logger,
            ),
            logger=self.logger
        )
        validator = DownloadRequestValidator(
            url_validator=UrlValidator(),
            blacklist_sites=self.settings.download_settings.blacklist_sites
        )
        decision_strategy = SizeBasedStorageDecisionStrategy()
        storage_service = GoogleDriveUploaderService(
            login_service=self.drive_login,
            drive_folder_id=self.settings.drive_settings.folder_id,
            logger=self.logger,
        )
        temp_service = TempService()

        usecase = DownloadUsecase(
            downloader_service=downloader_service,
            storage_service=storage_service,
            temp_service=temp_service,
            validator=validator,
            decision_strategy=decision_strategy,
            logger=self.logger
        )

        timed_usecase = TimedDownloadUseCase(usecase=usecase, logger=self.logger)

        extension_services: tuple[Any, ...] = (
            timed_usecase,
            self.settings.download_settings,
        )

        self.logger.info("Extension services built successfully")
        return extension_services
