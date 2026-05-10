import logging

from src.domain.models.settings import DriveSettings
from src.services.drive.google_drive_login_service import GoogleDriveLoginService


async def build_google_drive(drive_settings: DriveSettings) -> GoogleDriveLoginService:
    """Builds Google Drive-related components."""
    logger = logging.getLogger("BuildGoogleDriveStep")
    logger.info("Building Google Drive login service")

    login_service = GoogleDriveLoginService(
        account_filepath=drive_settings.credentials_path,
    )
    await login_service.login()

    logger.info("Google Drive login service built successfully")
    return login_service
