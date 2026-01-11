import asyncio
from logging import Logger
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build, Resource
from google.oauth2 import service_account

SERVICE_NAME = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

class GoogleDriveLoginService():
    """Only do the login process for Google Drive as a Singleton Service with async."""
    
    _instance: Optional['GoogleDriveLoginService'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleDriveLoginService, cls).__new__(cls)
        return cls._instance

    def __init__(self, logger: Logger, account_filepath: Path) -> None:
        if self._initialized:
            return

        self.logger = logger
        self.account_filepath = account_filepath
        self.drive_service: Optional[Resource] = None
        self._lock = asyncio.Lock()
        
        self._initialized = True
        self.logger.info("GoogleDriveLoginService initialized")

    async def login(self) -> None:
        """Authenticates and builds the Drive service asynchronously."""
        async with self._lock:
            if self.drive_service:
                self.logger.debug("Google Drive Service is already active.")
                return

            self.logger.info("Logging into Google Drive...")

            if not self.account_filepath.exists():
                msg = f"Service account file not found: {self.account_filepath}"
                self.logger.error(msg)
                raise FileNotFoundError(msg)

            try:
                self.drive_service = await asyncio.to_thread(self._sync_build_service)
                self.logger.info("Google Drive authenticated successfully.")
            except Exception as e:
                self.logger.error(f"Failed to login to Google Drive: {e}")
                raise e

    def _sync_build_service(self) -> Resource:
        """Internal synchronous method to run inside a thread."""
        credentials = service_account.Credentials.from_service_account_file(
            str(self.account_filepath),
            scopes=SCOPES
        )
        return build(SERVICE_NAME, API_VERSION, credentials=credentials)

    async def reconnect(self) -> None:
        """Forces a re-authentication."""
        self.logger.warning("Reconnecting to Google Drive...")
        async with self._lock:
            self.close_connection()
            await self.login()

    async def get_instance_drive(self) -> Resource:
        """Returns the Drive service instance, logging in if necessary."""
        self.logger.debug("Getting Google Drive instance...")
        
        async with self._lock:
            if self.drive_service is None:
                self.logger.warning("Drive service was None, attempting to login...")
                await self.login()
                
            return self.drive_service

    def close_connection(self) -> None:
        """Closes the connection to the Google Drive API."""
        if self.drive_service:
            self.logger.debug("Closing Google Drive connection...")
            try:
                self.drive_service.close()
            except Exception as e:
                self.logger.error(f"Error closing Drive connection: {e}")
            finally:
                self.drive_service = None
                self.logger.info("Google Drive connection closed.")
        else:
            self.logger.debug("No active connection to close.")