import logging
from typing import Any, Callable, Iterable

from src.application.usecases.download_usecase import DownloadUsecase
from src.application.usecases.downloader_service import DownloaderService
from src.application.usecases.timed_download_usecase import TimedDownloadUseCase
from src.bootstrap.steps.build_google_drive_step import build_google_drive
from src.services.config.models import ApplicationSettings
from src.services.drive.google_drive_uploader_service import GoogleDriveUploaderService
from src.services.temp_service import TempService
from src.services.yumeapi import YumeApiDownloadService


async def build_extension_services(
    settings: ApplicationSettings,
) -> tuple[Iterable[Any], list[Callable[[], None]]]:
    """Builds services for extensions."""
    logger = logging.getLogger("BuildExtensionServicesStep")
    logger.info("Building extension services")

    if settings.download is None:
        raise RuntimeError("Download settings must be configured to build services.")

    if settings.drive is None:
        raise RuntimeError("Drive settings must be configured to build services.")

    drive_login_service = await build_google_drive(drive_settings=settings.drive)

    downloader_service = DownloaderService(
        download_service=YumeApiDownloadService(
            base_url=settings.download.download_api,
            status_poll_interval_seconds=settings.download.api_poll_interval,
            job_timeout_seconds=settings.download.api_timeout,
        ),
    )

    storage_service = GoogleDriveUploaderService(
        login_service=drive_login_service,
        drive_folder_id=settings.drive.folder_id,
    )
    temp_service = TempService()

    usecase = DownloadUsecase(
        downloader_service=downloader_service,
        storage_service=storage_service,
        temp_service=temp_service,
        settings=settings.download,
    )

    timed_usecase = TimedDownloadUseCase(usecase=usecase)

    extension_services: tuple[Any, ...] = (
        timed_usecase,
        settings.download,
    )
    shutdown_callbacks = [
        drive_login_service.close_connection,
    ]

    logger.info("Extension services built successfully")
    return extension_services, shutdown_callbacks
