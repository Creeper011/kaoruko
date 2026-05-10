import asyncio
import hashlib
import logging
from logging import Logger
from pathlib import Path
from typing import Optional
from googleapiclient.http import MediaFileUpload
from src.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.constants import DRIVE_MAX_RETRY_COUNT, DRIVE_BASE_FILE_UPLOAD_URL

class GoogleDriveUploaderService():
    """Service for uploading files to Google Drive."""

    def __init__(self, login_service: GoogleDriveLoginService, drive_folder_id: str, max_retries: Optional[int] = DRIVE_MAX_RETRY_COUNT, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.login_service = login_service
        self.drive_folder_id = drive_folder_id
        self.max_retries = max_retries or DRIVE_MAX_RETRY_COUNT
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

        file_sha256 = await asyncio.to_thread(self._calculate_sha256, file_path)
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                drive_service = await self.login_service.get_instance_drive()
                existing_file_id = await asyncio.to_thread(
                    self._find_existing_file_id,
                    drive_service,
                    file_sha256,
                )

                if existing_file_id:
                    await asyncio.to_thread(self._ensure_public_permission, drive_service, existing_file_id)
                    self.logger.info("Reusing existing Drive file %s for %s", existing_file_id, file_path)
                    return "%s%s" % (DRIVE_BASE_FILE_UPLOAD_URL, existing_file_id)

                file_metadata = {
                    'name': file_path.name,
                    'parents': [self.drive_folder_id],
                    'appProperties': {
                        'sha256': file_sha256,
                    },
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
                await asyncio.to_thread(self._ensure_public_permission, drive_service, file_id)

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

    def _calculate_sha256(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as file_handle:
            while True:
                chunk = file_handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _find_existing_file_id(self, drive_service, file_sha256: str) -> str | None:
        query = (
            f"'{self.drive_folder_id}' in parents and trashed = false "
            f"and appProperties has {{ key='sha256' and value='{file_sha256}' }}"
        )
        response = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id)',
            pageSize=1,
        ).execute()
        files = response.get('files', [])
        if not files:
            return None
        return files[0].get('id')

    def _ensure_public_permission(self, drive_service, file_id: str) -> None:
        permissions = drive_service.permissions().list(
            fileId=file_id,
            fields='permissions(id,type,role)',
        ).execute()
        existing_permissions = permissions.get('permissions', [])
        if any(
            permission.get('type') == 'anyone' and permission.get('role') == 'reader'
            for permission in existing_permissions
        ):
            return

        drive_service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'},
            fields='id'
        ).execute()
