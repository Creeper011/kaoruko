from logging import Logger
from pathlib import Path
from infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService


class GoogleDriveUploaderService():
    """Service for uploading files to Google Drive."""
    
    def __init__(self, logger: Logger, login_service: GoogleDriveLoginService) -> None:
        self.logger = logger
        self.login_service = login_service
        self.logger.info("GoogleDriveUploaderService initialized")

    async def upload(self, file_path: Path) -> str:
        self.logger.info(f"Uploading file to Google Drive: {file_path}")

        # Implement the actual upload logic with a retry logic and using reconnect if needed