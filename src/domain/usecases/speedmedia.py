import asyncio
import os
import shutil
import time
import mimetypes
import logging
from pathlib import Path
import uuid
from discord import Attachment
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from src.domain.entities.speedmedia_entity import SpeedMediaResult
from src.domain.exceptions.speedmedia_exceptions import GenericError, FailedToUploadDrive, InvalidFileType
from src.infrastructure.services.speed import VideoSpeedService, AudioSpeedService
from src.infrastructure.services.drive import Drive

logger = logging.getLogger(__name__)

class SpeedMedia:
    def __init__(self):
        self.audio_service = AudioSpeedService()
        self.video_service = VideoSpeedService()
        self.drive = Drive("")
        self.session_id = str(uuid.uuid4())
        self.temp_dir = Path("temp/speed_control")
        self.max_file_size = 120 * 1024 * 1024

        self.audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']
        self.video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']

    def _cleanup(self) -> bool:
        try:
            session_path = self.temp_dir / self.session_id
            if session_path.exists():
                shutil.rmtree(session_path)
            logger.debug("Temporary files cleaned up.")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
            return False

    def _create_temp_directory(self) -> str:
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        return str(self.temp_dir)

    def _create_session_temp_directory(self) -> str:
        session_temp_dir = self.temp_dir / self.session_id
        if not session_temp_dir.exists():
            session_temp_dir.mkdir()
        return str(session_temp_dir)

    def _resolve_format(self, file_path: str) -> str:
        """Resolve file format based on MIME type with fallback to extension"""
        mime_type, _ = mimetypes.guess_type(file_path)
        logger.debug(f"Resolving format for {file_path}, guessed MIME type: {mime_type}")

        if mime_type:
            if mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'

        file_ext = Path(file_path).suffix.lower()
        if file_ext in self.audio_extensions:
            return 'audio'
        elif file_ext in self.video_extensions:
            return 'video'
        else:
            return 'unknown'

    def preserve_metadata(self, original_path: str, processed_path: str):
        """Preserve metadata between original and processed files"""
        try:
            original_ext = Path(original_path).suffix.lower()
            processed_ext = Path(processed_path).suffix.lower()
            
            if original_ext == '.mp3' and processed_ext == '.mp3':
                original_audio = MP3(original_path, ID3=ID3)
                processed_audio = MP3(processed_path, ID3=ID3)
                if original_audio.tags:
                    for key, value in original_audio.tags.items():
                        processed_audio.tags[key] = value
                    processed_audio.save()
                    logger.debug("MP3 metadata preserved.")

            elif original_ext == '.mp4' and processed_ext == '.mp4':
                original_audio = MP4(original_path)
                processed_audio = MP4(processed_path)
                if original_audio.tags:
                    for key, value in original_audio.tags.items():
                        processed_audio.tags[key] = value
                    processed_audio.save()
                    logger.debug("MP4 metadata preserved.")

            elif original_ext == '.flac' and processed_ext == '.flac':
                original_audio = FLAC(original_path)
                processed_audio = FLAC(processed_path)
                for key, value in original_audio.items():
                    processed_audio[key] = value
                processed_audio.save()
                logger.debug("FLAC metadata preserved.")

        except Exception as e:
            logger.debug(f"Warning: Could not preserve metadata: {e}")

    async def change_speed_attachment(self, attachment: Attachment, speed: float, preserve_pitch: bool) -> SpeedMediaResult:
        start_time = time.time()
        try:
            temp_input = f"temp_{attachment.id}_{attachment.filename}"
            await attachment.save(temp_input)
            logger.debug(f"Attachment saved to {temp_input}")

            result = await self.change_speed(temp_input, speed, preserve_pitch)

            if os.path.exists(temp_input):
                os.remove(temp_input)
                logger.debug(f"Temporary file {temp_input} removed.")

            result.elapsed = time.time() - start_time
            return result

        except (GenericError, FailedToUploadDrive, InvalidFileType) as e:
            logger.debug(f"Specific error changing speed for attachment {attachment.filename}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
        except Exception as e:
            logger.debug(f"Unexpected error changing speed for attachment {attachment.filename}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)


    async def change_speed(self, file_path: str, speed: float, preserve_pitch: bool, not_upload_to_drive: bool = None) -> SpeedMediaResult:
        start_time = time.time()

        session_path = self._create_session_temp_directory()

        output_path = f"{speed}x - {os.path.basename(os.path.splitext(file_path)[0])}.{os.path.splitext(file_path)[1]}"
        output_path = os.path.join(session_path, output_path)

        try:
            file_format = self._resolve_format(file_path)
            logger.debug(f"File format resolved as {file_format}")

            if file_format == 'audio':
                success, error, output_path = await asyncio.to_thread(self.audio_service.process, Path(file_path), Path(output_path), speed, preserve_pitch)
            elif file_format == 'video':
                success, error, output_path = await asyncio.to_thread(self.video_service.process, Path(file_path), Path(output_path), speed, preserve_pitch)
            else:
                raise InvalidFileType(f"Unsupported file type for file: {file_path}")

            if not success:
                raise GenericError(f"Speed change failed: {error}")

            self.preserve_metadata(file_path, output_path)

            file_size = os.path.getsize(output_path)
            drive_path = None

            if not_upload_to_drive is None or not_upload_to_drive is False:
                if file_size > self.max_file_size:
                    try:
                        drive_path = await self.drive.uploadToDrive(output_path)
                        logger.debug(f"File uploaded to Drive (size: {file_size / 1024 / 1024:.2f}MB): {drive_path}")
                    except Exception as e:
                        raise FailedToUploadDrive(f"Failed to upload {output_path} to Drive: {e}")

                return SpeedMediaResult(file_path=output_path, drive_path=drive_path, elapsed=time.time() - start_time)

            return SpeedMediaResult(file_path=output_path, elapsed=time.time() - start_time)
        
        except (GenericError, FailedToUploadDrive, InvalidFileType) as e:
            logger.debug(f"Specific error processing file {file_path}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
        except Exception as e:
            logger.debug(f"Unexpected error processing file {file_path}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
