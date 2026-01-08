import asyncio
import logging
from logging import Logger
from pathlib import Path
from typing import Optional
from googleapiclient.http import MediaFileUpload
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.core.constants import DRIVE_MAX_RETRY_COUNT, DRIVE_BASE_FILE_UPLOAD_URL

class GoogleDriveUploaderService():
    """Service for uploading files to Google Drive."""
    
    def __init__(self, login_service: GoogleDriveLoginService, drive_folder_id: str, max_retries: Optional[int] = DRIVE_MAX_RETRY_COUNT, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.login_service = login_service
        self.drive_folder_id = drive_folder_id
        self.max_retries = max_retries
        self.logger.info("GoogleDriveUploaderService initialized")

    async def upload(self, file_path: Path) -> str:
        """
        Uploads a file to Google Drive with retry logic and reconnection attempt.
        Returns the file ID.
        """
        self.logger.info(f"Starting upload for file: {file_path}")

        if not file_path.exists():
            msg = f"File to upload not found: {file_path}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                drive_service = await self.login_service.get_instance_drive()

                file_metadata = {
                    'name': file_path.name, 
                    'parents': [self.drive_folder_id]
                }
                
                media = MediaFileUpload(str(file_path), resumable=True)

                def _sync_upload():
                    request = drive_service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    )
                    response = request.execute()
                    return response.get('id')

                self.logger.debug(f"Executing upload attempt {attempt + 1}/{self.max_retries}...")
                file_id = await asyncio.to_thread(_sync_upload)

                def _make_public():
                    drive_service.permissions().create(
                        fileId=file_id,
                        body={'role': 'reader', 'type': 'anyone'},
                        fields='id'
                    ).execute()

                await asyncio.to_thread(_make_public)
                
                self.logger.info(f"File uploaded successfully. ID: {file_id}")
                return "%s%s" % (DRIVE_BASE_FILE_UPLOAD_URL, file_id)

            except Exception as e:
                attempt += 1
                last_error = e
                self.logger.warning(f"Upload failed (Attempt {attempt}/{self.max_retries}). Error: {e}")

                if attempt < self.max_retries:
                    self.logger.info("Attempting to reconnect before retrying...")
                    try:
                        await self.login_service.reconnect()
                    except Exception as reconnect_error:
                        self.logger.error(f"Reconnection failed: {reconnect_error}")
                else:
                    self.logger.critical(f"All upload attempts failed for {file_path}.")

        raise last_error