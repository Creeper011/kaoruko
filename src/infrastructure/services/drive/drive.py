import os
import time
import asyncio
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class Drive():
    """Google Drive Utils"""
    
    def __init__(self, folder, drive_path) -> None:
        logger.debug(f"Initializing Drive with folder='{folder}', drive_path='{drive_path}'")
        self.folder = folder
        self.drive_path = drive_path
        self.drive = None
        self._lock = asyncio.Lock()
        logger.debug("Drive instance initialized successfully")
    
    async def _ensure_drive_connection(self):
        """Ensures that the Drive connection is established"""
        logger.debug("Ensuring Drive connection")
        if self.drive is None:
            logger.debug("No existing Drive connection, acquiring lock")
            async with self._lock:
                if self.drive is None:
                    logger.debug("Creating new Drive connection")
                    self.drive = await self._login_to_drive_async()
                    logger.debug("Drive connection established successfully")
        else:
            logger.debug("Using existing Drive connection")
        return self.drive
    
    def _login_to_drive_sync(self):
        """Synchronous version of login to use with run_in_executor"""
        logger.debug(f"Attempting to login to Drive with credentials: {self.drive_path}")
        if os.path.exists(self.drive_path):
            try:
                logger.debug("Loading service account credentials")
                creds = service_account.Credentials.from_service_account_file(self.drive_path, scopes=["https://www.googleapis.com/auth/drive.file"])
                logger.debug("Building Drive service")
                drive_service = build('drive', 'v3', credentials=creds)
                logger.debug("Drive service built successfully")
                return drive_service
            except Exception as e:
                logger.error(f"Error loading Drive credentials: {e}")
                logger.debug(f"Drive login error details: {type(e).__name__}: {e}")
                raise FileNotFoundError(f"Invalid Drive credentials: {e}")
        else:
            logger.error(f"DrivePath not found: {self.drive_path}")
            raise FileNotFoundError(f"DrivePath not found: {self.drive_path}")
    
    async def _login_to_drive_async(self):
        """Async version of login"""
        logger.debug("Starting async Drive login")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._login_to_drive_sync)
        logger.debug("Async Drive login completed")
        return result
    
    def _upload_to_drive_sync(self, file, folder_id=None):
        """Synchronous version of upload to use with run_in_executor"""
        logger.debug(f"Starting sync upload of file: {file}")
        if not os.path.exists(file):
            logger.error(f"File not found: {file}")
            raise FileNotFoundError(f"File not found: {file}")
            
        if folder_id is None:
            folder_id = "1V4SV5RyMPztclV55xRZIIol874-se-1n" 
            logger.debug(f"Using default folder_id: {folder_id}")
        else:
            logger.debug(f"Using provided folder_id: {folder_id}")

        file_metadata = {
            'name': os.path.basename(file),
            'parents': [folder_id]
        }
        logger.debug(f"File metadata: {file_metadata}")
        media = MediaFileUpload(file)
        logger.debug("Media file upload object created")

        max_retry_count = 3
        retry_count = 0
        logger.debug(f"Starting upload with max retry count: {max_retry_count}")

        while retry_count < max_retry_count:
            try:
                logger.info(f"Uploading file to Drive: {os.path.basename(file)}")
                logger.debug(f"Upload attempt {retry_count + 1}/{max_retry_count}")
                file = self.drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
                file_id = file.get('id')
                logger.debug(f"File created with ID: {file_id}")
                
                logger.debug("Setting file permissions to public read")
                self.drive.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
                drive_link = f'https://drive.google.com/file/d/{file_id}/view'
                logger.info(f"Successfully uploaded to Drive: {drive_link}")
                logger.debug(f"Upload completed successfully on attempt {retry_count + 1}")
                return drive_link
            except Exception as e:
                retry_count += 1
                logger.warning(f'Error uploading to Drive. Attempt {retry_count}. Error: {e}')
                logger.debug(f"Upload error details: {type(e).__name__}: {e}")
                if retry_count < max_retry_count:
                    try:
                        logger.debug("Attempting to re-login to Drive")
                        self.drive = self._login_to_drive_sync()  # Create new session
                        logger.debug("Waiting 2 seconds before retry")
                        time.sleep(2)
                    except Exception as login_error:
                        logger.error(f"Failed to re-login to Drive: {login_error}")
                        logger.debug(f"Re-login error details: {type(login_error).__name__}: {login_error}")
                        raise e
                else:
                    logger.error(f"Failed to upload to Drive after {max_retry_count} attempts")
                    raise e

    async def uploadToDrive(self, file, folder_id=None):
        """Async upload to Google Drive.
        file: the path of the file to upload
        folder_id: the ID of the folder to upload the file to"""
        logger.debug(f"Starting async upload of file: {file}")
        await self._ensure_drive_connection()
        loop = asyncio.get_event_loop()
        logger.debug("Submitting upload task to executor")
        result = await loop.run_in_executor(None, self._upload_to_drive_sync, file, folder_id)
        logger.debug(f"Async upload completed: {result}")
        return result

    def _upload_folder_sync(self, path):
        """Synchronous version of folder upload to use with run_in_executor"""
        parent_folder_id = "1V4SV5RyMPztclV55xRZIIol874-se-1n"  # Parent folder ID
        folder_name = os.path.basename(path)
        
        # Create the new folder in Drive and get its ID
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        folder = self.drive.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        
        if not os.path.isdir(path):
            raise ValueError("The path provided is not a directory.")
        
        # Iterate over all files in the folder
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                self._upload_to_drive_sync(file_path, folder_id)
        
        # Return the link to the new folder
        return f'https://drive.google.com/drive/folders/{folder_id}'

    async def uploadFolder(self, path):
        """Async upload of all files in a folder to Google Drive and returns the folder link.
        path: the path of the folder to upload"""
        
        await self._ensure_drive_connection()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._upload_folder_sync, path)

    def _delete_all_files_sync(self, folder_id=None):
        """Synchronous version of deletion to use with run_in_executor"""
        query = "trashed=false"
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            logger.info("No files found to delete.")
            return

        for file in files:
            try:
                self.drive.files().delete(fileId=file['id']).execute()
                logger.info(f"Deleted: {file['name']}")
            except Exception as e:
                logger.error(f"Error deleting {file['name']}: {e}")

        logger.info("All files have been deleted.")

    async def deleteAllFiles(self, folder_id=None):
        """Deletes ALL files from Google Drive asynchronously (without sending to trash)."""
        
        await self._ensure_drive_connection()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._delete_all_files_sync, folder_id)
