import logging
from src.bootstrap.models import Builder

from src.domain.models.settings import DriveSettings
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService

class DriveBuilder(Builder):
    """Builds login service for Drive integration."""

    def __init__(self, drive_settings: DriveSettings) -> None:
        self.drive_settings = drive_settings
        self.logger = logging.getLogger(self.__class__.__name__)

    async def build(self) -> GoogleDriveLoginService:
        """Builds and returns the Google Drive login service."""
        self.logger.info("Building Google Drive login service")
        login_service = GoogleDriveLoginService(
            logger=self.logger,
            account_filepath=self.drive_settings.credentials_path,
        )
        await login_service.login()
        self.logger.info("Google Drive login service built successfully")
        return login_service